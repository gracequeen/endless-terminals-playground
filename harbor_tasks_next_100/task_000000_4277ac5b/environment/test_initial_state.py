# test_initial_state.py
"""
Tests to validate the initial state of the webhook processor environment
before the student performs any fixes.
"""

import json
import os
import subprocess
import pytest

WEBHOOKS_DIR = "/home/user/webhooks"
TEST_PAYLOADS_DIR = os.path.join(WEBHOOKS_DIR, "test_payloads")


class TestDirectoryStructure:
    """Verify the expected directory structure exists."""

    def test_webhooks_directory_exists(self):
        assert os.path.isdir(WEBHOOKS_DIR), f"Directory {WEBHOOKS_DIR} does not exist"

    def test_test_payloads_directory_exists(self):
        assert os.path.isdir(TEST_PAYLOADS_DIR), f"Directory {TEST_PAYLOADS_DIR} does not exist"

    def test_webhooks_directory_is_writable(self):
        assert os.access(WEBHOOKS_DIR, os.W_OK), f"Directory {WEBHOOKS_DIR} is not writable"


class TestRequiredFiles:
    """Verify all required files exist."""

    def test_validate_sh_exists(self):
        filepath = os.path.join(WEBHOOKS_DIR, "validate.sh")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_validate_sh_is_executable(self):
        filepath = os.path.join(WEBHOOKS_DIR, "validate.sh")
        assert os.access(filepath, os.X_OK), f"File {filepath} is not executable"

    def test_validator_py_exists(self):
        filepath = os.path.join(WEBHOOKS_DIR, "validator.py")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_schema_json_exists(self):
        filepath = os.path.join(WEBHOOKS_DIR, "schema.json")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_transform_jq_exists(self):
        filepath = os.path.join(WEBHOOKS_DIR, "transform.jq")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_event_01_json_exists(self):
        filepath = os.path.join(TEST_PAYLOADS_DIR, "event_01.json")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_event_02_json_exists(self):
        filepath = os.path.join(TEST_PAYLOADS_DIR, "event_02.json")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_event_03_json_exists(self):
        filepath = os.path.join(TEST_PAYLOADS_DIR, "event_03.json")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"


class TestValidateShContent:
    """Verify validate.sh calls validator.py correctly."""

    def test_validate_sh_calls_validator_py(self):
        filepath = os.path.join(WEBHOOKS_DIR, "validate.sh")
        with open(filepath, 'r') as f:
            content = f.read()
        assert "validator.py" in content, "validate.sh should call validator.py"
        assert "python3" in content or "python" in content, "validate.sh should use python to run validator.py"


class TestValidatorPyContent:
    """Verify validator.py uses jsonschema library."""

    def test_validator_py_uses_jsonschema(self):
        filepath = os.path.join(WEBHOOKS_DIR, "validator.py")
        with open(filepath, 'r') as f:
            content = f.read()
        assert "jsonschema" in content, "validator.py should use jsonschema library"
        assert "schema.json" in content, "validator.py should reference schema.json"


class TestSchemaJsonContent:
    """Verify schema.json is valid JSON and has expected structure with bugs."""

    def test_schema_json_is_valid_json(self):
        filepath = os.path.join(WEBHOOKS_DIR, "schema.json")
        with open(filepath, 'r') as f:
            try:
                schema = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"schema.json is not valid JSON: {e}")
        assert isinstance(schema, dict), "schema.json should be a JSON object"

    def test_schema_has_timestamp_pattern_bug(self):
        """The schema should have a timestamp pattern that doesn't allow Z suffix."""
        filepath = os.path.join(WEBHOOKS_DIR, "schema.json")
        with open(filepath, 'r') as f:
            schema = json.load(f)

        # Navigate to find timestamp pattern - could be in properties or nested
        schema_str = json.dumps(schema)
        # The buggy pattern doesn't end with Z or timezone handling
        assert "timestamp" in schema_str, "Schema should have timestamp field"
        # Check that there's a pattern for timestamp that's missing Z
        assert "pattern" in schema_str, "Schema should have pattern constraints"

    def test_schema_has_metadata_additional_properties_false(self):
        """The schema should have additionalProperties: false for metadata."""
        filepath = os.path.join(WEBHOOKS_DIR, "schema.json")
        with open(filepath, 'r') as f:
            schema = json.load(f)

        schema_str = json.dumps(schema)
        assert "additionalProperties" in schema_str, "Schema should have additionalProperties constraint"
        assert "metadata" in schema_str, "Schema should have metadata field"


