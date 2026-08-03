# Подробный отчёт о тестировании репозиториев со skills

Дата отчёта: 3 августа 2026 года.

## 1. Назначение отчёта

Этот документ консолидирует результаты проверки всех 16 репозиториев из
[`registry/skill-test-queue.yaml`](../registry/skill-test-queue.yaml). Для каждого
репозитория указаны:

- зафиксированная версия исходного кода;
- проверенные skills и файлы;
- применённые статические, функциональные и содержательные проверки;
- полученные результаты;
- обнаруженные ограничения и ошибки;
- итоговое решение о применении в проекте.

Исходный поисковый список пользователя сохранён отдельно в
[`skill-search-report-2026-07-30.md`](skill-search-report-2026-07-30.md). Оценки
`A`–`D` в нём считались гипотезами отбора, а не результатами тестов. Проверенными
считаются только артефакты `EXP-*`, перечисленные ниже.

## 2. Граница и методика проверки

### 2.1. Допустимая область

Skill допускался к содержательному прогону только в том случае, если его итогом
мог быть один из трёх результатов:

1. вопрос/ответ по предоставленному корпусу;
2. литературный обзор по предоставленному корпусу;
3. итоговая статья по предоставленным результатам и литературе.

Не принимались как целевые режимы:

- самостоятельный поиск и расширение корпуса;
- генерация research gaps, гипотез и планов нового исследования;
- выбор журнала, оценка вероятности принятия и submission strategy;
- оценка людей, ранжирование, funding/hiring decisions;
- вызовы внешней LLM или модельного API.

### 2.2. Среда и корпус

- Доступ к публикациям: Zotero MCP.
- Основное представление: нормализованный HTML полного текста.
- Резервное представление: PDF для страниц, рисунков и сложных таблиц.
- Исполнитель: текущий Codex-агент; внешняя LLM/API не использовалась.
- Сеть при содержательной обработке корпуса: запрещена.
- Исходный пилотный корпус EXP-0001: 8 публикаций, 46 777 слов, 980 блоков.
- Каждый блок имел стабильный идентификатор вида `SRC-AAR-002-B0080`.
- Исходный код сторонних репозиториев клонировался во временные каталоги и не
  включался в этот репозиторий.

### 2.3. Этапы одного теста

Для каждого кандидата применялся доступный набор из девяти этапов:

1. фиксация URL, commit, лицензии и SHA-256 `SKILL.md`;
2. инвентаризация файлов, scripts, references и побочных записей;
3. аудит сети, API, внешних моделей, subprocess и изменения состояния;
4. запуск upstream-тестов, если они существовали;
5. проверка соответствия области проекта;
6. создание offline-профиля, только если запрещённые ветви можно было полностью
   отключить;
7. содержательный smoke-test на замороженном входе;
8. проверка локаторов и чисел;
9. сравнительный verdict.

`Out_of_scope` и `rejected_as_is` кандидаты намеренно не получали научный корпус:
это защитное срабатывание scope/policy gate, а не пропуск проверки.

### 2.4. Значение verdict

| Verdict | Значение |
|---|---|
| `conditional_pass` | Кандидат полезен после явно записанных ограничений и проектного слоя трассировки. |
| `pass_with_offline_profile` | Принят только в конкретном offline-профиле без сети, API и нецелевых ветвей. |
| `adapt_required` | Исходный skill нельзя применять как есть; нужен fork или извлечение существенного подмножества. |
| `rejected_as_is` | В исходной архитектуре отсутствует целостный допустимый режим. |
| `out_of_scope` | Основной результат skill не относится к трём задачам проекта. |
| `eligible_for_content_smoke` | Статические и механические проверки пройдены, но честный содержательный тест требует ещё не предоставленного входа. |

Эти verdict не являются рейтингом авторов или абсолютной оценкой качества
репозитория. Они отвечают только на вопрос пригодности для данного проекта.

## 3. Сводная таблица решений

| № | Репозиторий | Проверенные кандидаты | Итоговое решение |
|---:|---|---|---|
| 1 | `K-Dense-AI/scientific-agent-skills` | `hypothesis-generation`, `scientific-critical-thinking`, `scholar-evaluation`, `literature-review` | Использовать critical Q&A и qualitative scholar review с offline-профилями; hypothesis и literature-review не использовать. |
| 2 | `stephenturner/skill-focus` | `focus` | Нужен локальный fork; исходный skill разрушает трассировку. |
| 3 | `mjkmain/paper_skills` | `paper-reader`, `paper-wiki`, `topic-literature`, `paper-collector` | Reader требует адаптации; wiki/topic заблокированы; collector вне области. |
| 4 | `borghei/Claude-Skills` | `research/litreview` | До корпуса не допущен; алгоритмы scoring и synthesis требуют переписывания. |
| 5 | `Master-cai/Research-Paper-Writing-Skills` | `research-paper-writing` | Условно принять как секционный writing-каркас. |
| 6 | `YSLAB-ai/manuscript-writing` | `manuscript-writing` | Принять как основной универсальный revision/review skill. |
| 7 | `WantongC/journal-adapt-writing-skill` | `journal-adapt` | Не использовать: обязательный результат — journal adaptation и publication fit. |
| 8 | `jin-s13/paper-writing-suite` | `ai-research-writing-skill` и локальные gates | Механически перспективен; content smoke заблокирован до предоставления raw research results. |
| 9 | `ngtiendong/Academic-Research-Agent-Skill` | `source_grounding`, `claim_verification`, `novelty_gate` | Сохранить grounding/claim gate; novelty и полный lifecycle исключить. |
| 10 | `HaoYangJin/Research-workflow-Skill` | `research-mentor` | Сохранить только reviewer-checklist; полный mentor workflow требует адаптации. |
| 11 | `keemanxp/slr-prisma` | `slr-prisma` | Сохранить только audit уже проведённого обзора; не реконструировать отсутствующий PRISMA process. |
| 12 | `bytedance/deer-flow` | `academic-paper-review`, `systematic-literature-review` | Внутренний review требует извлечения; SLR workflow отклонён. |
| 13 | `lishix520/academic-paper-skills` | `strategist` | Не использовать: вне области и содержит механические/алгоритмические дефекты. |
| 14 | `WenyuChiou/research-hub` | `literature-triage-matrix`, `paper-summarize` | Матрицу принять условно; summarizer отклонить. |
| 15 | `WenyuChiou/academic-writing-skills` | `academic-writing-skills` | Принять как независимый claim–evidence gate, не как основной редактор. |
| 16 | `Imbad0202/academic-research-skills-codex` | `academic-research-suite` | Монолитный suite не использовать; пересмотреть только после выделения малых workflows. |

