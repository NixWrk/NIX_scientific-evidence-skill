# Offline-профиль

Профиль извлекает из upstream только допустимый редакционный контур.

## Включено

- `SKILL.md` — классификация задачи и порядок self-audit;
- `references/writing_principles.md` — evidence calibration, числовая
  проверяемость, причинные границы и plain-language pass;
- `references/banned_words.md` — контроль раздувающих и шаблонных формулировок;
- подраздел `Abstract` из `references/section_checklists.md`;
- `references/claim_evidence_audit.md` — таблица аудита и dispositions 1–5.

## Замены

- нормализованные блоки `SRC-…-B####` являются authoritative evidence layer
  вместо `.paper/claims.yml` и `.paper/figures.yml`;
- проектная схема `claim_id → source_id → block_id` обязательна для каждого
  крупного утверждения;
- отсутствие `.paper/` не запускает создание memory layer и не расширяет задачу.

## Отключено

- `paper-memory-builder` и любые другие skills;
- поиск литературы, DOI/reference lookup и проверка novelty;
- reviewer response, submission, venue и journal-compliance workflows;
- создание новых данных, анализов, рисунков или экспериментов;
- любые сетевые вызовы и внешние модели при обработке корпуса.

Если факт нельзя подтвердить предоставленными блоками, он удаляется, ослабляется
или явно ограничивается. Новый источник не ищется.
