"""Tests for train/harbor/eval_harbor.py — covers compute_summary and load_tasks_from_manifest."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from train.harbor.eval_harbor import compute_summary, load_tasks_from_manifest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manifest(tmp_path: Path, train=2, eval_=1, test=2) -> Path:
    manifest = {
        "train": [f"task_train_{i:02d}" for i in range(train)],
        "eval":  [f"task_eval_{i:02d}"  for i in range(eval_)],
        "test":  [f"task_test_{i:02d}"  for i in range(test)],
        "metadata": {"seed": 42, "total": train + eval_ + test,
                     "task_dir": str(tmp_path), "split_fractions": {},
                     "counts": {"train": train, "eval": eval_, "test": test},
                     "difficulty_counts": {}},
    }
    p = tmp_path / "split.json"
    p.write_text(json.dumps(manifest))
    return p


def _make_task_dirs(tmp_path: Path, names: list[str], difficulty: str = "medium") -> None:
    for name in names:
        d = tmp_path / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "instruction.md").write_text(f"# {name}\n")
        (d / "task.toml").write_text(f'[metadata]\ndifficulty = "{difficulty}"\n')


# ---------------------------------------------------------------------------
# compute_summary
# ---------------------------------------------------------------------------

class TestComputeSummary:
    def test_empty(self):
        s = compute_summary([])
        assert s["pass_at_1"] == 0.0
        assert s["n_tasks"] == 0

    def test_all_pass(self):
        results = [{"reward": 1.0, "difficulty": "easy", "num_turns": 4}] * 5
        s = compute_summary(results)
        assert s["pass_at_1"] == 1.0
        assert s["n_success"] == 5

    def test_all_fail(self):
        results = [{"reward": 0.0, "difficulty": "hard", "num_turns": 8}] * 3
        s = compute_summary(results)
        assert s["pass_at_1"] == 0.0
        assert s["n_success"] == 0

    def test_partial(self):
        results = [
            {"reward": 1.0, "difficulty": "easy", "num_turns": 3},
            {"reward": 0.0, "difficulty": "easy", "num_turns": 8},
            {"reward": 1.0, "difficulty": "hard", "num_turns": 5},
            {"reward": 0.0, "difficulty": "hard", "num_turns": 8},
        ]
        s = compute_summary(results)
        assert s["pass_at_1"] == pytest.approx(0.5)
        assert s["n_success"] == 2
        assert s["n_tasks"] == 4

    def test_avg_reward(self):
        results = [{"reward": 0.5, "difficulty": "medium", "num_turns": 4}] * 4
        s = compute_summary(results)
        assert s["avg_reward"] == pytest.approx(0.5)

    def test_by_difficulty_keys(self):
        results = [
            {"reward": 1.0, "difficulty": "easy",   "num_turns": 2},
            {"reward": 0.0, "difficulty": "hard",   "num_turns": 8},
            {"reward": 1.0, "difficulty": "medium", "num_turns": 4},
        ]
        s = compute_summary(results)
        assert set(s["by_difficulty"].keys()) == {"easy", "hard", "medium"}

    def test_by_difficulty_pass_rate(self):
        results = [
            {"reward": 1.0, "difficulty": "easy", "num_turns": 2},
            {"reward": 1.0, "difficulty": "easy", "num_turns": 3},
            {"reward": 0.0, "difficulty": "hard", "num_turns": 8},
        ]
        s = compute_summary(results)
        assert s["by_difficulty"]["easy"]["pass_at_1"] == pytest.approx(1.0)
        assert s["by_difficulty"]["hard"]["pass_at_1"] == pytest.approx(0.0)

    def test_avg_turns(self):
        results = [
            {"reward": 1.0, "difficulty": "easy", "num_turns": 4},
            {"reward": 0.0, "difficulty": "easy", "num_turns": 8},
        ]
        s = compute_summary(results)
        assert s["avg_turns"] == pytest.approx(6.0)


# ---------------------------------------------------------------------------
# load_tasks_from_manifest
# ---------------------------------------------------------------------------

class TestLoadTasksFromManifest:
    def test_returns_correct_count(self, tmp_path):
        manifest = _make_manifest(tmp_path, train=3, eval_=1, test=4)
        _make_task_dirs(tmp_path, [f"task_test_{i:02d}" for i in range(4)])
        tasks = load_tasks_from_manifest(manifest, "test", tmp_path)
        assert len(tasks) == 4

    def test_task_has_required_keys(self, tmp_path):
        manifest = _make_manifest(tmp_path, test=2)
        _make_task_dirs(tmp_path, ["task_test_00", "task_test_01"])
        tasks = load_tasks_from_manifest(manifest, "test", tmp_path)
        for t in tasks:
            assert "name" in t
            assert "path" in t
            assert "difficulty" in t

    def test_difficulty_read_from_toml(self, tmp_path):
        manifest = _make_manifest(tmp_path, test=1)
        _make_task_dirs(tmp_path, ["task_test_00"], difficulty="hard")
        tasks = load_tasks_from_manifest(manifest, "test", tmp_path)
        assert tasks[0]["difficulty"] == "hard"

    def test_missing_toml_uses_unknown(self, tmp_path):
        manifest = _make_manifest(tmp_path, test=1)
        d = tmp_path / "task_test_00"
        d.mkdir()
        (d / "instruction.md").write_text("# task\n")
        # no task.toml
        tasks = load_tasks_from_manifest(manifest, "test", tmp_path)
        assert tasks[0]["difficulty"] == "unknown"

    def test_invalid_split_raises(self, tmp_path):
        manifest = _make_manifest(tmp_path)
        with pytest.raises((KeyError, ValueError)):
            load_tasks_from_manifest(manifest, "nonexistent", tmp_path)

    def test_path_is_absolute(self, tmp_path):
        manifest = _make_manifest(tmp_path, test=2)
        _make_task_dirs(tmp_path, ["task_test_00", "task_test_01"])
        tasks = load_tasks_from_manifest(manifest, "test", tmp_path)
        for t in tasks:
            assert Path(t["path"]).is_absolute()

    def test_eval_split(self, tmp_path):
        manifest = _make_manifest(tmp_path, eval_=2)
        _make_task_dirs(tmp_path, ["task_eval_00", "task_eval_01"])
        tasks = load_tasks_from_manifest(manifest, "eval", tmp_path)
        assert len(tasks) == 2


# ---------------------------------------------------------------------------
# Comparison output schema
# ---------------------------------------------------------------------------

class TestComparisonSchema:
    def test_delta_computation(self):
        pre  = {"pass_at_1": 0.10, "avg_reward": 0.10, "n_success": 1, "n_tasks": 10, "by_difficulty": {}}
        post = {"pass_at_1": 0.30, "avg_reward": 0.30, "n_success": 3, "n_tasks": 10, "by_difficulty": {}}
        delta_pass = post["pass_at_1"] - pre["pass_at_1"]
        assert delta_pass == pytest.approx(0.20)

    def test_no_regression_detection(self):
        pre  = {"pass_at_1": 0.40, "avg_reward": 0.40}
        post = {"pass_at_1": 0.20, "avg_reward": 0.20}
        assert post["pass_at_1"] - pre["pass_at_1"] < 0  # regression detected
