"""Componentes reutilizáveis da indexação e recuperação semântica da Olist."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def carregar_modelo(nome=MODELO, revisao=None):
    try:
        import torch
        from sentence_transformers import SentenceTransformer
    except ImportError as erro:
        raise RuntimeError("Instale as dependências de requirements.txt no ambiente do projeto.") from erro
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    return SentenceTransformer(nome, revision=revisao, device="cpu", trust_remote_code=False)


def abrir_banco(pasta):
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError as erro:
        raise RuntimeError("Instale chromadb pelo arquivo requirements.txt.") from erro
    return chromadb.PersistentClient(path=str(pasta), settings=Settings(anonymized_telemetry=False))


def dividir_texto(texto, tokenizer, max_tokens, overlap=20):
    """Recorta o texto ORIGINAL por offsets para não truncar tokens silenciosamente."""
    limite = int(max_tokens) - tokenizer.num_special_tokens_to_add(pair=False)
    if limite < 2:
        raise ValueError("Limite de tokens inválido.")
    codificado = tokenizer(texto, add_special_tokens=False, truncation=False, return_offsets_mapping=True, verbose=False)
    offsets = codificado["offset_mapping"]
    if len(offsets) <= limite:
        return [texto], len(offsets) + tokenizer.num_special_tokens_to_add(pair=False)
    partes = []
    inicio = 0
    while inicio < len(offsets):
        fim = min(inicio + limite, len(offsets))
        parte = texto[offsets[inicio][0]:offsets[fim - 1][1]].strip()
        while len(tokenizer(parte, add_special_tokens=True, truncation=False, verbose=False)["input_ids"]) > max_tokens:
            fim -= 1
            if fim <= inicio:
                raise ValueError("Não foi possível dividir um documento respeitando o limite de tokens.")
            parte = texto[offsets[inicio][0]:offsets[fim - 1][1]].strip()
        partes.append(parte)
        if fim == len(offsets):
            break
        inicio = max(inicio + 1, fim - min(overlap, max(0, limite // 4)))
    return partes, len(offsets) + tokenizer.num_special_tokens_to_add(pair=False)


def montar_unidades(documentos, modelo):
    unidades = []
    divididos = 0
    maior = 0
    for doc in documentos:
        partes, tamanho = dividir_texto(doc["text"], modelo.tokenizer, modelo.max_seq_length)
        maior = max(maior, tamanho)
        divididos += len(partes) > 1
        for numero, parte in enumerate(partes):
            meta = {"parent_id": doc["document_id"], "review_id": doc["review_id"],
                    "order_id": doc["order_id"], "chunk_id": numero, "chunks_in_review": len(partes)}
            if doc.get("review_score") is not None:
                meta["review_score"] = int(doc["review_score"])
            if doc.get("review_date"):
                meta["review_date"] = doc["review_date"]
            unidades.append({"id": f"{doc['document_id']}_c{numero:03d}", "text": parte, "metadata": meta})
    return unidades, {"reviews_split": divididos, "max_review_tokens_with_special_tokens": maior,
                      "model_max_tokens": int(modelo.max_seq_length), "chunk_overlap_tokens": 20}


def selecionar_resultados(resultado, top_k):
    """Evita repetir a mesma avaliação ou o mesmo texto no contexto."""
    fontes = []
    pais = set()
    textos = set()
    for doc_id, texto, meta, distancia in zip(
        resultado["ids"][0], resultado["documents"][0],
        resultado["metadatas"][0], resultado["distances"][0],
    ):
        chave_texto = " ".join(texto.casefold().split())
        if meta["parent_id"] in pais or chave_texto in textos:
            continue
        pais.add(meta["parent_id"])
        textos.add(chave_texto)
        fontes.append({"document_id": doc_id, "text": texto, "metadata": meta,
                       "cosine_distance": float(distancia), "cosine_similarity": 1.0 - float(distancia)})
        if len(fontes) >= top_k:
            break
    return fontes


class BuscaSemantica:
    def __init__(self, raiz: Path):
        self.raiz = Path(raiz)
        manifesto = self.raiz / "chroma_db" / "active_index.json"
        if not manifesto.is_file():
            raise FileNotFoundError("Índice ativo ausente. Execute criar_indice.py primeiro.")
        self.info = json.loads(manifesto.read_text(encoding="utf-8"))
        if self.info.get("status") != "ready":
            raise ValueError("A construção do índice ainda não terminou.")
        self.modelo = carregar_modelo(self.info["model"], self.info.get("model_revision"))
        self.banco = abrir_banco(self.raiz / "chroma_db")
        self.colecao = self.banco.get_collection(self.info["collection"], embedding_function=None)
        if self.colecao.count() != self.info["indexed_units"]:
            raise ValueError("Contagem do índice difere do manifesto; execute criar_indice.py novamente.")

    def buscar(self, pergunta: str, top_k=5, notas=None):
        pergunta = " ".join(pergunta.split())
        if not pergunta:
            raise ValueError("Digite uma pergunta não vazia.")
        if not 1 <= top_k <= 20:
            raise ValueError("top_k deve estar entre 1 e 20.")
        if len(self.modelo.tokenizer(pergunta, truncation=False, verbose=False)["input_ids"]) > self.modelo.max_seq_length:
            raise ValueError("Pergunta longa demais para o modelo. Reformule de forma mais curta.")
        filtro = None
        if notas is not None:
            if not notas or any(n not in [1, 2, 3, 4, 5] for n in notas):
                raise ValueError("Informe notas entre 1 e 5.")
            filtro = {"review_score": {"$in": sorted(set(notas))}}
            elegiveis = self.colecao.get(where=filtro, limit=1, include=[])["ids"]
            if not elegiveis:
                return []
        vetor = self.modelo.encode([pergunta], normalize_embeddings=True, show_progress_bar=False)
        # Busca candidatos adicionais para permitir deduplicação do contexto.
        parametros = {"query_embeddings": vetor.tolist(), "n_results": min(top_k * 4, self.colecao.count()),
                      "include": ["documents", "metadatas", "distances"]}
        if filtro is not None:
            parametros["where"] = filtro
        resultado = self.colecao.query(**parametros)
        return selecionar_resultados(resultado, top_k)
