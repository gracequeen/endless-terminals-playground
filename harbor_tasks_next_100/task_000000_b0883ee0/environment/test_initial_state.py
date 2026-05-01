# test_initial_state.py
"""
Tests to validate the initial OS/filesystem state before the student performs the action.
This verifies the buggy state described in the task.
"""

import os
import subprocess
import stat
import pytest


class TestInfraDirectoryStructure:
    """Test that the required directory structure exists."""

    def test_infra_directory_exists(self):
        """The /home/user/infra directory must exist."""
        assert os.path.isdir("/home/user/infra"), \
            "Directory /home/user/infra does not exist"

    def test_output_directory_exists(self):
        """The /home/user/infra/output directory must exist."""
        assert os.path.isdir("/home/user/infra/output"), \
            "Directory /home/user/infra/output does not exist"

    def test_output_directory_is_empty(self):
        """The output directory should be empty initially."""
        contents = os.listdir("/home/user/infra/output")
        assert len(contents) == 0, \
            f"Directory /home/user/infra/output should be empty but contains: {contents}"


class TestProvisionScript:
    """Test that provision.sh exists with correct properties."""

    def test_provision_script_exists(self):
        """The provision.sh script must exist."""
        assert os.path.isfile("/home/user/infra/provision.sh"), \
            "File /home/user/infra/provision.sh does not exist"

    def test_provision_script_is_executable(self):
        """The provision.sh script must be executable."""
        path = "/home/user/infra/provision.sh"
        assert os.access(path, os.X_OK), \
            f"File {path} is not executable"

    def test_provision_script_has_shebang(self):
        """The script must start with bash shebang."""
        with open("/home/user/infra/provision.sh", "r") as f:
            first_line = f.readline().strip()
        assert first_line == "#!/bin/bash", \
            f"Script should start with '#!/bin/bash', got: {first_line}"

    def test_provision_script_has_set_euo_pipefail(self):
        """The script must have set -euo pipefail."""
        with open("/home/user/infra/provision.sh", "r") as f:
            content = f.read()
        assert "set -euo pipefail" in content, \
            "Script must contain 'set -euo pipefail'"

    def test_provision_script_sources_env(self):
        """The script must source .env file."""
        with open("/home/user/infra/provision.sh", "r") as f:
            content = f.read()
        assert "source /home/user/infra/.env" in content, \
            "Script must contain 'source /home/user/infra/.env'"

    def test_provision_script_unsets_sensitive_vars(self):
        """The script must unset VAULT_ADDR, API_SECRET, DEPLOY_KEY."""
        with open("/home/user/infra/provision.sh", "r") as f:
            content = f.read()
        assert "unset VAULT_ADDR API_SECRET DEPLOY_KEY" in content, \
            "Script must contain 'unset VAULT_ADDR API_SECRET DEPLOY_KEY'"

    def test_provision_script_checks_env_secrets(self):
        """The script must check for .env.secrets file."""
        with open("/home/user/infra/provision.sh", "r") as f:
            content = f.read()
        assert "/home/user/infra/.env.secrets" in content, \
            "Script must reference /home/user/infra/.env.secrets"

    def test_provision_script_writes_config_json(self):
        """The script must write to config.json."""
        with open("/home/user/infra/provision.sh", "r") as f:
            content = f.read()
        assert "/home/user/infra/output/config.json" in content, \
            "Script must write to /home/user/infra/output/config.json"


