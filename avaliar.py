"""Executa casos de avaliação e exporta resultados para revisão."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import statistics
import time
from pathlib import Path
from config_api import carregar_config, erro_seguro
from busca_semantica import BuscaSemantica
from rag_llm import PROMPT_SISTEMA, responder, formatar_resposta

HUMANOS = ["fontes_relevantes", "fontes_avaliadas", "afirmacoes_sustentadas", "afirmacoes_avaliadas",
           "resposta_adequada_0_1", "abstencao_adequada_0_1", "observacoes"]


def fingerprint(raiz, motor, config):
    codigos = {}
    for nome in ["rag_llm.py", "busca_semantica.py", "config_api.py"]:
        p = raiz / nome
        codigos[nome] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    objeto = {"index": motor.info, "model": config.model, "threshold": config.min_similarity,
              "prompt": hashlib.sha256(PROMPT_SISTEMA.encode()).hexdigest(), "code": codigos}
    # O manifesto contém datas/tempo da construção; usar a coleção e sua configuração
    # como identidade evita invalidar os testes só por reabrir o mesmo índice.
    objeto["index"] = {k: motor.info.get(k) for k in ["collection", "model", "model_revision",
        "source_documents_sha256", "selected_reviews", "indexed_units", "sampling"]}
    return hashlib.sha256(json.dumps(objeto, sort_keys=True).encode()).hexdigest()


def executar_casos(raiz, casos, motor, config, intervalo=5.0, reprocessar=False, responder_func=responder):
    raiz = Path(raiz)
    pasta = raiz / "outputs" / "evaluation"
    pasta.mkdir(parents=True, exist_ok=True)
    versao = fingerprint(raiz, motor, config)
    resultados = []
    for numero, caso in enumerate(casos, 1):
        identidade = hashlib.sha256(json.dumps(caso, sort_keys=True).encode()).hexdigest()[:12]
        cache = pasta / f"{caso['id']}_{versao[:16]}_{identidade}.json"
        if cache.is_file() and not reprocessar:
            item = json.loads(cache.read_text(encoding="utf-8"))
            if item.get("technical_status") == "ok":
                resultados.append(item)
                print(f"[{numero}/{len(casos)}] {caso['id']}: execução anterior reutilizada.", flush=True)
                continue
        print(f"[{numero}/{len(casos)}] {caso['id']}: {caso['question']}", flush=True)
        item = {"case": caso, "pipeline_fingerprint": versao, "technical_status": "error"}
        try:
            item["result"] = responder_func(caso["question"], motor, raiz, notas=caso.get("scores"), config=config)
            item["technical_status"] = "ok"
            print("  Status retornado:", item["result"]["response"]["status"], flush=True)
        except Exception as erro:
            item["error"] = erro_seguro(erro, config.api_key)
            print("  Erro:", item["error"], flush=True)
        cache.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        resultados.append(item)
        if "429" in item.get("error", ""):
            print("Avaliação interrompida por limite de uso. Reexecute posteriormente para retomar.", flush=True)
            break
        if intervalo > 0 and numero < len(casos):
            time.sleep(intervalo)
    return resultados


def ratio_humano(linhas, numerador, denominador):
    a = b = casos = 0
    for linha in linhas:
        if linha.get(numerador, "") == "" or linha.get(denominador, "") == "":
            continue
        n, d = int(linha[numerador]), int(linha[denominador])
        if n == 0 and d == 0:
            continue
        if not 0 <= n <= d or d <= 0:
            raise ValueError(f"Revisão humana inválida em {linha['case_id']}: confira {numerador}/{denominador}.")
        a += n; b += d; casos += 1
    return {"value": a / b if b else None, "numerator": a, "denominator": b, "reviewed_cases": casos}


def escrever_relatorios(raiz, resultados, casos_totais):
    pasta = Path(raiz) / "outputs"
    pasta.mkdir(exist_ok=True)
    csv_path = pasta / "evaluation_summary.csv"
    anteriores = {}
    if csv_path.is_file():
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            anteriores = {(r["case_id"], r.get("run_id", "")): r for r in csv.DictReader(f)}
    linhas = []
    tempos = []
    for item in resultados:
        caso = item["case"]
        r = item.get("result", {})
        resposta = r.get("response", {})
        tempo = r.get("timing_seconds", {}).get("total_after_model_loading")
        if tempo is not None:
            tempos.append(float(tempo))
        linha = {"case_id": caso["id"], "run_id": r.get("run_id", ""), "question": caso["question"],
            "scores": ",".join(map(str, caso.get("scores") or [])), "expected_behavior": caso["expected_behavior"],
            "technical_status": item["technical_status"], "returned_status": resposta.get("status", ""),
            "sources_after_threshold": len(r.get("sources_sent_to_llm", [])), "claims": len(resposta.get("achados", [])),
            "seconds_after_loading": round(tempo, 3) if tempo is not None else "", "model": r.get("model", ""),
            "indexed_reviews": r.get("index", {}).get("selected_reviews", ""),
            "sampling": r.get("index", {}).get("sampling", ""), "technical_error": item.get("error", "")}
        anterior = anteriores.get((linha["case_id"], linha["run_id"]), {})
        linha.update({c: anterior.get(c, "") for c in HUMANOS})
        linhas.append(linha)
    if not linhas:
        raise ValueError("Nenhum resultado disponível para documentar.")
    # Validar julgamentos antes de reescrever os relatórios.
    precisao = ratio_humano(linhas, "fontes_relevantes", "fontes_avaliadas")
    fundamentacao = ratio_humano(linhas, "afirmacoes_sustentadas", "afirmacoes_avaliadas")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader(); w.writerows(linhas)
    metricas = {"evaluation_type": "exploratory, small fixed suite; not a representative or independent benchmark",
        "defined_cases": casos_totais, "recorded_cases": len(linhas),
        "completed_without_technical_error": sum(l["technical_status"] == "ok" for l in linhas),
        "technical_errors": sum(l["technical_status"] != "ok" for l in linhas),
        "latency_seconds_after_loading": {"n": len(tempos), "median": statistics.median(tempos) if tempos else None,
            "mean": statistics.mean(tempos) if tempos else None},
        "retrieved_source_relevance_human": precisao, "claim_grounding_human": fundamentacao,
        "notes": ["A technical success is not a correct answer.", "Human quality fields are blank until reviewed.",
            "Relevance is judged over displayed sources after threshold/deduplication, not all raw ANN candidates.",
            "Quoted text/ID matching is mechanical validation, not proof of semantic support.",
            "The suite includes topics used in development and cannot be treated as an independent holdout."]}
    (pasta / "evaluation_metrics.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    def num(v): return "não medido" if v is None else f"{v:.3f}"
    tabela = "\n".join(f"| {l['case_id']} | {l['technical_status']} | {l['returned_status'] or '—'} | {l['sources_after_threshold']} | {l['seconds_after_loading']} |" for l in linhas)
    texto = f"""# Avaliação — resultados da execução

