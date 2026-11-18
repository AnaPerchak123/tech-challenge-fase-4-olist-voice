# Preparação da base

| Indicador | Registros |
| --- | ---: |
| Originais | 99.224 |
| Duplicatas exatas removidas | 0 |
| Sem texto após a limpeza | 56.537 |
| Sem identificador após o filtro de texto | 0 |
| Avaliações preparadas | 42.687 |

Fonte: `olist_order_reviews_dataset.csv`.

SHA-256: `012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7`.

A preparação combina título e mensagem, normaliza ruídos leves e mantém os
campos originais. Registros distintos com review_id repetido são preservados.
O relatório JSON registra regras, ausentes, notas, datas e comprimentos.