## 4. Подробные результаты по репозиториям

### 4.1. `K-Dense-AI/scientific-agent-skills`

#### Зафиксированная версия

- Основной проверенный commit:
  `ab2f84ab10597c59fac186ecda6d5edd5dcc8b92`.
- Лицензия проверенных skills: MIT.
- Эксперименты: [EXP-0004](../experiments/EXP-0004-kdense-hypothesis-generation/report.md),
  [EXP-0005](../experiments/EXP-0005-kdense-critical-thinking/report.md),
  [EXP-0006](../experiments/EXP-0006-kdense-scholar-evaluation/report.md) и
  [EXP-0020](../experiments/EXP-0020-kdense-scholar-evaluation-content/report.md).

#### `hypothesis-generation`

Проверено:

- `SKILL.md`: 264 строки, SHA-256
  `e18e00ed9bd98939f57254b627b6db52c276f7c2f0ae2eac52da89fdd896ad49`;
- Agent Skills subset;
- Python scripts на сетевые импорты, внешние модели и subprocess;
- обязательная последовательность workflow;
- upstream-тесты на Windows.

Как проверялось:

- статический форматный аудит;
- ручной policy-аудит обязательных шагов;
- штатный test suite на синтетических fixtures;
- scope gate до доступа к научному корпусу.

Результат:

- формат пройден;
- сетевых импортов, внешней модели и subprocess в рабочих scripts не найдено;
- тесты: `26 passed, 1 failed`;
- единственный сбой — POSIX-проверка режима файла `0600`: Windows сообщил
  `0666`;
- обязательный шаг 4 требует литературного поиска;
- основной выход — гипотезы, прогнозы и research plan.

Решение: `out_of_scope`. Не устанавливать и не адаптировать для этого проекта.
Научный корпус модулю не передавался.

#### `scientific-critical-thinking`

Проверено:

- версия 1.2, SHA-256
  `48a3b32aa9273343dacae7532546a2fee375b148bb467305905b0ca169c1d3b0`;
- critical Q&A по замороженной матрице трёх публикаций из EXP-0003;
- отделение дизайна, наблюдения, интерпретации и ограничений;
- обработка внутренних противоречий и недостатка данных;
- производная трассировка до исходных блоков.

Как проверялось:

- optional OpenRouter figure branch отключена;
- research-design guidance исключена;
- входом служила зафиксированная матрица с SHA-256
  `7e725bba7566efd606bc143570e89f98109c666525541a78dd7505629c109d37`;
- выход проверен `validate_reference_subset.py`.

Результат:

- сохранён конфликт `N=131` против `N=139`;
- feasibility не превращена в clinical efficacy;
- формальный GRADE/RoB score не придуман при недостаточном входе;
- 34 ссылки, 21 уникальный `block_id`, добавленных/потерянных идентификаторов — 0.

Ограничение: тест проверял дисциплину критического ответа по уже подготовленной
матрице, а не полноту извлечения из полного HTML.

Решение: `conditional_pass` для critical Q&A с offline-профилем и обязательными
локаторами.

#### `scholar-evaluation`

Проверено:

- версия 2.1, `SKILL.md` 296 строк, SHA-256
  `14da13ae10564125d953fe6ab82760932ca119f963c69225667fbc82ff060405`;
- 19 файлов, включая 8 Python-файлов;
- hard boundary против person ranking и consequential decisions;
- local JSON/CSV tooling;
- static audit и затем отдельный содержательный тест исходного Abstract
  `SRC-AAR-002`.

Как проверялось:

- все upstream-тесты запущены на Windows;
- проверены отсутствие сети, модели, subprocess и чтения source text scripts;
- для content smoke определён узкий construct: поддержка и калибровка
  утверждений Abstract;
- ordinal ratings, weights, composite score и publication decision отключены;
- output проверен по нормализованным блокам и отдельным numeric audit.

Результат:

- upstream: `27 passed, 0 failed`;
- Agent Skills subset: pass;
- objective, design, self-care change и completion evidence распознаны как
  проверяемые;
- feasibility ограничена выборкой и support conditions;
- predictive utility и readmissions оставлены неустановленными;
- `literature_contribution` получила статус `not_assessed`, а не score 0;
- 20 ссылок, 11 уникальных блоков, отсутствующих — 0;
- новых числовых утверждений — 0.

Scoring toolkit не принят: upstream template прямо содержит
`content_validity_status: not_established` и требует минимум двух подготовленных
raters.

Решение: `pass_with_offline_profile` только для qualitative developmental review
scholarly work без score, ранжирования и публикационного решения.

#### `literature-review`

Проверено статически:

- основной workflow;
- зависимости от внешнего поиска и сервисов;
- ветвь AI figure generation;
- соответствие closed-corpus policy.

Результат: primary workflow расширяет корпус через внешний поиск, зависит от
внешних сервисов и генерации рисунков. Содержательный запуск не выполнялся.
Для этого кандидата в раннем реестре был сохранён путь `main`, а не отдельный
commit; перед любым будущим пересмотром статический аудит необходимо повторить
на новом frozen snapshot.

Решение: `rejected_as_is`.

#### Итог по репозиторию

В рабочий набор входят только:

