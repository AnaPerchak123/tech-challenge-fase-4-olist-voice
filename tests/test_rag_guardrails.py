"""Testes determinísticos; não usam chave real nem fazem chamadas à API."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config_api import ConfigAPI, FalhaRAG, erro_seguro
from rag_llm import (RespostaRAG, Achado, Citacao, responder, validar_resposta,
                     salvar_execucao, mascarar_contatos)


class MotorSimulado:
    info = {"sampling": "none", "selected_reviews": 2, "collection": "simulated_test"}

    def buscar(self, *args, **kwargs):
        return [{"document_id": "d1", "text": "Não recebi o produto. Contato: teste@example.com",
            "metadata": {"parent_id": "p1", "review_id": "r1", "review_score": 1},
            "cosine_similarity": .75, "cosine_distance": .25}]


def gerador_simulado(modelo, pergunta, fontes, info):
    return RespostaRAG(status="respondido", motivo="", achados=[Achado(
        afirmacao="Um cliente relata não ter recebido o produto.",
        evidencias=[Citacao(fonte="E1", trecho="Não recebi o produto.")])],
        limitacoes=["Relatos recuperados não permitem estimar a frequência na base."]), None


class TestGuardrails(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temp.name)
        self.config = ConfigAPI("dummy-key-only-for-offline-tests")
        self.resultado = responder("O que os clientes relatam?", MotorSimulado(), self.raiz,
            config=self.config, gerador=gerador_simulado)

    def tearDown(self):
        self.temp.cleanup()

    def test_resposta_rastreavel_e_registro_sem_chave(self):
        self.assertEqual(self.resultado["response"]["status"], "respondido")
        caminho = salvar_execucao(self.resultado, self.raiz)
        serializado = caminho.read_text(encoding="utf-8")
        self.assertNotIn(self.config.api_key, serializado)
        self.assertNotIn("teste@example.com", serializado)
        self.assertEqual(json.loads(serializado)["run_id"], self.resultado["run_id"])

    def test_fonte_inexistente_e_recusada(self):
        r = copy.deepcopy(self.resultado["response"])
        r["achados"][0]["evidencias"][0]["fonte"] = "E99"
        with self.assertRaises(ValueError):
            validar_resposta(RespostaRAG.model_validate(r), self.resultado["sources_sent_to_llm"])

    def test_trecho_inventado_e_recusado(self):
        r = copy.deepcopy(self.resultado["response"])
        r["achados"][0]["evidencias"][0]["trecho"] = "O produto chegou perfeitamente"
        with self.assertRaises(ValueError):
            validar_resposta(RespostaRAG.model_validate(r), self.resultado["sources_sent_to_llm"])

    def test_abstencao_nao_pode_conter_achados(self):
        r = copy.deepcopy(self.resultado["response"])
        r["status"] = "sem_evidencias"
        r["motivo"] = "Contexto insuficiente"
        with self.assertRaises(ValueError):
            validar_resposta(RespostaRAG.model_validate(r), self.resultado["sources_sent_to_llm"])

    def test_busca_fraca_nao_chama_gerador(self):
        class MotorFraco(MotorSimulado):
            def buscar(self, *args, **kwargs):
                fontes = super().buscar(*args, **kwargs)
                fontes[0]["cosine_similarity"] = .2
                return fontes
        def nao_chamar(*args):
            self.fail("O gerador foi chamado sem fontes acima do limiar.")
        r = responder("fotossíntese", MotorFraco(), self.raiz, config=self.config, gerador=nao_chamar)
        self.assertEqual(r["response"]["status"], "sem_evidencias")
        self.assertFalse(r["api_called"])

    def test_mascaramento_de_contatos(self):
        texto = mascarar_contatos("Ligue (11) 99999-1234 ou escreva teste@example.com")
        self.assertIn("[TELEFONE]", texto)
        self.assertIn("[EMAIL]", texto)

    def test_erro_de_cota_continua_como_erro_tecnico(self):
        class ErroCota(Exception):
            code = 429
        self.assertIn("429", erro_seguro(FalhaRAG(erro_seguro(ErroCota()))))

    def test_erro_de_servidor_preserva_codigo_e_oculta_chave(self):
        class ErroServidor(Exception):
            code = 503
            status = "UNAVAILABLE"
            message = "Service unavailable. key=segredo123&other=ok; token=outrosegredo"
        mensagem = erro_seguro(ErroServidor(), "segredo123")
        self.assertIn("503", mensagem)
        self.assertIn("UNAVAILABLE", mensagem)
        self.assertIn("Service unavailable", mensagem)
        self.assertNotIn("segredo123", mensagem)
        self.assertNotIn("outrosegredo", mensagem)

    def test_codigo_em_corpo_json_tambem_e_exibido(self):
        class ErroServidor(Exception):
            response_json = {"error": {"code": 500, "status": "INTERNAL", "message": "Internal error."}}
        mensagem = erro_seguro(ErroServidor())
        self.assertIn("500", mensagem)
        self.assertIn("INTERNAL", mensagem)
        self.assertIn("Internal error", mensagem)


if __name__ == "__main__":
    unittest.main()
