import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "scientific-evidence-workflow"
FIXTURES = ROOT / "tests" / "fixtures" / "notebooks"


def load_linter():
    path = SKILL / "scripts" / "lint_notebook.py"
    spec = importlib.util.spec_from_file_location("lint_notebook", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


LINTER = load_linter()


def lint(relative_path: str) -> dict:
    path = FIXTURES / relative_path
    data = json.loads(path.read_text(encoding="utf-8"))
    return LINTER.lint_notebook(data, path=str(path))


def rule_ids(report: dict) -> set[str]:
    return {finding["rule_id"] for finding in report["findings"]}


def test_scenario_1_clean_single_task_passes():
    report = lint("clean-single-task.ipynb")
    assert report["status"] == "pass"
    assert report["valid"] is True
    assert report["findings"] == []


def test_scenario_2_hidden_state_stale_output_and_unit_gap_fail():
    report = lint("hidden-state-stale-unit.ipynb")
    assert report["status"] == "fail"
    assert {
        "NB-EXEC-001",
        "NB-EXEC-002",
        "NB-REPRO-003",
        "NB-NUMBER-001",
    } <= rule_ids(report)


def test_scenario_3_negative_result_and_hypothesis_are_preserved():
    report = lint("negative-result-hypothesis.ipynb")
    assert report["status"] == "pass"
    assert "NB-NUMBER-001" not in rule_ids(report)
    assert "NB-SPLIT-001" not in rule_ids(report)


def test_scenario_4_semantically_overloaded_notebook_requests_review():
    report = lint("split-needed.ipynb")
    assert report["status"] == "review"
    assert report["valid"] is True
    assert rule_ids(report) == {"NB-SPLIT-001"}


def test_scenario_5_split_pair_passes_as_two_bounded_reports():
    reports = [
        lint("split-pair/prepare-data.ipynb"),
        lint("split-pair/evaluate-model.ipynb"),
    ]
    assert all(report["status"] == "pass" for report in reports)
    assert all("NB-SPLIT-001" not in rule_ids(report) for report in reports)


def test_template_is_valid_notebook_with_working_report_metadata():
    path = SKILL / "assets" / "notebook-narrative.template.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    report = notebook["metadata"]["scientific_report"]
    assert notebook["nbformat"] == 4
    rendered = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert "Паспорт" not in rendered
    assert "Наследуемое состояние" not in rendered
    assert "**Среда:**" not in rendered
    assert report == {
        "artifact_status": "working",
        "automation_status": "blocked",
        "bibliography_status": "not_applicable",
        "computational_validation_status": "not_checked",
        "execution_status": "not_run",
        "genre_profile": "model-derivation",
        "language_audit_status": "not_run",
        "language_profile": "genre-notebook",
        "narrative_language": "ru",
        "scientific_validation_status": "not_reviewed",
        "schema_version": "1.0",
        "selection_policy_status": "not_applicable",
        "selection_resolution_ref": None,
        "study_type": "computational",
        "technical_validation_status": "not_checked",
    }
    tags = {
        tag
        for cell in notebook["cells"]
        for tag in cell.get("metadata", {}).get("tags", [])
    }
    assert {
        "notebook-role",
        "research-question",
        "notebook-scope",
        "completion-criterion",
        "material-inputs",
        "technical-background",
        "calculation-chain",
        "equation-narrative",
        "verification-checks",
        "computed-narrative",
        "observable-output",
        "result-status",
        "figure-caption",
        "interpretation-and-limits",
        "report-summary",
        "artifact-handoff",
    } <= tags
    formula_cells = [
        index
        for index, cell in enumerate(notebook["cells"])
        if "\\tag{" in "".join(cell.get("source", []))
    ]
    assert formula_cells == [3]
    assert "equation-narrative" in notebook["cells"][formula_cells[0]]["metadata"]["tags"]


def test_output_size_ignores_binary_figures_but_counts_text() -> None:
    figure = {
        "outputs": [{"output_type": "display_data", "data": {"image/png": "x" * 200_000}}]
    }
    text_dump = {
        "outputs": [{"output_type": "stream", "name": "stdout", "text": "x" * 200_000}]
    }

    assert LINTER._output_size(figure) == (0, 0)
    assert LINTER._output_size(text_dump)[0] > 100_000


def test_frozen_snapshot_requires_release_identity_fields():
    path = FIXTURES / "clean-single-task.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    notebook["metadata"]["scientific_report"].pop("run_id")
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-REPRO-002" in rule_ids(report)


def test_lint_report_states_what_static_analysis_does_not_assess():
    report = lint("clean-single-task.ipynb")
    assert "actual_clean_kernel_execution" in report["not_assessed"]
    assert "scientific_method_validity" in report["not_assessed"]
    assert "current_upstream_resolution" in report["not_assessed"]
    assert "cross_notebook_chain_truth" in report["not_assessed"]
    assert "russian_language_quality_beyond_heuristics" in report["not_assessed"]
    assert "bibliographic_semantic_correctness" in report["not_assessed"]
    assert "selection_policy_truth" in report["not_assessed"]
    assert "validation_status_attestation" in report["not_assessed"]


def test_notebook_evidence_bundle_accepts_its_canonical_shape():
    validator_path = SKILL / "scripts" / "validate_bundle.py"
    spec = importlib.util.spec_from_file_location("validate_bundle_for_notebook", validator_path)
    validator = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(validator)

    bundle = json.loads(
        (SKILL / "assets" / "evidence-bundle.template.json").read_text(encoding="utf-8")
    )
    bundle["task"].update({"mode": "record", "genre": "notebook-narrative"})
    bundle["sources"][0]["representation"] = "data"
    bundle["evidence"][0]["support_type"] = "method"
    bundle["results"] = [
        {
            "result_id": "RES-NB-001",
            "source_id": "SRC-EXAMPLE-001",
            "locator": "cell:4/output:0",
            "value": 2.0,
            "unit": "ms",
            "version": "sha256:example",
            "analysis": "mean duration",
            "approved": True,
        }
    ]
    bundle["structure"] = [
        {"unit_id": "TASK-NB", "unit_type": "task", "label": "Q1", "status": "final"},
        {
            "unit_id": "CONC-NB",
            "unit_type": "conclusion",
            "label": "C1",
            "status": "final",
        },
    ]
    sections = (
        "notebook_scope",
        "technical_background",
        "method_and_assumptions",
        "observed_outputs",
        "interpretation_and_limits",
        "notebook_summary",
    )
    bundle["claims"] = [
        {
            "claim_id": f"CL-NB-{index}",
            "text": f"Bounded notebook statement {index}.",
            "output_section": section,
            "claim_type": "structural" if index == 1 else "factual",
            "certainty": "direct",
            "evidence_ids": ["EV-001"] if index == 2 else [],
            "result_ids": ["RES-NB-001"] if index >= 3 else [],
            "structure_ids": ["TASK-NB" if index < 5 else "CONC-NB"],
            "status": "supported",
            "disposition": "keep",
            "boundary": "Only the supplied run.",
            "causal_basis": None,
        }
        for index, section in enumerate(sections, start=1)
    ]
    report = validator.validate_bundle(bundle)
    assert report["valid"] is True, report["errors"]


def empirical_notebook(*, complete_arc: bool = True) -> dict:
    path = FIXTURES / "clean-single-task.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    report = notebook["metadata"]["scientific_report"]
    report["study_type"] = "empirical"
    report["genre_profile"] = "empirical-analysis"
    report["selection_policy_status"] = "clear"
    notebook["cells"][0]["metadata"]["tags"].append("selection-policy")
    if complete_arc:
        notebook["cells"][3]["source"] = [
            "impedance_ohm = 42.043\n",
            "display(Markdown(f\"\"\"**Наблюдение.** Базовый импеданс составил {impedance_ohm:.3f} Ом. **Интерпретация.** Результат относится только к EXP-001. **Ограничение.** Повторяемость не установлена.\"\"\"))",
        ]
        notebook["cells"][0]["metadata"]["tags"].append("experiment-context")
        notebook["cells"][1]["metadata"]["tags"].append("experiment-procedure")
        notebook["cells"][3]["metadata"]["tags"].extend(
            ["experimental-observation", "experimental-analysis"]
        )
    return notebook


def test_empirical_notebook_requires_and_accepts_complete_experimental_arc():
    report = LINTER.lint_notebook(empirical_notebook())
    assert report["status"] == "pass"
    assert not {f"NB-EXP-00{index}" for index in range(1, 5)} & rule_ids(report)


def test_empirical_notebook_reports_each_missing_experimental_function():
    report = LINTER.lint_notebook(empirical_notebook(complete_arc=False))
    assert report["status"] == "fail"
    assert {f"NB-EXP-00{index}" for index in range(1, 5)} <= rule_ids(report)


def test_unknown_study_type_is_rejected():
    notebook = empirical_notebook()
    notebook["metadata"]["scientific_report"]["study_type"] = "observationalish"
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"


def test_unknown_genre_profile_is_rejected():
    notebook = empirical_notebook()
    notebook["metadata"]["scientific_report"]["genre_profile"] = "generic-report"
    report = LINTER.lint_notebook(notebook)
    assert "NB-GENRE-001" in rule_ids(report)


def test_genre_profile_requires_its_semantic_functions():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["metadata"]["scientific_report"]["genre_profile"] = "inverse-estimation"
    report = LINTER.lint_notebook(notebook)
    assert "NB-GENRE-002" in rule_ids(report)


def test_validation_axes_are_independent_required_statuses():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["metadata"]["scientific_report"].pop("scientific_validation_status")
    report = LINTER.lint_notebook(notebook)
    assert "NB-VALID-001" in rule_ids(report)


def test_conflicting_selection_rules_block_automation():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    report_metadata = notebook["metadata"]["scientific_report"]
    report_metadata["selection_policy_status"] = "conflicted"
    report_metadata["automation_status"] = "permitted"
    report = LINTER.lint_notebook(notebook)
    assert "NB-AUTO-002" in rule_ids(report)


def test_automation_requires_all_validation_axes_to_pass():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    report_metadata = notebook["metadata"]["scientific_report"]
    report_metadata["computational_validation_status"] = "partial"
    report_metadata["automation_status"] = "permitted"
    report = LINTER.lint_notebook(notebook)
    assert "NB-AUTO-003" in rule_ids(report)


def test_resolved_selection_rules_require_resolution_reference():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["metadata"]["scientific_report"]["selection_policy_status"] = "resolved"
    report = LINTER.lint_notebook(notebook)
    assert "NB-AUTO-002" in rule_ids(report)


def test_impedance_units_ohm_and_ohm_meter_are_recognized():
    text = "Z = 42,043 " + "\u041e\u043c" + "; rho = 6,934304 " + "\u041e\u043c\u00b7\u043c."
    assert list(LINTER._numeric_lines_without_units(text)) == []


def test_static_result_number_in_markdown_is_rejected():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    cell = notebook["cells"][3]
    cell["cell_type"] = "markdown"
    cell.pop("execution_count")
    cell.pop("outputs")
    cell["metadata"]["tags"] = ["observable-output", "interpretation-and-limits"]
    cell["source"] = ["**Наблюдение.** Среднее время составило 2,0 мс."]
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-NUMBER-002" in rule_ids(report)


def test_semantic_tags_allow_natural_russian_headings():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][0]["source"] = [
        "# Оценка длительности операции\n",
        "Результаты стендового измерительного эксперимента используются для расчёта среднего.",
    ]
    notebook["cells"][1]["source"] = [
        "## Длительность операции и расчётная модель\n",
        "Описание объекта, величины, единицы и принятой процедуры. Ниже представлен график зависимости длительности операции от её номера; он используется для проверки порядка наблюдений.",
    ]
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "pass"