class TestEnvFile:
    """Test the .env file exists with correct content and the CRLF bug."""

    def test_env_file_exists(self):
        """The .env file must exist."""
        assert os.path.isfile("/home/user/infra/.env"), \
            "File /home/user/infra/.env does not exist"

    def test_env_file_contains_db_host(self):
        """The .env file must contain DB_HOST."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        assert b"DB_HOST=postgres.internal" in content, \
            ".env must contain DB_HOST=postgres.internal"

    def test_env_file_contains_redis_url(self):
        """The .env file must contain REDIS_URL."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        assert b"REDIS_URL=redis://cache:6379" in content, \
            ".env must contain REDIS_URL=redis://cache:6379"

    def test_env_file_contains_vault_addr(self):
        """The .env file must contain VAULT_ADDR."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        assert b"VAULT_ADDR=https://vault.internal:8200" in content, \
            ".env must contain VAULT_ADDR=https://vault.internal:8200"

    def test_env_file_contains_api_secret(self):
        """The .env file must contain API_SECRET."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        assert b"API_SECRET=sk-prod-29f8a3e1" in content, \
            ".env must contain API_SECRET=sk-prod-29f8a3e1"

    def test_env_file_contains_deploy_key(self):
        """The .env file must contain DEPLOY_KEY."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        assert b"DEPLOY_KEY=dk-7721-beta" in content, \
            ".env must contain DEPLOY_KEY=dk-7721-beta"

    def test_env_file_has_crlf_on_some_lines(self):
        """The .env file must have CRLF endings on lines 3-5 (the bug)."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        # Check that CRLF exists in the file (at least one \r\n)
        assert b"\r\n" in content, \
            ".env file must have CRLF line endings on some lines (this is the bug)"

    def test_env_file_has_mixed_line_endings(self):
        """The .env file must have mixed line endings (LF and CRLF)."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        # Should have both pure LF (not preceded by CR) and CRLF
        has_crlf = b"\r\n" in content
        # Check for LF not preceded by CR
        has_pure_lf = False
        for i, byte in enumerate(content):
            if byte == ord('\n'):
                if i == 0 or content[i-1] != ord('\r'):
                    has_pure_lf = True
                    break
        assert has_crlf and has_pure_lf, \
            ".env file must have mixed line endings (some LF, some CRLF)"


class TestEnvSecretsFile:
    """Test that .env.secrets does NOT exist (this is part of the bug)."""

    def test_env_secrets_does_not_exist(self):
        """The .env.secrets file must NOT exist (this is the core bug)."""
        assert not os.path.exists("/home/user/infra/.env.secrets"), \
            "File /home/user/infra/.env.secrets should NOT exist - this is part of the bug"


class TestRequiredTools:
    """Test that required tools are available."""

    def test_bash_available(self):
        """Bash must be available."""
        result = subprocess.run(["which", "bash"], capture_output=True)
        assert result.returncode == 0, "bash is not available"

    def test_bash_version_5(self):
        """Bash version should be 5.x."""
        result = subprocess.run(["bash", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "Could not get bash version"
        assert "version 5" in result.stdout or "version 5" in result.stderr, \
            f"Bash 5.x required, got: {result.stdout}"

    def test_curl_available(self):
        """curl must be available."""
        result = subprocess.run(["which", "curl"], capture_output=True)
        assert result.returncode == 0, "curl is not available"

    def test_jq_available(self):
        """jq must be available."""
        result = subprocess.run(["which", "jq"], capture_output=True)
        assert result.returncode == 0, "jq is not available"


class TestInfraDirectoryWritable:
    """Test that the infra directory is writable."""

    def test_infra_directory_writable(self):
        """The /home/user/infra directory must be writable."""
        assert os.access("/home/user/infra", os.W_OK), \
            "/home/user/infra is not writable"

    def test_output_directory_writable(self):
        """The /home/user/infra/output directory must be writable."""
        assert os.access("/home/user/infra/output", os.W_OK), \
            "/home/user/infra/output is not writable"


class TestProvisionScriptFailsInitially:
    """Test that running provision.sh fails in its current state."""

    def test_provision_script_fails(self):
        """The provision.sh script should fail due to unbound VAULT_ADDR."""
        result = subprocess.run(
            ["bash", "/home/user/infra/provision.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/infra"
        )
        assert result.returncode != 0, \
            "provision.sh should fail in its current buggy state, but it succeeded"

    def test_provision_script_fails_with_unbound_variable(self):
        """The error should mention unbound variable."""
        result = subprocess.run(
            ["bash", "/home/user/infra/provision.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/infra"
        )
        # The error could be in stdout or stderr
        combined_output = result.stdout + result.stderr
        assert "unbound variable" in combined_output.lower() or "VAULT_ADDR" in combined_output, \
            f"Expected 'unbound variable' error mentioning VAULT_ADDR, got: {combined_output}"
