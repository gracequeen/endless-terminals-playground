# test_final_state.py
"""
Tests to validate the final state of the webhook processor environment
after the student has fixed all bugs.
"""

import json
import os
import subprocess
import pytest

WEBHOOKS_DIR = "/home/user/webhooks"
TEST_PAYLOADS_DIR = os.path.join(WEBHOOKS_DIR, "test_payloads")


class TestDirectoryStructure:
    """Verify the expected directory structure still exists."""

    def test_webhooks_directory_exists(self):
        assert os.path.isdir(WEBHOOKS_DIR), f"Directory {WEBHOOKS_DIR} does not exist"

    def test_test_payloads_directory_exists(self):
        assert os.path.isdir(TEST_PAYLOADS_DIR), f"Directory {TEST_PAYLOADS_DIR} does not exist"


class TestRequiredFilesExist:
    """Verify all required files still exist."""

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

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_test_payload_exists(self, filename):
        filepath = os.path.join(TEST_PAYLOADS_DIR, filename)
        assert os.path.isfile(filepath), f"File {filepath} does not exist"


class TestValidateShStructure:
    """Verify validate.sh still calls validator.py (structure unchanged)."""

    def test_validate_sh_calls_validator_py(self):
        filepath = os.path.join(WEBHOOKS_DIR, "validate.sh")
        with open(filepath, 'r') as f:
            content = f.read()
        assert "validator.py" in content, "validate.sh should still call validator.py"


class TestValidationPasses:
    """Verify that validation now passes for all test payloads."""

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_validation_passes(self, filename):
        """Validation should now pass for all test payloads."""
        payload_path = os.path.join(TEST_PAYLOADS_DIR, filename)
        validate_script = os.path.join(WEBHOOKS_DIR, "validate.sh")

        result = subprocess.run(
            [validate_script, payload_path],
            capture_output=True,
            text=True,
            cwd=WEBHOOKS_DIR
        )
        assert result.returncode == 0, (
            f"validate.sh should exit 0 for {filename}, but got exit code {result.returncode}. "
            f"stderr: {result.stderr}"
        )


class TestTransformWorks:
    """Verify that transform.jq now works correctly."""

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_transform_exits_zero(self, filename):
        """Transform should exit 0 for all test payloads."""
        payload_path = os.path.join(TEST_PAYLOADS_DIR, filename)
        transform_path = os.path.join(WEBHOOKS_DIR, "transform.jq")

        with open(payload_path, 'r') as f:
            result = subprocess.run(
                ["jq", "-f", transform_path],
                stdin=f,
                capture_output=True,
                text=True,
                cwd=WEBHOOKS_DIR
            )
        assert result.returncode == 0, (
            f"jq -f transform.jq should exit 0 for {filename}, but got exit code {result.returncode}. "
            f"stderr: {result.stderr}"
        )

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_transform_produces_valid_json(self, filename):
        """Transform should produce valid JSON output."""
        payload_path = os.path.join(TEST_PAYLOADS_DIR, filename)
        transform_path = os.path.join(WEBHOOKS_DIR, "transform.jq")

        with open(payload_path, 'r') as f:
            result = subprocess.run(
                ["jq", "-f", transform_path],
                stdin=f,
                capture_output=True,
                text=True,
                cwd=WEBHOOKS_DIR
            )

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Transform output for {filename} is not valid JSON: {e}. Output: {result.stdout}")

        assert output is not None, f"Transform output for {filename} should not be null"

    def test_transform_event_01_has_correct_id(self):
        """Transform output for event_01.json should include id: 4521."""
        payload_path = os.path.join(TEST_PAYLOADS_DIR, "event_01.json")
        transform_path = os.path.join(WEBHOOKS_DIR, "transform.jq")

        with open(payload_path, 'r') as f:
            result = subprocess.run(
                ["jq", "-f", transform_path],
                stdin=f,
                capture_output=True,
                text=True,
                cwd=WEBHOOKS_DIR
            )

        output = json.loads(result.stdout)
        assert isinstance(output, dict), "Transform output should be a JSON object"
        assert "id" in output, "Transform output should contain 'id' field"
        assert output["id"] == 4521, (
            f"Transform output 'id' should be 4521 (the user_id), but got {output['id']}"
        )


