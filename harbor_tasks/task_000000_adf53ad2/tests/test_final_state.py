# test_final_state.py
"""
Tests to validate the final state after the student has fixed the git hooks issue.
The pre-push hook should no longer reference /srv/repos/project and pushes should work.
"""

import os
import re
import stat
import subprocess
import pytest


class TestPrePushHookFixed:
    """Tests to verify the pre-push hook has been properly fixed"""

    def test_pre_push_hook_exists(self):
        """Verify pre-push hook file still exists"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        assert os.path.isfile(hook_path), \
            f"pre-push hook does not exist at {hook_path} - hook should not be deleted"

    def test_pre_push_hook_is_executable(self):
        """Verify pre-push hook is still executable"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        file_stat = os.stat(hook_path)
        mode = file_stat.st_mode
        assert mode & stat.S_IXUSR, \
            f"pre-push hook at {hook_path} must be executable"

    def test_pre_push_hook_no_old_path_reference(self):
        """Verify pre-push hook no longer references /srv/repos/project"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        with open(hook_path, 'r') as f:
            content = f.read()
        assert "/srv/repos/project" not in content, \
            "pre-push hook still contains hardcoded /srv/repos/project - this path must be removed or updated"

    def test_pre_push_hook_no_srv_repos_reference(self):
        """Anti-shortcut: verify hook doesn't reference /srv/repos at all"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        result = subprocess.run(
            ["grep", "-q", "/srv/repos", hook_path],
            capture_output=True
        )
        assert result.returncode != 0, \
            "pre-push hook still references /srv/repos - the hardcoded path must be completely removed"

    def test_pre_push_hook_contains_git_rev_parse(self):
        """Verify pre-push hook still calls git rev-parse --verify HEAD (core functionality preserved)"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        with open(hook_path, 'r') as f:
            content = f.read()
        assert "git rev-parse" in content and "HEAD" in content, \
            "pre-push hook must still call 'git rev-parse --verify HEAD' - core functionality must be preserved"

    def test_pre_push_hook_logs_to_git_hooks_log(self):
        """Verify pre-push hook still logs to /var/log/git-hooks.log"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        with open(hook_path, 'r') as f:
            content = f.read()
        assert "/var/log/git-hooks.log" in content, \
            "pre-push hook must still log to /var/log/git-hooks.log - core functionality must be preserved"

    def test_pre_push_hook_not_empty(self):
        """Verify pre-push hook is not empty or a noop script"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        with open(hook_path, 'r') as f:
            content = f.read()
        # Remove comments and empty lines to check for actual content
        lines = [l.strip() for l in content.split('\n') 
                 if l.strip() and not l.strip().startswith('#')]
        # Should have at least git rev-parse and logging commands
        assert len(lines) >= 2, \
            "pre-push hook appears to be empty or a noop - it must still perform logging on push"

    def test_pre_push_hook_has_shebang(self):
        """Verify pre-push hook has a valid shebang"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        with open(hook_path, 'r') as f:
            first_line = f.readline().strip()
        assert first_line.startswith("#!"), \
            f"pre-push hook should start with a shebang, got: {first_line}"


class TestGitPushWorks:
    """Tests to verify git push now works correctly"""

    def test_git_push_succeeds(self):
        """Verify git commit and push completes successfully"""
        # First, create an empty commit
        commit_result = subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "test commit for validation"],
            cwd="/home/user/project",
            capture_output=True,
            text=True
        )
        assert commit_result.returncode == 0, \
            f"git commit failed: {commit_result.stderr}"

        # Then push to origin main
        push_result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd="/home/user/project",
            capture_output=True,
            text=True
        )
        assert push_result.returncode == 0, \
            f"git push origin main failed (exit code {push_result.returncode}): {push_result.stderr}"


