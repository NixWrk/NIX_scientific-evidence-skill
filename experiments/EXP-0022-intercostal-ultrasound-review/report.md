# EXP-0022 — отчёт

## Что проверено

Проверен режим `literature_review` собственного
`scientific-evidence-workflow` на восьми публикациях из Zotero collection
`TE9MV9FY`. Контроль — обзор того же корпуса тем же Codex-агентом без загрузки
файлов скилла в direct-фазе.

## Как проверено

Сначала зафиксированы состав коллекции, Zotero item versions и единый вопрос.
Служебный document `00. анализ` исключён до чтения. Затем прочитаны metadata и
доступный full text восьми journal articles. Direct review сохранён и
хеширован. После этого загружены `SKILL.md`, evidence contract и
literature-review workflow; созданы восемь study cards, cross-study matrix,
31 evidence record и 12 claim records. Связный skill review написан только после
успешной валидации bundle.

Проверялись охват источников, точность 12 групп чисел, выявление ретракции,
границы клинической интерпретации, source/locator consistency, rejected evidence
и добавление отсутствующих источников или данных.

## Результат

Обе версии охватили 8/8 публикаций, не добавили источников или чисел, корректно
сверили 12/12 числовых групп и исключили Ramaswamy et al. как ретрагированную
работу. Основной научный вывод совпал.

Skill-ветка дополнительно дала 31 atomic evidence locator, 12 claims, девять
явных applicability boundaries, один dropped unsupported claim и ноль
locator/source mismatches. Валидатор завершился с нулём ошибок и предупреждений.
Skill review имеет 1600 слов против 1234 в direct review.

## Решение

Вердикт: `pass_for_auditability_no_demonstrated_accuracy_gain_nonblind`.

Использовать скилл как внутренний evidence-first pipeline и хранить bundle рядом
с обзором. Для пользовательского текста уменьшать повторение и при необходимости
выносить ledger в приложение. Для доказательства прироста научной точности нужен
слепой прогон на новом корпусе моделью, которая ранее не видела скилл, либо
независимый human audit.