- `scientific-critical-thinking` как дополнительный critical Q&A;
- qualitative ветвь `scholar-evaluation` без scoring.

`hypothesis-generation` и `literature-review` исключены.

### 4.2. `stephenturner/skill-focus`

#### Зафиксированная версия

- Commit: `84e521dcf0a44786500cce60bac6ddf00c63b3e8`.
- Лицензия: MIT.
- `SKILL.md`: 85 строк, SHA-256
  `4ae85fe0e51267ab2c402fc5b1b4e689595291d1c9699de331d6820aefca79a5`.
- Эксперимент: [EXP-0007](../experiments/EXP-0007-focus-detailed-qa/report.md).

#### Что и как проверялось

- формат Agent Skills;
- двухстадийный процесс «подробное извлечение → организация»;
- правила очистки citations/links;
- требование direct quotes;
- наличие claim-to-locator schema;
- содержательный detailed Q&A по полному Zotero HTML одной статьи;
- автоматическая проверка всех локаторов.

Upstream scripts и tests отсутствовали. Полный вход содержал 185 блоков и
9 149 слов; его SHA-256 совпал с snapshot EXP-0001.

#### Результат

- frontmatter объявляет `name: focus`, а корень репозитория называется
  `skill-focus`; прямой format gate не проходит;
- Step 2 требует удалить citation markers, reference links, URL и DOI;
- direct quotes требуются практически в каждом пункте;
- нет схемы `claim → locator` и явного разделения source content от аналитической
  оценки;
- после существенной адаптации получен полезный подробный Q&A;
- 41 ссылка, 30 уникальных блоков, отсутствующих — 0.

#### Решение

`adapt_required`. Не устанавливать upstream как есть. Для повторного применения
нужен локальный fork, который меняет центральную очистку, сохраняет локаторы и
не требует повсеместных прямых цитат.

### 4.3. `mjkmain/paper_skills`

#### Зафиксированная версия

- Commit: `9b9c4a57138501d17992fa639ff44d469b3a9f3e`.
- Файл лицензии не найден.
- Upstream-тесты не предоставлены.
- Эксперимент: [EXP-0008](../experiments/EXP-0008-paper-skills-reader/report.md).

#### Что проверялось

| Skill | Строк | SHA-256 | Проверка |
|---|---:|---|---|
| `paper-reader` | 294 | `1f6f784cec30f5fd9116e584cc16338237deb212e721b715f5510ef8ce032694` | Static audit и content smoke. |
| `paper-wiki` | 462 | `685f3c1f59132fe08d6113d31523e62ad2898adc571caa9a6b6a1e8724f6a46c` | Static/policy audit цепочки наследования фактов. |
| `topic-literature` | 552 | `346647a628ee983547ba1fbaab9c529012eb7db584f4c9bd2023bb0ffd824bfc` | Static/policy audit синтеза из wiki. |
| `paper-collector` | 301 | `ef919f35a39fb948316f49691066c4f236e42ae76ce95dab01442c0b035e7b23` | Scope gate. |

Проверялись разрешённые tools, fallback по metadata, пути записи,
распространение локаторов между слоями, destructive rebuild и ветви расширения
корпуса.

#### `paper-reader`: результат

Адаптированный профиль сформировал компактную карточку статьи с целью, методом,
числами, сильными сторонами и ограничениями. Трассировка: 46 ссылок, 27
уникальных блоков, отсутствующих — 0.

Исходный skill при этом:

- разрешает `Agent`;
- пишет в общие `reference/notes` и `index.md`;
- не требует source locators;
- допускает заметку по abstract/metadata при сбое PDF, что противоречит его же
  запрету генерировать note только из metadata.

Verdict: `adapt_required`.

#### `paper-wiki` и `topic-literature`: результат

Цепочка остановлена до корпуса, потому что:

- notes не имеют обязательной claim-level трассировки;
- `paper-wiki` заменяет источник `[[wikilink]]` и объявляет derived graph
  источником истины для отношений;
- `topic-literature` предпочитает wiki как первичный источник, обращаясь к paper
  notes преимущественно за числами;
- ошибка первого пересказа может пройти два последующих слоя как установленный
  факт;
- присутствуют corpus-expansion, gaps и reading-list ветви;
- `paper-wiki` имеет destructive rebuild path.

Verdict: `blocked_before_content_smoke` до введения сквозной схемы
`claim_id → source block`.

#### `paper-collector`: результат

Основная функция — поиск/сбор новых публикаций, поэтому verdict `out_of_scope`.

#### Решение по репозиторию

Не устанавливать комплект целиком. Reader можно воспроизвести только после
адаптации; wiki/topic не использовать до исправления evidence chain и появления
явной лицензии.

### 4.4. `borghei/Claude-Skills`

#### Зафиксированная версия

- Commit: `da5a8626632f08c5513b0f73add1bf8075ef83bd`.
- Candidate: `research/litreview`, версия 1.0.0.
- `SKILL.md`: 181 строка, SHA-256
  `debc8707bdc8d55c5ef240601742fc6ac7454c85ead8a7194e88f077fd237caa`.
- Лицензия: MIT с Commons Clause 1.0; внутреннее тестирование разрешено,
  коммерческая продажа/сервис ограничены.
- Эксперимент: [EXP-0009](../experiments/EXP-0009-borghei-litreview/report.md).

#### Что и как проверялось

Проверены три Python-script:

- `search_strategy_builder.py`, 234 строки;
- `source_quality_scorer.py`, 265 строк;
- `thematic_synthesis_builder.py`, 245 строк.

Применены:

- compile/help/import/argparse/format checks штатного integration runner;
- статический аудит сети, внешней модели и subprocess;
- adversarial fixtures для quality scoring;
- adversarial fixtures для дубликатов, независимых источников и потери
  `claim_id`/locator;
- пустой JSON и PowerShell UTF-8 BOM;
- scope gate до научного корпуса.

#### Результат штатных тестов

