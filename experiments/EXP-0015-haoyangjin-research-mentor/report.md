# EXP-0015 — результат

## Вердикт

Полный `research-mentor` требует извлечения допустимого подмножества и получает
`adapt_required`. Изолированный reviewer-checklist проходит содержательный тест
с offline-профилем.

## Результат прогона

На исходном Abstract Aamodt et al. reviewer-mode нашёл пять существенных проблем
калибровки: безусловную feasibility, причинное прочтение self-care, отсутствие
показателей полноты, пропущенные ограничения и риск неверно представить
readmissions как результат. Правки ограничены имеющимся полным текстом и не
потребовали нового поиска или эксперимента.

Это полезный дополнительный red-team проход. Однако в стандартном Operating
Procedure reviewer должен связывать замечания с acceptance risk и указывать
дополнительные evidence/fixes. Reference-файлы прямо предлагают новые
эксперименты, ablations, venue comparison и submission planning. Для нашего
проекта такие ветви нельзя оставлять доступными по умолчанию.

## Переносимость

В репозитории 22 отслеживаемых файла, нет исполняемого кода и штатных тестов.
`SKILL.md` проходит статический формат после установки в документированный
каталог `research-mentor`; произвольное имя каталога клона даёт только ошибку
совпадения имени. Лицензия — MIT.

## Сравнительное решение

YSLAB `manuscript-writing` остаётся основным revision/review skill. У
`research-mentor` имеет смысл сохранить только порядок «major concerns → why →
bounded textual fix» и чеклисты drafting/self-review. Mentor, mixed, literature
planning, hypothesis, experiment, rebuttal и submission phases исключаются.
