# Apresentação da solução

Duração prevista: 6min40s. Limite: 7 minutos.

| Tempo | Conteúdo | Evidência visual |
| --- | --- | --- |
| 00:00–00:35 | Problema de negócio e objetivo | Tela inicial |
| 00:35–01:15 | Base e preparação | Contagens da preparação |
| 01:15–02:10 | Arquitetura e escolhas técnicas | Diagrama de ingestão e consulta |
| 02:10–04:35 | Demonstração | Atrasos, elogios e pergunta fora do domínio |
| 04:35–05:25 | Avaliação | Resultados e registros dos casos |
| 05:25–06:10 | Limitações e decisões | Recuperação, evidências e tratamento de erros |
| 06:10–06:40 | Reprodução e documentação | README e comandos |

## Problema e base

Apresentar a dificuldade de investigar milhares de avaliações textuais e o objetivo
de consultar relatos com fontes rastreáveis. Informar a origem Olist e distinguir
99.224 registros originais de 42.687 avaliações com texto preparadas.

Explicar a combinação de título e mensagem, a preservação de negações e a criação
do identificador técnico. Mostrar que uma avaliação dividida em dois fragmentos
resultou em 42.688 unidades vetoriais.

## Arquitetura

Separar ingestão de consulta. Na ingestão, apresentar documentos, embeddings e
persistência no Chroma. Na consulta, explicar filtros, representação da pergunta,
recuperação, seleção, contexto e geração. Identificar onde são validadas as citações.

## Demonstração

1. Perguntar sobre atraso com notas 1 e 2. Abrir duas fontes e relacionar seus
   trechos ao achado da resposta.
2. Perguntar sobre elogios com notas 4 e 5. Mostrar os relatos positivos e o filtro.
3. Fazer a pergunta sobre fotossíntese. Mostrar a abstenção por falta de fontes
   acima do limiar e explicar que não houve chamada ao LLM.

## Avaliação

Apresentar os quatro casos executados: dois com geração concluída, um com abstenção
local e um com erro 503. O caso de política oficial não teve resposta avaliável.
Os registros distinguem disponibilidade técnica de qualidade das respostas.

Explicar a limitação da fonte genérica E5 no caso dos elogios. Informar os tempos
como observações individuais, excluindo carregamento do modelo.

## Decisões e limites

Justificar embeddings multilíngues locais, índice persistente, filtro por nota,
contexto limitado e saída estruturada. Explicar que o top-k não mede frequência
global, que relatos não comprovam causa raiz e que verificar um trecho literal
não prova sustentação semântica.

## Reprodução

Mostrar o README, a configuração por ambiente e os comandos de preparação,
indexação, teste da API, interface e avaliação. Encerrar com as melhorias propostas:
ampliação da avaliação e comparação de estratégias de recuperação.