Integration runner сообщил `3 passed, 0 failed`, но проверял только механическую
запускаемость, а не научную корректность. Все scripts используют standard
library, не вызывают сеть, модель или subprocess.

#### Результат adversarial quality test

- Запись без метода, адекватной выборки и открытых данных/кода получила
  `quality_score=58`, `total_score=75` и `include` благодаря `tier1`, новизне и
  300 citations.
- Более старая RCT-запись с методом, адекватной выборкой и открытыми данными
  получила `quality_score=55`, `total_score=73` и только `candidate`.
- Запись из будущего, 2099 год, также получила `include`.

Причина: prestige площадки даёт до 20 баллов, citation rate — до 10; текущий
системный год используется вместо входного `as_of`.

#### Результат adversarial synthesis test

- три повтора одного `claim_id` из одного источника посчитаны как три источника и
  названы `well-supported`;
- три независимых источника среднего качества названы `anecdotal (single
  source)`;
- исходные `claim_id` и locator исчезли из результата.

Дополнительно все scripts приняли `{}` как успешный пустой вход, но отклонили
обычный PowerShell UTF-8 с BOM.

#### Решение

`adapt_required`, corpus smoke заблокирован. Простого offline-переключателя
недостаточно: нужны уникализация исследований, design-specific risk of bias,
сквозные локаторы и удаление prestige/citation-based quality gate. Исходный код
не включался в benchmark-репозиторий.

### 4.5. `Master-cai/Research-Paper-Writing-Skills`

#### Зафиксированная версия

- Commit: `77e7c2c1ba06f7d71844873147665437a03aac1b`.
- Лицензия: MIT.
- Candidate: `research-paper-writing`.
- `SKILL.md`: 99 строк, SHA-256
  `32c01a68b0d739a4750fd0901c7f021e762fec6851cc7575f32277fe58ccc248`.
- Пакет: 39 файлов, 0 scripts; upstream-тесты отсутствуют.
- Эксперимент: [EXP-0010](../experiments/EXP-0010-master-cai-abstract/report.md).

#### Что и как проверялось

- Agent Skills format и progressive disclosure;
- отсутствие обязательной сети, внешней модели, subprocess и side effects;
- `references/abstract.md`, `paper-review.md` и три abstract template;
- hard constraint «крупное утверждение → evidence»;
- содержательная переработка Abstract `SRC-AAR-002`;
- автоматическая проверка локаторов и отдельный numeric audit.

Offline-профиль запретил:

- добавлять evidence или новый эксперимент вне предоставленного входа;
- брать научные факты/формулировки из example bank;
- усиливать novelty/performance без прямой поддержки;
- использовать память модели как научный источник.

#### Результат

Сформированы outline, структурированный Abstract, self-review и карта из шести
claims. Возможное снижение readmissions не превращено в результат. Feasibility
ограничена 30-дневным процессом, caregiver/nurse support, малой выборкой и
невалидированным ежедневным symptom instrument.

- 17 ссылок;
- 8 уникальных блоков;
- отсутствующих — 0;
- новых числовых утверждений — 0.

#### Решение

`conditional_pass`. Использовать как дополнительный секционный каркас и источник
claim–evidence map, но не как самостоятельный источник содержания. Evidence field
upstream свободное, поэтому проектные `source_id` и locator обязательны.

### 4.6. `YSLAB-ai/manuscript-writing`

#### Зафиксированная версия

- Commit: `f83e99ff87c2dd4a76328e4f2d022685941c7246`.
- Лицензия: MIT.
- `SKILL.md`: 78 строк, SHA-256
  `d56756860bc64910c4e14ec5ac285e3c442a504781ba1c3e26a206a43c4f5803`.
- Обязательный `revision-checklist.md`: 236 строк, SHA-256
  `70da6e8cce77b4d857de27bbb652de895d06797236569ac32298cbd3a6669461`.
- 13 файлов, scripts и upstream-тестов нет.
- Эксперимент: [EXP-0011](../experiments/EXP-0011-yslab-manuscript-writing/report.md).

#### Что и как проверялось

- формат в документированном каталоге `manuscript-writing`;
- native запреты на выдумывание facts, citations, data, mechanisms, numbers,
  novelty и literature context;
- сохранение scope, certainty, causal relation, baseline и чисел;
- разделение review/revision modes;
- sequential checklist phases 0–5;
- парная переработка того же Abstract, что в EXP-0010;
- локаторы и numeric audit.

#### Результат

- временный каталог с произвольным именем дал ожидаемый name mismatch;
  документированная установка прошла format gate;
- переработанный Abstract сохранил design, sample, completion, self-care score и
  `P` value;
- feasibility ограничена caregiver и daily nurse support;
- predictive utility/readmissions не названы установленными;
- 9 ссылок, 8 уникальных блоков, отсутствующих — 0;
- новых чисел — 0;
- неизвестные journal headings/word limit и formal feasibility threshold
  вынесены в `Needs Verification`.

#### Решение

`conditional_pass`. Выбран основным универсальным revision/review skill. Поверх
него остаются обязательными проектная claim–evidence map и validator локаторов.

### 4.7. `WantongC/journal-adapt-writing-skill`

#### Зафиксированная версия

- Commit: `cc79265b0acc21bc488c4c3004d89113cf19335a`.
- Лицензия: MIT.
- Candidate: `journal-adapt`, 490 строк, SHA-256
  `719ad1f535775ef6d59af6fdc881d0fe63aa9fa3c18cf036aa95242d6a1a2e46`.
- 43 файла, scripts и upstream-тестов нет.
- Эксперимент: [EXP-0012](../experiments/EXP-0012-wantongc-journal-adapt/report.md).

#### Что и как проверялось

- формат в исходном каталоге `skill` и после документированной установки в
  `journal-adapt`;
- правила сохранения фактов, equations, citation keys, variables и numbers;
- обязательные Phase 1/Phase 2;
- зависимости от target-journal corpus, MinerU и внешних writing skills;
- scope gate до корпуса.

