# Genre: dissertation outline and table of contents

`mode: record` · `genre: dissertation-outline` · structural plan required

## Purpose

Build the addressable hierarchy of a candidate dissertation before drafting
its sections, and render the same hierarchy as a table of contents. The outline
is a control record; it does not claim that a planned chapter already proves a
result.

## Input

Require the dissertation topic, approved aim and tasks when available, frozen
research-result records, applicable normative cards, and any organization or
council requirements supplied by the user.

## Procedure

1. Create stable structure records for the introduction, chapters, sections,
   conclusion, bibliography, and conditional back matter.
2. Give every declared task its own `task` unit. Map it to the chapter and
   section intended to answer it without marking the mapping as established.
3. Give every planned proposition and conclusion a stable unit when already
   approved by the author.
4. Check that chapter order follows the argument rather than the chronology of
   file creation. Use observed work patterns only as variants, never as rules.
5. Render the reader-facing table of contents from labels and titles. Keep
   internal unit identifiers out of the document.
6. After layout, generate the final Word table of contents from heading styles
   and update its field. Do not type or predict final page numbers manually.

## Normative core

The manuscript contains a title page, table of contents, introduction, main
text, conclusion, and bibliography. Lists of abbreviations, terms, and
illustrations and appendices are included when applicable. This composition is
supported by the normative card for GOST R 7.0.11-2011; chapter count and
chapter names are not fixed by that standard.

## Gates

- At least one chapter and one nested section exist as structure records.
- Labels are unique among siblings and preserve a stable hierarchy.
- Every task maps to a planned or drafted unit and later to a conclusion.
- A planned unit may support a proposal for structure, never a claim that the
  work has already established a result.
- Conditional lists and appendices are included only when their content exists.
- Final page numbers come from the rendered artifact, not from model memory.

For Russian output, apply `references/russian/genre-dissertation.md` and run
the audit with `--profile genre-dissertation`.

Use `assets/dissertation-outline.template.md` for a file artifact.
