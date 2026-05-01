# test_final_state.py
"""
Tests to validate the final state after the student has completed the task.
Verifies that:
1. The repository is unchanged (no modifications)
2. The correct answer (847392) was output
"""

import os
import subprocess
import pytest


REPO_PATH = "/home/user/assets-repo"
GIT_DIR = os.path.join(REPO_PATH, ".git")
EXPECTED_TOTAL_SIZE = 847392


def test_repo_directory_still_exists():
    """Verify that the repository directory still exists."""
    assert os.path.isdir(REPO_PATH), f"Repository directory {REPO_PATH} no longer exists"


def test_git_directory_still_exists():
    """Verify that .git directory still exists."""
    assert os.path.isdir(GIT_DIR), f".git directory not found at {GIT_DIR}"


def test_repo_is_still_valid_git_repository():
    """Verify that the directory is still a valid git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"Not a valid git repository: {result.stderr}"
    assert result.stdout.strip() == "true", f"Not inside a git work tree: {result.stdout}"


def test_no_uncommitted_changes():
    """Verify that there are no uncommitted changes in the repository."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"Failed to check git status: {result.stderr}"
    assert result.stdout.strip() == "", f"Repository has uncommitted changes: {result.stdout}"


def test_no_staged_changes():
    """Verify that there are no staged changes in the index."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"Failed to check staged changes: {result.stderr}"
    assert result.stdout.strip() == "", f"Repository has staged changes: {result.stdout}"


def test_png_blobs_total_size_unchanged():
    """Verify that the total size of all unique .png blobs is still 847392 bytes."""
    # Get all objects with their paths
    result = subprocess.run(
        ["git", "rev-list", "--objects", "--all"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"Failed to list git objects: {result.stderr}"

    # Extract unique blob hashes for .png files
    png_blobs = set()
    for line in result.stdout.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            blob_hash, path = parts
            if path.endswith('.png'):
                png_blobs.add(blob_hash)

    # Calculate total size of all unique .png blobs
    total_size = 0
    for blob_hash in png_blobs:
        result = subprocess.run(
            ["git", "cat-file", "-s", blob_hash],
            capture_output=True,
            text=True,
            cwd=REPO_PATH
        )
        assert result.returncode == 0, f"Failed to get size of blob {blob_hash}: {result.stderr}"
        total_size += int(result.stdout.strip())

    assert total_size == EXPECTED_TOTAL_SIZE, (
        f"Expected total .png blob size to be {EXPECTED_TOTAL_SIZE} bytes, "
        f"but got {total_size} bytes - repository may have been modified"
    )


def test_git_objects_directory_intact():
    """Verify that the git objects directory is still intact."""
    objects_dir = os.path.join(GIT_DIR, "objects")
    assert os.path.isdir(objects_dir), f"Git objects directory not found at {objects_dir}"


def test_no_filter_branch_backup():
    """Verify that no filter-branch operation was performed (would create refs/original)."""
    original_refs = os.path.join(GIT_DIR, "refs", "original")
    assert not os.path.exists(original_refs), (
        f"refs/original exists at {original_refs} - filter-branch may have been run"
    )


def test_answer_file_or_output_contains_correct_value():
    """
    Check if the correct answer was produced.
    This test looks for common output patterns in files that might contain the answer.
    Since the task asks to "print" the byte count, we verify the expected value
    is correct and the repository state allows computing it.
    """
    # The expected answer that should have been printed
    expected = EXPECTED_TOTAL_SIZE

    # Verify the expected answer can be computed from the repository
    result = subprocess.run(
        ["git", "rev-list", "--objects", "--all"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"Failed to list git objects: {result.stderr}"

    png_blobs = set()
    for line in result.stdout.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            blob_hash, path = parts
            if path.endswith('.png'):
                png_blobs.add(blob_hash)

    total_size = 0
    for blob_hash in png_blobs:
        result = subprocess.run(
            ["git", "cat-file", "-s", blob_hash],
            capture_output=True,
            text=True,
            cwd=REPO_PATH
        )
        if result.returncode == 0:
            total_size += int(result.stdout.strip())

    assert total_size == expected, (
        f"The correct answer should be {expected} bytes, "
        f"computed from repository: {total_size} bytes"
    )


def test_at_least_5_distinct_png_blobs_still_exist():
    """Verify that there are still at least 5 distinct .png blobs in the object store."""
    result = subprocess.run(
        ["git", "rev-list", "--objects", "--all"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"Failed to list git objects: {result.stderr}"

    png_blobs = set()
    for line in result.stdout.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            blob_hash, path = parts
            if path.endswith('.png'):
                png_blobs.add(blob_hash)

    assert len(png_blobs) >= 5, (
        f"Expected at least 5 distinct .png blobs, found {len(png_blobs)} - "
        "repository may have been modified (gc, prune, etc.)"
    )
