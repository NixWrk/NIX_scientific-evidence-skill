# Word review output

The canonical artifact is a validated findings ledger. A reviewed DOCX only
materializes it.

## Profiles

- `comments`: add comments for every applicable finding.
- `track-changes`: add exact replacements only; fail if a finding lacks exact
  old and new text.
- `hybrid`: use tracked replacements when exact and comments otherwise; attach
  a comment to a meaning-changing replacement.

Preserve the source DOCX, existing comments, and existing revisions. Require an
exact-text locator and optional occurrence. Missing or ambiguous anchors are
errors, not invitations to select a nearby sentence.

Use unique integer OOXML identifiers, `w:delText` inside deletions, author and
UTC date attributes, and `w:trackRevisions` in settings. Comments require
`comments.xml`, document anchors, a relationship, and a content-type override.

After writing, run the structural audit. Then render all pages and inspect them.
Rendering can show redlines but does not reliably show comments, so it never
replaces the structural audit.
