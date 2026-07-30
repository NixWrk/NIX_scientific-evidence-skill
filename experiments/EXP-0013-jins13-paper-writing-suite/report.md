# EXP-0013 — результат предварительного аудита

## Промежуточный вердикт

`eligible_for_content_smoke` только с `offline-profile.md` и только на проекте,
где пользователь уже предоставил результаты исследования.

Это наиболее развитый из проверенных writing-наборов по механическим гарантиям.
Он содержит строгие схемы research handoff, numeric evidence, citation lock и
paper state. Числа в Results/Experiments и таблицах могут пересчитываться из
JSON/JSONL/CSV/TSV, а terminal gate закрывается при неразрешённых доказательствах,
цитатах, blockers или устаревшем build.

## Штатные тесты

На Windows прошли 27 из 28 тестов. Покрыты fail-closed citation lock,
пересчёт числового происхождения, строгий research handoff, stale build,
нечитаемый UTF-8 и защита распаковки от path traversal.

Единственный сбой — выполнение записанной build-команды: `record_build.py`
разбирает строку POSIX-функцией `shlex.split`, поэтому некавыченный Windows-путь к
`python.exe` теряет обратные слеши и превращается в `J:PCpythonpython.exe`.
Остальные 15 скриптов компилируются; используются только модули стандартной
библиотеки.

## Offline-граница

Сеть локализована в `verify_citations.py` и `fetch_template.py`, subprocess — в
`record_build.py`. Эти ветки отключаются вместе с image generation, подбором
литературы, venue и submission packaging. Локально остаются проверка `.bib`,
существующего citation lock, числового происхождения, handoff, TODO, build log и
общего paper contract.

Содержательная reviewer-ветка также требует ограничения: она может ослабить или
удалить неподдержанное утверждение, но не должна проектировать эксперимент или
расширять корпус.

## Почему corpus run пока не выполнен

Текущий Zotero-набор содержит публикации, но не отдельный research project с
авторскими raw results, experiment logs и manuscript state, для которых создано
главное преимущество кандидата. Прогон на одной опубликованной статье повторил бы
EXP-0010/0011 и не проверил бы numeric-evidence/handoff contracts.

Следующий честный тест должен использовать предоставленный проект исследования:
заморозить raw results, построить `numeric_evidence.json`, связать claims с
локаторами и сравнить итоговый раздел статьи с YSLAB revision baseline. До этого
кандидат не включается в основной набор.