class TestTransformExtractsCorrectUserIds:
    """Verify transform extracts different user_ids from different payloads (anti-hardcoding check)."""

    def test_different_payloads_produce_different_ids(self):
        """Each test payload should produce a different id in the transform output."""
        transform_path = os.path.join(WEBHOOKS_DIR, "transform.jq")
        ids = []

        for filename in ["event_01.json", "event_02.json", "event_03.json"]:
            payload_path = os.path.join(TEST_PAYLOADS_DIR, filename)

            with open(payload_path, 'r') as f:
                result = subprocess.run(
                    ["jq", "-f", transform_path],
                    stdin=f,
                    capture_output=True,
                    text=True,
                    cwd=WEBHOOKS_DIR
                )

            assert result.returncode == 0, f"Transform failed for {filename}"
            output = json.loads(result.stdout)
            assert "id" in output, f"Transform output for {filename} should have 'id' field"
            ids.append(output["id"])

        # The ids should not all be the same (anti-hardcoding check)
        # At minimum, we expect event_01.json to have user_id 4521
        assert ids[0] == 4521, f"event_01.json should produce id=4521, got {ids[0]}"

        # Check that transform actually reads from input, not hardcoded
        # At least one other payload should have a different user_id
        unique_ids = set(ids)
        assert len(unique_ids) >= 2, (
            f"Transform appears to be hardcoded - all payloads produced the same id: {ids}. "
            "Transform must actually extract data from input."
        )


class TestSchemaStillValidates:
    """Verify the schema still performs actual validation (anti-shortcut check)."""

    def test_schema_is_valid_json(self):
        """Schema should still be valid JSON."""
        filepath = os.path.join(WEBHOOKS_DIR, "schema.json")
        with open(filepath, 'r') as f:
            try:
                schema = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"schema.json is not valid JSON: {e}")
        assert isinstance(schema, dict), "schema.json should be a JSON object"

    def test_schema_is_not_empty_or_trivial(self):
        """Schema should not be empty, just 'true', or just '{}'."""
        filepath = os.path.join(WEBHOOKS_DIR, "schema.json")
        with open(filepath, 'r') as f:
            schema = json.load(f)

        # Schema should not be trivially permissive
        assert schema != {}, "Schema cannot be empty object (must perform actual validation)"
        assert schema != True, "Schema cannot be just 'true' (must perform actual validation)"
        assert "properties" in schema or "type" in schema, (
            "Schema should have 'properties' or 'type' constraints"
        )

    def test_schema_requires_event_type(self):
        """Schema should still require event_type field."""
        filepath = os.path.join(WEBHOOKS_DIR, "schema.json")
        with open(filepath, 'r') as f:
            schema = json.load(f)

        schema_str = json.dumps(schema)
        assert "event_type" in schema_str, "Schema should still define event_type field"

    def test_schema_requires_timestamp(self):
        """Schema should still require timestamp field."""
        filepath = os.path.join(WEBHOOKS_DIR, "schema.json")
        with open(filepath, 'r') as f:
            schema = json.load(f)

        schema_str = json.dumps(schema)
        assert "timestamp" in schema_str, "Schema should still define timestamp field"

    def test_schema_requires_data(self):
        """Schema should still require data field."""
        filepath = os.path.join(WEBHOOKS_DIR, "schema.json")
        with open(filepath, 'r') as f:
            schema = json.load(f)

        schema_str = json.dumps(schema)
        assert "data" in schema_str, "Schema should still define data field"

    def test_invalid_payload_still_rejected(self):
        """An actually invalid payload should still be rejected by validation."""
        validate_script = os.path.join(WEBHOOKS_DIR, "validate.sh")

        # Create a temporary invalid payload
        import tempfile
        invalid_payload = {"wrong_field": "this is not a valid webhook payload"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_payload, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                [validate_script, temp_path],
                capture_output=True,
                text=True,
                cwd=WEBHOOKS_DIR
            )
            assert result.returncode != 0, (
                "Schema validation should reject payloads missing required fields. "
                "The schema must perform actual validation, not accept everything."
            )
        finally:
            os.unlink(temp_path)


