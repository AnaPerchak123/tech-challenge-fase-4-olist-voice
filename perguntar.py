"""Executa o RAG pelo terminal, com resposta e fontes."""
import argparse
from pathlib import Path
from busca_semantica import BuscaSemantica
from config_api import carregar_config, erro_seguro
from rag_llm import responder, salvar_execucao, formatar_resposta


def main():
    parser = argparse.ArgumentParser(description="Consultar avaliações com RAG e evidências.")
    parser.add_argument("pergunta")
    parser.add_argument("--notas", nargs="+", type=int)
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parent
    chave = ""
    try:
        config = carregar_config(raiz)
        chave = config.api_key
        print("Carregando busca semântica...", flush=True)
        motor = BuscaSemantica(raiz)
        resultado = responder(args.pergunta, motor, raiz, notas=args.notas, config=config)
        print("\n" + formatar_resposta(resultado))
        for f in resultado["sources_sent_to_llm"]:
            print(f"\n[{f['label']}] Nota {f['metadata'].get('review_score')} | review_id {f['metadata']['review_id']}")
            print(f["text"])
        salvar_execucao(resultado, raiz)
        print("\nExecução registrada em outputs/rag_runs/.")
        return 0
    except Exception as erro:
        print("ERRO:", erro_seguro(erro, chave))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
