# EXP-0033 — read-only critic run on the Kalmykov notebooks

## Decision

The folder is a coherent working research report, but it is not yet a frozen reproducible result package. The modern notebooks generally have a clear task, inputs, assumptions, calculations, observations and conclusions. The principal defects are not lack of narrative structure; they are several claims stated more strongly than their evidence permits, weak provenance of derived JSON artifacts, external data dependencies and two notebooks with non-canonical saved execution state.

The source folder was not changed. The only source-side dirty file before and after the run was `09_Статическая_оценка_параметров.ipynb`; this experiment did not create that change.

## Scope and non-assessed properties

The run covered 9 notebooks, 8 Markdown documents, 22 JSON artifacts and the supporting Java/MATLAB files in the supplied folder. It was deliberately static and read-only.

The notebooks were not executed because several of them read data from `Z:\...`, and execution of notebooks 08–10 can overwrite `timestamps/*.json` or `params/*.json`. Therefore this run does not establish:

- successful execution from a clean kernel;
- correctness of the numerical implementation;
- correctness of raw CSV/DICOM data or segmentation;
- truth of source-dependent physiological and material-property claims;
- reproducibility on a machine without the external `Z:` data and environment.

No versioned primary literature corpus is present in the supplied folder. The few external links are mainly Wikipedia pages and the IT'IS tissue-property site. Literature-dependent conclusions can only be marked `not_assessed`, not accepted or rejected.

## What is already strong

The modern sequence 05 and 07–14 is much better than the raw lint score suggests:

- the umbrella methodology in `13_Методология_ФВ_УО.md` separates the current achievable result from the unclosed chamber-specific ejection-fraction hypothesis;
- notebooks normally distinguish inputs, assumptions, computation, analysis and conclusions;
- all 34 saved plot cells in the modern notebooks are followed immediately by an `Анализ результатов` block;
- local cross-references form a real report graph; 154 genuine local links resolve;
- negative and uncertain outcomes are often retained, especially the non-identifiability for thick tissues and the absence of a current external reference for ejection fraction;
- notebook 14 explicitly labels its analytical geometry as a proxy rather than truth and uses a fixed seed;
- notebook 05 openly marks `L_max = 200 мм` as a placeholder rather than a validated design boundary.

## Confirmed findings

### F-01 — absolute and causal interpretation of the pulse result is overstated

**Severity:** major before publication; acceptable as a working hypothesis only.

`00_Отчёт.md` lines 99 and 125 state that the lung-channel cardiac signal *is* pulmonary blood filling, give an absolute `Δρ₂ ≈ -0.08 Ом·м`, and say the original goal has been achieved. Notebook 11 repeats the physical attribution. However, `00_Отчёт.md` line 135 and notebook 11 itself state that the gain/derivative transfer of `RHEO` is not calibrated. Notebook 09 §5.2 additionally reports disagreement between the base and pulse channels, a variable pulse/base ratio of 1.5–13 and low coherence.

The defensible result is narrower: under the adopted two-layer sensitivity model, the size-dependent heart-synchronous component is consistent with a dominant deep/lung contribution, while the absolute `Δρ₂` scale and exclusive physiological attribution remain provisional until the pulse-channel transfer function and an independent physiological reference are validated.

### F-02 — the CT comparison is not an independent parameter confirmation “without fitting”

**Severity:** major wording/evidence-boundary defect.

Notebook 10 cells 16 and 20 and `00_Отчёт.md` line 90 call the agreement near 17 Ω·m an independent confirmation without fitting. CT-derived air fraction is independent of impedance, but the conversion to `ρ₂` depends linearly on the adopted free parameter `ρ_матр = 2.5 Ом·м`. Notebook 10 acknowledges this in cells 1–3 and 20. Its saved numerical output is absent, the raw DICOM is external, and the local folder does not contain a frozen literature source for `ρ_матр`.

The defensible formulation is “conditional consistency of CT-derived air fraction and impedance-derived `ρ₂` under the adopted mixture law and `ρ_матр = 2.5 Ом·м`”, not independent confirmation of the full two-layer model.

### F-03 — conditioning is demonstrated, but not established as the unique cause

**Severity:** moderate.

`00_Отчёт.md` line 123 says the cause of the Georgiy scatter is attributed unambiguously to conditioning. The repository does demonstrate loss of sensitivity with thickness. At the same time, it retains model mismatch, the difference between electrical and anatomical thickness, flatness limits and a future CT/FEM check as open issues. Conditioning is therefore a demonstrated mechanism and likely major contributor, not the uniquely established cause.

### F-04 — future FEM behavior is written as an achieved property

**Severity:** moderate.

Notebook 12 cell 29 says CT-based FEM “removes leakage into `Δρ₁`”. No such FEM result is present in this folder; the umbrella methodology explicitly describes FEM as an external/future component. This must be phrased as a hypothesis or validation target: depth-resolved FEM is expected to test whether the leakage is reduced.

### F-05 — release provenance of derived artifacts is insufficient

**Severity:** major for release, low for exploratory work.

`params/static.json`, `params/ct.json` and `timestamps/*.json` contain useful values, but do not carry a run ID, source hash, notebook/code version, environment identity, validation status or explicit units for all fields. No environment/lock file was found in the supplied folder. Consequently, the JSON files are usable inside the current notebook graph but cannot independently prove which inputs and code produced them.

