import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "scientific-evidence-workflow"


def load_module(name: str, relative_path: str):
    path = SKILL / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_module("validate_reader_html", "scripts/validate_reader_html.py")
EXPORTER = load_module("export_reader_html", "scripts/export_reader_html.py")


def rule_ids(report: dict) -> set[str]:
    return {finding["rule_id"] for finding in report["findings"]}


def test_reader_html_accepts_prose_formula_image_and_clickable_links(tmp_path):
    html = """
    <html><body>
      <h1 id="result">Результат</h1>
      <a id="equation"></a>
      <script type="application/vnd.jupyter.widget-state+json">{}</script>
      <p>По формуле <span class="math">y=ax</span> получена оценка.</p>
      <img src="data:image/png;base64,AA==" alt="График">
      <p><a href="#result">К результату</a></p>
      <p><a href="https://doi.org/10.1000/example">Научная публикация</a></p>
    </body></html>
    """
    report = VALIDATOR.validate_reader_html(html, path=tmp_path / "report.html")
    assert report["status"] == "pass"
    assert report["metrics"]["code_input_areas"] == 0


def test_reader_html_rejects_anchor_without_target_or_link(tmp_path):
    report = VALIDATOR.validate_reader_html(
        "<html><body><a>пустой якорь</a></body></html>",
        path=tmp_path / "report.html",
    )
    assert "HTML-LINK-001" in rule_ids(report)


def test_reader_html_rejects_visible_code_and_broken_anchor(tmp_path):
    html = """
    <html><body>
      <div class="jp-CodeCell">
        <div class="jp-InputArea"><pre>print('hidden')</pre></div>
      </div>
      <a href="#missing">Переход</a>
    </body></html>
    """
    report = VALIDATOR.validate_reader_html(html, path=tmp_path / "report.html")
    assert {"HTML-CODE-001", "HTML-LINK-003"} <= rule_ids(report)


def test_exporter_removes_code_inputs_and_preserves_markdown_links(tmp_path):
    nbformat = pytest.importorskip("nbformat")
    pytest.importorskip("nbconvert")
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell(
                "# Результат\n\n[Публикация](https://doi.org/10.1000/example)"
            ),
            nbformat.v4.new_code_cell(
                "secret_source = 42",
                execution_count=1,
                outputs=[nbformat.v4.new_output("stream", name="stdout", text="42\n")],
            ),
        ]
    )
    source = tmp_path / "report.ipynb"
    output = tmp_path / "report.html"
    nbformat.write(notebook, source)
    report = EXPORTER.export_notebook(source, output)
    rendered = output.read_text(encoding="utf-8")
    assert report["status"] == "pass"
    assert "secret_source" not in rendered
    assert "https://doi.org/10.1000/example" in rendered
    assert "42" in rendered
