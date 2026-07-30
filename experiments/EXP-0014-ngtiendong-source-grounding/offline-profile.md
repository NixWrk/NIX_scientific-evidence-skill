# Offline-профиль для `research-agent`

## Включено

- `references/source_grounding.md`;
- `_agents/rules/source_ingestion.md`;
- `_agents/rules/claim_verification.md`;
- чтение уже нормализованного Zotero HTML;
- матрица источников и проверка утверждений;
- локаторы блока для каждого фактического тезиса.

## Отключено

- весь default workflow как единый автономный процесс;
- поиск, загрузка и добавление публикаций;
- closest-prior-work и novelty gate;
- формулирование новой гипотезы;
- planning, pilot, implementation и experiment protocol;
- рекомендации по направлению исследования;
- любые внешние LLM, API и сетевые инструменты.

Статус `inspected` означает, что текущий Codex-агент прочитал локальное полное
представление источника. Метаданные или аннотация сами по себе дают только
`abstract-only`. В матрице и claim table обязательны `source_id` и один или
несколько локаторов `block_id`; upstream-шаблоны этих полей не требуют, поэтому
это обязательное расширение профиля.