#### Результат

Положительные свойства:

- запрещено добавлять facts, empirical claims, citations и data;
- reference papers используются для стиля, а не как источник научного текста;
- есть human confirmation gate;
- MinerU опционален для PDF.

Блокирующие свойства:

- Phase 1 обязательно создаёт journal style cards, агрегированный journal
  culture profile и новый `dynamic_writing_skill.md`;
- Phase 2 ставит paragraph-level journal match score и acceptance severity;
- самостоятельного neutral revision mode без Phase 1 нет;
- основной выход — publication adaptation, а не один из трёх результатов проекта.

#### Решение

`out_of_scope`. Corpus run не выполнялся; offline-профиль не создавался. Полезные
запреты уже покрыты YSLAB без journal-fit scoring.

### 4.8. `jin-s13/paper-writing-suite`

#### Зафиксированная версия

- Commit: `5d6e4244e532189099ca5a9c5585b23febcae955`.
- Лицензия: MIT.
- Skill name: `ai-research-writing-skill`.
- `SKILL.md`: 65 строк, SHA-256
  `7c5fe169ac7b2c6ed14ff72338c0ac258b3cd80b61c4c2840ad878866b8e67cc`.
- Эксперимент: [EXP-0013](../experiments/EXP-0013-jins13-paper-writing-suite/report.md).

#### Что и как проверялось

- schemas research handoff, numeric evidence и paper state;
- 15 Python scripts;
- compileall и upstream test suite;
- citation lock, numeric provenance, stale build, invalid UTF-8, TODO/blocker
  gates и archive path traversal;
- статическое разделение local core, network scripts и subprocess script;
- Windows portability;
- scope/offline profile.

#### Результат

- все 15 scripts компилируются и используют standard library;
- upstream: `27 passed, 1 failed`;
- единственный сбой: `record_build.py` применяет POSIX `shlex.split` к
  некавыченному Windows path и превращает путь к Python в
  `J:PCpythonpython.exe`;
- local gates fail closed при unresolved evidence, citations, blockers и stale
  build;
- numeric claims могут пересчитываться из JSON/JSONL/CSV/TSV;
- `verify_citations.py` и `fetch_template.py` содержат сетевые функции;
- `record_build.py` использует subprocess;
- default workflow также включает image generation, venue/submission и
  new-experiment planning.

#### Почему content smoke не завершён

Главное преимущество suite проверяется только на авторском research project с:

- raw results;
- experiment logs;
- manuscript state;
- numeric evidence manifest;
- claims, связанными с конкретными result rows.

Текущий Zotero-корпус содержит опубликованные статьи, но не такой проект.
Использование одной статьи повторило бы writing tests EXP-0010/0011 и не
проверило бы handoff/numeric contracts.

#### Решение

`eligible_for_content_smoke`, статус
`blocked_waiting_for_supplied_results`. До появления raw research results suite
не включается в основной набор. При будущем тесте сетевые, image, venue и
submission branches должны быть отключены.

### 4.9. `ngtiendong/Academic-Research-Agent-Skill`

#### Зафиксированная версия

- Commit: `b96e3a135a1e707704da81809ddf78ea24455883`.
- Лицензия: MIT.
- Main skill: `research-agent`, 52 строки, SHA-256
  `aa3ac74ba2309a466b8d0b2595e29c6fdb2cbd9b663a438f24818137b35cb729`.
- 84 tracked files, executable scripts и upstream-тестов нет.
- Эксперимент: [EXP-0014](../experiments/EXP-0014-ngtiendong-source-grounding/report.md).

#### Что и как проверялось

- main `SKILL.md` и references `source_grounding`, `claim_verification`,
  `novelty_gate`;
- требования inspected source before evidential use;
- разделение evidence, interpretation и hypothesis;
- поведение на шести заранее сформулированных claims из `SRC-AAR-002` и
  `SRC-AAR-003`;
- конфликт sample size `N=131/139`;
- формат в произвольном каталоге и после установки в `research-agent`;
- две независимые проверки локаторов.

#### Результат

Claim gate:

- сохранил ограниченный вывод о feasibility;
- удалил неподдержанное снижение readmissions;
- снял причинность с изменения EHFScBS;
- не позволил делать градуировку по `Zo`;
- не разрешил догадкой конфликт `N`.

Трассировка:

- grounding matrix: 15 ссылок, 12 уникальных, отсутствующих — 0;
- claim verification: 14 ссылок, 12 уникальных, отсутствующих — 0.

Недостатки:

- upstream tables не требуют locator и иногда даже отдельного source column;
- full workflow включает closest-prior-work search, novelty, experiment planning,
  pilot и implementation;
- tool references предлагают downloaders/URLs, хотя Zotero HTML уже дан.

#### Решение

- `source_grounding` и `claim_verification`: `pass_with_offline_profile`;
- `novelty_gate`: `out_of_scope`;
- полный `research-agent`: `adapt_required`.

Сохранить короткие grounding/claim rules как общий предохранитель; suite целиком
не устанавливать.

### 4.10. `HaoYangJin/Research-workflow-Skill`

#### Зафиксированная версия

- Commit: `b089a37bfd9143426bf00f5cdf7eeff78db73568`.
- Лицензия: MIT.
- Skill: `research-mentor`, 73 строки, SHA-256
  `c3bbac1724e5ee238f34631f2b924b2a03c730ee4afae018f6a7cc00c0bd51d0`.
- 22 tracked files, scripts и upstream-тестов нет.
- Эксперимент: [EXP-0015](../experiments/EXP-0015-haoyangjin-research-mentor/report.md).

#### Что и как проверялось

- phase routing и progressive loading references;
- reviewer mode;
- native запреты на invented data/citations/venues/opinions/claims;
- сохранение technical intent;
- scope full mentor/mixed/literature/method/results/submission phases;
- reviewer content smoke на исходном Abstract `SRC-AAR-002`;
- validator локаторов.

