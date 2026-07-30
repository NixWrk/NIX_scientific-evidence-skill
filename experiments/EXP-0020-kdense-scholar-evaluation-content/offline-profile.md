# Offline-профиль qualitative review

## Конструкт

Проверяется трассируемая поддержка целей, дизайна, результатов и границ вывода в
предоставленном Abstract.

Не проверяются качество автора, научная репутация, журнальная пригодность,
новизна, ожидаемое влияние, полный reporting standard или воспроизводимость всей
статьи. Вывод применим только к этому Abstract и выбранным full-text blocks.

## Применяемые критерии

- `question_scope`;
- `method_design` в объёме, необходимом для калибровки Abstract;
- `analysis_claims`;
- `transparency_integrity` только как наличие в Abstract важных условий и
  ограничений, доступных в полном тексте.

`literature_contribution` имеет статус `not_assessed`: source-selection boundary
и систематическая comparison base не входят в этот вход. Отсутствие такой оценки
не считается нулём и не используется как отрицательный вывод.

## Отключённые ветви

- research-idea и organizational assessment;
- ordinal ratings 0–4, weights, normalization и composite score;
- inter-rater agreement и weight sensitivity;
- process governance для кадровых, грантовых и иных решений;
- publication-readiness, accept/reject и любые рекомендации о людях;
- внешний поиск и расширение корпуса.

Причина отключения score: upstream указывает `content_validity_status:
not_established`, требует минимум двух подготовленных raters и запрещает
подменять criterion evidence общей цифрой. В этом single-agent benchmark число
создало бы ложную точность.

## Трассировка

Каждое наблюдение получает существующий `SRC-…-B####`. `missing` означает, что
нужная информация отсутствует в проверяемом Abstract; это не score 0. Full-text
block может использоваться для предложения правки, но не превращается в новый
результат.
