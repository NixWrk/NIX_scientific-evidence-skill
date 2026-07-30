# Offline-профиль `research-mentor`

Используется только canonical `reviewer` mode и только две ссылки:

- `references/06-paper-drafting.md`;
- `references/07-self-review-peer-review.md`.

Reviewer проверяет предоставленный текст на поддержку утверждений, ясность,
внутреннюю согласованность и ограничения. Для каждого замечания допустимы только
три действия: исправить по имеющемуся источнику, ослабить claim либо явно назвать
отсутствующее доказательство.

Отключены mentor/mixed modes, topic scoping, поиск и план обзора, research
questions/hypotheses, experimental design, ablation design, сбор данных,
reproducibility planning, rebuttal, venue/submission strategy, acceptance-risk
score и рекомендации новых экспериментов. Не используется формула «что нужно
доделать для публикации»; результат — Q&A-аудит уже данного текста.

Upstream не требует source locators, поэтому профиль добавляет обязательные
`source_id` и `block_id` ко всем фактическим замечаниям.
