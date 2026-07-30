# EXP-0019 — claim–evidence audit и правка Abstract

## Задача

Проверить `WenyuChiou/academic-writing-skills` на том же Abstract Aamodt et al.
(2020), `SRC-AAR-002`, который использовался в EXP-0010 и EXP-0011.

Тест включает два последовательных результата:

1. аудит утверждений исходного Abstract по схеме
   `claim → evidence → certainty → disposition`;
2. новую редакцию Abstract только после устранения обнаруженных разрывов.

## Условия

- единственный источник фактов — нормализованный Zotero HTML;
- все проверяемые утверждения привязаны к существующим `block_id`;
- сеть, внешняя LLM/API и дополнительный поиск во время прогона запрещены;
- `.paper/`, `paper-memory-builder`, journal lookup и reference verification не
  используются;
- journal-specific word limit и формат не проверяются, поскольку журнал не задан;
- исходная публикация и Zotero не изменяются.
