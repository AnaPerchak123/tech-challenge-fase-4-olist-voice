"""Prepara as avaliações da Olist para indexação RAG.

Uso: python preparar_base.py
Ou:  python preparar_base.py --input "caminho/archive.zip"
Não usa API, não gera embeddings e não altera a fonte.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import platform
import re
import sys
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


COLUNAS = [
    "review_id", "order_id", "review_score", "review_comment_title",
    "review_comment_message", "review_creation_date", "review_answer_timestamp",
]
NOME_CSV = "olist_order_reviews_dataset.csv"
VERSAO_PREPARACAO = "1.0.0"


def limpar_texto(valor: str) -> str:
    """Preserva caixa, acentos, negações e pontuação; normaliza ruídos leves."""
    texto = unicodedata.normalize("NFC", html.unescape(valor))
    texto = re.sub(r"</?(?:br|p|div|span|b|strong|i|em)\b[^>]*>", " ", texto, flags=re.I)
    texto = "".join(" " if unicodedata.category(c).startswith("C") else c for c in texto)
    return re.sub(r"\s+", " ", texto).strip()


def ler_fonte(caminho: Path) -> tuple[pd.DataFrame, str, str]:
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}\n"
            f"Coloque {NOME_CSV} em data/raw/ ou use --input com o caminho do CSV/ZIP."
        )
    if caminho.suffix.lower() == ".zip":
        with zipfile.ZipFile(caminho) as arquivo:
            nomes = [n for n in arquivo.namelist() if Path(n).name == NOME_CSV]
            if len(nomes) != 1:
                raise ValueError(f"O ZIP deve conter exatamente um arquivo chamado {NOME_CSV}.")
            conteudo = arquivo.read(nomes[0])
            origem = f"{caminho.name}::{nomes[0]}"
    else:
        conteudo = caminho.read_bytes()
        origem = caminho.name
    dados = pd.read_csv(io.BytesIO(conteudo), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    faltantes = sorted(set(COLUNAS) - set(dados.columns))
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(faltantes)}")
    return dados[COLUNAS].copy(), hashlib.sha256(conteudo).hexdigest(), origem


def preparar(caminho: Path, raiz: Path) -> dict:
    dados, fonte_hash, origem = ler_fonte(caminho)
    total = len(dados)
    ausentes = {c: int(dados[c].str.strip().eq("").sum()) for c in COLUNAS}
    ids_repetidos = int(dados.loc[dados.review_id.str.strip().ne(""), "review_id"].value_counts().gt(1).sum())

    # Duplicação exata é definida pelos SETE campos originais, antes da limpeza.
    duplicadas = dados.duplicated(subset=COLUNAS, keep="first")
    qtde_duplicadas = int(duplicadas.sum())
    dados = dados.loc[~duplicadas].copy()
    # Índice do registro lógico no CSV, não o número de linha física do arquivo.
    dados["source_record_index"] = dados.index + 1
    dados["document_id"] = [
        "olist_" + hashlib.sha256(
            json.dumps(list(valores), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        for valores in dados[COLUNAS].itertuples(index=False, name=None)
    ]
    titulo = dados.review_comment_title.map(limpar_texto)
    mensagem = dados.review_comment_message.map(limpar_texto)
    dados["text"] = (titulo + " " + mensagem).str.strip()
    sem_texto = dados.text.eq("")
    qtde_sem_texto = int(sem_texto.sum())
    dados = dados.loc[~sem_texto].copy()

    sem_identificador = dados.review_id.str.strip().eq("") | dados.order_id.str.strip().eq("")
    qtde_sem_identificador = int(sem_identificador.sum())
    dados = dados.loc[~sem_identificador].copy()
    if dados.empty:
        raise ValueError("Nenhuma avaliação com texto e identificadores restou após a preparação.")

    notas = pd.to_numeric(dados.review_score, errors="coerce")
    notas_validas = notas.isin([1, 2, 3, 4, 5])
    dados["score"] = notas.where(notas_validas).astype("Int64")
    datas = pd.to_datetime(dados.review_creation_date, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    dados["review_date"] = datas.dt.strftime("%Y-%m-%dT%H:%M:%S").where(datas.notna(), None)
    dados["text_length"] = dados.text.str.len()
    assert dados.document_id.is_unique, "IDs técnicos devem ser únicos."
    assert total == qtde_duplicadas + qtde_sem_texto + qtde_sem_identificador + len(dados)

    pasta_dados = raiz / "data" / "processed"
    pasta_relatorios = raiz / "outputs"
    pasta_dados.mkdir(parents=True, exist_ok=True)
    pasta_relatorios.mkdir(parents=True, exist_ok=True)
    dados.to_csv(pasta_dados / "reviews_prepared.csv", index=False, encoding="utf-8-sig")
    documentos = dados[["document_id", "review_id", "order_id", "score", "review_date", "text", "source_record_index"]].rename(columns={"score": "review_score"})
    documentos.to_json(pasta_dados / "documents.jsonl", orient="records", lines=True, force_ascii=False)

    relatorio = {
        "preparation_version": VERSAO_PREPARACAO,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": origem,
        "source_csv_sha256": fonte_hash,
        "source_url": "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
        "runtime": {"python": platform.python_version(), "pandas": pd.__version__},
        "sampling": "none; all eligible textual reviews",
        "rows_original": total,
        "missing_by_column_original": ausentes,
        "review_ids_with_multiple_rows_original": ids_repetidos,
        "rows_removed_exact_duplicates": qtde_duplicadas,
        "rows_removed_no_text_after_dedup": qtde_sem_texto,
        "rows_removed_missing_id_after_text_filter": qtde_sem_identificador,
        "documents_final": len(dados),
        "rows_with_invalid_or_missing_score_final": int((~notas_validas).sum()),
        "rows_with_unparsed_review_date_final": int(datas.isna().sum()),
        "review_date_min": datas.min().isoformat() if datas.notna().any() else None,
        "review_date_max": datas.max().isoformat() if datas.notna().any() else None,
        "score_distribution_final": {str(int(k)): int(v) for k, v in dados.score.value_counts().sort_index().items()},
        "text_length_characters": {"min": int(dados.text_length.min()), "median": float(dados.text_length.median()), "p95": float(dados.text_length.quantile(.95)), "max": int(dados.text_length.max())},
        "document_unit": "one eligible review per document; token limit must be checked before embedding",
        "rules": [
            "Exclude exact duplicates over the seven raw columns, then empty cleaned text, then missing IDs.",
            "Retain distinct records with a repeated review_id; generate a content-derived document_id.",
            "Retain repeated text across distinct reviews; do not interpret text repetition as record duplication.",
            "Use title and message; normalize Unicode, basic HTML, controls and whitespace.",
            "Preserve sentiment, negation, accents, case and punctuation; no lowercasing or stopword removal.",
            "Do not infer purchase date, delivery outcome or sentiment class from review date or score.",
            "No API calls or embeddings occur in this preparation step.",
        ],
    }
    (pasta_relatorios / "data_quality.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    distribuicao = "\n".join(f"| {nota} | {qtde:,} |" for nota, qtde in relatorio["score_distribution_final"].items())
    texto_relatorio = f"""# Preparação da base Olist — resultado executado