Avaliação exploratória com perguntas fixas. Casos registrados: {len(linhas)} de {casos_totais} definidos.
Sucesso técnico significa apenas que a execução terminou e a validação mecânica passou; não comprova acerto.

| Caso | Execução técnica | Status retornado | Fontes selecionadas | Tempo após carregar (s) |
| --- | --- | --- | ---: | ---: |
{tabela}

Mediana de latência nas {len(tempos)} execuções concluídas: {num(metricas['latency_seconds_after_loading']['median'])} s.
Carregamento inicial do modelo não está incluído. Cada caso foi executado uma vez; não é um teste de carga.

## Revisão humana

- Relevância das fontes selecionadas: {num(precisao['value'])}; numerador {precisao['numerator']}, denominador {precisao['denominator']}.
- Fundamentação das afirmações: {num(fundamentacao['value'])}; numerador {fundamentacao['numerator']}, denominador {fundamentacao['denominator']}.

Campos humanos não preenchidos não são computados como acertos. Avaliar as respostas e as fontes nos JSONs
locais de `outputs/evaluation/` e preencher `outputs/evaluation_summary.csv` antes de concluir sobre qualidade.
As regras de revisão estão em [avaliacao.md](avaliacao.md). A suíte inclui temas usados no desenvolvimento;
seus resultados não estimam desempenho em perguntas novas ou representatividade de toda a base.