class TestTransformJqContent:
    """Verify transform.jq exists and has the userid typo bug."""

    def test_transform_jq_has_userid_typo(self):
        """The transform.jq should have .data.userid (missing underscore) bug."""
        filepath = os.path.join(WEBHOOKS_DIR, "transform.jq")
        with open(filepath, 'r') as f:
            content = f.read()
        # Should have the typo userid instead of user_id
        assert "userid" in content.lower(), "transform.jq should reference userid field"


class TestTestPayloadsContent:
    """Verify test payloads are valid JSON with expected structure."""

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_payload_is_valid_json(self, filename):
        filepath = os.path.join(TEST_PAYLOADS_DIR, filename)
        with open(filepath, 'r') as f:
            try:
                payload = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"{filename} is not valid JSON: {e}")
        assert isinstance(payload, dict), f"{filename} should be a JSON object"

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_payload_has_required_fields(self, filename):
        filepath = os.path.join(TEST_PAYLOADS_DIR, filename)
        with open(filepath, 'r') as f:
            payload = json.load(f)

        assert "event_type" in payload, f"{filename} should have event_type field"
        assert "timestamp" in payload, f"{filename} should have timestamp field"
        assert "data" in payload, f"{filename} should have data field"

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_payload_timestamp_has_z_suffix(self, filename):
        """Payloads should have Z suffix which triggers the schema bug."""
        filepath = os.path.join(TEST_PAYLOADS_DIR, filename)
        with open(filepath, 'r') as f:
            payload = json.load(f)

        timestamp = payload.get("timestamp", "")
        assert timestamp.endswith("Z"), f"{filename} timestamp should end with Z (this triggers the schema bug)"

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_payload_metadata_has_version(self, filename):
        """Payloads should have version in metadata which triggers the schema bug."""
        filepath = os.path.join(TEST_PAYLOADS_DIR, filename)
        with open(filepath, 'r') as f:
            payload = json.load(f)

        metadata = payload.get("data", {}).get("metadata", {})
        assert "version" in metadata, f"{filename} metadata should have version field (this triggers the schema bug)"

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_payload_has_user_id(self, filename):
        """Payloads should have user_id in data."""
        filepath = os.path.join(TEST_PAYLOADS_DIR, filename)
        with open(filepath, 'r') as f:
            payload = json.load(f)

        data = payload.get("data", {})
        assert "user_id" in data, f"{filename} data should have user_id field"


class TestDependencies:
    """Verify required tools and libraries are installed."""

    def test_python3_available(self):
        result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "python3 should be available"

    def test_jsonschema_library_installed(self):
        result = subprocess.run(
            ["python3", "-c", "import jsonschema; print(jsonschema.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "jsonschema library should be installed"

    def test_jq_available(self):
        result = subprocess.run(["jq", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "jq should be available"


class TestCurrentBrokenState:
    """Verify that the pipeline is currently broken as described."""

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_validation_currently_fails(self, filename):
        """Validation should currently fail for all test payloads (this is the bug)."""
        payload_path = os.path.join(TEST_PAYLOADS_DIR, filename)
        validate_script = os.path.join(WEBHOOKS_DIR, "validate.sh")

        result = subprocess.run(
            [validate_script, payload_path],
            capture_output=True,
            text=True,
            cwd=WEBHOOKS_DIR
        )
        assert result.returncode != 0, f"validate.sh should currently FAIL for {filename} (this is the bug to fix)"

    def test_transform_currently_fails(self):
        """Transform should currently fail due to the userid typo."""
        payload_path = os.path.join(TEST_PAYLOADS_DIR, "event_01.json")
        transform_path = os.path.join(WEBHOOKS_DIR, "transform.jq")

        result = subprocess.run(
            ["jq", "-f", transform_path],
            stdin=open(payload_path, 'r'),
            capture_output=True,
            text=True,
            cwd=WEBHOOKS_DIR
        )
        # Either it fails with error, or produces null/incorrect output
        # The typo .data.userid returns null, and tonumber on null fails
        if result.returncode == 0:
            # If it doesn't fail, the output should be wrong (null or missing id)
            try:
                output = json.loads(result.stdout)
                # Check if user_id was correctly extracted - it shouldn't be
                if isinstance(output, dict) and output.get("id") == 4521:
                    pytest.fail("transform.jq should NOT correctly extract user_id yet (this is the bug)")
            except json.JSONDecodeError:
                pass  # Invalid JSON output is expected for broken state
        # If returncode != 0, that's the expected broken state