#### Результат

Reviewer mode выявил пять существенных проблем:

1. безусловная feasibility;
2. причинное прочтение self-care;
3. отсутствие completion rates;
4. пропущенные ограничения;
5. риск представить readmissions как результат.

Правки были ограничены существующим полным текстом. Трассировка: 14 ссылок, 10
уникальных блоков, отсутствующих — 0.

Полный workflow при этом планирует research directions, literature search,
experiments/ablations, venue comparison, acceptance risk, rebuttal и submission.
Claim-level locator schema отсутствует.

#### Решение

Полный skill: `adapt_required`. Сохранить только reviewer pattern
`major concerns → why → bounded textual fix`. YSLAB остаётся основным review/
revision workflow.

### 4.11. `keemanxp/slr-prisma`

#### Зафиксированная версия

- Commit: `0614d2f6d39f5d31d0ae63fdff39f9553c90449c`.
- Main skill license: MIT.
- PRISMA checklist/flow references: CC BY 4.0, требуется атрибуция.
- `SKILL.md`: 418 строк, SHA-256
  `cd1531a696ddf29cc1cc621f73bcd0688be93e432ec6b00db037025dcfe358cf`.
- 5 файлов, scripts и upstream-тестов нет.
- Эксперимент: [EXP-0016](../experiments/EXP-0016-keemanxp-slr-prisma/report.md).

#### Что и как проверялось

- различение PRISMA reporting и conduct of review;
- records/reports/studies;
- все 27 PRISMA items/subitems;
- default web verification и external `/mnt` dependencies;
- допустимость placeholder counts;
- audit-only content smoke на существующей матрице EXP-0003;
- намеренная проверка запрета придумывать flow diagram.

#### Результат

Audit корректно признал:

- сильными: study characteristics, individual results, synthesis и evidence
  limitations;
- отсутствующими: search methods, selection, risk of bias, certainty, protocol и
  declarations.

Ключевой защитный результат: flow diagram не создан. Восемь документов benchmark
и три строки матрицы нельзя интерпретировать как records identified и studies
included.

Трассировка audit: 14 ссылок, 11 уникальных блоков, отсутствующих — 0.

Полный skill также строит search strings, использует web verification, внешние
`docx`/`apa-referencing` skills по `/mnt`, visual и submission-ready Word output.

#### Решение

Полный workflow: `adapt_required`. Изолированный `PRISMA-reporting-audit`:
`pass_with_offline_profile`. Он может только перечислять отсутствующие элементы;
методы, flow counts и diagram без реальных logs не создаются.

### 4.12. `bytedance/deer-flow`

В репозитории проверялись два разных компонента на двух frozen snapshots.

#### `academic-paper-review`

- Snapshot: `0d8e11ad492bfa1a15b4409cc744ee66d6d188c0`.
- Формат: pass по ручной проверке.
- Проверка: обязательные фазы internal review, literature positioning, output
  tooling и web requirements.
- Результат: literature-positioning phase требует web search; outputs предполагают
  host-specific tools.
- Corpus run не выполнялся.
- Решение: `adapt_required`; потенциально сохраняемы только paper-internal review
  phases после извлечения.

#### `systematic-literature-review`

- Snapshot: `150f7740c703292a154762f3a71aa9e18d17bda3`.
- Лицензия: MIT.
- `SKILL.md`: 235 строк, SHA-256
  `9fe4891e86b29d0f0f192bddab4ff913b123ffd764a2af737a4d6bb334209b6a`.
- 7 файлов, 1 Python script, 5 workflow eval definitions, 20 trigger cases.
- Эксперимент: [EXP-0017](../experiments/EXP-0017-deerflow-systematic-literature-review/report.md).

Что проверялось:

- обязательные пять phases;
- `arxiv_search.py` compile и локальные pure functions;
- zero-result CLI, query construction, modern/legacy arXiv IDs;
- eval JSON и наличие executable runner;
- API endpoint, persistence, subagents и paths;
- SLR/PRISMA методологический минимум;
- claim-level provenance.

Результат:

- script компилируется; локальные query/ID tests прошли;
- live API не вызывался;
- endpoint — `http://export.arxiv.org/api/query`, без TLS на первом переходе;
- arXiv API и DeerFlow task subagents обязательны;
- synthesis строится по abstracts;
- нет заранее заданных eligibility criteria, independent screening, multi-source
  search, full-text extraction, risk of bias и certainty assessment;
- top-N arXiv results названы systematic literature review;
- search results не сохраняются;
- subagent outputs не имеют source span/locator и могут добавлять «obviously
  missing» limitations;
- executable eval runner отсутствует; evals проверяют mechanics, а не factual
  support.

Решение: `rejected_as_is`. Корпус не передавался, workflow не устанавливать и не
fork-ать ради общих theme templates.

### 4.13. `lishix520/academic-paper-skills`

#### Зафиксированная версия

- Commit: `c325557646e9418939ccc7b99171b149ad6314f1`.
- Лицензия: MIT.
- Candidate: `strategist` / declared name `academic-paper-strategist`.
- `SKILL.md`: 670 строк, SHA-256
  `55164ac3fb2b7b4f60d43f2d2637242550fab85252d793e6885b67c2fe818f15`.
- 5 tracked files, 2 Python scripts; upstream-тестов нет.
- Эксперимент: [EXP-0018](../experiments/EXP-0018-lishix520-strategist/report.md).

#### Что и как проверялось

- Agent Skills format limits;
- scope mandatory Exa/Tavily/platform search;
- Python 3.11 compilation;
- dependency declaration;
- adversarial sample-quality fixture;
- gap evidence validation;
- Windows cp1251 output.

#### Результат

Format:

- name не совпадает с каталогом `strategist`;
- description — 1050 символов при limit 1024;
- 670 строк выше рекомендованных 500.

Scripts:

