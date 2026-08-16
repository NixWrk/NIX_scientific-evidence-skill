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

## Reading the middle of the chapters

Levels 2 through 5 above can be answered from a table of contents, an
introduction, chapter conclusions and the seams. That is pass A, and it is
cheap. It cannot see how an argument is actually built inside a subsection,
because it never reads one.

Pass B reads a work end to end, every page, and writes one observation per line
into `references/reading-logs/<work_id>.jsonl`, checked by
`scripts/validate_reading_log.py`. Two rules make it a discovery pass rather
than a checklist:

- an observation the list of kinds does not cover is written as `unnamed` with
  a **proposed name**, so the reader is never confined to the kinds someone
  thought of in advance;
- a proposed name becomes a kind on **three or more separate locators**. One
  occurrence is an event, two is a coincidence. Single occurrences stay in the
  log and are never promoted.

The records that earn a promotion keep `kind: "unnamed"`. They are the evidence
for it, and the validator reports such a name under «уже стало видом» instead
of proposing it again.

### Kinds

The first ten were named in advance. What each looks for:

`открытие-раздела` — what a subsection opens with: a problem, an announcement,
a continuation of the previous one, a definition. `ход-довода` — what is
claimed and what supports it. `опора` — what a reference does *here*: supplies
a fact, a method, a value to compare against, marks a gap, carries a competing
view. `своё-чужое` — how the boundary between the author's work and other
people's is marked. `число` — how a numeric result is given: magnitude, unit,
uncertainty, sample, base of comparison. `иллюстрация` — how a figure or table
is introduced, what the prose adds beyond the caption, where the object sits
relative to the sentence naming it. `термин` — where a term is introduced, how
abbreviated, whether the designation holds. `переход` — the seam between
subsections, not only between chapters. `оговорка` — where a limit on a
conclusion sits and how it is worded. `закрытие-раздела` — what a subsection
ends on.

### Kinds found by reading

Seven more were found on WORK-TIKHOMIROV-2021-DISS, read page by page. Each is
recorded with the locators that promoted it, so a later reader can check the
promotion rather than take it.

**A kind names something to look at, not something wrong.** Every one of the
seven below turned out, once weighed, to be ordinary practice. That is the
point rather than a disappointment: a reader needs a name for a recurring move
before they can tell an ordinary instance of it from a telling one, and none of
these had a name before.

- **`обзор-по-изделиям`** — a review conducted through marketed products with
  their manufacturers rather than through publications. *с. 18, 25, 26; all six
  review subsections end in a list of devices.* This is a stage of a review in
  its own right: surveying the market and surveying the methods are two
  different jobs, and a review chapter can carry both. What transfers is which
  stages a review has and in what order.
- **`дословный-повтор`** — a conclusion assembled from conclusions already
  stated in the body, often verbatim. *с. 40, 52, 59, 71, 92, 93; the chain runs
  body → chapter conclusions → general conclusions.* An unbroken chain is
  evidence that the argument was staged and that the closing claims are the ones
  the body actually made. The case worth stopping at is the opposite one: a
  closing claim that traces back to no sentence in the body.
- **`решение-без-лица`** — a methodological choice recorded by an impersonal
  passive: «было решено», «принималось», «брались». *с. 33, 35, 62, 75.*
  Ordinary in Russian scientific prose, and who decided reads from context. It
  earns a name because it marks **where** the choices are, not because the form
  is a defect.
- **`формула-с-глоссарием`** — a numbered relation followed by «где» and a list
  of symbols with units. *с. 15, 30, 31, 54, 57.* This is the form to expect;
  the observation is how completely it is carried out — which symbols the gloss
  covers, whether units appear, whether a range of validity is attached.
- **`формула-без-функции`** — a relation whose right-hand side is the word
  `func` with a list of arguments, the function itself not given. *с. 38, 69,
  70, 81.* A normal way to assert that a dependence exists and defer its form.
- **`заголовок-из-заголовка`** — a subsection heading built from the chapter
  heading rather than naming its own subject. *с. 42, 46, 53; on с. 46 the
  subsection heading is the chapter heading, differing by one letter.* It says
  the chapter's internal progression is not carried by its headings. Where it
  is, the headings are themselves a summary of the argument.
- **`страница-без-прозы`** — a page carrying no running text. *с. 1, 3, 4, 37,
  56, 65, 77, 82, 84, 86–89, 91, 94–96, 100 — eighteen of 102,* and
  unremarkable: appendices and figure-heavy chapters run this way. Its use is
  bookkeeping. A page with no observation is either unread or has nothing on it,
  and only this kind tells the two apart.

One more was found on WORK-MALAKHOV-2016-DISS:

