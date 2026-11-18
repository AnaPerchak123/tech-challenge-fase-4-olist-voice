"""Verifica arquivos do projeto e registra o ambiente de execução."""
from pathlib import Path
import importlib.metadata
import json
import platform
import sys


def main():
    raiz = Path(__file__).resolve().parent
    obrigatorios = ["preparar_base.py", "criar_indice.py", "busca_semantica.py", "buscar_avaliacoes.py",
        "config_api.py", "rag_llm.py", "testar_api.py", "perguntar.py", "app.py", "avaliar.py",
        "README.md", "requirements.txt", ".gitignore", ".env.example", "docs/arquitetura.md",
        "docs/decisoes_tecnicas.md", "docs/avaliacao.md"]
    faltantes = [n for n in obrigatorios if not (raiz / n).is_file()]
    versoes = {}
    for nome in ["pandas", "sentence-transformers", "chromadb", "torch", "transformers", "google-genai", "streamlit", "python-dotenv", "pydantic"]:
        try: versoes[nome] = importlib.metadata.version(nome)
        except importlib.metadata.PackageNotFoundError: versoes[nome] = "not installed"
    artefatos = {}
    for nome in ["data_quality.json", "index_summary.json", "api_test.json", "evaluation_metrics.json"]:
        caminho = raiz / "outputs" / nome
        artefatos[nome] = json.loads(caminho.read_text(encoding="utf-8")) if caminho.is_file() else None
    exemplo = raiz / ".env.example"
    exemplo_ok = False
    if exemplo.is_file():
        valores = [l.partition("=")[2].strip().strip("\"'") for l in exemplo.read_text(encoding="utf-8-sig").splitlines() if l.strip().startswith("GEMINI_API_KEY=")]
        exemplo_ok = len(valores) == 1 and valores[0] in {"", "cole_sua_chave_aqui", "SUA_CHAVE_AQUI"}
    relatorio = {"python": sys.version.split()[0], "platform": platform.system(), "packages": versoes,
        "missing_project_files": faltantes, "env_example_has_placeholder_only": exemplo_ok,
        "prepared_data": artefatos["data_quality.json"], "index": artefatos["index_summary.json"],
        "last_api_test": artefatos["api_test.json"], "evaluation": artefatos["evaluation_metrics.json"]}
    pasta = raiz / "outputs"; pasta.mkdir(exist_ok=True)
    (pasta / "environment.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Diagnóstico salvo em outputs/environment.json. O conteúdo do .env não foi lido.")
    print("Arquivos obrigatórios ausentes:", ", ".join(faltantes) if faltantes else "nenhum")
    print(".env.example contém apenas placeholder:", exemplo_ok)
    if artefatos["index_summary.json"]:
        i = artefatos["index_summary.json"]
        print("Avaliações no índice:", i.get("selected_reviews"), "| Amostragem:", i.get("sampling"))
    if not exemplo_ok:
        print("Revisar .env.example antes de publicar; nunca colocar uma chave real nesse arquivo.")
    if not artefatos["evaluation_metrics.json"]:
        print("Avaliação ainda sem relatório. Execute avaliar.py.")
    return int(bool(faltantes) or not exemplo_ok)


if __name__ == "__main__":
    raise SystemExit(main())
