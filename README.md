# Paper Analyzer Writer Benchmarks

Репозиторий для воспроизводимого тестирования библиотек, инструментов, приложений и skills, которые обрабатывают **уже имеющийся** корпус научных публикаций.

Zotero MCP является штатным слоем доступа к материалам. Основное представление публикации — HTML полного текста; PDF используется как резервное представление и для проверки страниц, таблиц и рисунков.

## Политика выполнения

- Научный корпус не передаётся внешним LLM и API.
- Роль LLM выполняет текущий Codex-агент или локально запущенная модель.
- Skills должны быть переносимыми: обычный `SKILL.md`, локальные скрипты и явные зависимости без обязательной привязки к одному облачному провайдеру.
- Сеть можно использовать только для получения и аудита исходного кода, документации и skills. Содержимое Zotero в такие запросы не включается.
- Любой скрытый сетевой вызов во время обработки корпуса считается критической ошибкой.

## Допустимые задачи

1. Вопрос/ответ по заданной коллекции Zotero.
2. Литературный обзор по заданному корпусу.
3. Итоговая научная статья по предоставленным результатам исследования и литературному корпусу.

## Основной принцип

```text
Zotero MCP
→ HTML/PDF и метаданные
→ нормализация
→ извлечение проверяемых фрагментов
→ evidence table
→ ответ, обзор или статья
→ независимый аудит
```

Качество связного текста не компенсирует вымышленный источник, неверный фрагмент, изменение числа или добавление отсутствующих данных.

## Структура

```text
docs/           область, методика и кандидаты
registry/       машиночитаемый реестр тестируемых компонентов
experiments/    протоколы и результаты отдельных сравнений
schemas/        форматы входов, доказательств и отчётов
skills/         переносимые инструкции, шаблоны и локальные валидаторы
third_party/    точные снимки исходников проверенных сторонних скиллов
tools/          локальные нормализаторы, валидаторы и аудиторы
```

Локальные закрытые корпуса, ключи доступа и сырые рабочие каталоги не коммитятся.

Сторонние исходники сохранены отдельно от рабочего скилла. Их точные URL,
коммиты, лицензии и связь с экспериментами приведены в
[`third_party/manifest.json`](third_party/manifest.json). Наличие исходника не
означает положительного решения; перед использованием сверяйся с
[`registry/skills.yaml`](registry/skills.yaml). Проект без найденной лицензии
подключён только как git-подмодуль и не копируется в историю этого репозитория.

## Статус

- [x] Зафиксирована область проекта.
- [x] Zotero MCP принят как штатный вход.
- [x] Определены три класса выходов и критические ошибки.
- [x] Подготовлен контрольный корпус Zotero (`EXP-0001`, коллекция `ААР`, 8 публикаций).
- [x] Выполнен статический аудит переносимых skills (`EXP-0002`).
- [x] Выполнен первый offline-прогон `literature-triage-matrix` (`EXP-0003`, 3 публикации).
- [x] Сохранён поисковый отчёт и начата поэтапная очередь репозиториев со skills.
- [x] Выполнен scope- и portability-аудит `hypothesis-generation` (`EXP-0004`).
- [x] Выполнен offline critical Q&A с `scientific-critical-thinking` (`EXP-0005`).
- [x] Завершён предварительный аудит `scholar-evaluation` (`EXP-0006`, 27/27 тестов).
- [x] Выполнен подробный Q&A с адаптированным `skill-focus` (`EXP-0007`).
- [x] Проверен первый слой `paper_skills` (`EXP-0008`); wiki-цепочка остановлена до трассировки.
- [x] Проверен `borghei/Claude-Skills/research/litreview` (`EXP-0009`); прогон на корпусе остановлен из-за ошибок агрегации и потери локаторов.
- [x] Выполнена evidence-traceable правка Abstract с `research-paper-writing` (`EXP-0010`); 17/17 ссылок на блоки валидны.
- [x] Выполнена парная правка Abstract с YSLAB `manuscript-writing` (`EXP-0011`); кандидат выбран базовым для revision/review.
- [x] `journal-adapt` отсечён до корпуса (`EXP-0012`): обязательный результат относится к журнальной адаптации, а не к трём целевым выходам.
- [x] Проверено offline-ядро `paper-writing-suite` (`EXP-0013`): 27/28 тестов; content smoke отложен до проекта с предоставленными raw results.
- [x] Проверены `source_grounding` и claim gate из `Academic-Research-Agent-Skill` (`EXP-0014`); novelty gate исключён как исследовательское планирование.
- [x] Проверен reviewer-mode `research-mentor` (`EXP-0015`); полезный checklist сохранён как дополнение, полный lifecycle требует извлечения допустимого подмножества.
- [x] Проверен audit-only режим `slr-prisma` (`EXP-0016`); PRISMA flow не создаётся без реальных журналов поиска и отбора.
- [x] `deer-flow/systematic-literature-review` отклонён до корпуса (`EXP-0017`): обязательны arXiv API, abstracts и DeerFlow subagents.
- [x] `academic-paper-strategist` исключён (`EXP-0018`): выходы относятся к research/publication planning, а scoring-скрипты не выдержали adversarial audit.
- [x] `academic-writing-skills` прошёл парный content smoke (`EXP-0019`): принят как независимый claim–evidence gate; YSLAB остаётся основным revision/review skill.
- [x] Завершён qualitative content smoke `scholar-evaluation` (`EXP-0020`): developmental review принят без ordinal/composite scoring и без person/publication decisions.
- [x] Все найденные skill-репозитории получили воспроизводимый verdict; content smoke `paper-writing-suite` отдельно заблокирован до предоставления raw research results и manuscript state.
- [x] Создан `scientific-evidence-workflow` v0.1 и выполнен неслепой Q&A smoke (`EXP-0021`, 23/23 теста); запуск на отдельной локальной LLM ожидает доступного runner.
- [x] Выполнено парное сравнение direct и evidence-first литобзора (`EXP-0022`, 8 публикаций): обе версии корректны, skill улучшил трассируемость, но прирост точности в неслепом тесте не доказан.
- [x] Добавлен слой русского научно-технического языка (`EXP-0023`): на обзоре `EXP-0022` число предусмотренных аудитором срабатываний уменьшено с 236 до нуля без изменения 12 утверждений, 28 используемых доказательных записей и 12 числовых групп.
- [ ] Создан baseline прямого вопрос/ответ по Zotero HTML.
- [ ] Создан evidence-first baseline.