- `evaluate_samples.py` компилируется;
- `gap_analysis.py:334` не компилируется на Python 3.11 из-за same-quote nested
  f-string;
- используется `python-dateutil`, dependency manifest отсутствует;
- adversarial fixture из 8 пустых papers, без DOI/URL и со всеми
  `quality_indicators=false`, прошёл gate после вручную заданного relevance=10,
  нужных date buckets и author strings;
- evidence validator проверяет citations/quotes только на непустую строку;
- символы `✓`/`⚠` вызывают `UnicodeEncodeError` в active cp1251 stdout.

Scope:

- обязательны 35–50 внешних работ через Exa/Tavily;
- output включает platform choice, gaps, originality score, impact prediction,
  paper outline и pivot research direction.

#### Решение

`out_of_scope`; corpus не использовался. Не устанавливать и не извлекать даже
outline/gap шаблон: результаты запрещены областью, а quality gates не
калиброваны.

### 4.14. `WenyuChiou/research-hub`

#### Зафиксированная версия

- Commit: `3143d2d62f798960731cae5a2b4f91aeaca25e75`.
- Лицензия skills: MIT.
- Проверены `literature-triage-matrix` и `paper-summarize`.
- Статический аудит: [EXP-0002](../experiments/EXP-0002-portable-skill-audit/report.md).
- Content smoke матрицы: [EXP-0003](../experiments/EXP-0003-literature-matrix-offline/report.md).

#### `literature-triage-matrix`

- 128 строк;
- SHA-256
  `a437f44253b5113e3f38fd649042d1e89d012b757304f41353de96e2df676366`;
- Agent Skills format: pass;
- portability: pass.

Как проверялось:

- static audit model-memory, DOI lookup и workspace paths;
- offline-профиль запретил знания модели, DOI lookup, Zotero writes и внешние
  материалы;
- на трёх публикациях построена единая comparative matrix по вопросу, design,
  sample, methods, results, limitations и допустимой роли в обзоре;
- локаторы проверены по frozen Zotero HTML.

Результат:

- корректно разделены viewpoint review, feasibility study и diagnostic
  comparison;
- найден внутренний конфликт `N=131` против `N=139`;
- self-care не превращён в снижение hospitalizations;
- association `Zo` с abnormal CXR не названа superiority;
- 32 ссылки, 30 уникальных блоков, отсутствующих — 0.

Решение: `conditional_pass` / `pass_with_offline_profile`. Использовать как
cross-paper evidence matrix; следующий строгий benchmark — сравнение с direct
baseline.

#### `paper-summarize`

- 107 строк;
- SHA-256
  `385162d00efc94406fd41aacb30aecbb4ee219dabc4b5184c8573ac96af6b800`;
- Agent Skills format: pass;
- static scanner обнаружил 4 external-model и 6 state-mutation signals.

Результат static/policy audit:

- вызывает LLM CLI для отдельных papers;
- пишет Zotero notes;
- жёстко связан с research-hub workspace;
- требует изменения состояния вне изолированного experiment output.

Content smoke не выполнялся.

Решение: `rejected_as_is`.

#### Решение по репозиторию

Использовать только `literature-triage-matrix` с проектным offline-профилем.
`paper-summarize` не использовать.

### 4.15. `WenyuChiou/academic-writing-skills`

#### Зафиксированная версия

- Commit: `6524dd9e204660894dcdeefebfed94d8fcdef3fa`.
- Лицензия: MIT.
- `SKILL.md`: 301 строка, description 845 символов, SHA-256
  `a306070c8205a9d6c36b674c9d737c622e9f19c0ecf1fde29b2617cd573e07a9`.
- 20 tracked files, 14 skill files, 0 Python scripts, 11 eval definitions.
- Эксперимент: [EXP-0019](../experiments/EXP-0019-wenyuchiou-academic-writing-skills/report.md).

#### Что и как проверялось

Полностью прочитаны и зафиксированы:

- `writing_principles.md`, 713 строк;
- `banned_words.md`, 279 строк;
- `section_checklists.md`, 346 строк, применён Abstract subsection;
- `claim_evidence_audit.md`, 193 строки.

Проверены:

- Agent Skills format;
- upstream pytest;
- обязательная цепочка `claim → evidence → certainty → revision`;
- five dispositions для unverifiable claims;
- numeric visibility и causal-claim gate;
- content smoke на том же Abstract, что EXP-0010/0011;
- трёхстороннее сравнение с Master-cai и YSLAB.

Offline-профиль заменил `.paper/claims.yml`, `.paper/figures.yml` и
`paper-memory-builder` на нормализованные Zotero block locators. Reference lookup,
journal compliance и submission workflows отключены.

#### Результат

- Agent Skills audit: pass без warnings;
- первый `unittest discover` собрал 0 tests, поэтому не считался успехом;
- корректный runner `pytest`: `9 passed, 0 failed`;
- проверено 7 групп claims;
- dispositions: 2 drop, 3 hedge, 1 caveat, 1 retain;
- новых числовых claims — 0;
- revised Abstract: 9 ссылок, 8 уникальных blocks, missing 0;
- claim audit: 15 ссылок, 12 уникальных blocks, missing 0.

#### Решение

`pass_with_offline_profile`. Не заменяет YSLAB как редактор, а используется как
предпочтительный независимый claim–evidence gate до и после revision Abstract,
Results, Discussion и Conclusion.

### 4.16. `Imbad0202/academic-research-skills-codex`

#### Зафиксированная версия

- Commit: `f8d6b061efe98564a3f554c917fce66dcef6ca54`.
- Candidate: `academic-research-suite`.
- Лицензия: CC-BY-NC-4.0.
- `SKILL.md`: 329 строк; authoritative entry хранит commit и verdict, но
  отдельный SHA-256 этого skill в текущем реестре не записан.
- Эксперимент: [EXP-0002](../experiments/EXP-0002-portable-skill-audit/report.md).

#### Что и как проверялось

