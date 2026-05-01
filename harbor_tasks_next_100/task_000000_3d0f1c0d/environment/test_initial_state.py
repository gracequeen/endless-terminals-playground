# test_initial_state.py
"""
Tests to validate the initial state before the student performs the task.
Verifies that /home/user/assets-repo is a valid git repository with the expected structure.
"""

import os
import subprocess
import pytest


REPO_PATH = "/home/user/assets-repo"
GIT_DIR = os.path.join(REPO_PATH, ".git")


def test_repo_directory_exists():
    """Verify that the repository directory exists."""
    assert os.path.isdir(REPO_PATH), f"Repository directory {REPO_PATH} does not exist"


def test_git_directory_exists():
    """Verify that .git directory exists (it's a git repository)."""
    assert os.path.isdir(GIT_DIR), f".git directory not found at {GIT_DIR} - not a git repository"


def test_git_is_installed():
    """Verify that git is installed and accessible."""
    result = subprocess.run(
        ["git", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Git is not installed or not accessible"
    assert "git version" in result.stdout.lower(), f"Unexpected git version output: {result.stdout}"


def test_repo_is_valid_git_repository():
    """Verify that the directory is a valid git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"Not a valid git repository: {result.stderr}"
    assert result.stdout.strip() == "true", f"Not inside a git work tree: {result.stdout}"


def test_repo_has_commits():
    """Verify that the repository has at least one commit."""
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"Failed to count commits: {result.stderr}"
    commit_count = int(result.stdout.strip())
    assert commit_count >= 1, "Repository has no commits"


def test_repo_has_multiple_commits():
    """Verify that the repository has multiple commits (as per task description)."""
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"Failed to count commits: {result.stderr}"
    commit_count = int(result.stdout.strip())
    assert commit_count > 1, f"Repository should have multiple commits, but has only {commit_count}"


def test_repo_has_png_blobs_in_history():
    """Verify that there are .png files in the git history."""
    # List all objects that are blobs with .png extension across all history
    result = subprocess.run(
        ["git", "rev-list", "--objects", "--all"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"Failed to list git objects: {result.stderr}"

    png_entries = [line for line in result.stdout.splitlines() if line.endswith('.png')]
    assert len(png_entries) > 0, "No .png files found in git history"


def test_repo_has_at_least_5_distinct_png_blobs():
    """Verify that there are at least 5 distinct .png blobs in the object store."""
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

    assert len(png_blobs) >= 5, f"Expected at least 5 distinct .png blobs, found {len(png_blobs)}"


def test_repo_is_readable():
    """Verify that the repository is readable."""
    assert os.access(REPO_PATH, os.R_OK), f"Repository {REPO_PATH} is not readable"
    assert os.access(GIT_DIR, os.R_OK), f".git directory {GIT_DIR} is not readable"


def test_git_objects_directory_exists():
    """Verify that the git objects directory exists and is intact."""
    objects_dir = os.path.join(GIT_DIR, "objects")
    assert os.path.isdir(objects_dir), f"Git objects directory not found at {objects_dir}"


def test_git_refs_directory_exists():
    """Verify that the git refs directory exists and is intact."""
    refs_dir = os.path.join(GIT_DIR, "refs")
    assert os.path.isdir(refs_dir), f"Git refs directory not found at {refs_dir}"


def test_git_head_exists():
    """Verify that HEAD exists in the repository."""
    head_file = os.path.join(GIT_DIR, "HEAD")
    assert os.path.isfile(head_file), f"Git HEAD file not found at {head_file}"


def test_can_run_git_cat_file():
    """Verify that git cat-file command works (needed to get blob sizes)."""
    result = subprocess.run(
        ["git", "cat-file", "--version"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    # git cat-file --version may not exist in all versions, try a different approach
    result = subprocess.run(
        ["git", "cat-file", "-t", "HEAD"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    assert result.returncode == 0, f"git cat-file command failed: {result.stderr}"


def test_png_blobs_total_size_is_expected():
    """Verify that the total size of all unique .png blobs is 847392 bytes."""
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

    assert total_size == 847392, f"Expected total .png blob size to be 847392 bytes, but got {total_size} bytes"
