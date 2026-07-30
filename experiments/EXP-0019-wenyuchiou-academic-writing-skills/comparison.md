# Сравнение трёх writing skills на одном Abstract

Все кандидаты получили один `SRC-AAR-002`; сеть и дополнительные публикации не
использовались.

| Критерий | Master-cai, EXP-0010 | YSLAB, EXP-0011 | WenyuChiou, EXP-0019 |
|---|---|---|---|
| Запрет фабрикации | Требует усиления offline-профилем | Сильный прямой upstream-контракт | Прямой запрет оставлять непроверяемые claims и числа |
| Архитектура Abstract | Специализированные шаблоны | Последовательный revision checklist | Section checklist с обязательным contribution move |
| Claim–evidence контроль | Upstream map, локаторы добавляет профиль | Необязателен upstream, добавлен профилем | Самый подробный audit table и dispositions 1–5 |
| Причинные границы | Общий claim-support check | Явное сохранение causality/certainty | Отдельный causal audit и certainty по типу evidence |
| Локальная трассировка | 17 ссылок / 8 уникальных / 0 пропусков | 9 / 8 / 0 | Abstract: 9 / 8 / 0; audit: 15 / 12 / 0 |
| Лишняя инфраструктура | Нет | Нет | `.paper/` и `paper-memory-builder`, отключены профилем |
| Лучшее применение | Секционный каркас | Универсальная revision/review | Независимый claim–evidence gate перед и после правки |

## Решение

YSLAB остаётся основным универсальным revision/review skill: его контракт короче,
не зависит от отдельного memory layer и уже требует сохранять технический смысл.
`academic-writing-skills` добавляется как предпочтительный независимый
claim–evidence gate, особенно для Abstract, Results и Conclusion. Он не заменяет
YSLAB, а проверяет результат до выдачи.

Шаблоны Master-cai остаются дополнительным каркасом. Проектная схема локаторов
обязательна для всех трёх, потому что ни один upstream-формат напрямую не знает
наши `SRC-…-B####`.
