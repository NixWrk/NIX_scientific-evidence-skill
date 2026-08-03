# focus

A Claude skill for rigorous, detail-preserving summarization of academic papers and long-form documents.

Adapted from the FOCUS workflow described in [Lin (2025), *Nature Biotechnology*](https://doi.org/10.1038/s41587-025-02947-8). The method extracts every key point from a document, section by section, with specific details and naturally embedded direct quotes, then produces a clean final output with an overview at the top.

## What it does

Most AI-generated summaries lose the details that make a paper worth reading: effect sizes, method names, exact comparisons, the author's own language where it matters. This skill takes the opposite approach. It treats exhaustiveness as a feature, not a bug, and preserves the specificity of the source material.

The two-step process:

1. **Extract** every key point from the document, section by section, with concrete details and direct quotes embedded naturally (not restated alongside paraphrase).
2. **Clean up** by stripping citation markers, adding a concise overview/takeaway, and organizing sections for readability.

The output is a numbered list organized under section headings, with bold key terms and italicized quotes. No meta-commentary, no attribution to "the authors," no filler.

## Installation

**Option 1: Download ZIP**

Click the green **Code** button at the top of this repo, then **Download ZIP**. Extract the ZIP and add the folder to your Claude skills directory.

**Option 2: Releases**

Go to the [Releases](https://github.com/stephenturner/skill-focus/releases) page and download the latest `.skill` file. Add it to your Claude skills in [customize/skills](https://claude.ai/customize/skills) on the web, or double-click it if you have Claude Desktop installed.

**Option 3: Build it yourself**

Build a `.skill` file from the source code, then add it to your Claude skills as described above.

```sh
git clone https://github.com/stephenturner/skill-focus.git
cd skill-focus
zip -r focus.skill SKILL.md references/
```

## Usage

Trigger the skill with any of:

- `/focus` (followed by or alongside an uploaded document)
- "Summarize with FOCUS"
- "FOCUS summary"
- "Use the focus method"

It also triggers on requests for exhaustive or detail-preserving summaries where the user wants every key insight captured with supporting quotes.

## Example output format

```markdown
## Overview

[3-6 sentence paragraph summarizing the document's main contribution and findings.]

## Section Title

1. **Key finding in sentence case**
The experiment showed a 23% reduction in error rate across all conditions,
with the strongest effect in the high-complexity group. The method
*"outperformed all baselines on both precision and recall"* when applied
to datasets with more than 10,000 samples.

2. **Another insight**
...
```

## What this skill is not

It is not a high-level gloss or an abstract rewrite. If you want a two-sentence summary, this is the wrong tool. It is designed for researchers who need to capture the full content of a paper in structured, searchable form, with enough fidelity that you can decide which sections to read in depth.

## Attribution

The summarization method is prompt #6 from:

> Lin, Z. FOCUS: an AI-assisted reading workflow for information overload. *Nat. Biotechnol.* **43**, 2070-2075 (2025). https://doi.org/10.1038/s41587-025-02947-8

## License

MIT