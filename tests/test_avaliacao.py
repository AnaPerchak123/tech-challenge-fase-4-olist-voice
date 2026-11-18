"""Avalia o registrador sem rede, com gerador e fontes simulados."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from avaliar import executar_casos, escrever_relatorios
from config_api import ConfigAPI
from rag_llm import responder
from test_rag_guardrails import MotorSimulado, gerador_simulado


class TestAvaliacao(unittest.TestCase):
    def test_cache_campos_vazios_e_preservacao_da_revisao(self):
        with tempfile.TemporaryDirectory() as temp:
            raiz = Path(temp)
            casos = [{"id": "T01", "question": "Relatos de entrega?", "scores": [1], "expected_behavior": "Responder com fonte"},
                     {"id": "T04", "question": "fotossíntese", "scores": None, "expected_behavior": "Abster-se"}]
            class Motor(MotorSimulado):
                def buscar(self, pergunta, *args, **kwargs):
                    f = super().buscar(pergunta, *args, **kwargs)
                    if pergunta == "fotossíntese": f[0]["cosine_similarity"] = .1
                    return f
            config = ConfigAPI("dummy-key-offline-evaluation-test")
            chamadas = []
            def simular(pergunta, motor, raiz, **kwargs):
                chamadas.append(pergunta)
                return responder(pergunta, motor, raiz, gerador=gerador_simulado, **kwargs)
            r = executar_casos(raiz, casos, Motor(), config, intervalo=0, responder_func=simular)
            self.assertEqual(len(chamadas), 2)
            m = escrever_relatorios(raiz, r, len(casos))
            self.assertIsNone(m["retrieved_source_relevance_human"]["value"])
            self.assertIsNone(m["claim_grounding_human"]["value"])
            arquivo = raiz / "outputs/evaluation_summary.csv"
            with arquivo.open(encoding="utf-8-sig", newline="") as f:
                linhas = list(csv.DictReader(f))
            linhas[0].update(fontes_relevantes="1", fontes_avaliadas="1", afirmacoes_sustentadas="1", afirmacoes_avaliadas="1", resposta_adequada_0_1="1")
            linhas[1].update(fontes_relevantes="0", fontes_avaliadas="0", afirmacoes_sustentadas="0", afirmacoes_avaliadas="0", abstencao_adequada_0_1="1")
            with arquivo.open("w", encoding="utf-8-sig", newline="") as f:
                w=csv.DictWriter(f,fieldnames=list(linhas[0]));w.writeheader();w.writerows(linhas)
            def nao_chamar(*args, **kwargs):self.fail("O caso concluído foi repetido desnecessariamente")
            repetidos = executar_casos(raiz, casos, Motor(), config, intervalo=0, responder_func=nao_chamar)
            m = escrever_relatorios(raiz, repetidos, len(casos))
            self.assertEqual(m["retrieved_source_relevance_human"]["value"], 1)
            self.assertEqual(m["claim_grounding_human"]["value"], 1)
            self.assertEqual(m["claim_grounding_human"]["denominator"], 1)
            with arquivo.open(encoding="utf-8-sig", newline="") as f:
                revisadas=list(csv.DictReader(f))
            self.assertEqual(revisadas[0]["resposta_adequada_0_1"], "1")
            self.assertTrue((raiz/'docs/exemplos_reais.md').is_file())
            self.assertNotIn(config.api_key, (raiz/'docs/exemplos_reais.md').read_text())


if __name__ == "__main__":
    unittest.main()
