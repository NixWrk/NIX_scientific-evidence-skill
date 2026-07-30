# EXP-0018 — результат

## Вердикт

`out_of_scope`; scientific corpus не использовался.

`academic-paper-strategist` не обрабатывает имеющиеся данные в один из трёх
разрешённых результатов. Он выбирает preprint platform, ищет 35–50 работ через
Exa/Tavily, генерирует gaps, вычисляет «процент сходства», прогнозирует impact и
создаёт publication-ready outline. При неудаче workflow предлагает новый поиск
или pivot research direction. Это исследовательское и публикационное
планирование.

## Формат и переносимость

Исходный `SKILL.md` не проходит локальный Agent Skills subset: имя
`academic-paper-strategist` не совпадает с каталогом `strategist`, а description
длиной 1050 символов превышает предел 1024. Файл содержит 670 строк по
валидатору, выше рекомендованных 500. Локальный script дополнительно импортирует
`python-dateutil`, но dependency manifest отсутствует.

## Скрипты

`evaluate_samples.py` компилируется, но его gate проверяет только распределение
дат, средний вручную заданный relevance score и число уникальных author strings.
Adversarial fixture из восьми пустых записей, у которых все quality indicators
равны false, прошёл gate после присвоения score=10 и подходящих дат/имён.

`gap_analysis.py` не компилируется на Python 3.11: строка 334 использует
same-quote nested f-string синтаксис. Даже вне этой ошибки validator проверяет
citation и quote только на непустую строку — три повторённых или вымышленных
фрагмента удовлетворили бы формальному evidence count.

Отчёты используют символы `✓`/`⚠`; активный Windows stdout cp1251 не может их
напечатать без явного UTF-8 и завершает выполнение `UnicodeEncodeError`.

## Решение для набора

Не устанавливать и не извлекать шаблон research gap или outline: сами эти
результаты запрещены областью проекта, а численные пороги не калиброваны.
Reviewer checklist уже лучше и безопаснее покрыт EXP-0015 без originality,
impact и platform-fit scoring.