class TestTestPayloadsUnchanged:
    """Verify test payloads are unchanged (invariant check)."""

    def test_event_01_has_expected_structure(self):
        """event_01.json should have the original structure."""
        filepath = os.path.join(TEST_PAYLOADS_DIR, "event_01.json")
        with open(filepath, 'r') as f:
            payload = json.load(f)

        assert payload.get("event_type") == "user.created", "event_01.json event_type should be 'user.created'"
        assert payload.get("timestamp") == "2024-01-15T10:30:00Z", "event_01.json timestamp should be unchanged"
        assert payload.get("data", {}).get("user_id") == 4521, "event_01.json user_id should be 4521"
        assert payload.get("data", {}).get("email") == "test@example.com", "event_01.json email should be unchanged"
        assert payload.get("data", {}).get("metadata", {}).get("source") == "api", "event_01.json metadata.source should be 'api'"
        assert payload.get("data", {}).get("metadata", {}).get("version") == "2.1", "event_01.json metadata.version should be '2.1'"

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_payload_still_has_z_suffix_timestamp(self, filename):
        """Test payloads should still have Z suffix on timestamp (they weren't modified)."""
        filepath = os.path.join(TEST_PAYLOADS_DIR, filename)
        with open(filepath, 'r') as f:
            payload = json.load(f)

        timestamp = payload.get("timestamp", "")
        assert timestamp.endswith("Z"), f"{filename} timestamp should still end with Z (payload should not be modified)"

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_payload_still_has_metadata_version(self, filename):
        """Test payloads should still have version in metadata (they weren't modified)."""
        filepath = os.path.join(TEST_PAYLOADS_DIR, filename)
        with open(filepath, 'r') as f:
            payload = json.load(f)

        metadata = payload.get("data", {}).get("metadata", {})
        assert "version" in metadata, f"{filename} should still have metadata.version (payload should not be modified)"


class TestFullPipelineIntegration:
    """Test the complete pipeline: validate then transform."""

    @pytest.mark.parametrize("filename", ["event_01.json", "event_02.json", "event_03.json"])
    def test_full_pipeline(self, filename):
        """Full pipeline should work: validate passes, then transform produces valid output."""
        payload_path = os.path.join(TEST_PAYLOADS_DIR, filename)
        validate_script = os.path.join(WEBHOOKS_DIR, "validate.sh")
        transform_path = os.path.join(WEBHOOKS_DIR, "transform.jq")

        # Step 1: Validate
        validate_result = subprocess.run(
            [validate_script, payload_path],
            capture_output=True,
            text=True,
            cwd=WEBHOOKS_DIR
        )
        assert validate_result.returncode == 0, (
            f"Pipeline step 1 failed: validation should pass for {filename}. "
            f"Exit code: {validate_result.returncode}, stderr: {validate_result.stderr}"
        )

        # Step 2: Transform
        with open(payload_path, 'r') as f:
            transform_result = subprocess.run(
                ["jq", "-f", transform_path],
                stdin=f,
                capture_output=True,
                text=True,
                cwd=WEBHOOKS_DIR
            )
        assert transform_result.returncode == 0, (
            f"Pipeline step 2 failed: transform should succeed for {filename}. "
            f"Exit code: {transform_result.returncode}, stderr: {transform_result.stderr}"
        )

        # Step 3: Verify output is valid JSON with expected structure
        try:
            output = json.loads(transform_result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Pipeline output for {filename} is not valid JSON: {e}")

        assert "id" in output, f"Pipeline output for {filename} should contain 'id' field"
        assert isinstance(output["id"], int), f"Pipeline output 'id' for {filename} should be an integer"
