# Experiments

Каждый эксперимент хранится в отдельном каталоге:

```text
experiments/EXP-0001-short-name/
  manifest.yaml
  task.md
  gold.jsonl
  outputs/
  audit.json
  report.md
```

## Обязательные правила

- Один `experiment_id` соответствует одной неизменной конфигурации.
- Изменение корпуса, модели, инструмента, skill, prompt или параметров создаёт новый эксперимент.
- Закрытые полные тексты и конфиденциальные результаты не коммитятся.
- В репозитории можно хранить Zotero item key, хэши и локаторы, если они не раскрывают закрытое содержание.
- Сырые ответы сохраняются до нормализации, но для закрытого корпуса остаются только локально.
- Итоговый `report.md` обязан перечислять критические ошибки, а не только среднюю оценку.

## Минимальный manifest

```yaml
experiment_id: EXP-0001
task: qa
corpus_id: CORPUS-001
input_representation: zotero_html
tool: direct-zotero-html
tool_version: baseline-v1
model: null
skill: null
prompt_hash: null
corpus_hash: null
started_at: null
completed_at: null
```