## Reproduzir

Executar `python avaliar.py`. O script reutiliza os casos concluídos da mesma configuração, preserva os
julgamentos humanos associados ao mesmo run_id e atualiza este relatório. Usar `--reprocessar` gera
novas respostas; os julgamentos de respostas antigas não são transferidos para respostas novas.
"""
    docs = Path(raiz) / "docs"; docs.mkdir(exist_ok=True)
    (docs / "avaliacao_resultados.md").write_text(texto, encoding="utf-8")
    exemplos = ["# Exemplos reais de execução", "",
        "Conteúdo gerado a partir dos casos T01 e T02. Revisar as afirmações e os trechos antes de publicar.", ""]
    for item in resultados:
        if item["case"]["id"] not in {"T01", "T02"} or item["technical_status"] != "ok":
            continue
        r = item["result"]
        exemplos += ["## " + item["case"]["id"], "", "Pergunta: " + r["question"], "",
            f"Modelo: `{r['model']}`. Avaliações indexadas: {r['index'].get('selected_reviews')}. Amostragem: {r['index'].get('sampling')}.",
            "", "Resposta registrada:", "", formatar_resposta(r), "", "Fontes recuperadas:", ""]
        for f in r["sources_sent_to_llm"]:
            exemplos += [f"- **[{f['label']}]** Nota {f['metadata'].get('review_score')}; review_id `{f['metadata']['review_id']}`.",
                         "", "> " + f["text"].replace("\n", "\n> "), ""]
        exemplos += [f"Tempo após carregar o modelo: {r['timing_seconds']['total_after_model_loading']:.3f} s.", ""]
    if len(exemplos) == 4:
        exemplos += ["Nenhum exemplo concluído de T01/T02 disponível. ", ""]
    (docs / "exemplos_reais.md").write_text("\n".join(exemplos), encoding="utf-8")
    return metricas


def main():
    parser = argparse.ArgumentParser(description="Executar casos exploratórios e preparar revisão humana.")
    parser.add_argument("--limit", type=int, help="Limitar a quantidade de casos do primeiro teste.")
    parser.add_argument("--intervalo", type=float, default=5)
    parser.add_argument("--reprocessar", action="store_true")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1 or args.intervalo < 0:
        parser.error("Informe --limit positivo e --intervalo não negativo.")
    raiz = Path(__file__).resolve().parent
    chave = ""
    try:
        casos = json.loads((raiz / "docs" / "casos_avaliacao.json").read_text(encoding="utf-8"))
        config = carregar_config(raiz); chave = config.api_key
        print(f"Modelo: {config.model}. Carregando índice...", flush=True)
        motor = BuscaSemantica(raiz)
        resultados = executar_casos(raiz, casos[:args.limit] if args.limit else casos, motor, config,
                                    args.intervalo, args.reprocessar)
        metricas = escrever_relatorios(raiz, resultados, len(casos))
        print(f"Concluídos sem erro técnico: {metricas['completed_without_technical_error']} de {metricas['recorded_cases']} registrados.")
        print("Relatórios salvos em outputs/evaluation_summary.csv e docs/avaliacao_resultados.md.")
        return 0
    except Exception as erro:
        print("ERRO:", erro_seguro(erro, chave)); return 1


if __name__ == "__main__":
    raise SystemExit(main())
