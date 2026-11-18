"""Configuração local da Gemini API; nunca imprime credenciais."""
from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv


class FalhaRAG(RuntimeError):
    """Erro já convertido em orientação segura para a interface."""


@dataclass
class ConfigAPI:
    api_key: str = field(repr=False)
    model: str = "gemini-3.5-flash-lite"
    min_similarity: float = 0.45


def carregar_config(raiz: Path) -> ConfigAPI:
    load_dotenv(Path(raiz) / ".env", override=False)
    chave = os.getenv("GEMINI_API_KEY", "").strip()
    if not chave or chave in {"cole_sua_chave_aqui", "SUA_CHAVE_AQUI"}:
        raise ValueError("Configure GEMINI_API_KEY no arquivo .env, na raiz do projeto.")
    modelo = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    limiar = float(os.getenv("RAG_MIN_SIMILARITY", "0.45"))
    if not modelo or not -1 <= limiar <= 1:
        raise ValueError("Revise GEMINI_MODEL e RAG_MIN_SIMILARITY no .env.")
    return ConfigAPI(chave, modelo, limiar)


def criar_cliente(config: ConfigAPI):
    from google import genai
    from google.genai import types
    return genai.Client(api_key=config.api_key, http_options=types.HttpOptions(
        timeout=60000, retry_options=types.HttpRetryOptions(attempts=1)))


def erro_seguro(erro, chave=""):
    """Preserva o diagnóstico HTTP e a mensagem do serviço, com credencial ocultada."""
    def ocultar(texto):
        texto = str(texto)
        if chave:
            texto = texto.replace(chave, "[CHAVE OCULTA]")
        texto = re.sub(r"(?i)((?:api_key|key|token)=)[^&\s]+", r"\1[OCULTO]", texto)
        return " ".join(texto.split())[:1200]

    codigo = getattr(erro, "code", None) or getattr(erro, "status_code", None)
    status = getattr(erro, "status", None)
    mensagem = getattr(erro, "message", None)
    corpo = getattr(erro, "response_json", None)
    if isinstance(corpo, dict):
        detalhe = corpo.get("error", corpo)
        if isinstance(detalhe, dict):
            codigo = codigo or detalhe.get("code")
            status = status or detalhe.get("status")
            mensagem = mensagem or detalhe.get("message")
    codigo = str(codigo or "")
    if isinstance(erro, (ValueError, FileNotFoundError, FalhaRAG)):
        return ocultar(erro)
    orientacoes = {
        "400": "A solicitação foi recusada. Confira a mensagem do serviço e a configuração do modelo.",
        "401": "Confira a chave e a autorização do projeto.",
        "403": "Confira permissões e disponibilidade da API para a conta e o projeto.",
        "404": "Confira o modelo com testar_api.py --listar-modelos e ajuste GEMINI_MODEL no .env.",
        "429": "Cota ou limite atingido. Confira os limites do projeto/modelo no AI Studio. Não há repetição automática.",
        "500": "O serviço retornou erro interno. Tente novamente; se persistir, compare o teste simples e o estruturado.",
        "502": "O serviço retornou falha de gateway. Tente novamente mais tarde.",
        "503": "O serviço informou indisponibilidade. Tente novamente mais tarde; se persistir, confira os modelos disponíveis.",
        "504": "O serviço excedeu o tempo de resposta. Tente novamente mais tarde.",
    }
    identificacao = " ".join(x for x in [codigo, str(status or "")] if x) or type(erro).__name__
    orientacao = orientacoes.get(codigo, "Confira a conexão e o diagnóstico abaixo. A falha é técnica, não ausência de evidências.")
    texto = f"Falha da API ({identificacao}). {orientacao}"
    mensagem = mensagem or str(erro)
    if mensagem:
        texto += "\nDetalhe do serviço: " + ocultar(mensagem)
    return ocultar(texto)
