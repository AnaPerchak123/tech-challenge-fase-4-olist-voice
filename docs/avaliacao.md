# Método de avaliação

A avaliação é exploratória, com oito casos definidos e quatro execuções registradas.
Os temas incluem exemplos usados no desenvolvimento; não são um conjunto independente
ou representativo das perguntas de usuários.

## Dimensões

1. Relevância das avaliações selecionadas para a pergunta.
2. Sustentação das afirmações pelas fontes citadas.
3. Respeito aos filtros de nota e ao período histórico.
4. Reconhecimento de perguntas sem suporte.
5. Distinção entre falha técnica e abstenção.
6. Latência após o carregamento do modelo.

## Execução

```powershell
.\.venv\Scripts\python.exe avaliar.py --limit 4
```

O script registra resposta, fontes e diagnóstico de cada caso. Execuções concluídas
da mesma configuração são reutilizadas; as que falharam podem ser retomadas. Erro
429 interrompe o lote. `--reprocessar` gera respostas novas.

Os registros locais ficam em `outputs/evaluation/`. O CSV `evaluation_summary.csv`
reúne metadados e campos de revisão; os JSONs publicados em `docs/evidencias/`
documentam os quatro casos selecionados.

## Critérios de revisão

Uma fonte relevante deve tratar do tema investigado, não apenas compartilhar palavras.
Uma afirmação sustentada deve estar apoiada no conteúdo da fonte, sem inferir
causalidade, frequência global ou condições atuais não demonstradas.

A validação automática confirma a existência do rótulo e do trecho literal. Ela
não demonstra que a conclusão decorra da citação. O status do próprio modelo e a
ausência de exceção não são critérios suficientes de acerto.

Os campos quantitativos de revisão permanecem em branco no CSV publicado. Não foi
calculada acurácia nem taxa de fundamentação. As observações qualitativas estão no
[relatório de resultados](avaliacao_resultados.md).

Quando preenchidos, os campos de relevância e sustentação devem informar numerador
e denominador. Uma razão 0/0 é indefinida; casos não revisados não são acertos.
Recall exige um conjunto de referência de documentos relevantes e não foi medido.

## Latência

O tempo exclui carregamento do modelo e considera uma execução por caso. A abstenção
local sem chamada à API deve ser distinguida das consultas com geração. Esses dados
não caracterizam teste de carga nem uma distribuição estável de desempenho.