def test_reader_facing_passport_is_rejected():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][0]["source"] = [
        "# Паспорт расчёта\n",
        "Результаты стендового измерительного эксперимента используются для расчёта.",
    ]
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-NARR-014" in rule_ids(report)


def test_reader_facing_environment_and_inherited_state_are_rejected():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][0]["source"].extend(
        ["\n", "**Среда:** requirements.lock.\n", "**Наследуемое состояние:** DATA-001."]
    )
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-NARR-017" in rule_ids(report)


def test_opening_formula_catalogue_is_rejected():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][1]["source"] = [
        "## Модель и словарь терминов\n",
        "### Формулы\n",
        "$$ y=x \\tag{1} $$\n",
        "$$ z=y^2 \\tag{2} $$\n",
    ]
    report = LINTER.lint_notebook(notebook)
    assert "NB-NARR-018" in rule_ids(report)


def test_equation_bundle_inside_term_glossary_is_rejected():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][1]["source"] = [
        "## Методика и словарь терминов\n",
        "Связи перечислены заранее.\n",
        "$$ y=x \\tag{1} $$\n",
        "$$ z=y^2 \\tag{2} $$\n",
    ]
    report = LINTER.lint_notebook(notebook)
    assert "NB-NARR-018" in rule_ids(report)


def test_file_identifier_alone_is_not_a_material_input_description():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][0]["source"] = ["# Задача\n", "DATA-001; input.csv."]
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-NARR-015" in rule_ids(report)


