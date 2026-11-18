"""Testa a chave e a geração estruturada sem enviar dados da Olist."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
from config_api import carregar_config, criar_cliente, erro_seguro


class TesteConexao(BaseModel):
    status: Literal["API_OK"]


def main():
    parser = argparse.ArgumentParser(description="Validar acesso à Gemini API sem exibir credenciais.")
    parser.add_argument("--listar-modelos", action="store_true")
    parser.add_argument("--simples", action="store_true", help="Testar geração de texto sem esquema JSON.")
    args = parser.parse_args()
    chave = ""
    cliente = None
    try:
        config = carregar_config(Path(__file__).resolve().parent)
        chave = config.api_key
        cliente = criar_cliente(config)
        if args.listar_modelos:
            for modelo in cliente.models.list():
                nome = (modelo.name or "").removeprefix("models/")
                if nome.startswith("gemini-"):
                    print(nome)
            print("A listagem não garante cota ou suporte a todos os métodos; valide o modelo escolhido.")
            return 0
        from google.genai import types
        if args.simples:
            print(f"Testando geração simples com {config.model}...", flush=True)
            resposta = cliente.models.generate_content(model=config.model,
                contents="Responda apenas: API_OK", config=types.GenerateContentConfig(max_output_tokens=1024))
            if not resposta.text:
                raise ValueError("A API retornou conteúdo vazio no teste simples.")
            print(resposta.text.strip())
            print("Geração simples concluída; executar também o teste estruturado antes de usar o RAG.")
            return 0
        print(f"Testando geração estruturada com {config.model}...", flush=True)
        resposta = cliente.models.generate_content(model=config.model,
            contents="Teste de conexão. Preencha status com API_OK.",
            config=types.GenerateContentConfig(response_mime_type="application/json",
                response_schema=TesteConexao, max_output_tokens=1024))
        if not resposta.text:
            raise ValueError("A API retornou conteúdo vazio; confira a resposta do serviço antes de integrar o RAG.")
        teste = TesteConexao.model_validate_json(resposta.text)
        print(teste.status)
        print("Chave e geração estruturada funcionando. Nenhum comentário da base foi enviado neste teste.")
        pasta = Path(__file__).resolve().parent / "outputs"
        pasta.mkdir(exist_ok=True)
        (pasta / "api_test.json").write_text(json.dumps({"status": teste.status,
            "model": config.model, "structured_output": True}, indent=2) + "\n", encoding="utf-8")
        return 0
    except Exception as erro:
        print("ERRO:", erro_seguro(erro, chave))
        return 1
    finally:
        if cliente is not None:
            cliente.close()


if __name__ == "__main__":
    raise SystemExit(main())
