# test_initial_state.py
"""
Tests to validate the initial state before the student fixes the policy scanner.
Verifies the scanner, rules, and test-repo exist with the expected structure and content.
"""

import os
import subprocess
import stat
import pytest

# Base paths
SCANNER_DIR = "/home/user/scanner"
SCANNER_SCRIPT = "/home/user/scanner/scan.sh"
RULES_DIR = "/home/user/scanner/rules"
TEST_REPO = "/home/user/test-repo"

# Expected rule files
EXPECTED_RULES = ["secrets.rule", "perms.rule", "deps.rule", "docker.rule", "network.rule"]


class TestScannerExists:
    """Verify the scanner directory and script exist."""

    def test_scanner_directory_exists(self):
        assert os.path.isdir(SCANNER_DIR), f"Scanner directory {SCANNER_DIR} does not exist"

    def test_scanner_script_exists(self):
        assert os.path.isfile(SCANNER_SCRIPT), f"Scanner script {SCANNER_SCRIPT} does not exist"

    def test_scanner_script_is_executable(self):
        assert os.access(SCANNER_SCRIPT, os.X_OK), f"Scanner script {SCANNER_SCRIPT} is not executable"

    def test_scanner_script_is_bash(self):
        with open(SCANNER_SCRIPT, 'r') as f:
            first_line = f.readline()
        assert first_line.strip().startswith("#!") and "bash" in first_line, \
            f"Scanner script should be a bash script, got shebang: {first_line.strip()}"


class TestRulesDirectory:
    """Verify the rules directory and rule files exist."""

    def test_rules_directory_exists(self):
        assert os.path.isdir(RULES_DIR), f"Rules directory {RULES_DIR} does not exist"

    def test_all_rule_files_exist(self):
        for rule in EXPECTED_RULES:
            rule_path = os.path.join(RULES_DIR, rule)
            assert os.path.isfile(rule_path), f"Rule file {rule_path} does not exist"

    def test_exactly_five_rule_files(self):
        rule_files = [f for f in os.listdir(RULES_DIR) if f.endswith('.rule')]
        assert len(rule_files) == 5, f"Expected 5 rule files, found {len(rule_files)}: {rule_files}"

    @pytest.mark.parametrize("rule_name", EXPECTED_RULES)
    def test_rule_file_has_three_lines(self, rule_name):
        rule_path = os.path.join(RULES_DIR, rule_name)
        with open(rule_path, 'r') as f:
            content = f.read()
        # Rule files should have at least 3 lines (glob, regex, severity)
        lines = content.split('\n')
        # Filter out completely empty trailing lines for counting meaningful lines
        meaningful_lines = [l for i, l in enumerate(lines) if l.strip() or i < 3]
        assert len(meaningful_lines) >= 3, \
            f"Rule file {rule_name} should have at least 3 lines (glob, regex, severity), found {len(meaningful_lines)}"


class TestTestRepoExists:
    """Verify the test repository exists with expected structure."""

    def test_test_repo_directory_exists(self):
        assert os.path.isdir(TEST_REPO), f"Test repo directory {TEST_REPO} does not exist"

    def test_config_directory_exists(self):
        config_dir = os.path.join(TEST_REPO, "config")
        assert os.path.isdir(config_dir), f"Config directory {config_dir} does not exist"

    def test_db_env_exists(self):
        db_env = os.path.join(TEST_REPO, "config", "db.env")
        assert os.path.isfile(db_env), f"db.env file {db_env} does not exist"

    def test_db_env_contains_password(self):
        db_env = os.path.join(TEST_REPO, "config", "db.env")
        with open(db_env, 'r') as f:
            content = f.read()
        assert "DB_PASSWORD" in content, "db.env should contain DB_PASSWORD"

    def test_scripts_directory_exists(self):
        scripts_dir = os.path.join(TEST_REPO, "scripts")
        assert os.path.isdir(scripts_dir), f"Scripts directory {scripts_dir} does not exist"

    def test_deploy_sh_exists(self):
        deploy_sh = os.path.join(TEST_REPO, "scripts", "deploy.sh")
        assert os.path.isfile(deploy_sh), f"deploy.sh file {deploy_sh} does not exist"

    def test_src_directory_exists(self):
        src_dir = os.path.join(TEST_REPO, "src")
        assert os.path.isdir(src_dir), f"Src directory {src_dir} does not exist"

    def test_setup_sh_exists(self):
        setup_sh = os.path.join(TEST_REPO, "src", "setup.sh")
        assert os.path.isfile(setup_sh), f"setup.sh file {setup_sh} does not exist"

    def test_setup_sh_contains_chmod_777(self):
        setup_sh = os.path.join(TEST_REPO, "src", "setup.sh")
        with open(setup_sh, 'r') as f:
            content = f.read()
        assert "chmod 777" in content, "setup.sh should contain 'chmod 777'"

    def test_config_py_exists(self):
        config_py = os.path.join(TEST_REPO, "src", "config.py")
        assert os.path.isfile(config_py), f"config.py file {config_py} does not exist"

    def test_config_py_contains_api_key(self):
        config_py = os.path.join(TEST_REPO, "src", "config.py")
        with open(config_py, 'r') as f:
            content = f.read()
        assert "API_KEY" in content, "config.py should contain API_KEY"

    def test_requirements_txt_exists(self):
        req_txt = os.path.join(TEST_REPO, "requirements.txt")
        assert os.path.isfile(req_txt), f"requirements.txt file {req_txt} does not exist"

    def test_requirements_contains_versioned_deps(self):
        req_txt = os.path.join(TEST_REPO, "requirements.txt")
        with open(req_txt, 'r') as f:
            content = f.read()
        assert "requests==" in content, "requirements.txt should contain requests with version"
        assert "flask==" in content, "requirements.txt should contain flask with version"

    def test_dockerfile_exists(self):
        dockerfile = os.path.join(TEST_REPO, "Dockerfile")
        assert os.path.isfile(dockerfile), f"Dockerfile {dockerfile} does not exist"

    def test_dockerfile_contains_user_root(self):
        dockerfile = os.path.join(TEST_REPO, "Dockerfile")
        with open(dockerfile, 'r') as f:
            content = f.read()
        assert "USER root" in content, "Dockerfile should contain 'USER root'"

    def test_docker_compose_exists(self):
        compose = os.path.join(TEST_REPO, "docker-compose.yml")
        assert os.path.isfile(compose), f"docker-compose.yml {compose} does not exist"

    def test_docker_compose_contains_privileged(self):
        compose = os.path.join(TEST_REPO, "docker-compose.yml")
        with open(compose, 'r') as f:
            content = f.read()
        assert "privileged" in content, "docker-compose.yml should contain 'privileged'"

    def test_k8s_directory_exists(self):
        k8s_dir = os.path.join(TEST_REPO, "k8s")
        assert os.path.isdir(k8s_dir), f"k8s directory {k8s_dir} does not exist"

    def test_service_yaml_exists(self):
        service_yaml = os.path.join(TEST_REPO, "k8s", "service.yaml")
        assert os.path.isfile(service_yaml), f"service.yaml file {service_yaml} does not exist"

    def test_service_yaml_contains_hostnetwork(self):
        service_yaml = os.path.join(TEST_REPO, "k8s", "service.yaml")
        with open(service_yaml, 'r') as f:
            content = f.read()
        assert "hostNetwork" in content, "service.yaml should contain 'hostNetwork'"


