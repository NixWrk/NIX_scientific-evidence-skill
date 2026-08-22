# Reader HTML for scientific notebooks

Publish every released notebook with a sibling reader-facing `.html` artifact.
The executable `.ipynb` remains the computational source; the HTML is the
scientific report intended for reading and citation.

Build the HTML only after the regenerated `.ipynb` and companion Markdown have
their final narrative, formula numbering, captions, outputs, internal anchors,
and bibliography links. Never repair a missing source citation only in the
HTML. A scientific bibliography entry must contain an explicit clickable link
to the publication, preferably its DOI URL or the publisher/repository record
supplied with the corpus. Preserve the exact original publication title.

Exclude code inputs, input prompts, and output prompts from the reader artifact.
Retain Markdown prose, numbered formulae, tables, displayed numerical data,
textual outputs that constitute results, figures, images, captions, and their
analysis. Do not replace executable code in the `.ipynb`; remove it only from
the reader representation.

Require every internal link to resolve to an emitted anchor. Preserve external
links as `<a href>` elements and require every local linked file and image to
exist beside the published artifact or to be embedded. Prefer embedded images
for a self-contained HTML when the exporter supports them.

Use `scripts/export_reader_html.py` for a standard nbconvert export. The host
must provide `nbformat`, `nbconvert`, and `traitlets`. Then run
`scripts/validate_reader_html.py` on every HTML file. A release fails when a
visible notebook input area remains, an anchor is unresolved, a link has no
target, or a local image/link target is absent. Record remote URL availability
and scientific citation support as separate checks; the static HTML validator
does not establish either one.
