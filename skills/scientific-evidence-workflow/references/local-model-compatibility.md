# Local-model compatibility

The core skill is plain text. A local model needs only:

- instruction-following capability;
- access to the supplied context or local files through its host application;
- UTF-8 input and output;
- enough context for one bounded stage at a time.

It does not need function calling, MCP, a vector database, or an online service.
The host may provide these features, but the workflow must remain valid without
them.

## Context packet

Give a local model one task packet at a time:

1. the relevant mode reference;
2. the evidence contract;
3. the user question or target section;
4. source records or stable chunks;
5. the current evidence and claim ledgers;
6. the requested output template.

Do not load every reference file for every task. For long corpora, run extraction
per source, validate records, then provide only the relevant evidence matrix for
synthesis.

## Capability fallback

- If the model cannot emit valid JSON reliably, let it fill Markdown tables and
  convert them deterministically before validation.
- If the model cannot read files, the host must inline bounded source chunks
  with stable locator labels.
- If the context window is small, separate extraction, claim mapping, drafting,
  and audit into independent passes.
- If no Python runtime is available, apply the evidence gate manually. Do not
  report deterministic validation as completed.

## Portable invocation

Use a host-neutral instruction such as:

```text
Apply the scientific-evidence-workflow in Q&A mode. Use only the supplied source
records. Build evidence and claim ledgers before the answer. Preserve every
locator and report unsupported or conflicting claims.
```

Product-specific metadata under `agents/` is optional and may be ignored by a
local-model host.