def test_technical_background_is_required():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][1]["metadata"]["tags"].remove("technical-background")
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-NARR-016" in rule_ids(report)


def test_computed_narrative_must_render_dynamic_markdown():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][3]["source"] = ["display(Markdown('ручной текст'))"]
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-NUMBER-003" in rule_ids(report)


def test_plot_requires_semantically_marked_caption():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][3]["metadata"]["tags"].remove("figure-caption")
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-FIGURE-001" in rule_ids(report)


def test_traceable_calculation_chain_is_required():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][1]["metadata"]["tags"].remove("calculation-chain")
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-NARR-011" in rule_ids(report)


def test_calculation_chain_must_follow_material_inputs():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][0]["metadata"]["tags"].remove("material-inputs")
    notebook["cells"][3]["metadata"]["tags"].append("material-inputs")
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-NARR-013" in rule_ids(report)


def test_material_result_requires_scientific_status():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][3]["metadata"]["tags"].remove("result-status")
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-NARR-012" in rule_ids(report)


def test_russian_notebook_requires_notebook_language_profile():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["metadata"]["scientific_report"].pop("language_profile")
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-LANG-002" in rule_ids(report)


def test_frozen_russian_notebook_requires_passed_language_audit():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["metadata"]["scientific_report"]["language_audit_status"] = "not_run"
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-LANG-004" in rule_ids(report)


