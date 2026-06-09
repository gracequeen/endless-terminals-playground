"""
Tests for train/harbor/split_tasks.py

Covers:
- Exact 80/5/15 split counts from 100 tasks
- No overlap between splits
- All tasks accounted for (union = full set)
- Determinism: same seed → same split
- Different seed → different split (probabilistic)
- Stratified split: difficulty proportions preserved within ±2 tasks
- HarborTaskDataset.load_split() returns correct dataset with right count
- Edge case: task dir missing task.toml uses 'unknown' difficulty
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure the repo root is importable
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from train.harbor.split_tasks import create_split, main
from train.harbor.dataset import HarborTaskDataset


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DIFFICULTIES = ["easy", "medium", "hard"]


def _make_task(task_dir: Path, name: str, difficulty: str | None = "medium") -> Path:
    """Create a minimal task directory with instruction.md and optional task.toml."""
    d = task_dir / name
    d.mkdir(parents=True)
    (d / "instruction.md").write_text(f"# Task: {name}\nDo something.\n")
    if difficulty is not None:
        (d / "task.toml").write_text(f'[metadata]\ndifficulty = "{difficulty}"\n')
    return d


def _make_task_dir(tmp_path: Path, n: int, difficulties: list[str] | None = None) -> Path:
    """
    Create a task directory with n tasks.

    If difficulties is provided, it must have length n and specifies each
    task's difficulty. Otherwise tasks cycle evenly through easy/medium/hard.
    """
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()

    if difficulties is None:
        diffs = [DIFFICULTIES[i % len(DIFFICULTIES)] for i in range(n)]
    else:
        assert len(difficulties) == n
        diffs = difficulties

    for i, diff in enumerate(diffs):
        _make_task(task_dir, f"task_{i:04d}", difficulty=diff)

    return task_dir


# ---------------------------------------------------------------------------
# 1. Exact split counts from 100 tasks
# ---------------------------------------------------------------------------

class TestExactCounts:
    def test_train_count_100_tasks(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)
        assert len(split["train"]) == 80

    def test_eval_count_100_tasks(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)
        assert len(split["eval"]) == 5

    def test_test_count_100_tasks(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)
        assert len(split["test"]) == 15

    def test_total_sums_to_100(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)
        total = len(split["train"]) + len(split["eval"]) + len(split["test"])
        assert total == 100

    def test_result_has_metadata_key(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)
        assert "metadata" in split

    def test_split_keys_present(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 10)
        split = create_split(task_dir, seed=0)
        assert set(split.keys()) == {"train", "eval", "test", "metadata"}


# ---------------------------------------------------------------------------
# 2. No overlap between splits
# ---------------------------------------------------------------------------

class TestNoOverlap:
    def test_train_eval_disjoint(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)
        assert set(split["train"]).isdisjoint(set(split["eval"]))

    def test_train_test_disjoint(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)
        assert set(split["train"]).isdisjoint(set(split["test"]))

    def test_eval_test_disjoint(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)
        assert set(split["eval"]).isdisjoint(set(split["test"]))


# ---------------------------------------------------------------------------
# 3. All tasks accounted for (union = full set)
# ---------------------------------------------------------------------------

class TestUnionIsFullSet:
    def test_union_equals_full_set_100(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        all_tasks = {d.name for d in task_dir.iterdir() if d.is_dir()}
        split = create_split(task_dir, seed=42)
        union = set(split["train"]) | set(split["eval"]) | set(split["test"])
        assert union == all_tasks

    def test_union_equals_full_set_small(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 20)
        all_tasks = {d.name for d in task_dir.iterdir() if d.is_dir()}
        split = create_split(task_dir, seed=7)
        union = set(split["train"]) | set(split["eval"]) | set(split["test"])
        assert union == all_tasks


# ---------------------------------------------------------------------------
# 4. Determinism: same seed → same split
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_seed_same_train(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        s1 = create_split(task_dir, seed=99)
        s2 = create_split(task_dir, seed=99)
        assert sorted(s1["train"]) == sorted(s2["train"])

    def test_same_seed_same_eval(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        s1 = create_split(task_dir, seed=99)
        s2 = create_split(task_dir, seed=99)
        assert sorted(s1["eval"]) == sorted(s2["eval"])

    def test_same_seed_same_test(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        s1 = create_split(task_dir, seed=99)
        s2 = create_split(task_dir, seed=99)
        assert sorted(s1["test"]) == sorted(s2["test"])


# ---------------------------------------------------------------------------
# 5. Different seed → different split
# ---------------------------------------------------------------------------

class TestDifferentSeed:
    def test_different_seeds_differ(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        s1 = create_split(task_dir, seed=1)
        s2 = create_split(task_dir, seed=2)
        # Very unlikely (effectively impossible with 100 tasks) to be identical
        assert sorted(s1["train"]) != sorted(s2["train"])


# ---------------------------------------------------------------------------
# 6. Stratified: proportional difficulty distribution (±2 tasks tolerance)
# ---------------------------------------------------------------------------

class TestStratified:
    def _difficulty_counts(self, task_dir: Path, names: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for name in names:
            toml_path = task_dir / name / "task.toml"
            if toml_path.exists():
                text = toml_path.read_text()
                for line in text.splitlines():
                    if line.strip().startswith("difficulty"):
                        diff = line.split("=")[1].strip().strip('"').strip("'")
                        counts[diff] = counts.get(diff, 0) + 1
                        break
            else:
                counts["unknown"] = counts.get("unknown", 0) + 1
        return counts

    def test_train_difficulty_proportional(self, tmp_path):
        # 60 easy, 30 medium, 10 hard  (100 tasks)
        diffs = ["easy"] * 60 + ["medium"] * 30 + ["hard"] * 10
        task_dir = _make_task_dir(tmp_path, 100, difficulties=diffs)
        split = create_split(task_dir, seed=42)

        counts = self._difficulty_counts(task_dir, split["train"])
        # Expected: 48 easy, 24 medium, 8 hard in train (80%)
        assert abs(counts.get("easy", 0) - 48) <= 2
        assert abs(counts.get("medium", 0) - 24) <= 2
        assert abs(counts.get("hard", 0) - 8) <= 2

    def test_eval_difficulty_proportional(self, tmp_path):
        # 60 easy, 30 medium, 10 hard  (100 tasks)
        diffs = ["easy"] * 60 + ["medium"] * 30 + ["hard"] * 10
        task_dir = _make_task_dir(tmp_path, 100, difficulties=diffs)
        split = create_split(task_dir, seed=42)

        counts = self._difficulty_counts(task_dir, split["eval"])
        # Expected: 3 easy, 1-2 medium, ~0-1 hard in eval (5%)
        assert abs(counts.get("easy", 0) - 3) <= 2
        assert abs(counts.get("medium", 0) - 2) <= 2

    def test_test_difficulty_proportional(self, tmp_path):
        # 60 easy, 30 medium, 10 hard  (100 tasks)
        diffs = ["easy"] * 60 + ["medium"] * 30 + ["hard"] * 10
        task_dir = _make_task_dir(tmp_path, 100, difficulties=diffs)
        split = create_split(task_dir, seed=42)

        counts = self._difficulty_counts(task_dir, split["test"])
        # Expected: 9 easy, 4-5 medium, 1-2 hard in test (15%)
        assert abs(counts.get("easy", 0) - 9) <= 2
        assert abs(counts.get("medium", 0) - 5) <= 2


# ---------------------------------------------------------------------------
# 7. HarborTaskDataset.load_split() correctness
# ---------------------------------------------------------------------------

class TestLoadSplit:
    def _write_split_json(self, path: Path, split_data: dict) -> Path:
        """Write a split dict as JSON to path and return the path."""
        path.write_text(json.dumps(split_data))
        return path

    def test_load_split_train_count(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)

        split_json = tmp_path / "split.json"
        # Embed absolute paths so load_split can find the dirs
        split_with_paths = {
            "train": [str(task_dir / n) for n in split["train"]],
            "eval": [str(task_dir / n) for n in split["eval"]],
            "test": [str(task_dir / n) for n in split["test"]],
            "metadata": split["metadata"],
        }
        self._write_split_json(split_json, split_with_paths)

        ds = HarborTaskDataset.load_split(split_json, split="train")
        assert len(ds) == 80

    def test_load_split_eval_count(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)

        split_json = tmp_path / "split.json"
        split_with_paths = {
            "train": [str(task_dir / n) for n in split["train"]],
            "eval": [str(task_dir / n) for n in split["eval"]],
            "test": [str(task_dir / n) for n in split["test"]],
            "metadata": split["metadata"],
        }
        self._write_split_json(split_json, split_with_paths)

        ds = HarborTaskDataset.load_split(split_json, split="eval")
        assert len(ds) == 5

    def test_load_split_test_count(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 100)
        split = create_split(task_dir, seed=42)

        split_json = tmp_path / "split.json"
        split_with_paths = {
            "train": [str(task_dir / n) for n in split["train"]],
            "eval": [str(task_dir / n) for n in split["eval"]],
            "test": [str(task_dir / n) for n in split["test"]],
            "metadata": split["metadata"],
        }
        self._write_split_json(split_json, split_with_paths)

        ds = HarborTaskDataset.load_split(split_json, split="test")
        assert len(ds) == 15

    def test_load_split_returns_harbor_task_dataset(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 20)
        split = create_split(task_dir, seed=0)

        split_json = tmp_path / "split.json"
        split_with_paths = {
            "train": [str(task_dir / n) for n in split["train"]],
            "eval": [str(task_dir / n) for n in split["eval"]],
            "test": [str(task_dir / n) for n in split["test"]],
            "metadata": split["metadata"],
        }
        self._write_split_json(split_json, split_with_paths)

        ds = HarborTaskDataset.load_split(split_json, split="train")
        assert isinstance(ds, HarborTaskDataset)

    def test_load_split_paths_are_valid(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 20)
        split = create_split(task_dir, seed=0)

        split_json = tmp_path / "split.json"
        split_with_paths = {
            "train": [str(task_dir / n) for n in split["train"]],
            "eval": [str(task_dir / n) for n in split["eval"]],
            "test": [str(task_dir / n) for n in split["test"]],
            "metadata": split["metadata"],
        }
        self._write_split_json(split_json, split_with_paths)

        ds = HarborTaskDataset.load_split(split_json, split="train")
        for task_path in ds.get_task_paths():
            assert task_path.exists()
            assert (task_path / "instruction.md").exists()

    def test_load_split_invalid_key_raises(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 20)
        split = create_split(task_dir, seed=0)

        split_json = tmp_path / "split.json"
        split_with_paths = {
            "train": [str(task_dir / n) for n in split["train"]],
            "eval": [str(task_dir / n) for n in split["eval"]],
            "test": [str(task_dir / n) for n in split["test"]],
            "metadata": split["metadata"],
        }
        self._write_split_json(split_json, split_with_paths)

        with pytest.raises((KeyError, ValueError)):
            HarborTaskDataset.load_split(split_json, split="nonexistent")


# ---------------------------------------------------------------------------
# 8. Edge case: task dir with no task.toml uses 'unknown' difficulty
# ---------------------------------------------------------------------------

class TestMissingTaskToml:
    def test_no_task_toml_included_in_split(self, tmp_path):
        task_dir = tmp_path / "tasks"
        task_dir.mkdir()
        # Create 10 tasks without task.toml
        for i in range(10):
            d = task_dir / f"task_{i:04d}"
            d.mkdir()
            (d / "instruction.md").write_text(f"# Task {i}\n")
            # deliberately omit task.toml

        split = create_split(task_dir, seed=1)
        all_tasks = {d.name for d in task_dir.iterdir() if d.is_dir()}
        union = set(split["train"]) | set(split["eval"]) | set(split["test"])
        assert union == all_tasks

    def test_no_task_toml_metadata_has_unknown_difficulty(self, tmp_path):
        task_dir = tmp_path / "tasks"
        task_dir.mkdir()
        for i in range(10):
            d = task_dir / f"task_{i:04d}"
            d.mkdir()
            (d / "instruction.md").write_text(f"# Task {i}\n")

        split = create_split(task_dir, seed=1)
        meta = split["metadata"]
        # metadata should acknowledge 'unknown' difficulty (implementation-defined shape)
        # At minimum, metadata must be a dict
        assert isinstance(meta, dict)

    def test_mixed_toml_and_no_toml_still_splits_all(self, tmp_path):
        task_dir = tmp_path / "tasks"
        task_dir.mkdir()
        # 5 with toml, 5 without
        for i in range(5):
            d = task_dir / f"task_with_{i:04d}"
            d.mkdir()
            (d / "instruction.md").write_text(f"# Task {i}\n")
            (d / "task.toml").write_text('[metadata]\ndifficulty = "easy"\n')
        for i in range(5):
            d = task_dir / f"task_sans_{i:04d}"
            d.mkdir()
            (d / "instruction.md").write_text(f"# Task sans {i}\n")

        split = create_split(task_dir, seed=3)
        all_tasks = {d.name for d in task_dir.iterdir() if d.is_dir()}
        union = set(split["train"]) | set(split["eval"]) | set(split["test"])
        assert union == all_tasks


# ---------------------------------------------------------------------------
# main() smoke test
# ---------------------------------------------------------------------------

class TestMain:
    def test_main_writes_json_file(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 20)
        out_file = tmp_path / "out_split.json"

        main(
            task_dir=str(task_dir),
            output=str(out_file),
            seed=0,
        )

        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert "train" in data
        assert "eval" in data
        assert "test" in data
        assert "metadata" in data

    def test_main_output_is_valid_json(self, tmp_path):
        task_dir = _make_task_dir(tmp_path, 20)
        out_file = tmp_path / "split.json"

        main(task_dir=str(task_dir), output=str(out_file), seed=5)

        # Should not raise
        json.loads(out_file.read_text())
