# Decisões técnicas

| Decisão | Motivo | Contrapartida |
| --- | --- | --- |
| Utilizar o CSV de avaliações | Concentrar a solução no conteúdo textual do desafio | Sem cruzamento com categorias e eventos de entrega |
| Combinar título e mensagem | Aproveitar registros com apenas um dos campos preenchido | Títulos podem ser genéricos |
| Preservar acentos, negações e pontuação | Manter o sentido dos relatos | Permanecem erros de escrita e ruídos |
| Remover apenas duplicatas exatas | Evitar exclusão de registros distintos com IDs repetidos | Textos iguais podem existir na população |
| Criar identificador técnico por hash | Garantir rastreabilidade do documento | Alterar o registro modifica o identificador |
| Usar embeddings multilíngues locais | Processar português sem serviço externo de embeddings | Exige download inicial e recursos locais |
| Persistir o índice no Chroma | Reutilizar vetores e permitir filtros por metadados | A busca HNSW é aproximada |
| Dividir por tokens quando necessário | Evitar truncamento silencioso | Fragmentos precisam manter vínculo com a avaliação |
| Selecionar até cinco fontes | Limitar o contexto e permitir inspeção | Não cobre todos os relatos relevantes |
| Evitar repetição de texto no contexto | Reduzir redundância entre as fontes | Não garante diversidade temática |
| Aplicar limiar de 0,45 | Descartar parte dos vizinhos pouco relacionados | Heurística não calibrada estatisticamente |
| Exigir resposta estruturada | Validar status, achados e citações | Uma saída válida pode conter inferências inadequadas |
| Usar Streamlit | Implementar a interface em Python | Execução local, sem requisitos de produção |

## Modelo de geração

O ambiente avaliado utilizou `gemini-3.5-flash-lite`. A conexão e a saída estruturada
foram confirmadas. O modelo `gemini-3.8-flash` havia retornado 504 no teste de
conexão. Essa troca foi operacional; não constitui comparação de qualidade entre modelos.

O nome é configurável por `GEMINI_MODEL`. Falhas de autenticação, cota, serviço e
validação são diferenciadas de insuficiência de evidências. O sistema não muda de
modelo nem ativa cobrança automaticamente.

## Indexação e rastreabilidade

O índice completo contém 42.687 avaliações e 42.688 unidades vetoriais, com 384
dimensões. Uma avaliação ultrapassou 128 tokens e foi dividida. Perguntas e
documentos usam o mesmo modelo de embeddings; o manifesto registra a revisão
quando ela é disponibilizada pelo carregamento. Na execução documentada, esse campo
ficou nulo, o que limita a reprodução exata do artefato do modelo.

O manifesto registra hash dos documentos, parâmetros, população e versões. Cada
consulta registra pergunta, filtros, fontes, modelo de geração, hash do prompt,
resposta e tempos. IDs e trechos citados são verificados antes da apresentação.

## Interpretação

O projeto realiza síntese qualitativa de relatos recuperados. Quantificar temas em
toda a base exigiria classificação, definição de denominadores e agregação própria.
Não foi realizado treinamento supervisionado nem ajuste fino do modelo de linguagem.

As avaliações são históricas e refletem a percepção de quem escreveu. Não permitem
afirmar causa raiz, política institucional ou situação operacional atual.