| Indicador | Quantidade |
| --- | ---: |
| Registros originais | {total:,} |
| Duplicatas exatas removidas | {qtde_duplicadas:,} |
| Registros sem texto removidos após deduplicação | {qtde_sem_texto:,} |
| Registros sem identificador removidos após filtro de texto | {qtde_sem_identificador:,} |
| Documentos finais | {len(dados):,} |
| Valores de review_id presentes em mais de uma linha original | {ids_repetidos:,} |

Contagens separadas por vírgula para milhar. As remoções são sequenciais e reconciliam com o total original.

## Distribuição das notas nos documentos finais

| Nota | Documentos |
| --- | ---: |
{distribuicao}

## Decisões e limites

- Todos os registros elegíveis foram preparados; não houve amostragem.
- Um documento corresponde a uma avaliação textual elegível, combinando título e mensagem.
- review_id repetido não basta para excluir um registro. O ID técnico usa SHA-256 dos sete campos originais serializados.
- Comentários curtos e notas baixas são preservados. Registros distintos com o mesmo texto também são preservados.
- O texto é normalizado sem remover acentos, negações ou pontuação. Os campos originais permanecem no CSV preparado.
- A data corresponde à criação da avaliação, não à compra. Nota não é rótulo de sentimento do texto.
- A distribuição acima descreve apenas avaliações com texto e identificadores, não todos os pedidos ou clientes.
- O limite de tokens é verificado pelo processo de indexação.
- Os dados preparados contêm relatos brutos e não passaram por anonimização adicional nesta etapa. São arquivos locais excluídos do Git; revisar trechos antes de publicar ou enviar ao LLM.
- O relatório cobre a preparação; recuperação e geração são avaliadas separadamente.

## Reprodução

Origem: {origem}

SHA-256 do CSV de origem: `{fonte_hash}`

Versão da preparação: {VERSAO_PREPARACAO}. Python: {platform.python_version()}. pandas: {pd.__version__}.

Executar `python preparar_base.py` a partir do projeto, usando o ambiente virtual configurado. O JSON contém parâmetros, ausentes por coluna, intervalo de datas e comprimentos de texto.
"""
    (pasta_relatorios / "preparacao_base.md").write_text(texto_relatorio, encoding="utf-8")
    return relatorio


def main() -> int:
    raiz = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Preparar avaliações da Olist para RAG, sem alterar a fonte.")
    parser.add_argument("--input", type=Path, default=raiz / "data" / "raw" / NOME_CSV, help="CSV ou ZIP da Olist")
    args = parser.parse_args()
    try:
        relatorio = preparar(args.input, raiz)
    except (FileNotFoundError, ValueError, zipfile.BadZipFile, pd.errors.ParserError) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1
    print("Preparação concluída.")
    print(f"Registros originais: {relatorio['rows_original']:,}")
    print(f"Duplicatas exatas removidas: {relatorio['rows_removed_exact_duplicates']:,}")
    print(f"Registros sem texto: {relatorio['rows_removed_no_text_after_dedup']:,}")
    print(f"Documentos finais: {relatorio['documents_final']:,}")
    print("Arquivos preparados: data/processed/")
    print("Relatórios: outputs/data_quality.json e outputs/preparacao_base.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
