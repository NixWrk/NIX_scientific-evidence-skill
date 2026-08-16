# Work-pattern memory

## Purpose

A defended work shows what one council accepted. It never shows what is
required. This file governs reading such works so that what they show can be
reused without ever hardening into a rule.

Three memories sit side by side and must not be confused:

- `normative-pattern-memory.md` — documents that **state requirements**;
- `journal-pattern-memory.md` — a venue's **house style**;
- this file — a **finished work of the kind being written**, read for its form.

## What transfers, and what does not

Extract only what transfers to another subject. A work's subject — the device,
the measurement, the clinical question — does not transfer, and it is not
recorded here. It belongs to the review pipeline, which has its own contract.

What transfers is shape: which parts exist and in what order, how a chapter
argues, how one chapter hands off to the next, how the through-line runs from
the gap in the field to the result. That is what a genre of the qualification
family needs, and it is the same whether the device is a tonometer or an
impedance rheograph.

If an observation cannot be stated without naming the subject, it is not a
form observation and does not belong in a work card.

## The guarantee is structural, not dutiful

The work-card schema has **no field in which an obligation can be written**.
There is no `binding`, no `requirements`, no `mandatory`. A normative card
relies on the author choosing `observed_practice`; that is discipline, and
discipline fails quietly. A schema that cannot express a rule cannot leak one,
and the validator rejects those keys wherever they appear.

The same applies to prose. An observation about someone else's work says what
is there — «разделена», «заканчивается», «приведено» — never «должен» or
«требуется». Verbatim text from the work goes in a `quote` field, where
obligation words are expected and allowed.

## Strata

A claim can only rest on works that could bear it. Each card declares one:

- `council` — defended in the target council. Only these can support a claim
  about that council's practice.
- `specialty` — the same specialty, including under the superseded
  nomenclature, but a different or unrecorded council. These support a claim
  about the specialty, never about the council.
- `outside` — another specialty, another genre (a research report is governed
  by its own standard), or foreign literature. These support neither, and are
  carded only when there is a reason to record why they were excluded.

The nomenclature changed: 05.11.17 «Приборы, системы и изделия медицинского
назначения» is the predecessor of 2.2.12. A work carrying the old code is the
same specialty, not a different one, and the card records the code as printed.

## What to look at

Five levels. The order is not arbitrary: the further down, the less any
normative document says about it, and the more the works are the only source.

**1. Скелет.** Parts and their order with page ranges; volumes — pages,
sources, figures, tables, publications. *Checkable against GOST R 7.0.11 and
the council card.*

**2. Роль и ход главы.** What each chapter is for, and the ordered moves
inside it — how the argument is actually built from its first page to its
last. *No normative document in the base says anything about this.*

**3. Стык.** How a chapter ends and hands off to the next: whether there are
per-chapter conclusions, whether the closing of one names the question the
next opens, how cross-references run. *Nothing in the base says anything.*

**4. Сквозная линия.** The through-line of the whole work and where each link
physically sits. The links are **not fixed by this file** — see below.
*Nothing.*

**5. Формулировки.** How the load-bearing statements are actually worded: цель,
задачи, научная новизна, положения на защиту, практическая значимость. Record
them verbatim in `quote`, then observe their shape — how many there are, what
word each one opens with, whether they are enumerated or run as prose, whether
a proposition states a result or an activity. *GOST R 7.0.11 names these
elements and never touches their wording, so the element is settled and the
form is not.*

**6. Формальная практика.** Reference-list order and grouping, citation form,
the author's publication list, patents, title page, numbering of figures and
tables. *Partly checkable; the reference-list order in particular is settled by
no document and is the clearest case where practice is the only source.*

Levels 2 through 5 are the reason for doing this at all. Levels 1 and 6 mostly
confirm what cards already establish.

## Signal against statistics