class TestScannerScriptStructure:
    """Verify the scanner script has the expected buggy structure."""

    def test_scanner_uses_find_command(self):
        with open(SCANNER_SCRIPT, 'r') as f:
            content = f.read()
        assert "find " in content, "Scanner should use find command"

    def test_scanner_uses_xargs(self):
        with open(SCANNER_SCRIPT, 'r') as f:
            content = f.read()
        assert "xargs" in content, "Scanner should use xargs"

    def test_scanner_uses_grep(self):
        with open(SCANNER_SCRIPT, 'r') as f:
            content = f.read()
        assert "grep" in content, "Scanner should use grep"

    def test_scanner_reads_rule_files(self):
        with open(SCANNER_SCRIPT, 'r') as f:
            content = f.read()
        assert ".rule" in content, "Scanner should reference .rule files"

    def test_scanner_has_rules_dir_reference(self):
        with open(SCANNER_SCRIPT, 'r') as f:
            content = f.read()
        assert "rules" in content.lower(), "Scanner should reference rules directory"


class TestRequiredToolsAvailable:
    """Verify required tools are available on the system."""

    def test_bash_available(self):
        result = subprocess.run(["which", "bash"], capture_output=True)
        assert result.returncode == 0, "bash is not available"

    def test_python3_available(self):
        result = subprocess.run(["which", "python3"], capture_output=True)
        assert result.returncode == 0, "python3 is not available"

    def test_grep_available(self):
        result = subprocess.run(["which", "grep"], capture_output=True)
        assert result.returncode == 0, "grep is not available"

    def test_find_available(self):
        result = subprocess.run(["which", "find"], capture_output=True)
        assert result.returncode == 0, "find is not available"

    def test_xargs_available(self):
        result = subprocess.run(["which", "xargs"], capture_output=True)
        assert result.returncode == 0, "xargs is not available"

    def test_sed_available(self):
        result = subprocess.run(["which", "sed"], capture_output=True)
        assert result.returncode == 0, "sed is not available"


class TestHomeDirectoryWritable:
    """Verify /home/user is writable."""

    def test_home_user_exists(self):
        assert os.path.isdir("/home/user"), "/home/user directory does not exist"

    def test_home_user_writable(self):
        assert os.access("/home/user", os.W_OK), "/home/user is not writable"


class TestScannerCanRun:
    """Verify the scanner can be executed (even if results are non-deterministic)."""

    def test_scanner_runs_without_crash(self):
        result = subprocess.run(
            [SCANNER_SCRIPT, TEST_REPO],
            capture_output=True,
            text=True,
            timeout=30
        )
        # We don't check return code as it might be non-zero
        # Just verify it doesn't crash completely
        assert result.returncode is not None, "Scanner failed to execute"

    def test_scanner_produces_some_output(self):
        result = subprocess.run(
            [SCANNER_SCRIPT, TEST_REPO],
            capture_output=True,
            text=True,
            timeout=30
        )
        # The scanner should produce some output (violations)
        # Even with bugs, it should find something
        output = result.stdout.strip()
        assert len(output) > 0, "Scanner produced no output at all"
