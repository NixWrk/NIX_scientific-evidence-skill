# EXP-0017 — результат

## Вердикт

`rejected_as_is`; доступ к корпусу не предоставлен.

Skill не имеет режима «синтезировать уже предоставленные публикации». Его пять
фаз обязательны: topic → arXiv API → DeerFlow task-subagents → synthesis → файл.
Это прямо нарушает два условия репозитория: supplied corpus only и отсутствие
API. Обойти фазы означало бы тестировать новый, ещё не существующий fork.

## Методологическая проблема

Результат top-N одного arXiv query называется systematic literature review, хотя
нет заранее заданных eligibility criteria, независимого screening, поиска в
нескольких источниках, full-text extraction, risk-of-bias или certainty
assessment. Извлечение выполняется по abstracts. Поэтому даже успешный запуск не
был бы эквивалентен SLR или PRISMA-совместимому обзору.

Потеря трассировки тоже фундаментальна: subagent возвращает свободные поля
`research_question`, `methodology`, `key_findings`, `limitations`, но не source
span/locator. Формулировка разрешает ограничения, которые «obviously missing»,
то есть не обязательно заявлены авторами. Затем из этих полей строятся themes и
gaps без обратной связи с фрагментом источника.

## Код и штатные проверки

`arxiv_search.py` компилируется; без сети прошли нулевой CLI-вызов, построение
query и нормализация modern/legacy IDs. Два JSON-набора содержат пять workflow
eval definitions и 20 trigger cases, но исполняемого eval runner нет. Проверки
оценивают вызов arXiv, batching и формат, а не достоверность итоговых тезисов.

Дополнительный риск: endpoint задан как `http://export.arxiv.org/api/query`, то
есть первый сетевой переход не аутентифицирован. Live-вызов намеренно не сделан.

## Решение для набора

Не устанавливать и не адаптировать по месту. Общая идея themes/convergences/
disagreements уже лучше реализуется EXP-0003 вместе с source-grounding и claim
gate, где сохраняются локаторы полного Zotero HTML. Шаблоны citation formatting
не дают уникальной ценности, достаточной для fork этого workflow.