def test_notebook_rules_make_russian_language_gate_mandatory():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    genre = (SKILL / "references" / "genres" / "notebook-narrative.md").read_text(
        encoding="utf-8"
    )
    language = (SKILL / "references" / "russian" / "genre-notebook.md").read_text(
        encoding="utf-8"
    )
    assert "references/russian-scientific-style.md" in skill
    assert "references/russian/genre-notebook.md" in skill
    assert "programmatically rendered narrative" in skill
    assert "language check is a release gate" in genre
    assert "extract both static Markdown" in genre
    assert "rendered narrative text" in genre
    assert "Профиль обязателен" in language
    assert "сформированные программой подписи" in language


def test_notebook_rules_require_logic_within_and_between_notebooks():
    genre = (SKILL / "references" / "genres" / "notebook-narrative.md").read_text(
        encoding="utf-8"
    )
    assert "Make the logic reproducible and evidential" in genre
    assert "Across a sequence of notebooks" in genre
    assert "artifact-handoff" in genre
    assert "identifiability and confounding stop rule" in genre

def test_telegraphic_result_shorthand_is_rejected():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][1]["source"].append(
        "\n- **Сильнее всего — от размера L.** Увеличение базы снижает ошибку ⟹ сигнал растёт."
    )
    report = LINTER.lint_notebook(notebook)
    assert "NB-NARR-019" in rule_ids(report)


def test_plot_requires_explicit_pre_figure_introduction():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][1]["source"] = ["## Измеряемая величина\nОписан расчёт среднего времени."]
    report = LINTER.lint_notebook(notebook)
    assert "NB-FIGURE-002" in rule_ids(report)


def test_plot_requires_connected_post_figure_analysis():
    notebook = json.loads((FIXTURES / "clean-single-task.ipynb").read_text(encoding="utf-8"))
    notebook["cells"][3]["source"] = [
        "from IPython.display import Markdown, display\n",
        "display(Markdown(f\"**Рисунок 1.** Значение {mean_ms:.1f} мс.\"))",
    ]
    report = LINTER.lint_notebook(notebook)
    assert "NB-FIGURE-003" in rule_ids(report)

