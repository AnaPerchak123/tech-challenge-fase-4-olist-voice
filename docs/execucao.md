# Instalação e execução

[Voltar à apresentação do projeto](../README.md).

## Preparar o ambiente e iniciar a aplicação

Ambiente registrado: Windows, Python 3.14.5. As versões das bibliotecas estão em `requirements.txt` e `outputs/environment.json`. A instalação em outros sistemas pode exigir ajuste das dependências.

Na raiz do projeto, pelo PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure a chave no arquivo `.env`:

```dotenv
GEMINI_API_KEY=cole_sua_chave_aqui
GEMINI_MODEL=gemini-3.5-flash-lite
RAG_MIN_SIMILARITY=0.45
```

A chave é obtida no [Google AI Studio](https://aistudio.google.com/api-keys). O acesso e as cotas dependem da conta e do modelo. Variáveis já definidas no terminal têm prioridade sobre o arquivo `.env`.

Coloque o CSV original em `data/raw/` e execute:

```powershell
.\.venv\Scripts\python.exe preparar_base.py
.\.venv\Scripts\python.exe criar_indice.py
.\.venv\Scripts\python.exe testar_api.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra a URL local indicada pelo Streamlit. O primeiro uso exige o download do modelo de embeddings. O índice é persistido em `chroma_db/`; a mesma construção pode retomar lotes já gravados.

Para desenvolver com uma amostra, use `criar_indice.py --limit 1000`. A interface identifica quando o índice ativo está amostrado.

Em Linux/macOS, crie o ambiente com `python3 -m venv .venv`, use `.venv/bin/python` nos comandos e `cp .env.example .env` para a configuração inicial.

### Consultas por terminal

Somente recuperação:

```powershell
.\.venv\Scripts\python.exe buscar_avaliacoes.py "O que os clientes relatam sobre atraso na entrega?" --notas 1 2
```

Recuperação e geração:

```powershell
.\.venv\Scripts\python.exe perguntar.py "O que os clientes elogiam sobre a entrega?" --notas 4 5
```

## Testes e avaliação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe avaliar.py --limit 4
.\.venv\Scripts\python.exe verificar_entrega.py
```

Há oito casos definidos em `docs/casos_avaliacao.json`. O comando acima executa os quatro primeiros. Os resultados publicados estão em [resultados da avaliação](avaliacao_resultados.md).

Casos concluídos da mesma configuração são reutilizados. Para executar toda a suíte, remova `--limit 4`. A opção `--reprocessar` solicita novas respostas. As execuções que acionam o modelo estão sujeitas às cotas e condições da API.

## Organização dos arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `preparar_base.py` | Limpeza e auditoria da base |
| `criar_indice.py` | Embeddings e indexação |
| `busca_semantica.py` | Recuperação e seleção das fontes |
| `config_api.py` / `testar_api.py` | Configuração e diagnóstico da API |
| `rag_llm.py` | Contexto, geração, validação e registro |
| `app.py` | Interface |
| `avaliar.py` | Execução dos casos e relatórios |
| `docs/` | Documentação e evidências selecionadas |
| `tests/` | Testes sem chamadas reais à API |

Dados, índice, credenciais e logs locais ficam fora do versionamento. O repositório inclui apenas relatórios agregados e os registros de avaliação selecionados para documentar o comportamento observado.