- Agent Skills format;
- размер и монолитность main workflow;
- static scanner для external model и network signals;
- наличие search workflows и cross-model routing;
- portability в текущем Codex-first окружении;
- scope gate до научного корпуса.

#### Результат

- format: pass;
- static scanner main `SKILL.md`: 18 external-model и 3 network signals;
- suite объединяет literature search, research workflow и manuscript tasks;
- присутствует optional cross-model routing;
- large context surface не позволяет безопасно изолировать небольшой workflow
  простым runtime flag;
- license запрещает часть коммерческого применения;
- content smoke не выполнялся.

#### Решение

`rejected_as_is`. Не устанавливать весь suite. Пересмотреть можно только после
выделения малых самостоятельных workflows с отдельным `SKILL.md`, явным
offline-контрактом и независимыми тестами.

## 5. Сравнительные выводы

### 5.1. Принятый рабочий контур

На текущих данных наиболее обоснована следующая комбинация:

```text
Zotero MCP / supplied research results
→ нормализованные blocks и result locators
→ WenyuChiou literature-triage-matrix для cross-paper extraction
→ ngtiendong source-grounding/claim-verification
→ YSLAB manuscript-writing для revision/review
→ WenyuChiou academic-writing-skills claim–evidence gate
→ при необходимости K-Dense qualitative scholar-evaluation
→ PRISMA audit только при наличии реального review protocol/logs
```

### 5.2. Основной writing skill

YSLAB выбран основным редактором, потому что native contract уже запрещает
фабрикацию и требует сохранять technical meaning, causality, certainty и numbers.
Master-cai остаётся секционным каркасом. `academic-writing-skills` добавляет самый
детальный claim gate, но его отдельный `.paper/` memory layer в этом проекте
заменён Zotero locators.

### 5.3. Основной literature-review слой

`literature-triage-matrix` показал полезный многодокументный синтез и обнаружил
внутренний конфликт sample size. Однако полноценное сравнение с direct и
evidence-first baseline ещё не завершено, поэтому verdict остаётся условным.

### 5.4. Что систематически отклонялось

Повторяющиеся причины отказа:

- обязательное расширение корпуса через search/API;
- модель/CLI как обязательная зависимость;
- потеря claim-level locators;
- prestige/citation-based quality scores;
- novelty/gap/research planning;
- publication-fit/acceptance scoring;
- derived notes/wiki как источник истины;
- создание PRISMA counts без реальных search/screening logs.

### 5.5. Единственный незавершённый content smoke

`jin-s13/paper-writing-suite` остаётся заблокирован не из-за найденной
фактической ошибки core contracts, а из-за отсутствия подходящего входа. Для
завершения нужны предоставленные исследователем:

- raw results;
- protocol/methods snapshot;
- experiment logs;
- tables/figures и их версии;
- manuscript state;
- соответствие claims конкретным result rows.

Пока эти материалы отсутствуют, положительный окончательный verdict был бы
необоснованным.

## 6. Ограничения данного отчёта

1. Все решения относятся к указанным frozen commits, а не к будущим версиям
   upstream repositories.
2. Где upstream-тестов не было, проверялось фактическое поведение текущего агента
   по инструкциям, а не исполняемая реализация.
3. `literature-review` K-Dense в раннем реестре не получил отдельный frozen
   commit; его отказ нужно перепроверять при любом возвращении к кандидату.
4. Content smoke отдельных writing skills выполнялся на одном biomedical
   Abstract. Это проверяет evidence calibration, но не заменяет тест полного
   manuscript с tables, figures и author-provided results.
5. `conditional_pass` не означает готовность к автоматической установке без
   offline-профиля и project locators.

## 7. Проверяемые первичные артефакты

- [Очередь репозиториев](../registry/skill-test-queue.yaml)
- [Реестр skills и frozen commits](../registry/skills.yaml)
- [Методика проекта](scope-and-methodology.md)
- [EXP-0002 — первичный static audit](../experiments/EXP-0002-portable-skill-audit/report.md)
- [EXP-0003 — literature matrix](../experiments/EXP-0003-literature-matrix-offline/report.md)
- [EXP-0004 — hypothesis-generation](../experiments/EXP-0004-kdense-hypothesis-generation/report.md)
- [EXP-0005 — critical thinking](../experiments/EXP-0005-kdense-critical-thinking/report.md)
- [EXP-0006/0020 — scholar evaluation](../experiments/EXP-0020-kdense-scholar-evaluation-content/report.md)
- [EXP-0007 — skill-focus](../experiments/EXP-0007-focus-detailed-qa/report.md)
- [EXP-0008 — paper_skills](../experiments/EXP-0008-paper-skills-reader/report.md)
- [EXP-0009 — borghei litreview](../experiments/EXP-0009-borghei-litreview/report.md)
- [EXP-0010 — Master-cai](../experiments/EXP-0010-master-cai-abstract/report.md)
- [EXP-0011 — YSLAB](../experiments/EXP-0011-yslab-manuscript-writing/report.md)
- [EXP-0012 — journal-adapt](../experiments/EXP-0012-wantongc-journal-adapt/report.md)
- [EXP-0013 — paper-writing-suite](../experiments/EXP-0013-jins13-paper-writing-suite/report.md)
- [EXP-0014 — source grounding](../experiments/EXP-0014-ngtiendong-source-grounding/report.md)
- [EXP-0015 — research mentor](../experiments/EXP-0015-haoyangjin-research-mentor/report.md)
- [EXP-0016 — PRISMA audit](../experiments/EXP-0016-keemanxp-slr-prisma/report.md)
- [EXP-0017 — DeerFlow SLR](../experiments/EXP-0017-deerflow-systematic-literature-review/report.md)
- [EXP-0018 — academic paper strategist](../experiments/EXP-0018-lishix520-strategist/report.md)
- [EXP-0019 — academic writing evidence audit](../experiments/EXP-0019-wenyuchiou-academic-writing-skills/report.md)