class TestLogFileUpdated:
    """Tests to verify the log file is properly updated after push"""

    def test_log_file_exists(self):
        """Verify /var/log/git-hooks.log exists"""
        log_path = "/var/log/git-hooks.log"
        assert os.path.isfile(log_path), \
            f"{log_path} does not exist"

    def test_log_contains_push_verified_entry(self):
        """Verify log contains 'push verified' entry with valid SHA"""
        log_path = "/var/log/git-hooks.log"
        with open(log_path, 'r') as f:
            content = f.read()

        # Check for "push verified" text
        assert "push verified" in content.lower(), \
            f"Log file should contain 'push verified' entry, content: {content}"

    def test_log_contains_valid_sha(self):
        """Verify log contains HEAD= followed by a valid 40-char SHA"""
        log_path = "/var/log/git-hooks.log"
        with open(log_path, 'r') as f:
            content = f.read()

        # Look for HEAD= followed by 40 hex characters
        sha_pattern = r'HEAD=([a-f0-9]{40})'
        match = re.search(sha_pattern, content, re.IGNORECASE)
        assert match is not None, \
            f"Log file should contain 'HEAD=' followed by a valid 40-char SHA. Content: {content}"

    def test_log_contains_timestamp(self):
        """Verify log contains a timestamp entry"""
        log_path = "/var/log/git-hooks.log"
        with open(log_path, 'r') as f:
            content = f.read()

        # The date command typically produces patterns like "Mon Jan 1" or "2024-01-01" etc.
        # Check for common date patterns or just that there's content before "push verified"
        lines = [l for l in content.split('\n') if 'push verified' in l.lower()]
        assert len(lines) > 0, "No 'push verified' lines found in log"

        # Check that the line has some content before the push verified part (timestamp)
        for line in lines:
            if 'push verified' in line.lower():
                # There should be something before "push verified" (the timestamp from date command)
                idx = line.lower().find('push verified')
                prefix = line[:idx].strip()
                if prefix and ':' in line:  # date output typically has colons in time
                    return  # Found a valid entry

        # If we get here, check if any line has reasonable timestamp indicators
        assert any(':' in l and 'push verified' in l.lower() for l in lines), \
            f"Log entries should contain timestamps. Lines with 'push verified': {lines}"


class TestRepositoryIntegrity:
    """Tests to verify repository integrity is maintained"""

    def test_project_is_still_valid_git_repo(self):
        """Verify /home/user/project is still a valid git repository"""
        result = subprocess.run(
            ["git", "status"],
            cwd="/home/user/project",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"git status failed - repository may be corrupted: {result.stderr}"

    def test_repo_history_preserved(self):
        """Verify repository still has at least 10 commits (history preserved)"""
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd="/home/user/project",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Failed to count commits: {result.stderr}"
        commit_count = int(result.stdout.strip())
        assert commit_count >= 10, \
            f"Repository should have at least 10 commits (history preserved), got {commit_count}"

    def test_bare_repo_still_functional(self):
        """Verify /home/user/project.git bare repository is still functional"""
        bare_repo = "/home/user/project.git"
        assert os.path.isdir(bare_repo), \
            f"Bare repository {bare_repo} should still exist"

        # Check it's a valid bare repo by checking HEAD
        head_file = os.path.join(bare_repo, "HEAD")
        assert os.path.isfile(head_file), \
            f"{bare_repo} should be a valid bare git repository"

    def test_origin_remote_still_configured(self):
        """Verify 'origin' remote is still properly configured"""
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd="/home/user/project",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"'origin' remote should still be configured: {result.stderr}"


class TestAntiShortcutGuards:
    """Tests to prevent shortcut solutions that don't properly fix the issue"""

    def test_srv_repos_not_created_as_workaround(self):
        """Verify /srv/repos/project was not created as a workaround"""
        assert not os.path.exists("/srv/repos/project"), \
            "/srv/repos/project should NOT exist - creating it as a workaround is not acceptable"

    def test_no_symlink_workaround(self):
        """Verify /srv/repos/project is not a symlink workaround"""
        if os.path.exists("/srv/repos/project"):
            assert not os.path.islink("/srv/repos/project"), \
                "/srv/repos/project should not be a symlink - the hook must reference the correct location directly"

    def test_hook_grep_returns_nonzero_for_old_path(self):
        """Anti-shortcut: grep for /srv/repos in hook must return non-zero"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        result = subprocess.run(
            ["grep", "-q", "/srv/repos", hook_path],
            capture_output=True
        )
        assert result.returncode != 0, \
            "grep -q '/srv/repos' must return non-zero - the hardcoded path must be removed from the hook"
