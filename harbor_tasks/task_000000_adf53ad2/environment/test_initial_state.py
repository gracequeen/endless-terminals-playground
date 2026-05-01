# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the git hooks debugging task.
"""

import os
import stat
import subprocess
import pytest


class TestGitRepository:
    """Tests for the main git repository at /home/user/project"""

    def test_project_directory_exists(self):
        """Verify /home/user/project directory exists"""
        assert os.path.isdir("/home/user/project"), \
            "/home/user/project directory does not exist"

    def test_project_is_git_repo(self):
        """Verify /home/user/project is a valid git repository"""
        git_dir = "/home/user/project/.git"
        assert os.path.isdir(git_dir), \
            f"{git_dir} does not exist - not a git repository"

    def test_git_status_works(self):
        """Verify git status works in the project directory"""
        result = subprocess.run(
            ["git", "status"],
            cwd="/home/user/project",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"git status failed in /home/user/project: {result.stderr}"

    def test_git_log_works(self):
        """Verify git log works in the project directory"""
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd="/home/user/project",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"git log failed in /home/user/project: {result.stderr}"

    def test_repo_has_at_least_10_commits(self):
        """Verify the repository has at least 10 commits on main"""
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
            f"Repository has only {commit_count} commits, expected at least 10"

    def test_main_branch_exists(self):
        """Verify main branch exists"""
        result = subprocess.run(
            ["git", "branch", "--list", "main"],
            cwd="/home/user/project",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0 and result.stdout.strip(), \
            "main branch does not exist in /home/user/project"


class TestPrePushHook:
    """Tests for the pre-push hook configuration"""

    def test_hooks_directory_exists(self):
        """Verify .git/hooks directory exists"""
        hooks_dir = "/home/user/project/.git/hooks"
        assert os.path.isdir(hooks_dir), \
            f"{hooks_dir} directory does not exist"

    def test_pre_push_hook_exists(self):
        """Verify pre-push hook file exists"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        assert os.path.isfile(hook_path), \
            f"pre-push hook does not exist at {hook_path}"

    def test_pre_push_hook_is_executable(self):
        """Verify pre-push hook is executable (mode 755)"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        file_stat = os.stat(hook_path)
        mode = file_stat.st_mode
        # Check for executable bit (at least user executable)
        assert mode & stat.S_IXUSR, \
            f"pre-push hook at {hook_path} is not executable"

    def test_pre_push_hook_has_shebang(self):
        """Verify pre-push hook starts with bash shebang"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        with open(hook_path, 'r') as f:
            first_line = f.readline().strip()
        assert first_line == "#!/bin/bash", \
            f"pre-push hook should start with #!/bin/bash, got: {first_line}"

    def test_pre_push_hook_contains_hardcoded_old_path(self):
        """Verify pre-push hook contains the buggy hardcoded path /srv/repos/project"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        with open(hook_path, 'r') as f:
            content = f.read()
        assert "/srv/repos/project" in content, \
            "pre-push hook should contain hardcoded /srv/repos/project (the bug to fix)"

    def test_pre_push_hook_contains_cd_to_old_path(self):
        """Verify pre-push hook has 'cd /srv/repos/project' command"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        with open(hook_path, 'r') as f:
            content = f.read()
        assert "cd /srv/repos/project" in content, \
            "pre-push hook should contain 'cd /srv/repos/project' (the bug)"

    def test_pre_push_hook_contains_git_rev_parse(self):
        """Verify pre-push hook calls git rev-parse --verify HEAD"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        with open(hook_path, 'r') as f:
            content = f.read()
        assert "git rev-parse --verify HEAD" in content, \
            "pre-push hook should contain 'git rev-parse --verify HEAD'"

    def test_pre_push_hook_logs_to_git_hooks_log(self):
        """Verify pre-push hook logs to /var/log/git-hooks.log"""
        hook_path = "/home/user/project/.git/hooks/pre-push"
        with open(hook_path, 'r') as f:
            content = f.read()
        assert "/var/log/git-hooks.log" in content, \
            "pre-push hook should log to /var/log/git-hooks.log"


class TestOldLocationRemoved:
    """Tests to verify the old repository location doesn't exist"""

    def test_srv_repos_project_does_not_exist(self):
        """Verify /srv/repos/project does NOT exist (old location removed)"""
        assert not os.path.exists("/srv/repos/project"), \
            "/srv/repos/project should NOT exist - it was the old location that was removed"


class TestLogFile:
    """Tests for the git hooks log file"""

    def test_git_hooks_log_exists(self):
        """Verify /var/log/git-hooks.log exists"""
        log_path = "/var/log/git-hooks.log"
        assert os.path.isfile(log_path), \
            f"{log_path} does not exist"

    def test_git_hooks_log_is_writable(self):
        """Verify /var/log/git-hooks.log is writable by current user"""
        log_path = "/var/log/git-hooks.log"
        assert os.access(log_path, os.W_OK), \
            f"{log_path} is not writable by current user"


class TestBareRemoteRepository:
    """Tests for the bare repository used as push target"""

    def test_bare_repo_exists(self):
        """Verify /home/user/project.git bare repository exists"""
        bare_repo = "/home/user/project.git"
        assert os.path.isdir(bare_repo), \
            f"Bare repository {bare_repo} does not exist"

    def test_bare_repo_is_bare(self):
        """Verify /home/user/project.git is a bare git repository"""
        bare_repo = "/home/user/project.git"
        # A bare repo has HEAD file directly in the directory
        head_file = os.path.join(bare_repo, "HEAD")
        assert os.path.isfile(head_file), \
            f"{bare_repo} does not appear to be a bare git repository (no HEAD file)"

    def test_origin_remote_configured(self):
        """Verify 'origin' remote is configured pointing to the bare repo"""
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd="/home/user/project",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"'origin' remote not configured: {result.stderr}"
        remote_url = result.stdout.strip()
        assert "project.git" in remote_url or "/home/user/project.git" in remote_url, \
            f"'origin' remote should point to /home/user/project.git, got: {remote_url}"


class TestGitInstallation:
    """Tests for git installation"""

    def test_git_installed(self):
        """Verify git is installed"""
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "git is not installed or not in PATH"

    def test_git_version_2_39_or_higher(self):
        """Verify git version is 2.39 or higher"""
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get git version"
        # Output format: "git version X.Y.Z"
        version_str = result.stdout.strip().split()[-1]
        parts = version_str.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        assert (major > 2) or (major == 2 and minor >= 39), \
            f"git version should be 2.39+, got {version_str}"


class TestProjectWritable:
    """Tests for write permissions on project directories"""

    def test_project_directory_writable(self):
        """Verify /home/user/project is writable"""
        assert os.access("/home/user/project", os.W_OK), \
            "/home/user/project is not writable"

    def test_hooks_directory_writable(self):
        """Verify /home/user/project/.git/hooks is writable"""
        hooks_dir = "/home/user/project/.git/hooks"
        assert os.access(hooks_dir, os.W_OK), \
            f"{hooks_dir} is not writable"
