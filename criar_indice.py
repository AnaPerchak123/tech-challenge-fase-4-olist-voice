"""Gera embeddings e persiste índice Chroma; retoma lotes após interrupção."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from busca_semantica import MODELO, abrir_banco, carregar_modelo, montar_unidades


def criar(raiz, limite=None, batch_size=32, lote_indice=256, seed=42):
    inicio = time.perf_counter()
    fonte = raiz / "data" / "processed" / "documents.jsonl"
    if not fonte.is_file():
        raise FileNotFoundError("Execute preparar_base.py antes: falta data/processed/documents.jsonl.")
    conteudo = fonte.read_bytes()
    documentos = [json.loads(linha) for linha in conteudo.decode("utf-8").splitlines() if linha.strip()]
    if not documentos:
        raise ValueError("O arquivo de documentos está vazio.")
    if len({d["document_id"] for d in documentos}) != len(documentos):
        raise ValueError("O arquivo de documentos contém IDs duplicados; revise a preparação.")
    total = len(documentos)
    if limite is not None:
        if limite < 1:
            raise ValueError("--limit deve ser positivo.")
        documentos = random.Random(seed).sample(documentos, min(limite, total))
    print(f"Avaliações selecionadas: {len(documentos):,} de {total:,}", flush=True)
    print("Carregando modelo multilíngue. Na primeira vez será necessário baixá-lo.", flush=True)
    modelo = carregar_modelo()
    revisao = getattr(modelo[0].auto_model.config, "_commit_hash", None)
    print("Conferindo tokens e dividindo apenas textos que excedam o limite...", flush=True)
    unidades, tokens = montar_unidades(documentos, modelo)
    config = {"schema_version": 1, "model": MODELO, "model_revision": revisao,
              "source_documents_sha256": hashlib.sha256(conteudo).hexdigest(),
              "selected_reviews": len(documentos), "sampling_seed": seed if limite is not None else None,
              "sampling": "random_without_replacement" if len(documentos) < total else "none",
              "max_seq_length": int(modelo.max_seq_length), "normalize_embeddings": True,
              "distance_metric": "cosine", "chunk_overlap_tokens": 20}
    identidade = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:24]
    nome = f"olist_reviews_{identidade}"
    banco = abrir_banco(raiz / "chroma_db")
    colecao = banco.get_or_create_collection(name=nome, embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}}, metadata={"config_sha256_prefix": identidade, "model": MODELO})
    print(f"Unidades para indexação: {len(unidades):,}. Persistência em chroma_db/.", flush=True)
    gerados = 0
    for posicao in range(0, len(unidades), lote_indice):
        lote = unidades[posicao:posicao + lote_indice]
        existentes = set(colecao.get(ids=[u["id"] for u in lote], include=[])["ids"])
        pendentes = [u for u in lote if u["id"] not in existentes]
        if pendentes:
            vetores = modelo.encode([u["text"] for u in pendentes], batch_size=batch_size,
                                    normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)
            colecao.upsert(ids=[u["id"] for u in pendentes], embeddings=vetores.tolist(),
                           documents=[u["text"] for u in pendentes], metadatas=[u["metadata"] for u in pendentes])
            gerados += len(pendentes)
        concluidos = min(posicao + lote_indice, len(unidades))
        print(f"Progresso: {concluidos:,}/{len(unidades):,} ({100 * concluidos / len(unidades):.1f}%)", flush=True)
    if colecao.count() != len(unidades):
        raise ValueError("Contagem final inconsistente. Execute novamente para retomar a construção.")
    info = {**config, **tokens, "status": "ready", "collection": nome,
            "available_reviews": total, "indexed_units": colecao.count(),
            "embedding_dimension": (modelo.get_embedding_dimension() if hasattr(modelo, "get_embedding_dimension") else modelo.get_sentence_embedding_dimension()),
            "new_embeddings_this_run": gerados, "seconds_this_run": round(time.perf_counter() - inicio, 3),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
            "packages": {p: importlib.metadata.version(p) for p in ["sentence-transformers", "chromadb", "torch", "transformers"]}}
    pasta = raiz / "chroma_db"
    temporario = pasta / "active_index.tmp"
    temporario.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporario.replace(pasta / "active_index.json")
    (raiz / "outputs").mkdir(exist_ok=True)
    (raiz / "outputs" / "index_summary.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Índice concluído: {len(documentos):,} avaliações; {len(unidades):,} unidades vetoriais.", flush=True)
    print("Resumo salvo em outputs/index_summary.json", flush=True)
    return info


def main():
    parser = argparse.ArgumentParser(description="Criar índice semântico local para as avaliações preparadas.")
    parser.add_argument("--limit", type=int, help="Amostra aleatória para teste inicial; omitir para usar toda a base.")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size deve ser positivo.")
    try:
        criar(Path(__file__).resolve().parent, args.limit, args.batch_size)
    except KeyboardInterrupt:
        print("\nInterrompido. Reexecute o mesmo comando para retomar os lotes persistidos.", file=sys.stderr)
        return 130
    except Exception as erro:
        print(f"ERRO ({type(erro).__name__}): {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
