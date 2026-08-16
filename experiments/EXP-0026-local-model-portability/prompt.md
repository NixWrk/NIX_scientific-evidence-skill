# Prompt assembly

## Run 01

System prompt:

> You are an offline instruction-following scientific writing model. Follow
> the provided local skill exactly.

User prefix:

> Apply the supplied scientific-evidence-workflow in Q&A mode. Work offline.
> Use only the supplied evidence bundle; do not add sources or facts from
> memory. Produce a concise Russian answer, a claim-evidence ledger, explicit
> unsupported conclusions, and a short validation disclosure. Preserve
> evidence IDs and locators exactly. Do not rewrite the bundle.

The host appended, in order:

1. `skills/scientific-evidence-workflow/SKILL.md`;
2. `skills/scientific-evidence-workflow/references/qa-workflow.md`;
3. `skills/scientific-evidence-workflow/references/evidence-contract.md`;
4. `experiments/EXP-0021-scientific-evidence-workflow/task.md`;
5. `experiments/EXP-0021-scientific-evidence-workflow/evidence-bundle.json`.

## Run 02

System prompt:

> You are the second offline verification pass. Check evidence before
> language. Output only the revised artifact.

User prefix:

> Perform a separate evidence-and-language revision pass on the candidate
> answer. Use only the validated bundle. Compare every scientific noun,
> statistic, denominator, status, and causal strength against the bundle;
> preserve median/mean distinctions exactly. Evidence columns may contain only
> evidence IDs or result IDs, never claim IDs. Remove corrupted or unnecessary
> mixed-language prose. Do not say that Python, a validator, or a style audit
> ran: this pass is model self-review only. Output the corrected Russian
> reader-facing answer and compact ledger, followed by an honest disclosure of
> what this model pass did and did not verify. Do not add facts.

The host appended the evidence bundle, the Russian style contract, and the
exact final artifact from Run 01. LM Studio exposed the model's reasoning trace
on stdout; the stored Markdown files retain only reader-facing artifacts.
