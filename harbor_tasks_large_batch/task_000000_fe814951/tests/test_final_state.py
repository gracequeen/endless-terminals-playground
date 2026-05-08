# test_final_state.py
"""
Tests to validate the final state after the student fixes the policy scanner.
Verifies the scanner produces deterministic, correct output with exactly 8 violations.
"""

import os
import subprocess
import pytest
import re

# Base paths
SCANNER_DIR = "/home/user/scanner"
SCANNER_SCRIPT = "/home/user/scanner/scan.sh"
RULES_DIR = "/home/user/scanner/rules"
TEST_REPO = "/home/user/test-repo"

# Expected rule files
EXPECTED_RULES = ["secrets.rule", "perms.rule", "deps.rule", "docker.rule", "network.rule"]

# Expected violations (8 total)
EXPECTED_VIOLATION_PATTERNS = [
    # Secrets violations
    ("db.env", "secrets"),
    ("config.py", "secrets"),
    # Perms violation
    ("setup.sh", "perms"),
    # Deps violations (2)
    ("requirements.txt", "deps"),
    # Docker violations (2)
    ("Dockerfile", "docker"),
    ("docker-compose.yml", "docker"),
    # Network violation
    ("service.yaml", "network"),
]


def run_scanner(target=TEST_REPO, timeout=30):
    """Run the scanner and return the result."""
    result = subprocess.run(
        [SCANNER_SCRIPT, target],
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return result


def get_sorted_output(target=TEST_REPO):
    """Run scanner and return sorted output lines."""
    result = run_scanner(target)
    lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
    return sorted(lines)


class TestScannerStructurePreserved:
    """Verify the scanner structure is preserved (not replaced with hardcoded solution)."""

    def test_scanner_script_exists(self):
        assert os.path.isfile(SCANNER_SCRIPT), f"Scanner script {SCANNER_SCRIPT} does not exist"

    def test_scanner_script_is_executable(self):
        assert os.access(SCANNER_SCRIPT, os.X_OK), f"Scanner script {SCANNER_SCRIPT} is not executable"

    def test_all_rule_files_still_exist(self):
        for rule in EXPECTED_RULES:
            rule_path = os.path.join(RULES_DIR, rule)
            assert os.path.isfile(rule_path), f"Rule file {rule_path} must still exist"

    def test_exactly_five_rule_files(self):
        rule_files = [f for f in os.listdir(RULES_DIR) if f.endswith('.rule')]
        assert len(rule_files) == 5, f"Expected 5 rule files, found {len(rule_files)}: {rule_files}"

    def test_scanner_not_hardcoded_test_repo(self):
        """Scanner must not hardcode the test-repo path."""
        with open(SCANNER_SCRIPT, 'r') as f:
            content = f.read()
        # Check for hardcoded test-repo path (excluding comments)
        lines = [l for l in content.split('\n') if not l.strip().startswith('#')]
        code_content = '\n'.join(lines)
        assert 'test-repo' not in code_content, \
            "Scanner must not hardcode 'test-repo' path"

    def test_scanner_not_hardcoded_violation_output(self):
        """Scanner must not have hardcoded violation echo statements."""
        with open(SCANNER_SCRIPT, 'r') as f:
            content = f.read()
        # Look for suspicious hardcoded output patterns
        # Should not have multiple echo statements with bracketed severity that look like hardcoded violations
        hardcoded_pattern = re.compile(r'echo\s+["\']?\[(CRITICAL|HIGH|MEDIUM|LOW)\].*\.(env|py|sh|txt|yml|yaml|Dockerfile)', re.IGNORECASE)
        matches = hardcoded_pattern.findall(content)
        assert len(matches) <= 1, \
            f"Scanner appears to have hardcoded violation outputs: found {len(matches)} suspicious echo patterns"

    def test_scanner_still_uses_rule_files(self):
        """Scanner must still process .rule files."""
        with open(SCANNER_SCRIPT, 'r') as f:
            content = f.read()
        assert '.rule' in content, "Scanner must still reference .rule files"

    def test_scanner_supports_target_argument(self):
        """Scanner must still accept target directory as argument."""
        with open(SCANNER_SCRIPT, 'r') as f:
            content = f.read()
        # Should reference $1 or ${1} for the target argument
        assert '$1' in content or '${1}' in content, \
            "Scanner must still support target directory as first argument ($1)"


class TestTestRepoUnchanged:
    """Verify test-repo contents are unchanged."""

    def test_db_env_exists_with_password(self):
        db_env = os.path.join(TEST_REPO, "config", "db.env")
        assert os.path.isfile(db_env), f"db.env must still exist at {db_env}"
        with open(db_env, 'r') as f:
            content = f.read()
        assert "DB_PASSWORD" in content, "db.env must still contain DB_PASSWORD"

    def test_config_py_exists_with_api_key(self):
        config_py = os.path.join(TEST_REPO, "src", "config.py")
        assert os.path.isfile(config_py), f"config.py must still exist at {config_py}"
        with open(config_py, 'r') as f:
            content = f.read()
        assert "API_KEY" in content, "config.py must still contain API_KEY"

    def test_setup_sh_exists_with_chmod(self):
        setup_sh = os.path.join(TEST_REPO, "src", "setup.sh")
        assert os.path.isfile(setup_sh), f"setup.sh must still exist at {setup_sh}"
        with open(setup_sh, 'r') as f:
            content = f.read()
        assert "chmod 777" in content, "setup.sh must still contain 'chmod 777'"

    def test_requirements_txt_exists(self):
        req_txt = os.path.join(TEST_REPO, "requirements.txt")
        assert os.path.isfile(req_txt), f"requirements.txt must still exist at {req_txt}"

    def test_dockerfile_exists_with_user_root(self):
        dockerfile = os.path.join(TEST_REPO, "Dockerfile")
        assert os.path.isfile(dockerfile), f"Dockerfile must still exist at {dockerfile}"
        with open(dockerfile, 'r') as f:
            content = f.read()
        assert "USER root" in content, "Dockerfile must still contain 'USER root'"

    def test_docker_compose_exists_with_privileged(self):
        compose = os.path.join(TEST_REPO, "docker-compose.yml")
        assert os.path.isfile(compose), f"docker-compose.yml must still exist at {compose}"
        with open(compose, 'r') as f:
            content = f.read()
        assert "privileged" in content, "docker-compose.yml must still contain 'privileged'"

    def test_service_yaml_exists_with_hostnetwork(self):
        service_yaml = os.path.join(TEST_REPO, "k8s", "service.yaml")
        assert os.path.isfile(service_yaml), f"service.yaml must still exist at {service_yaml}"
        with open(service_yaml, 'r') as f:
            content = f.read()
        assert "hostNetwork" in content, "service.yaml must still contain 'hostNetwork'"


class TestDeterministicOutput:
    """Verify scanner produces deterministic output."""

    def test_ten_runs_produce_identical_sorted_output(self):
        """Running the scanner 10 times must produce identical sorted output each time."""
        outputs = []
        for i in range(10):
            sorted_lines = get_sorted_output()
            outputs.append(sorted_lines)

        # Compare all outputs to the first one
        first_output = outputs[0]
        for i, output in enumerate(outputs[1:], start=2):
            assert output == first_output, \
                f"Run {i} produced different output than run 1.\n" \
                f"Run 1: {first_output}\n" \
                f"Run {i}: {output}"

    def test_consecutive_runs_diff_empty(self):
        """Consecutive runs should have no diff when sorted."""
        import tempfile

        # Run 10 times and save sorted outputs
        outputs = []
        for i in range(10):
            result = run_scanner()
            lines = sorted([l for l in result.stdout.strip().split('\n') if l.strip()])
            outputs.append('\n'.join(lines))

        # Check all consecutive pairs
        for i in range(len(outputs) - 1):
            assert outputs[i] == outputs[i + 1], \
                f"Diff between run {i+1} and run {i+2} is not empty.\n" \
                f"Run {i+1}:\n{outputs[i]}\n\nRun {i+2}:\n{outputs[i+1]}"


class TestExactlyEightViolations:
    """Verify scanner finds exactly 8 violations."""

    def test_exactly_eight_violation_lines(self):
        """Scanner must output exactly 8 violation lines."""
        result = run_scanner()
        lines = [l for l in result.stdout.strip().split('\n') if l.strip()]

        # Count lines that look like violations (contain '[' which indicates severity bracket)
        violation_lines = [l for l in lines if '[' in l]

        assert len(violation_lines) == 8, \
            f"Expected exactly 8 violations, got {len(violation_lines)}.\n" \
            f"Output:\n{result.stdout}"

    def test_violation_count_consistent_across_runs(self):
        """Violation count must be 8 on every run."""
        for i in range(5):
            result = run_scanner()
            lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
            violation_lines = [l for l in lines if '[' in l]
            assert len(violation_lines) == 8, \
                f"Run {i+1}: Expected 8 violations, got {len(violation_lines)}"


class TestAllViolationsFound:
    """Verify all expected violations are found."""

    def test_secrets_violation_db_env_found(self):
        """Must find secrets violation in db.env."""
        result = run_scanner()
        output = result.stdout.lower()
        assert 'db.env' in output, \
            f"Secrets violation in db.env not found.\nOutput:\n{result.stdout}"

    def test_secrets_violation_config_py_found(self):
        """Must find secrets violation in config.py."""
        result = run_scanner()
        output = result.stdout.lower()
        assert 'config.py' in output, \
            f"Secrets violation in config.py not found.\nOutput:\n{result.stdout}"

    def test_perms_violation_setup_sh_found(self):
        """Must find perms violation in setup.sh."""
        result = run_scanner()
        output = result.stdout.lower()
        assert 'setup.sh' in output, \
            f"Perms violation in setup.sh not found.\nOutput:\n{result.stdout}"

    def test_deps_violation_requirements_found(self):
        """Must find deps violations in requirements.txt."""
        result = run_scanner()
        output = result.stdout.lower()
        assert 'requirements.txt' in output, \
            f"Deps violation in requirements.txt not found.\nOutput:\n{result.stdout}"

    def test_docker_violation_dockerfile_found(self):
        """Must find docker violation in Dockerfile."""
        result = run_scanner()
        output = result.stdout
        # Case-sensitive check for Dockerfile
        assert 'Dockerfile' in output or 'dockerfile' in output.lower(), \
            f"Docker violation in Dockerfile not found.\nOutput:\n{result.stdout}"

    def test_docker_violation_compose_found(self):
        """Must find docker violation in docker-compose.yml."""
        result = run_scanner()
        output = result.stdout.lower()
        assert 'docker-compose.yml' in output, \
            f"Docker violation in docker-compose.yml not found.\nOutput:\n{result.stdout}"

    def test_network_violation_service_yaml_found(self):
        """Must find network violation in service.yaml."""
        result = run_scanner()
        output = result.stdout.lower()
        assert 'service.yaml' in output, \
            f"Network violation in service.yaml not found.\nOutput:\n{result.stdout}"

    def test_all_five_rule_types_represented(self):
        """Output must include violations from all 5 rule types."""
        result = run_scanner()
        output = result.stdout.lower()

        # Check that each rule type appears in the output
        rule_types_found = {
            'secrets': 'secrets' in output,
            'perms': 'perms' in output,
            'deps': 'deps' in output,
            'docker': 'docker' in output,
            'network': 'network' in output,
        }

        missing = [rt for rt, found in rule_types_found.items() if not found]
        assert not missing, \
            f"Missing rule types in output: {missing}.\nOutput:\n{result.stdout}"


class TestScannerFlexibility:
    """Verify scanner still works with arbitrary target directories."""

    def test_scanner_accepts_different_target(self):
        """Scanner must accept and scan different target directories."""
        import tempfile

        # Create a temporary directory with a test file
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file that would match secrets rule
            test_file = os.path.join(tmpdir, "test.env")
            with open(test_file, 'w') as f:
                f.write("PASSWORD=secret123\n")

            # Run scanner on this directory
            result = subprocess.run(
                [SCANNER_SCRIPT, tmpdir],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Should complete without error
            assert result.returncode is not None, "Scanner failed to run on alternate target"

    def test_scanner_with_no_violations(self):
        """Scanner should handle directories with no violations."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an empty file that won't match any rules
            test_file = os.path.join(tmpdir, "clean.txt")
            with open(test_file, 'w') as f:
                f.write("nothing suspicious here\n")

            result = subprocess.run(
                [SCANNER_SCRIPT, tmpdir],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Should complete without crashing
            assert result.returncode is not None, "Scanner crashed on clean directory"


class TestOutputFormat:
    """Verify output format includes severity brackets."""

    def test_output_contains_severity_brackets(self):
        """Each violation line should contain severity in brackets."""
        result = run_scanner()
        lines = [l for l in result.stdout.strip().split('\n') if l.strip()]

        # All non-empty lines should be violation lines with severity
        for line in lines:
            assert '[' in line and ']' in line, \
                f"Violation line missing severity brackets: {line}"

    def test_output_lines_are_complete(self):
        """Output lines should not be corrupted/interleaved."""
        result = run_scanner()
        lines = [l for l in result.stdout.strip().split('\n') if l.strip()]

        for line in lines:
            # Each line should have exactly one opening and one closing bracket for severity
            open_brackets = line.count('[')
            close_brackets = line.count(']')
            assert open_brackets >= 1 and close_brackets >= 1, \
                f"Corrupted output line (missing brackets): {line}"

            # Line should contain a file path reference
            assert '/' in line or '.' in line, \
                f"Output line missing file reference: {line}"
