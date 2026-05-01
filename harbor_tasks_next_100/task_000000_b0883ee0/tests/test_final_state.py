# test_final_state.py
"""
Tests to validate the final OS/filesystem state after the student has fixed the provisioning script.
This verifies that provision.sh runs successfully and produces the expected output.
"""

import os
import subprocess
import json
import pytest


class TestProvisionScriptSuccess:
    """Test that provision.sh now runs successfully."""

    def test_provision_script_exits_zero(self):
        """The provision.sh script must exit with code 0."""
        result = subprocess.run(
            ["bash", "/home/user/infra/provision.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/infra"
        )
        assert result.returncode == 0, \
            f"provision.sh should exit 0, but exited {result.returncode}.\nStdout: {result.stdout}\nStderr: {result.stderr}"


class TestConfigJsonExists:
    """Test that config.json was created."""

    def test_config_json_exists(self):
        """The config.json file must exist after running provision.sh."""
        # First run the script to ensure config.json is generated
        subprocess.run(
            ["bash", "/home/user/infra/provision.sh"],
            capture_output=True,
            cwd="/home/user/infra"
        )
        assert os.path.isfile("/home/user/infra/output/config.json"), \
            "File /home/user/infra/output/config.json does not exist after running provision.sh"


class TestConfigJsonValid:
    """Test that config.json is valid JSON with correct structure."""

    @pytest.fixture(autouse=True)
    def run_provision(self):
        """Run provision.sh before each test in this class."""
        subprocess.run(
            ["bash", "/home/user/infra/provision.sh"],
            capture_output=True,
            cwd="/home/user/infra"
        )

    def test_config_json_is_valid_json(self):
        """The config.json must be valid JSON."""
        with open("/home/user/infra/output/config.json", "r") as f:
            content = f.read()
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"config.json is not valid JSON: {e}\nContent: {content}")

    def test_config_json_has_database_key(self):
        """config.json must have 'database' key."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        assert "database" in config, \
            f"config.json missing 'database' key. Keys present: {list(config.keys())}"

    def test_config_json_has_cache_key(self):
        """config.json must have 'cache' key."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        assert "cache" in config, \
            f"config.json missing 'cache' key. Keys present: {list(config.keys())}"

    def test_config_json_has_vault_key(self):
        """config.json must have 'vault' key."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        assert "vault" in config, \
            f"config.json missing 'vault' key. Keys present: {list(config.keys())}"

    def test_config_json_has_api_key_key(self):
        """config.json must have 'api_key' key."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        assert "api_key" in config, \
            f"config.json missing 'api_key' key. Keys present: {list(config.keys())}"

    def test_config_json_has_deploy_key(self):
        """config.json must have 'deploy' key."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        assert "deploy" in config, \
            f"config.json missing 'deploy' key. Keys present: {list(config.keys())}"


class TestConfigJsonValues:
    """Test that config.json contains the correct values."""

    @pytest.fixture(autouse=True)
    def run_provision(self):
        """Run provision.sh before each test in this class."""
        subprocess.run(
            ["bash", "/home/user/infra/provision.sh"],
            capture_output=True,
            cwd="/home/user/infra"
        )

    def test_database_value_non_empty(self):
        """The 'database' value must be non-empty."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        assert config.get("database"), \
            f"'database' value is empty or missing: {config.get('database')}"

    def test_cache_value_non_empty(self):
        """The 'cache' value must be non-empty."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        assert config.get("cache"), \
            f"'cache' value is empty or missing: {config.get('cache')}"

    def test_vault_value_correct(self):
        """The 'vault' value must be 'https://vault.internal:8200'."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        expected = "https://vault.internal:8200"
        actual = config.get("vault", "")
        assert actual == expected, \
            f"'vault' value should be '{expected}', got: '{actual}'"

    def test_api_key_value_correct(self):
        """The 'api_key' value must be 'sk-prod-29f8a3e1'."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        expected = "sk-prod-29f8a3e1"
        actual = config.get("api_key", "")
        assert actual == expected, \
            f"'api_key' value should be '{expected}', got: '{actual}'"

    def test_deploy_value_correct(self):
        """The 'deploy' value must be 'dk-7721-beta'."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        expected = "dk-7721-beta"
        actual = config.get("deploy", "")
        assert actual == expected, \
            f"'deploy' value should be '{expected}', got: '{actual}'"

    def test_database_value_correct(self):
        """The 'database' value must be 'postgres.internal'."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        expected = "postgres.internal"
        actual = config.get("database", "")
        assert actual == expected, \
            f"'database' value should be '{expected}', got: '{actual}'"

    def test_cache_value_correct(self):
        """The 'cache' value must be 'redis://cache:6379'."""
        with open("/home/user/infra/output/config.json", "r") as f:
            config = json.load(f)
        expected = "redis://cache:6379"
        actual = config.get("cache", "")
        assert actual == expected, \
            f"'cache' value should be '{expected}', got: '{actual}'"


class TestConfigJsonNoCarriageReturns:
    """Test that config.json has no embedded carriage returns."""

    @pytest.fixture(autouse=True)
    def run_provision(self):
        """Run provision.sh before each test in this class."""
        subprocess.run(
            ["bash", "/home/user/infra/provision.sh"],
            capture_output=True,
            cwd="/home/user/infra"
        )

    def test_no_carriage_returns_in_config(self):
        """config.json must not contain any carriage return characters."""
        with open("/home/user/infra/output/config.json", "rb") as f:
            content = f.read()
        assert b"\r" not in content, \
            "config.json contains embedded carriage return (\\r) characters - values are not clean"

    def test_grep_no_cr_in_config(self):
        """grep -a for \\r in config.json must return no match."""
        result = subprocess.run(
            ["grep", "-a", "\r", "/home/user/infra/output/config.json"],
            capture_output=True
        )
        # grep returns 1 when no match found, 0 when match found
        assert result.returncode == 1, \
            "grep found carriage return characters in config.json - values contain \\r"


class TestProvisionScriptInvariants:
    """Test that the script maintains required invariants."""

    def test_script_still_has_set_euo_pipefail(self):
        """provision.sh must still contain 'set -euo pipefail'."""
        with open("/home/user/infra/provision.sh", "r") as f:
            content = f.read()
        assert "set -euo pipefail" in content, \
            "provision.sh must still contain 'set -euo pipefail' - don't remove set -u to hide the problem"

    def test_script_still_uses_source_command(self):
        """provision.sh must still use 'source' command for loading env files."""
        with open("/home/user/infra/provision.sh", "r") as f:
            content = f.read()
        # Check that source is used (either 'source' or '.')
        has_source = "source /home/user/infra/.env" in content or "source " in content
        assert has_source, \
            "provision.sh must still use the source command for loading env files"

    def test_script_still_writes_config_json(self):
        """provision.sh must still write to config.json."""
        with open("/home/user/infra/provision.sh", "r") as f:
            content = f.read()
        assert "/home/user/infra/output/config.json" in content, \
            "provision.sh must still write to /home/user/infra/output/config.json"


class TestAntiShortcutGuards:
    """Test that the fix is proper and not a shortcut."""

    def test_config_generated_by_script(self):
        """config.json must be generated by running provision.sh, not manually created."""
        # Remove config.json if it exists
        config_path = "/home/user/infra/output/config.json"
        if os.path.exists(config_path):
            os.remove(config_path)

        # Run provision.sh
        result = subprocess.run(
            ["bash", "/home/user/infra/provision.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/infra"
        )

        # Check that script succeeded and config.json was created
        assert result.returncode == 0, \
            f"provision.sh must succeed. Exit code: {result.returncode}\nStderr: {result.stderr}"
        assert os.path.isfile(config_path), \
            "config.json must be created by running provision.sh"

    def test_script_not_hardcoded_values(self):
        """provision.sh should not have hardcoded values in the config.json template."""
        with open("/home/user/infra/provision.sh", "r") as f:
            content = f.read()

        # Check that the actual secret values are not hardcoded in the script
        # (they should come from env files)
        # We allow the values to appear if they're in an env file being created,
        # but they shouldn't appear directly in the heredoc for config.json

        # Find the heredoc section for config.json
        if "cat > /home/user/infra/output/config.json" in content:
            # The heredoc should use variable references, not hardcoded values
            # This is a heuristic check - we look for ${VAR} patterns in the heredoc
            heredoc_start = content.find("cat > /home/user/infra/output/config.json")
            heredoc_end = content.find("EOF", heredoc_start)
            if heredoc_start != -1 and heredoc_end != -1:
                heredoc_section = content[heredoc_start:heredoc_end]
                # Should contain variable references
                has_var_refs = "${" in heredoc_section or "$" in heredoc_section
                assert has_var_refs, \
                    "config.json heredoc should use variable references, not hardcoded values"


class TestEnvValuesPreserved:
    """Test that the original .env values are preserved."""

    def test_env_file_still_has_db_host(self):
        """The .env file must still contain DB_HOST value."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        # Strip any \r to check the actual value
        content_clean = content.replace(b"\r", b"")
        assert b"DB_HOST=postgres.internal" in content_clean, \
            ".env must still contain DB_HOST=postgres.internal"

    def test_env_file_still_has_redis_url(self):
        """The .env file must still contain REDIS_URL value."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        content_clean = content.replace(b"\r", b"")
        assert b"REDIS_URL=redis://cache:6379" in content_clean, \
            ".env must still contain REDIS_URL=redis://cache:6379"

    def test_env_file_still_has_vault_addr(self):
        """The .env file must still contain VAULT_ADDR value."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        content_clean = content.replace(b"\r", b"")
        assert b"VAULT_ADDR=https://vault.internal:8200" in content_clean, \
            ".env must still contain VAULT_ADDR=https://vault.internal:8200"

    def test_env_file_still_has_api_secret(self):
        """The .env file must still contain API_SECRET value."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        content_clean = content.replace(b"\r", b"")
        assert b"API_SECRET=sk-prod-29f8a3e1" in content_clean, \
            ".env must still contain API_SECRET=sk-prod-29f8a3e1"

    def test_env_file_still_has_deploy_key(self):
        """The .env file must still contain DEPLOY_KEY value."""
        with open("/home/user/infra/.env", "rb") as f:
            content = f.read()
        content_clean = content.replace(b"\r", b"")
        assert b"DEPLOY_KEY=dk-7721-beta" in content_clean, \
            ".env must still contain DEPLOY_KEY=dk-7721-beta"


class TestMultipleRuns:
    """Test that the script works correctly on multiple runs."""

    def test_script_idempotent(self):
        """Running provision.sh multiple times should always succeed."""
        for i in range(3):
            result = subprocess.run(
                ["bash", "/home/user/infra/provision.sh"],
                capture_output=True,
                text=True,
                cwd="/home/user/infra"
            )
            assert result.returncode == 0, \
                f"provision.sh failed on run {i+1}. Exit code: {result.returncode}\nStderr: {result.stderr}"

    def test_config_consistent_across_runs(self):
        """config.json should have the same content across multiple runs."""
        configs = []
        for _ in range(2):
            subprocess.run(
                ["bash", "/home/user/infra/provision.sh"],
                capture_output=True,
                cwd="/home/user/infra"
            )
            with open("/home/user/infra/output/config.json", "r") as f:
                configs.append(json.load(f))

        assert configs[0] == configs[1], \
            f"config.json content differs between runs:\nRun 1: {configs[0]}\nRun 2: {configs[1]}"
