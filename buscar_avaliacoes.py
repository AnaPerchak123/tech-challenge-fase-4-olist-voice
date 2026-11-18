"""Consulta o índice semântico e apresenta as avaliações recuperadas."""
from __future__ import annotations
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from busca_semantica import BuscaSemantica


def main():
    parser = argparse.ArgumentParser(description="Buscar avaliações por significado, com fontes e filtro opcional.")
    parser.add_argument("pergunta")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--notas", nargs="+", type=int)
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parent
    try:
        print("Carregando índice e modelo...", flush=True)
        motor = BuscaSemantica(raiz)
        inicio = time.perf_counter()
        fontes = motor.buscar(args.pergunta, args.top_k, args.notas)
        segundos = time.perf_counter() - inicio
        print(f"\nPergunta: {args.pergunta}")
        print(f"Avaliações no índice ativo: {motor.info['selected_reviews']:,}")
        if motor.info["sampling"] != "none":
            print("ATENÇÃO: este índice usa uma amostra de desenvolvimento.")
        if not fontes:
            print("Nenhuma avaliação encontrada para os filtros informados.")
        for numero, fonte in enumerate(fontes, 1):
            meta = fonte["metadata"]
            print(f"\n[E{numero}] Nota: {meta.get('review_score', 'ausente')} | Similaridade: {fonte['cosine_similarity']:.3f}")
            print(f"review_id: {meta['review_id']}")
            print(f"document_id: {fonte['document_id']}")
            print(fonte["text"])
        print(f"\nTempo da busca (após carregar modelo): {segundos:.2f}s")
        print("Similaridade não é probabilidade de acerto. Revise a relevância das fontes.")
        print("Os resultados são candidatos; sua existência não prova que respondam à pergunta.")
        saida = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "question": args.pergunta,
                 "filters": {"scores": args.notas}, "top_k": args.top_k, "query_seconds": segundos,
                 "index_collection": motor.info["collection"], "indexed_reviews": motor.info["selected_reviews"],
                 "sampling": motor.info["sampling"], "sources": fontes}
        (raiz / "outputs").mkdir(exist_ok=True)
        (raiz / "outputs" / "ultima_busca.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as erro:
        print(f"ERRO ({type(erro).__name__}): {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
