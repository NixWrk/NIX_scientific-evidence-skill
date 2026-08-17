# Dissertation workflow routing

Load only the row needed for the current request. The orchestrator selects a
child skill; it does not repeat that child's instructions.

| Request or state | Child skill / capability | Mode and genre | Required input gate |
|---|---|---|---|
| Find publications or similar dissertations | Zotero/web/search capability available to the host | acquisition only | Record query, date, filters, source and stable identifier; do not draft from live results |
| Freeze and analyse a supplied corpus | `scientific-evidence-workflow` | `qa` or `literature_review` | Versioned source inventory and locators |
| Build the document hierarchy | `scientific-evidence-workflow` | `record`, `dissertation-outline` | Normative profile and planned structure records |
| Draft or criticise the introduction | `scientific-evidence-workflow` | `manuscript`, `dissertation-introduction` | Literature, organizational cards and structure IDs |
| Draft or criticise the review chapter | `scientific-evidence-workflow` | `manuscript`, `dissertation-literature-review-chapter` | Frozen corpus of at least three literature sources |
| Draft or criticise methods | `scientific-evidence-workflow` | `manuscript`, `dissertation-methods-chapter` | Protocol/data records |
| Draft or criticise results | `scientific-evidence-workflow` | `manuscript`, `dissertation-results-chapter` | Approved result records; literature is not result support |
| Interpret and compare results | `scientific-evidence-workflow` | `manuscript`, `dissertation-synthesis-chapter` | Approved results plus frozen literature |
| Close tasks and conclusions | `scientific-evidence-workflow` | `manuscript`, `dissertation-conclusion` | Final task, result and structure ledgers |
| Form defense propositions | `scientific-evidence-workflow` | `manuscript`, `defense-propositions` | Falsifiable statement with result and structure anchors |
| Form novelty and significance | `scientific-evidence-workflow` | `manuscript`, `novelty-statement` | Frozen literature boundary plus own-result anchors |
| Record approbation and publications | `scientific-evidence-workflow` | `record`, `approbation-record` | Organizational records; they do not prove scientific claims |
| Build or audit the synopsis | `scientific-evidence-workflow` | `manuscript`, `thesis-synopsis` | Final dissertation claims and organizational records |
| Build title page, TOC, abbreviations, terminology or bibliography | `dissertation-formatting-and-apparatus` | generate or audit | Approved manuscript and applicable normative profile |
| Audit figures, tables and appendices | `dissertation-formatting-and-apparatus` | audit | Frozen register plus DOCX/text |
| Add Word comments or tracked changes | `dissertation-formatting-and-apparatus` and the host document skill | critic journal -> reviewed DOCX | Valid PSES journal and exact locators |
| Decide what to do next or release the whole work | `candidate-dissertation-workflow` | project routing | Valid project manifest and release gates |

## Routing precedence

1. Resolve authority and input quality before selecting a writing action.
2. If the corpus is still changing, remain in acquisition/freeze; do not draft.
3. If a requested claim lacks evidence or an approved result, route to a
   blocker, not to prose generation.
4. Route scientific content before document formatting. Formatting may not
   repair scientific meaning.
5. Route a reviewed DOCX only from the same validated critic journal that is
   returned as the machine-readable result.

Search and Zotero access are optional host capabilities. If unavailable, leave
the acquisition stage blocked and state the exact missing connector or file;
never replace it with model-memory citations.
