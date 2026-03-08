from swarmlens.engine.utils import normalize_text, jaccard_similarity
from swarmlens.io.loaders import load_case, validate_case
from swarmlens.engine.analyzer import analyze_case
from pathlib import Path


def test_normalize_text():
    assert normalize_text("Hello, WORLD!! #Tag") == "hello world #tag"


def test_jaccard_similarity():
    assert round(jaccard_similarity(["a", "b"], ["b", "c"]), 2) == 0.33


def test_demo_case_analysis():
    base = Path(__file__).resolve().parents[1] / "swarmlens" / "demo_data" / "case_alpha"
    data = load_case(base)
    result = validate_case(data)
    assert result["ok"] is True
    report = analyze_case(data, case_name="case_alpha")
    assert report["summary"]["accounts"] >= 5
    assert "account_scores" in report
    assert len(report["graph"]["nodes"]) >= 5