Текущие эксперименты: [EXP-0001 — Direct Q&A over Zotero source HTML](experiments/EXP-0001-zotero-direct-qa/task.md), [EXP-0002 — аудит переносимых skills](experiments/EXP-0002-portable-skill-audit/task.md), [EXP-0003 — offline literature matrix](experiments/EXP-0003-literature-matrix-offline/task.md), [EXP-0004 — аудит K-Dense hypothesis-generation](experiments/EXP-0004-kdense-hypothesis-generation/task.md), [EXP-0005 — critical Q&A](experiments/EXP-0005-kdense-critical-thinking/task.md), [EXP-0006 — аудит scholar-evaluation](experiments/EXP-0006-kdense-scholar-evaluation/task.md), [EXP-0007 — адаптированный FOCUS Q&A](experiments/EXP-0007-focus-detailed-qa/task.md), [EXP-0008 — аудит paper_skills](experiments/EXP-0008-paper-skills-reader/task.md), [EXP-0009 — аудит borghei litreview](experiments/EXP-0009-borghei-litreview/task.md), [EXP-0010 — правка Abstract](experiments/EXP-0010-master-cai-abstract/task.md), [EXP-0011 — парная YSLAB-правка](experiments/EXP-0011-yslab-manuscript-writing/task.md), [EXP-0012 — scope-аудит journal-adapt](experiments/EXP-0012-wantongc-journal-adapt/task.md), [EXP-0013 — offline-ядро paper-writing-suite](experiments/EXP-0013-jins13-paper-writing-suite/task.md), [EXP-0014 — source grounding и claim gate](experiments/EXP-0014-ngtiendong-source-grounding/task.md), [EXP-0015 — reviewer-mode research-mentor](experiments/EXP-0015-haoyangjin-research-mentor/task.md), [EXP-0016 — PRISMA audit-only](experiments/EXP-0016-keemanxp-slr-prisma/task.md), [EXP-0017 — аудит DeerFlow SLR](experiments/EXP-0017-deerflow-systematic-literature-review/task.md), [EXP-0018 — аудит academic-paper-strategist](experiments/EXP-0018-lishix520-strategist/task.md), [EXP-0019 — claim–evidence benchmark](experiments/EXP-0019-wenyuchiou-academic-writing-skills/task.md), [EXP-0020 — qualitative scholar evaluation](experiments/EXP-0020-kdense-scholar-evaluation-content/task.md), [EXP-0021 — portable scientific evidence workflow](experiments/EXP-0021-scientific-evidence-workflow/task.md), [EXP-0022 — direct vs evidence-first literature review](experiments/EXP-0022-intercostal-ultrasound-review/task.md) и [EXP-0023 — русскоязычное научное редактирование](experiments/EXP-0023-russian-scientific-style/task.md). Корпус EXP-0001 нормализован, gold-набор готов; следующий Q&A-запуск должен выполняться без доступа runner к `gold.jsonl`. Очередь кандидатов описана в [дорожной карте](docs/skill-testing-roadmap.md).

## Первый milestone

На одной коллекции Zotero из 20–50 открытых статей:

1. сохранить нормализованный снимок HTML и метаданных;
2. подготовить 15–30 вопросов и эталонные фрагменты;
3. сравнить прямой агентный проход с evidence-first workflow;
4. измерить поддержку утверждений, точность локаторов, чисел и единиц;
5. затем сравнить прямой проход с локальным индексом и переносимыми skills.

Подробности: [методика](docs/scope-and-methodology.md) и [реестр направлений тестирования](docs/processing-tools.md).

Сводный подробный отчёт по всем 16 проверенным репозиториям: [repository-skill-testing-report-2026-08-03.md](docs/repository-skill-testing-report-2026-08-03.md).
