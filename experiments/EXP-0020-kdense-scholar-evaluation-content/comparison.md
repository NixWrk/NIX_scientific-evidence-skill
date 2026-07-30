# Сравнение developmental review-контуров

| Критерий | `scholar-evaluation` | YSLAB `manuscript-writing` | WenyuChiou claim gate | `research-mentor` reviewer mode |
|---|---|---|---|---|
| Основной результат | Criterion-level developmental Q&A | Review или готовая revision | Claim → evidence → disposition | Приоритизированные reviewer comments |
| Защитная граница | Самая сильная против person ranking, prestige и decisions | Сильная против fabrication | Сильная против unsupported claims/numbers | Сильная против invented data/citations |
| Численный score | Есть optional toolkit, отключён | Нет | Нет | Нет |
| Missing vs zero | Явно различает | Через Needs Verification | Через dispositions | Через вопросы/замечания |
| Локаторы upstream | Opaque local refs | Нет проектной схемы | `.paper/` schema, заменённая блоками | Нет проектной схемы |
| Лишний контур | Rubric governance и organizational audit | Минимальный | `.paper/` memory layer | Research/publication lifecycle |
| Роль в наборе | Развивающий обзор целого scholarly work | Основной редактор | Основной evidence gate | Дополнительный reviewer checklist |

## Решение

`scholar-evaluation` полезен как qualitative developmental reviewer, когда нужно
организовать обратную связь по нескольким критериям и явно отделить отсутствующие
данные от отрицательного результата. Для проверки отдельных утверждений
WenyuChiou gate точнее и компактнее, а для переписывания YSLAB остаётся лучше.

Scoring toolkit не принимать в основной контур: upstream template не имеет
установленной content validity, а веса и ordinal ratings не добавляют надёжности
single-agent проверке. `research-mentor` не нужен там, где достаточно безопасной
developmental ветви без lifecycle-планирования.
