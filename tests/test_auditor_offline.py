"""Tests for auditor package — offline conformance and semantic quality checks."""

from __future__ import annotations

import ast
import json
import textwrap
from pathlib import Path

import pytest

from auditor import Decision, TaskAuditResult
from auditor.offline import (
    GateCriteria,
    assert_diversity,
    build_gate_criteria,
    check_batch,
    check_task,
    classify_asserts,
    dataset_summary,
    desc_overlap,
    structural_score,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_task(tmp_path: Path, *, final_state_src: str = "", instruction: str = "", toml: str = "") -> Path:
    """Create a minimal valid task directory."""
    d = tmp_path / "task_000001_abc"
    (d / "environment").mkdir(parents=True)
    (d / "tests").mkdir()

    (d / "instruction.md").write_text(instruction or "Print hello to stdout using python.")
    (d / "task.toml").write_text(toml or "[metadata]\ndifficulty = \"easy\"\ncategory = \"scripting\"\n")
    (d / "environment" / "Dockerfile").write_text("FROM ubuntu:22.04\n")
    (d / "environment" / "task.json").write_text(json.dumps({"description": "hello", "truth": "", "name": "task_000001_abc"}))
    (d / "environment" / "test_initial_state.py").write_text("def test_setup():\n    assert True\n")
    (d / "tests" / "test.sh").write_text("pytest tests/\n")
    (d / "tests" / "test_final_state.py").write_text(final_state_src or textwrap.dedent("""\
        import subprocess
        def test_output():
            result = subprocess.run(["python", "hello.py"], capture_output=True, text=True)
            assert result.returncode == 0
            assert "hello" in result.stdout
        """))
    return d


def _parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


# ---------------------------------------------------------------------------
# Decision enum + TaskAuditResult
# ---------------------------------------------------------------------------

class TestDecision:
    def test_values(self):
        assert Decision.PASS == "pass"
        assert Decision.FLAG == "flag"
        assert Decision.REJECT == "reject"

    def test_is_str_enum(self):
        assert isinstance(Decision.PASS, str)


class TestTaskAuditResult:
    def test_defaults(self, tmp_path):
        r = TaskAuditResult(task_id="t1", task_dir=tmp_path, decision=Decision.PASS)
        assert r.metrics == {}
        assert r.flags == []

    def test_fields(self, tmp_path):
        r = TaskAuditResult(
            task_id="t2",
            task_dir=tmp_path,
            decision=Decision.FLAG,
            metrics={"structural_score": 0.1},
            flags=["structural_score_low"],
        )
        assert r.task_id == "t2"
        assert r.decision == Decision.FLAG
        assert r.metrics["structural_score"] == 0.1
        assert "structural_score_low" in r.flags


# ---------------------------------------------------------------------------
# GateCriteria + build_gate_criteria
# ---------------------------------------------------------------------------

class TestGateCriteria:
    def test_defaults(self):
        c = GateCriteria()
        assert c.structural_reject == 0.0
        assert c.structural_flag == 0.2
        assert c.desc_overlap_reject == 0.0
        assert c.assert_diversity_flag == 2


class TestBuildGateCriteria:
    def test_fixed_threshold(self):
        c = build_gate_criteria(structural_flag=0.3)
        assert c.structural_flag == 0.3

    def test_default_threshold(self):
        c = build_gate_criteria()
        assert c.structural_flag == 0.2

    def test_percentile_mode_bottom_20(self):
        scores = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        c = build_gate_criteria(percentile_flag=0.2, scores=scores)
        # bottom 20% of 10 scores = 2 scores → threshold is scores[1] = 0.1
        assert c.structural_flag == pytest.approx(0.1)

    def test_percentile_mode_bottom_0_flags_nothing(self):
        scores = [0.0, 0.5, 1.0]
        c = build_gate_criteria(percentile_flag=0.0, scores=scores)
        assert c.structural_flag == 0.0

    def test_mutual_exclusion_raises(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            build_gate_criteria(structural_flag=0.2, percentile_flag=0.2)

    def test_percentile_without_scores_raises(self):
        with pytest.raises(ValueError, match="scores must be provided"):
            build_gate_criteria(percentile_flag=0.2)

    def test_percentile_empty_scores_raises(self):
        with pytest.raises(ValueError, match="scores must be provided"):
            build_gate_criteria(percentile_flag=0.2, scores=[])


# ---------------------------------------------------------------------------
# classify_asserts
# ---------------------------------------------------------------------------

class TestClassifyAsserts:
    def test_process_exit(self):
        tree = _parse("def t():\n    assert result.returncode == 0\n")
        counts = classify_asserts(tree)
        assert counts["process_exit"] >= 1

    def test_stdout_output(self):
        tree = _parse("def t():\n    assert 'hello' in result.stdout\n")
        counts = classify_asserts(tree)
        assert counts["stdout_output"] >= 1

    def test_file_content(self):
        tree = _parse("def t():\n    assert Path('/tmp/out').read_text() == 'expected'\n")
        counts = classify_asserts(tree)
        assert counts["file_content"] >= 1

    def test_file_exists(self):
        tree = _parse("def t():\n    assert os.path.exists('/tmp/out')\n")
        counts = classify_asserts(tree)
        assert counts["file_exists"] >= 1

    def test_permissions(self):
        tree = _parse("def t():\n    assert oct(os.stat(p).st_mode)\n")
        counts = classify_asserts(tree)
        assert counts["permissions"] >= 1

    def test_other_category(self):
        tree = _parse("def t():\n    assert x == 42\n")
        counts = classify_asserts(tree)
        assert counts["other"] >= 1

    def test_no_asserts_all_zero(self):
        tree = _parse("def t():\n    pass\n")
        counts = classify_asserts(tree)
        assert all(v == 0 for v in counts.values())

    def test_all_categories_present_in_result(self):
        tree = _parse("def t():\n    pass\n")
        counts = classify_asserts(tree)
        for cat in ("file_exists", "file_content", "permissions", "process_exit", "stdout_output", "other"):
            assert cat in counts


# ---------------------------------------------------------------------------
# structural_score
# ---------------------------------------------------------------------------

class TestStructuralScore:
    def test_all_outcome_asserts(self):
        src = textwrap.dedent("""\
            def t():
                assert result.returncode == 0
                assert "hello" in result.stdout
            """)
        assert structural_score(_parse(src)) == pytest.approx(1.0)

    def test_no_asserts_returns_zero(self):
        assert structural_score(_parse("def t():\n    pass\n")) == pytest.approx(0.0)

    def test_mixed(self):
        # 2 outcome, 2 passive → 0.5
        src = textwrap.dedent("""\
            def t():
                assert result.returncode == 0
                assert "hello" in result.stdout
                assert os.path.exists("/f")
                assert os.path.exists("/g")
            """)
        assert structural_score(_parse(src)) == pytest.approx(0.5)

    def test_only_passive_returns_zero(self):
        src = "def t():\n    assert os.path.exists('/f')\n"
        assert structural_score(_parse(src)) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# assert_diversity
# ---------------------------------------------------------------------------

class TestAssertDiversity:
    def test_zero_asserts(self):
        assert assert_diversity(_parse("def t():\n    pass\n")) == 0

    def test_single_category(self):
        src = textwrap.dedent("""\
            def t():
                assert result.returncode == 0
                assert result.returncode == 1
            """)
        assert assert_diversity(_parse(src)) == 1

    def test_two_categories(self):
        src = textwrap.dedent("""\
            def t():
                assert result.returncode == 0
                assert "hello" in result.stdout
            """)
        assert assert_diversity(_parse(src)) == 2

    def test_three_categories(self):
        src = textwrap.dedent("""\
            def t():
                assert result.returncode == 0
                assert "hello" in result.stdout
                assert os.path.exists("/f")
            """)
        assert assert_diversity(_parse(src)) == 3


# ---------------------------------------------------------------------------
# desc_overlap
# ---------------------------------------------------------------------------

class TestDescOverlap:
    def test_full_overlap(self):
        # both asserts mention keywords from instruction
        src = "def t():\n    assert 'hello' in result.stdout\n    assert 'python' in result.stdout\n"
        overlap = desc_overlap(_parse(src), "Print hello using python script")
        assert overlap == pytest.approx(1.0)

    def test_zero_overlap(self):
        src = "def t():\n    assert os.path.exists('/f')\n"
        overlap = desc_overlap(_parse(src), "Deploy nginx web server")
        assert overlap == pytest.approx(0.0)

    def test_partial_overlap(self):
        src = textwrap.dedent("""\
            def t():
                assert 'nginx' in result.stdout
                assert os.path.exists('/etc/foo')
            """)
        overlap = desc_overlap(_parse(src), "Deploy nginx web server")
        assert 0.0 < overlap < 1.0

    def test_no_asserts_returns_zero(self):
        assert desc_overlap(_parse("def t():\n    pass\n"), "some instruction") == pytest.approx(0.0)

    def test_empty_instruction_returns_zero(self):
        src = "def t():\n    assert result.returncode == 0\n"
        assert desc_overlap(_parse(src), "") == pytest.approx(0.0)

    def test_stopwords_only_instruction_returns_zero(self):
        src = "def t():\n    assert result.returncode == 0\n"
        # "the and for" → all stopwords → no keywords extracted
        assert desc_overlap(_parse(src), "the and for") == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# check_task — schema conformance
# ---------------------------------------------------------------------------

class TestCheckTaskSchemaMissing:
    def test_missing_instruction_md_rejects(self, tmp_path):
        d = _make_task(tmp_path)
        (d / "instruction.md").unlink()
        r = check_task(d)
        assert r.decision == Decision.REJECT
        assert any("instruction.md" in f for f in r.flags)

    def test_missing_task_toml_rejects(self, tmp_path):
        d = _make_task(tmp_path)
        (d / "task.toml").unlink()
        r = check_task(d)
        assert r.decision == Decision.REJECT

    def test_missing_dockerfile_rejects(self, tmp_path):
        d = _make_task(tmp_path)
        (d / "environment" / "Dockerfile").unlink()
        r = check_task(d)
        assert r.decision == Decision.REJECT

    def test_missing_test_final_state_rejects(self, tmp_path):
        d = _make_task(tmp_path)
        (d / "tests" / "test_final_state.py").unlink()
        r = check_task(d)
        assert r.decision == Decision.REJECT


# ---------------------------------------------------------------------------
# check_task — syntax errors
# ---------------------------------------------------------------------------

class TestCheckTaskSyntaxError:
    def test_syntax_error_in_final_state_rejects(self, tmp_path):
        d = _make_task(tmp_path, final_state_src="def broken(\n")
        r = check_task(d)
        assert r.decision == Decision.REJECT
        assert any("syntax_error" in f for f in r.flags)

    def test_syntax_error_in_initial_state_rejects(self, tmp_path):
        d = _make_task(tmp_path)
        (d / "environment" / "test_initial_state.py").write_text("def broken(\n")
        r = check_task(d)
        assert r.decision == Decision.REJECT


# ---------------------------------------------------------------------------
# check_task — metadata validity
# ---------------------------------------------------------------------------

class TestCheckTaskMetadata:
    def test_missing_difficulty_flags(self, tmp_path):
        d = _make_task(tmp_path, toml="[metadata]\ncategory = \"scripting\"\n")
        r = check_task(d)
        assert Decision.FLAG in (r.decision, Decision.FLAG)
        assert r.decision in (Decision.FLAG, Decision.REJECT)
        assert any("missing_metadata" in f or "metadata" in f for f in r.flags)

    def test_missing_category_flags(self, tmp_path):
        d = _make_task(tmp_path, toml="[metadata]\ndifficulty = \"easy\"\n")
        r = check_task(d)
        assert r.decision in (Decision.FLAG, Decision.REJECT)

    def test_invalid_difficulty_flags(self, tmp_path):
        d = _make_task(tmp_path, toml="[metadata]\ndifficulty = \"super_hard\"\ncategory = \"scripting\"\n")
        r = check_task(d)
        assert r.decision in (Decision.FLAG, Decision.REJECT)
        assert any("invalid_difficulty" in f for f in r.flags)

    def test_valid_difficulties_pass_metadata(self, tmp_path):
        for diff in ("easy", "medium", "hard", "intricate"):
            d = _make_task(tmp_path / diff, toml=f"[metadata]\ndifficulty = \"{diff}\"\ncategory = \"scripting\"\n")
            r = check_task(d)
            assert "invalid_difficulty" not in " ".join(r.flags), f"difficulty {diff} should be valid"


# ---------------------------------------------------------------------------
# check_task — structural_score thresholds
# ---------------------------------------------------------------------------

class TestCheckTaskStructuralScore:
    def test_zero_structural_score_rejects(self, tmp_path):
        # only file_exists asserts → structural_score == 0
        final = "def t():\n    assert os.path.exists('/f')\n"
        d = _make_task(tmp_path, final_state_src=final)
        r = check_task(d)
        assert r.decision == Decision.REJECT
        assert "structural_score_zero" in r.flags

    def test_low_structural_score_flags(self, tmp_path):
        # 1 outcome assert out of 6 → ~0.17 < 0.2 → flag
        final = textwrap.dedent("""\
            def t():
                assert os.path.exists('/a')
                assert os.path.exists('/b')
                assert os.path.exists('/c')
                assert os.path.exists('/d')
                assert os.path.exists('/e')
                assert result.returncode == 0
            """)
        d = _make_task(tmp_path, final_state_src=final)
        r = check_task(d)
        assert r.decision in (Decision.FLAG, Decision.REJECT)
        assert "structural_score_low" in r.flags

    def test_high_structural_score_does_not_flag(self, tmp_path):
        final = textwrap.dedent("""\
            import subprocess
            def t():
                result = subprocess.run(["python", "hi.py"], capture_output=True, text=True)
                assert result.returncode == 0
                assert "hello" in result.stdout
            """)
        d = _make_task(tmp_path, final_state_src=final)
        r = check_task(d)
        assert "structural_score_zero" not in r.flags
        assert "structural_score_low" not in r.flags

    def test_structural_score_stored_in_metrics(self, tmp_path):
        d = _make_task(tmp_path)
        r = check_task(d)
        assert "structural_score" in r.metrics
        assert 0.0 <= r.metrics["structural_score"] <= 1.0


# ---------------------------------------------------------------------------
# check_task — desc_overlap threshold
# ---------------------------------------------------------------------------

class TestCheckTaskDescOverlap:
    def test_zero_desc_overlap_rejects(self, tmp_path):
        # asserts reference "xyz" which has no overlap with instruction keywords
        final = "def t():\n    assert os.path.exists('/xyz_totally_unrelated_path')\n"
        instruction = "Deploy nginx web server configuration"
        d = _make_task(tmp_path, final_state_src=final, instruction=instruction)
        r = check_task(d)
        assert "desc_overlap_zero" in r.flags

    def test_nonzero_desc_overlap_does_not_reject_for_overlap(self, tmp_path):
        final = "def t():\n    assert result.returncode == 0\n    assert 'nginx' in result.stdout\n"
        instruction = "Deploy nginx web server"
        d = _make_task(tmp_path, final_state_src=final, instruction=instruction)
        r = check_task(d)
        assert "desc_overlap_zero" not in r.flags


# ---------------------------------------------------------------------------
# check_task — assert_diversity threshold
# ---------------------------------------------------------------------------

class TestCheckTaskAssertDiversity:
    def test_low_diversity_flags(self, tmp_path):
        # only one category used
        final = textwrap.dedent("""\
            def t():
                assert result.returncode == 0
                assert result.returncode != 1
            """)
        d = _make_task(tmp_path, final_state_src=final)
        r = check_task(d)
        assert "assert_diversity_low" in r.flags

    def test_sufficient_diversity_does_not_flag(self, tmp_path):
        final = textwrap.dedent("""\
            import subprocess
            def t():
                result = subprocess.run(["python", "hi.py"], capture_output=True, text=True)
                assert result.returncode == 0
                assert "hello" in result.stdout
            """)
        d = _make_task(tmp_path, final_state_src=final)
        r = check_task(d)
        assert "assert_diversity_low" not in r.flags


# ---------------------------------------------------------------------------
# check_task — clean pass
# ---------------------------------------------------------------------------

class TestCheckTaskPass:
    def test_clean_task_passes(self, tmp_path):
        d = _make_task(tmp_path)
        r = check_task(d)
        assert r.decision == Decision.PASS
        assert r.flags == []

    def test_task_id_matches_dir_name(self, tmp_path):
        d = _make_task(tmp_path)
        r = check_task(d)
        assert r.task_id == d.name

    def test_task_dir_stored(self, tmp_path):
        d = _make_task(tmp_path)
        r = check_task(d)
        assert r.task_dir == d


# ---------------------------------------------------------------------------
# check_task — configurable criteria
# ---------------------------------------------------------------------------

class TestCheckTaskConfigurableCriteria:
    def test_custom_flag_threshold_triggers(self, tmp_path):
        # structural_score will be 1.0 for our clean task; use a threshold > 1.0 to force flag
        criteria = build_gate_criteria(structural_flag=1.1)
        d = _make_task(tmp_path)
        r = check_task(d, criteria=criteria)
        assert "structural_score_low" in r.flags

    def test_zero_flag_threshold_never_flags_on_score(self, tmp_path):
        criteria = build_gate_criteria(structural_flag=0.0)
        d = _make_task(tmp_path)
        r = check_task(d, criteria=criteria)
        assert "structural_score_low" not in r.flags


# ---------------------------------------------------------------------------
# check_batch
# ---------------------------------------------------------------------------

class TestCheckBatch:
    def test_returns_aligned_list(self, tmp_path):
        dirs = [_make_task(tmp_path / f"t{i}") for i in range(3)]
        results = check_batch(dirs)
        assert len(results) == 3
        for r, d in zip(results, dirs):
            assert r.task_dir == d

    def test_empty_list(self):
        assert check_batch([]) == []

    def test_mixed_decisions(self, tmp_path):
        good = _make_task(tmp_path / "good")
        bad_final = "def t():\n    assert os.path.exists('/f')\n"
        bad = _make_task(tmp_path / "bad", final_state_src=bad_final)
        results = check_batch([good, bad])
        # Both dirs produce task_id "task_000001_abc"; check by position instead
        assert results[0].decision == Decision.PASS
        assert results[1].decision == Decision.REJECT


# ---------------------------------------------------------------------------
# dataset_summary
# ---------------------------------------------------------------------------

class TestDatasetSummary:
    def test_counts(self, tmp_path):
        good = _make_task(tmp_path / "good")
        bad_final = "def t():\n    assert os.path.exists('/f')\n"
        bad = _make_task(tmp_path / "bad", final_state_src=bad_final)
        results = check_batch([good, bad])
        s = dataset_summary(results)
        assert s["total"] == 2
        assert s["pass"] + s["flag"] + s["reject"] == 2
        assert s["reject"] >= 1

    def test_score_statistics_present(self, tmp_path):
        d = _make_task(tmp_path)
        results = check_batch([d])
        s = dataset_summary(results)
        assert "mean_structural_score" in s
        assert "median_structural_score" in s
        assert "mean_desc_overlap" in s

    def test_domain_distribution(self, tmp_path):
        d = _make_task(tmp_path)
        results = check_batch([d])
        s = dataset_summary(results)
        assert "scripting" in s["domain_distribution"]

    def test_difficulty_distribution(self, tmp_path):
        d = _make_task(tmp_path)
        results = check_batch([d])
        s = dataset_summary(results)
        assert "easy" in s["difficulty_distribution"]

    def test_empty_results(self):
        s = dataset_summary([])
        assert s["total"] == 0
        assert s["pass"] == 0
        assert s["flag"] == 0
        assert s["reject"] == 0
        assert s["mean_structural_score"] == 0.0


# ---------------------------------------------------------------------------
# Robustness: unreadable / invalid-encoding files
# ---------------------------------------------------------------------------

class TestUnreadableFiles:
    def test_unreadable_test_file_rejects(self, tmp_path):
        d = _make_task(tmp_path)
        target = d / "tests" / "test_final_state.py"
        target.chmod(0o000)
        try:
            r = check_task(d)
            assert r.decision == Decision.REJECT
            assert any("unreadable_file" in f for f in r.flags)
        finally:
            target.chmod(0o644)

    def test_unreadable_initial_state_rejects(self, tmp_path):
        d = _make_task(tmp_path)
        target = d / "environment" / "test_initial_state.py"
        target.chmod(0o000)
        try:
            r = check_task(d)
            assert r.decision == Decision.REJECT
            assert any("unreadable_file" in f for f in r.flags)
        finally:
            target.chmod(0o644)

    def test_unreadable_toml_flags(self, tmp_path):
        d = _make_task(tmp_path)
        target = d / "task.toml"
        target.chmod(0o000)
        try:
            r = check_task(d)
            assert "toml_parse_error" in r.flags
        finally:
            target.chmod(0o644)


# ---------------------------------------------------------------------------
# GateCriteria frozen
# ---------------------------------------------------------------------------

class TestGateCriteriaFrozen:
    def test_cannot_mutate_fields(self):
        c = GateCriteria()
        with pytest.raises((AttributeError, TypeError)):
            c.structural_flag = 0.99  # type: ignore[misc]

