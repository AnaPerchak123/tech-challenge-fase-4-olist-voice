# Resultados da avaliação

Configuração: `gemini-3.5-flash-lite`, índice completo de 42.687 avaliações e 42.688
unidades vetoriais. Foram executados quatro dos oito casos definidos.

| Caso | Execução | Comportamento observado | Tempo |
| --- | --- | --- | ---: |
| T01 — atraso | Concluída | Resposta com fontes sobre atraso e demora | 3,117 s |
| T02 — elogios | Concluída | Resposta com satisfação e cumprimento de prazo | 2,930 s |
| T03 — política de reembolso | Erro 503 | Serviço indisponível; comportamento não avaliado | — |
| T04 — fotossíntese | Concluída | Sem evidências acima do limiar; nenhuma chamada ao LLM | 0,034 s |

Três execuções terminaram sem erro técnico. Esse total não é uma medida de acurácia.
A mediana entre as três execuções concluídas foi 2,930 s, incluindo a abstenção
local. Nas duas consultas com geração, os tempos foram 3,117 s e 2,930 s.

## Revisão das evidências

### T01 — atraso na entrega

As cinco fontes mencionam atraso ou demora. A conclusão “Clientes relataram atrasos
e demora nas entregas” é compatível com esses comentários. A resposta limita o
alcance dos achados às fontes recuperadas, sem estimar frequência na população.

### T02 — elogios sobre entrega

As fontes E1–E4 tratam de satisfação com a entrega ou cumprimento de prazo. A fonte
E5 expressa satisfação genérica e não menciona entrega; portanto, sua relevância
para a pergunta é limitada. Essa fonte não foi citada no achado final.

A resposta utiliza E1, E2 e E4 para relatar satisfação e prazo cumprido. O caso
mostra que similaridade elevada não elimina a necessidade de julgar a pertinência
do comentário.

### T03 — política oficial de reembolso

A API retornou `503 UNAVAILABLE`, informando alta demanda. Não houve resposta
avaliável. O erro não foi contado como reconhecimento correto de falta de suporte.
Esse caso precisa de nova execução para avaliar o comportamento sobre fonte normativa.

### T04 — pergunta fora do domínio

Nenhuma fonte atingiu o limiar inicial. O sistema explicou a insuficiência do
contexto e não apresentou uma definição externa de fotossíntese. A resposta foi
produzida pelo tratamento local, sem chamar a API.

## Limitações

O conjunto é pequeno, tem uma execução por pergunta e inclui temas usados no
desenvolvimento. As observações não estimam desempenho em perguntas novas nem
garantem ausência de respostas sem fundamento. Não foram atribuídas notas
quantitativas de revisão independente.

## Registros

- [T01](evidencias/T01.json)
- [T02](evidencias/T02.json)
- [T03](evidencias/T03.json)
- [T04](evidencias/T04.json)

Os exemplos de respostas e comentários estão em [exemplos de execução](exemplos_reais.md).