- **`плюсы-минусы-списком`** — a method surveyed by two mirrored bullet lists,
  what it is good for and what it is not, with no running argument between them.
  *с. 16, 18, 20, 22, 57 — four methods in the review chapter and five more in
  the second review inside chapter 3.* It is an alternative to arguing a method
  through in prose, and it decides what a review chapter looks like.

`дословный-повтор` and `заголовок-из-заголовка` require a `quote`, for the same
reason `термин` and `оговорка` do: both are observations about wording, and a
paraphrase destroys the evidence.

### What the second work did to the first work's kinds

Reading Malakhov was the first test of names coined on Tikhomirov, and it is
the reason the corpus exists rather than a single deep read:

| kind | on Malakhov |
|---|---|
| `формула-с-глоссарием` | held — с. 37, 60, 70, 76 |
| `дословный-повтор` | held, and moved: sideways between parallel lists and captions, not only body → conclusions — с. 22, 24, 38, 55, 58, 63, 116 |
| `решение-без-лица` | held — с. 81 |
| `заголовок-из-заголовка` | held — с. 56 |
| `страница-без-прозы` | held — nine pages |
| `обзор-по-изделиям` | **absent.** Malakhov names no marketed device anywhere; his review runs by imaging modality |
| `формула-без-функции` | **absent.** Every relation is given in full |

An absence is a result. `обзор-по-изделиям` was the most confident finding of
the Tikhomirov read and it did not survive the nearest neighbour in the same
school under the same supervisor — which settles that it is one author's way of
writing a review, not the school's and certainly not the field's.

The citation practice split the same way. Tikhomirov's introduction cites
exclusively author-year and carries no bracket at all; Malakhov brackets from
first sentence to last and never uses author-year. Both name the same
predecessors; Tikhomirov leaves eight of eleven of them out of his bibliography,
Malakhov numbers them. Nothing about this is a school habit.

Names that stayed single are still in the log and did not become kinds:
`расхождение-нумерации`, `разнобой-заголовка`, `ссылка-на-изделие`,
`задача-без-главы`, `сдвоенный-элемент`, `соответствие-паспорту`,
`грантовая-поддержка`, `анонс-мимо-структуры`, `вывод-предписанием`,
`цель-внутри-раздела`, `формула-дважды`. A second work may promote them.

### What a full reading is not allowed to call a finding

Pass B turns up anomalies easily, and most of them are ordinary practice being
seen for the first time. The measurements of pass A make this worse: a
distribution with a hole in it looks like a defect long before anyone has asked
what normally fills it. Before an observation is written up as a finding:

- **A missing citation is not automatically a gap.** Introductions and
  physiological background often carry none — the facts are common knowledge, or
  the reference list is deliberately being kept short. A gap is where a specific
  contestable number rests on nothing.
- **Uncertainty is not owed on every number.** It matters where accuracy is the
  claim: instrument and method accuracy, patient parameters, ages, and anything
  a later reader would compare against. A model's geometric parameter or the
  step of a sweep does not need a ±.
- **Counts of the introduction's elements are individual.** Three novelty points
  or four, two significance items or three — the number belongs to the work and
  its council, and a corpus-wide tally of them measures nothing.
- **Tasks need not map onto chapters one to one.** Tasks can be close in
  meaning, one can be answered in passing while another is being worked, and one
  can turn out not to be answerable. A task without its own chapter is worth
  recording and is not a defect.
- **The sample studied need not equal the sample shown.** A work can carry the
  main, the problematic and the interesting cases in full and give the rest as
  statistics, plots or groups. A difference between the two numbers is a
  question about presentation, not a contradiction.
- **Sentence-length statistics say nothing.** Only the extremes carry anything —
  sentences too long or too short to read — and the middle of the distribution
  is noise.

What survives this filter is narrow and worth having: a number that contradicts
another number in the same work, a cross-reference that points at the wrong
object, a designation that changes meaning between two pages, a closing claim
the body never made.

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

## A defended work is a model, not a standard

Every work in this store passed a council, and none of them is faultless. This
one contradicts itself between a table and the prose that cites it, points at
table 13 where table 12 stands, and carries three abbreviations for one
quantity. Those are facts about the work and they are recorded as such. They do
not become a norm because a council accepted them, and they do not become a
prohibition because a reader noticed them.

The consequence for reading is the whole reason there is a corpus: **a move seen
in one work is a candidate, and it takes about five works by different authors
before it is a pattern.** One author's habit, one supervisor's house style and
one year's fashion all look exactly like a rule when the sample is one.

This bounds what pass B produces. The seven kinds found by reading Tikhomirov
were promoted on three locators **within a single work**, which is enough to
name a recurring move and to make the next reading look for it. It is not
enough to say the move is how such works are written. Only the aggregate, over
works by different authors, can say that — and even then it names the works
rather than a percentage.

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
