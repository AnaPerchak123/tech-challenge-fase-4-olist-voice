# Resultados da avaliação

Configuração: `gemini-3.5-flash-lite`, índice completo de 42.687 avaliações e 42.688
unidades vetoriais. Foram registrados os oito casos definidos. Os casos concluídos
da mesma configuração foram reutilizados; casos novos ou com erro foram executados.

| Caso | Execução | Comportamento observado | Tempo |
| --- | --- | --- | ---: |
| T01 — atraso | Concluída | Resposta com fontes sobre atraso e demora | 3,117 s |
| T02 — elogios | Concluída | Resposta com satisfação e cumprimento de prazo | 2,930 s |
| T03 — política de reembolso | Concluída | Reconhece que os relatos não comprovam a política oficial | 2,988 s |
| T04 — fotossíntese | Concluída | Sem fontes acima do limiar; nenhuma chamada ao LLM | 0,034 s |
| T05 — produto diferente | Concluída | Resposta com relatos de divergência em relação ao anúncio | 2,453 s |
| T06 — prazo atual | Concluída | Reconhece que dados históricos não informam o prazo atual | 1,721 s |
| T07 — percentual global | Concluída | Recusa estimar um percentual a partir dos relatos recuperados | 2,325 s |
| T08 — fontes sobre atraso | Concluída | Apresenta cinco fontes e trechos sobre atraso ou demora | 2,411 s |

Oito execuções terminaram sem erro técnico. Esse total não é uma medida de acurácia.
A mediana entre os oito casos foi 2,432 s, incluindo a abstenção local. Os tempos
excluem o carregamento do modelo e não representam garantia de latência.

## Revisão das evidências

### T01 — atraso na entrega

As cinco fontes mencionam atraso ou demora. A conclusão sobre relatos de atraso
é compatível com esses comentários e não estima frequência na população.

### T02 — elogios sobre entrega

As fontes E1–E4 tratam de satisfação com a entrega ou cumprimento de prazo. A fonte
E5 expressa satisfação genérica e não menciona entrega; sua relevância para a
pergunta é limitada. Essa fonte não foi citada no achado final.

A resposta utiliza E1, E2 e E4 para relatar satisfação e prazo cumprido. Similaridade
elevada não elimina a necessidade de julgar a pertinência do comentário.

### T03 — política oficial de reembolso

A execução anterior retornou erro 503 e não teve resposta avaliável. Na nova
execução, a resposta reconheceu que os comentários recuperados descrevem solicitações
de reembolso e questões de pagamento, sem estabelecer a política oficial.

A fonte E2 aborda política de entrega, sem esclarecer reembolso. O caso mostra
que podem existir documentos próximos à pergunta sem suporte para a conclusão
solicitada. A resposta não inventou regras ou prazos de reembolso.

### T04 — pergunta fora do domínio

Nenhuma fonte atingiu o limiar inicial. O sistema explicou a insuficiência do
contexto e não apresentou uma definição externa de fotossíntese. A resposta foi
produzida pelo tratamento local, sem chamar a API.

### T05 — produto diferente do anunciado

As cinco fontes descrevem produto ou estampa diferentes do anúncio. A resposta
resume essa divergência e cita os trechos correspondentes, sem atribuir volume
ou prevalência global ao problema.

### T06 — prazo de entrega atual

As fontes recuperadas abordam prazo e entrega em relatos históricos. A resposta
reconhece que esses comentários não permitem informar o prazo atual da empresa.

### T07 — percentual de atrasos

A busca encontra relatos de atraso, mas não fornece a contagem de todos os
pedidos nem um denominador global. A resposta não apresenta percentual. O conjunto
recuperado é uma seleção por relevância, não uma amostra estatística representativa.

### T08 — rastreabilidade de atrasos

As cinco fontes mencionam atraso ou demora. Os trechos citados existem nos
comentários e sustentam a síntese apresentada, sem extrapolação de frequência.

## Limitações

O conjunto é pequeno, tem uma resposta registrada por pergunta e inclui temas usados
no desenvolvimento. As observações não estimam desempenho em perguntas novas nem
garantem ausência de respostas sem fundamento. A revisão acima é qualitativa;
os campos quantitativos de revisão independente permanecem sem preenchimento.

## Registros

- [T01](evidencias/T01.json)
- [T02](evidencias/T02.json)
- [T03](evidencias/T03.json)
- [T04](evidencias/T04.json)
- [T05](evidencias/T05.json)
- [T06](evidencias/T06.json)
- [T07](evidencias/T07.json)
- [T08](evidencias/T08.json)

Os exemplos de respostas e comentários estão em [exemplos de execução](exemplos_reais.md).
