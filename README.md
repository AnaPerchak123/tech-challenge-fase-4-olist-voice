# Olist Voice

Aplicação para investigar avaliações de clientes da Olist por meio de perguntas em português. A resposta reúne os relatos encontrados e apresenta os comentários que a sustentam.

Projeto desenvolvido para o **Tech Challenge da Fase 4** da pós-graduação em Ciência de Dados e Inteligência Artificial da **FIAP**.

## Qual problema o projeto resolve?

Ler milhares de avaliações individualmente dificulta a investigação de reclamações e elogios. O Olist Voice permite que gestores e analistas explorem esses relatos e consultem as fontes de cada resposta na própria tela.

Por exemplo, é possível investigar atrasos nas entregas ou experiências positivas, filtrando as avaliações pela nota atribuída pelo cliente.

## Como usar

1. Digite uma pergunta sobre as experiências relatadas pelos clientes.
2. Se desejar, selecione as notas das avaliações que quer consultar.
3. Leia a resposta e abra os comentários apresentados como evidência.
4. Confira os trechos citados antes de usar o achado em uma decisão.

| Exemplo de pergunta | Filtro sugerido |
| --- | --- |
| O que os clientes relatam sobre atraso na entrega? | Notas 1 e 2 |
| O que os clientes elogiam sobre a entrega? | Notas 4 e 5 |
| Quais problemas relacionados à qualidade do produto são relatados? | Notas 1 e 2 |

As perguntas são exemplos de exploração. Os [exemplos de respostas registradas](docs/exemplos_reais.md) mostram o comportamento observado nas execuções avaliadas.

Quando não encontra comentários suficientes para responder, a aplicação informa essa limitação. Uma falha no serviço de geração é apresentada como erro técnico, separadamente da falta de evidências.

## Como a solução funciona

O projeto utiliza **RAG**, uma abordagem em que o modelo de linguagem recebe comentários recuperados da base para elaborar a resposta.

Antes das consultas, os textos são preparados e transformados em representações numéricas, chamadas *embeddings*. Essas representações permitem buscar comentários pelo significado, além da correspondência exata de palavras.

A cada pergunta, a aplicação:

1. Busca avaliações relacionadas ao tema, respeitando o filtro de nota.
2. Seleciona os comentários que serão enviados como contexto ao Gemini.
3. Solicita uma resposta baseada nesse contexto, com referências às fontes.
4. Verifica se os identificadores e os trechos citados existem nas fontes selecionadas.
5. Exibe a resposta e as evidências para conferência.

A verificação das citações ajuda na rastreabilidade, mas não garante, por si só, que toda conclusão esteja correta.

| Tecnologia | Papel no projeto |
| --- | --- |
| Python e pandas | Preparar e conferir os dados |
| Sentence Transformers | Representar perguntas e comentários para a busca por significado |
| Chroma | Armazenar e recuperar as avaliações |
| Gemini API | Elaborar a resposta com base nos comentários selecionados |
| Pydantic | Validar a estrutura da resposta |
| Streamlit | Disponibilizar a interface de consulta |

Modelo de busca: `paraphrase-multilingual-MiniLM-L12-v2`. Modelo de geração utilizado na avaliação: `gemini-3.5-flash-lite`.

Consulte a [arquitetura](docs/arquitetura.md) e as [decisões técnicas](docs/decisoes_tecnicas.md) para conhecer os parâmetros e as justificativas.

## Base utilizada

Fonte: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), com avaliações históricas de **2016 a 2018**. O arquivo utilizado é `olist_order_reviews_dataset.csv`.

| Etapa | Quantidade |
| --- | ---: |
| Registros originais | 99.224 |
| Duplicatas exatas removidas | 0 |
| Registros sem texto após a limpeza | 56.537 |
| Avaliações preparadas e indexadas | 42.687 |

A preparação combina título e mensagem, normaliza espaços e HTML básico e preserva acentos, negações e pontuação. Registros distintos com o mesmo identificador de avaliação são mantidos com um identificador técnico próprio.