### F-06 — saved execution state is non-canonical in notebooks 02 and 08

**Severity:** major for reproducibility.

Notebook 02 has 23 code cells with stored output but no execution count and a mixed execution sequence. Notebook 08 also has a non-monotonic sequence (`... 7, 10, 8`) and a final unexecuted cell. This is evidence of a non-canonical saved state, although it is not proof that the calculations are wrong.

### F-07 — notebook 02 is a legacy scratch workspace, not a notebook report

**Severity:** structural.

`02_Kandidadskaya.ipynb` mixes several heart-sphere investigations, large embedded figures, cross-cell globals and exploratory fragments without a bounded question, completion criterion, final summary or explicit limitations. `TODO.md` independently records cross-cell dependencies, duplicate code, hard-coded paths and a prior global-variable defect. It should remain a labeled legacy archive or be split by research question; retrofitting it into one large report would preserve the wrong boundary.

### F-08 — notebooks 07 and 08 end without a bounded final summary

**Severity:** minor for working notebooks, moderate for handoff/release.

Both contain local analysis after calculations, but neither closes the notebook with what was established, what was not established, limitations and outputs. Notebook 08 also claims stable segmentation over all records while only selected visual checks are visible in the saved notebook. A release version needs a compact aggregate QC statement or per-record QC artifact.

### F-09 — several “reliable” or exhaustive formulations need narrower bounds

**Severity:** moderate.

- Notebook 09 concludes that `ρ₁` is recovered reliably, but the claim is not accompanied by an uncertainty interval and coexists with appreciable model mismatch and an unresolved effective-thickness question.
- Notebook 12 says all negative results follow from two facts. The derivation supports these mechanisms within the simplified model, not an exhaustive causal statement about the experiment.
- Notebook 08 reports a mechanical-onset median near 0 ms after the R wave. The notebook labels the measure auxiliary, but no literature or independent mechanical reference in scope establishes its physiological interpretation. This result requires verification rather than automatic rejection.

## Reproducibility and repository boundary

Five modern notebooks contain absolute `Z:\...` paths. These are legitimate working-infrastructure references but make the release non-portable unless mapped through documented configuration. Notebook 10 has no saved computational output and says the calculation requires network DICOM access. The canonical data flow (`08 → 10 → 09 → 11 → 05 §8`) is documented, but the artifacts do not yet encode that lineage.

The target Git repository was already dirty. This run observed the source at commit `441b71c7f0453aec7f1ae1159cc72ca2bb8ca0dc` plus an existing modification to notebook 09. A frozen release must use explicit file hashes or a clean commit, not the commit ID alone.

## Adjudication of the automated notebook lint

The raw lint returned 59 errors and 103 warnings. This number is not a valid quality score.

| Rule family | Raw result | Manual decision |
|---|---:|---|
| Missing execution count | 23 | confirmed, all in legacy notebook 02 |
| Non-monotonic execution | 2 | confirmed for notebooks 02 and 08 |
| Missing research task | 9 | false for 8 modern notebooks; confirmed for 02 |
| Missing bounded final summary | 9 | confirmed for 02, 07 and 08; false/overbroad for the others |
| Missing scope/limitations | 2/4 | false for notebook 14; mixed elsewhere |
| Plot lacks interpretation | 54 | at least 34 false: every modern saved plot has an immediate analysis block; legacy 02 remains a real concern |
| Large output | 33 | all are PNG figures; this is a size advisory, not evidence of a scientific defect |
| Absolute path | 5 | confirmed portability warning |
| Missing release metadata | 9 | confirmed, but correctly a working/release-state warning |
| Random operation without seed | 2 | false: notebooks 11 and 14 use fixed `default_rng(0)` seeds |

The Russian-style audit was even less precise on notebook Markdown: it emitted 313 findings, of which 302 were ordinary mathematical identifiers or LaTeX fragments. The remaining cases were mainly valid terms (`c-оптимальность`, `sidecar-метка`) and criterion-defined uses of “optimal”. One phrase in notebook 11 — “размах в целом возрастает” — could be made more quantitative, but the machine result cannot be treated as a language verdict.

## Skill evaluation

The compact `notebook-narrative` contract is useful for manual criticism: it correctly directs attention to task boundaries, observation versus interpretation, uncertainty, artifact lineage and release state. The deterministic tools are not yet calibrated for real Russian scientific notebooks.

Before using their counts as gates, the lint should:

1. recognize numbered Russian headings such as `§0. Решаемая задача`, `§5. Выводы` and `Результаты и умозаключения`;
2. recognize `Анализ результатов` as an interpretation block;
3. recognize seeded `numpy.random.default_rng(seed)`;
4. distinguish large image outputs from large textual/data dumps;
5. mask LaTeX, inline code, identifiers and introduced mixed-script terms in the Russian-style audit;
6. report a working-notebook advisory separately from a release-blocking gate.

## Overall verdict

The repository is scientifically candid in many important places and already behaves as a connected family of small reports. It should not be rejected because the current lint says `fail`. The honest release verdict is **not ready for frozen reproduction or publication wording**, primarily because of F-01, F-02, F-05 and F-06. The working-research verdict is **usable with explicit provisional status**.

No source correction is proposed or applied in this experiment.
