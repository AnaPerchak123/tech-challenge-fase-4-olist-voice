# Olist Voice

Sistema de análise da voz do cliente com Retrieval-Augmented Generation (RAG), desenvolvido para o Tech Challenge da Fase 4 da pós-graduação em Ciência de Dados e Inteligência Artificial da FIAP.

A aplicação permite investigar avaliações da Olist em linguagem natural. Cada resposta apresenta os comentários utilizados como evidência, com nota, identificador e trechos citados.

## Funcionalidades

- Busca semântica em avaliações de clientes.
- Filtro por nota antes da recuperação.
- Respostas em português com referências às fontes.
- Verificação dos identificadores e trechos citados.
- Tratamento de evidências insuficientes e falhas da API.
- Registro das consultas e avaliação reproduzível.

## Dados

Fonte: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). O projeto utiliza o arquivo `olist_order_reviews_dataset.csv`, com avaliações históricas de 2016 a 2018. Os dados brutos não são distribuídos neste repositório; devem ser obtidos na fonte, observando sua licença e atribuição.

| Indicador | Quantidade |
| --- | ---: |
| Registros originais | 99.224 |
| Duplicatas exatas removidas | 0 |
| Registros sem texto após a limpeza | 56.537 |
| Avaliações preparadas e indexadas | 42.687 |
| Unidades vetoriais | 42.688 |

Título e mensagem são combinados. A limpeza normaliza espaços, caracteres de controle e HTML básico, preservando acentos, negações e pontuação. Registros distintos com `review_id` repetido são mantidos e recebem um identificador técnico derivado do conteúdo original.

Uma avaliação excedeu o limite de tokens do modelo e foi dividida em duas partes. Por isso, o número de unidades vetoriais é maior que o número de avaliações.

## Arquitetura

**Ingestão:** CSV → preparação → documentos e metadados → verificação de tokens → embeddings → Chroma.

**Consulta:** pergunta e filtros → embedding → recuperação → seleção de fontes → contexto → Gemini → validação → resposta com evidências.

| Componente | Tecnologia |
| --- | --- |
| Preparação | Python e pandas |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2`, Sentence Transformers |
| Índice vetorial | Chroma local, HNSW e distância de cosseno |
| Geração | Gemini API, `gemini-3.5-flash-lite` |
| Validação | Pydantic e verificação de citações |
| Interface | Streamlit |

Detalhes em [arquitetura](docs/arquitetura.md) e [decisões técnicas](docs/decisoes_tecnicas.md).

## Execução

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

## Avaliação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe avaliar.py --limit 4
.\.venv\Scripts\python.exe verificar_entrega.py
```

A suíte possui oito casos definidos. O registro publicado contém quatro casos executados: três concluídos e um interrompido por erro `503` da API. Esse resultado representa disponibilidade técnica, não acurácia.

| Caso | Resultado observado | Tempo após carregar o modelo |
| --- | --- | ---: |
| Atraso na entrega | Resposta sustentada por relatos de atraso | 3,117 s |
| Elogios sobre entrega | Resposta com satisfação e cumprimento de prazo | 2,930 s |
| Política oficial de reembolso | Erro 503; comportamento não avaliado | — |
| Fotossíntese | Abstenção local, sem chamada ao LLM | 0,034 s |

[Resultados e revisão das evidências](docs/avaliacao_resultados.md) · [Exemplos de respostas](docs/exemplos_reais.md) · [Método de avaliação](docs/avaliacao.md).

Casos concluídos da mesma configuração são reutilizados. Para executar toda a suíte, remova `--limit 4`. A opção `--reprocessar` solicita novas respostas. As execuções que acionam o modelo estão sujeitas às cotas e condições da API.

## Limitações

- O contexto recuperado não representa uma amostra estatística da base e não permite estimar percentuais ou rankings globais.
- O limiar de similaridade de 0,45 é uma heurística exploratória; não é probabilidade de acerto.
- A existência de uma fonte e de um trecho literal não comprova a sustentação semântica da conclusão.
- Relatos de clientes não comprovam causa raiz, política oficial ou condições atuais da empresa.
- O conjunto de avaliação é pequeno e inclui temas usados no desenvolvimento.
- A revisão exata do modelo de embeddings não foi registrada no ambiente avaliado; o manifesto registra o nome do modelo, os parâmetros e o hash dos documentos.

## Organização

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

## Referências

- FIAP — Tech Challenge Fase 4: Voice of Customer Intelligence com RAG.
- [Olist no Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
- [Sentence Transformers](https://sbert.net/).
- [Modelo de embeddings](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).
- [Chroma](https://docs.trychroma.com/).
- [Google Gen AI SDK](https://googleapis.github.io/python-genai/).
- [Streamlit](https://docs.streamlit.io/).