Level 6 produces findings easily and they are almost always worthless. Whether
a work writes «Выводы к главе» or «Выводы по главе», whether the novelty is
bulleted or numbered, whether a table caption takes a full stop — these split
the corpus cleanly, and a clean split is seductive. It is still only a
statistic.

The test is whether the observation would change how a work is **written**. A
review chapter titled after the system being built rather than after the field
surveyed changes what goes in it, in what order, and what it must end on; that
transfers to any subject and belongs in a skill. A preposition in a heading
changes nothing and belongs in `practice`, where it can be looked up if anyone
ever needs it.

Record level 6 anyway — it is cheap, and an absent record cannot be consulted
later. But do not let it into the aggregate as a feature, and do not report it
as a finding. A pattern earns that word by constraining the writing.

## The expected arc is a hypothesis, and it lives in data

Someone who knows the field can say in advance roughly how such a work runs —
for this specialty: a literature review that forms the **medical** problem, then
a review of technical solutions that forms the **medico-technical** problem, and
only then the development, the calculation, the modelling, the experiment.

That is worth having and dangerous to hold wrongly. Read eight works looking for
a five-link arc and eight of them will show it, because the reading was
organised by it. The frame would then be confirmed by its own application.

Three rules keep it honest:

- **The arc is data, not code.** The validator fixes no vocabulary of links.
  An aggregate declares its `expected_arc` together with `source` — who said
  so — and `stated_on`. A later reader can then see that the frame came from
  the author in advance and not from the corpus.
- **Every link carries a status.** `observed` or `absent`. A work that does not
  form the medical problem before reviewing technical solutions is a finding,
  not a failed reading, and `absent` is where such findings live.
- **An absent link still needs its evidence.** Say how the absence was
  established — which sections were read and what stands in its place — because
  «нет» asserted without a locator is unverifiable in the same way an invented
  quotation is.

Where a work shows a link the frame did not anticipate, add it. The frame is
the starting hypothesis, and a corpus that only ever confirms its frame has
taught nobody anything.

## Confounders

Every card records, or explicitly marks unknown: supervisor, year, council,
specialty code as printed, organization.

Without these, «восемь из восьми» can silently be «eight students of one
supervisor», or a practice of 2012 that the council no longer follows. A
shared feature across works of one supervisor is that supervisor's habit until
a work from another supervisor shows it too.

## The aggregate

A second artifact collects features across works. For each feature it records:

- the question being asked;
- which work cards show what, by `work_id` — the evidence stays in the cards,
  the aggregate points at it;
- the common pattern, where there is one;
- the **variants**, named with the works that show them;
- the relation to the normative base.

Variants are a result, not noise. Where works differ, record the alternatives
and who does which. Do not let the majority win: three works doing something
and one doing otherwise is two ways of building the section, and the minority
one may be the better fit.

## Relation to the normative base

Exactly three, and only one of them is actionable:

- **confirms** — a card already establishes it. The aggregate adds confidence
  and nothing else.
- **norm_silent** — no card settles it. This is the only case where practice
  supplies a default, and the default is a starting point, not an obligation.
- **diverges** — a card settles it otherwise. The card wins, always. The
  divergence is recorded as a fact about practice, never as licence to depart
  from the norm.

## Counting

`N of M` never becomes a rule, for any N. Eight works over fourteen years are
eight works. The aggregate carries the names, not a percentage, so that a later
reader sees the sample rather than a statistic that has forgotten its size.

Counts are never stored: they are recomputed from the cited cards, because a
stored count and its evidence drift apart and the count is the half that gets
read.

## Running the validator

```text
python scripts/validate_work_card.py card.json
```

It checks structure, locators, strata, the absence of obligation — in keys and
in prose — and, for an aggregate, that every cited work exists, that no claim
rests on a stratum too weak to bear it, and that every spine link used by a work
belongs to the arc the aggregate declares. It cannot check whether a chapter was
read correctly; that needs a second reading against the locator.
