# Exemplos de execução

Modelo: `gemini-3.5-flash-lite`. Índice completo: 42.687 avaliações e 42.688 unidades vetoriais.

## T01

**Pergunta:** O que os clientes relatam sobre atraso na entrega?

- Clientes relataram atrasos e demora nas entregas. [E1] [E2] [E3] [E4] [E5]

Limitações: A base recuperada contém apenas uma amostra limitada de cinco avaliações, não representando a totalidade da base histórica nem um ranking global de frequência.

**[E1]** Nota 1 · review_id `7c4c2d10a57d4aab58a570a5a8ac9f2c`

> Gostaria de esclarecimentos acerca da entrega que está em atraso

**[E2]** Nota 1 · review_id `0fc42b14539f4177f534382d69d82d3c`

> demora na entrega

**[E3]** Nota 2 · review_id `18215615f60e6771c00faaaa1ade4cea`

> Compra Um demora pra entrega

**[E4]** Nota 1 · review_id `7528a396f7625967f05cb09946286608`

> Ultimamente estão atrasando muito as entregas

**[E5]** Nota 1 · review_id `72926e5236768ffc912764ca429d0e00`

> Muita demora na entrega

Tempo após carregar o modelo: 3.117 s.

[Registro da execução](evidencias/T01.json)

## T02

**Pergunta:** O que os clientes elogiam sobre a entrega?

- Clientes relataram satisfação geral com a entrega e cumprimento de prazo. [E1] [E2] [E4]

Limitações: O escopo dos relatos recuperados é limitado e não representa a totalidade da base histórica.

**[E1]** Nota 5 · review_id `37c35442208c3077f15ff19e742e0c3e`

> Satisfeito com a entrega... atendimento e produto

**[E2]** Nota 5 · review_id `715d3f3f7ef4c0d9dc0e8fc2b7d64d3c`

> Com relação à compra e entrega, só tenho a elogiar. Muito obrigada!

**[E3]** Nota 5 · review_id `a807ea65e5f33c7fdc436a6e95676660`

> relogio de parende muito satisfeito com o produto e a entrega

**[E4]** Nota 5 · review_id `6c612bde41f4ce34be1b41efb17aa695`

> Prazo cumprido, qualidade presente entrega o que vende

**[E5]** Nota 5 · review_id `891251e205309fb9fdc3a1f63d113120`

> Ótima Satisfação ao cliente

Tempo após carregar o modelo: 2.930 s.

[Registro da execução](evidencias/T02.json)

## T04

**Pergunta:** O que é fotossíntese?

As avaliações recuperadas não atingiram o critério inicial de relevância. Reformule a pergunta ou investigue outro tema.

Limitações: A ausência de fontes adequadas nesta busca não prova ausência do tema em toda a base.

Tempo após carregar o modelo: 0.034 s.

[Registro da execução](evidencias/T04.json)