Uma avaliação precisou ser dividida em duas partes por exceder o limite de tamanho do modelo de busca. Por isso, o índice contém **42.688 partes pesquisáveis**, correspondentes às **42.687 avaliações**.

Os dados brutos devem ser baixados na fonte, observando sua licença e atribuição. O [relatório de preparação](outputs/preparacao_base.md) registra as contagens e os tratamentos.

## Executar o projeto

O [guia de instalação e execução](docs/execucao.md) reúne os comandos para criar o ambiente, instalar as dependências, configurar a chave da API, preparar a base e construir o índice.

Após essas etapas, inicie a interface pelo PowerShell:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra o endereço local indicado pelo Streamlit. O ambiente utilizado na avaliação foi Windows com Python 3.14.5; as versões das bibliotecas estão em `requirements.txt`.

A chave da API fica apenas no arquivo local `.env`. Dados brutos, ambiente virtual, índice e logs locais ficam fora do versionamento.

## O que foi observado na avaliação?

Foram registrados **os oito casos definidos**, reutilizando os resultados já concluídos da mesma configuração e executando os casos novos ou com erro:

| Consulta | Resultado observado |
| --- | --- |
| Atraso na entrega | Resposta com fontes sobre atraso e demora |
| Elogios sobre entrega | Resposta com relatos de satisfação e cumprimento de prazo |
| Política oficial de reembolso | Reconhece que os relatos não comprovam uma política oficial |
| Fotossíntese | Informação de falta de evidências, sem chamada ao modelo de linguagem |
| Produto diferente do anunciado | Resposta com relatos de divergência em relação ao anúncio |
| Prazo de entrega atual | Reconhece o limite dos dados históricos |
| Percentual global de atrasos | Não estima percentual a partir dos relatos recuperados |
| Avaliações que sustentam atrasos | Apresenta fontes e trechos sobre atraso ou demora |

Oito execuções terminaram sem erro técnico. **Isso não representa uma taxa de acerto.** A avaliação é inicial e não permite estimar o desempenho em perguntas novas.

Consulte os [resultados e a revisão das evidências](docs/avaliacao_resultados.md), os [exemplos de respostas](docs/exemplos_reais.md) e o [método de avaliação](docs/avaliacao.md). Os comandos dos testes estão no [guia de execução](docs/execucao.md#testes-e-avaliação).

## Limites da análise

- Os relatos recuperados permitem investigar experiências, mas não medir a frequência de um problema em toda a base nem construir rankings globais.
- Comentários de clientes não comprovam a causa de um problema, políticas oficiais ou a situação atual da empresa.
- A busca pode selecionar comentários pouco específicos. O limiar de similaridade de 0,45 é um parâmetro inicial e não representa probabilidade de acerto.
- A avaliação ainda é pequena. A revisão exata do modelo de busca não foi registrada no ambiente avaliado; os demais parâmetros e o hash dos documentos estão no manifesto do índice.

## Documentação

| Conteúdo | Onde consultar |
| --- | --- |
| Instalação, comandos e organização dos arquivos | [Guia de execução](docs/execucao.md) |
| Fluxos de preparação e consulta | [Arquitetura](docs/arquitetura.md) |
| Escolhas de modelos, busca e validação | [Decisões técnicas](docs/decisoes_tecnicas.md) |
| Método e critérios de revisão | [Avaliação](docs/avaliacao.md) |
| Resultados, falhas e evidências | [Resultados da avaliação](docs/avaliacao_resultados.md) |
| Perguntas e respostas registradas | [Exemplos reais](docs/exemplos_reais.md) |

## Referências

- FIAP — Tech Challenge Fase 4: Voice of Customer Intelligence com RAG.
- [Olist no Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
- [Sentence Transformers](https://sbert.net/).
- [Modelo de embeddings](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).
- [Chroma](https://docs.trychroma.com/).
- [Google Gen AI SDK](https://googleapis.github.io/python-genai/).
- [Streamlit](https://docs.streamlit.io/).
