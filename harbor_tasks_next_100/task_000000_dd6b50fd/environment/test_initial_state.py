# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student performs the task.
This verifies the auditgen compliance doc generator environment is set up correctly with the known bug.
"""

import os
import subprocess
import pytest
import yaml
import json


HOME = "/home/user"
AUDITGEN_DIR = os.path.join(HOME, "auditgen")
DATA_DIR = os.path.join(AUDITGEN_DIR, "data")
TEMPLATES_DIR = os.path.join(AUDITGEN_DIR, "templates")
OUTPUT_DIR = os.path.join(AUDITGEN_DIR, "output")


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_auditgen_directory_exists(self):
        assert os.path.isdir(AUDITGEN_DIR), f"Directory {AUDITGEN_DIR} does not exist"

    def test_data_directory_exists(self):
        assert os.path.isdir(DATA_DIR), f"Directory {DATA_DIR} does not exist"

    def test_templates_directory_exists(self):
        assert os.path.isdir(TEMPLATES_DIR), f"Directory {TEMPLATES_DIR} does not exist"

    def test_output_directory_exists(self):
        assert os.path.isdir(OUTPUT_DIR), f"Directory {OUTPUT_DIR} does not exist"


class TestRequiredFiles:
    """Test that required files exist."""

    def test_generate_py_exists(self):
        filepath = os.path.join(AUDITGEN_DIR, "generate.py")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_schema_yaml_exists(self):
        filepath = os.path.join(AUDITGEN_DIR, "schema.yaml")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_records_yaml_exists(self):
        filepath = os.path.join(DATA_DIR, "records.yaml")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_template_exists(self):
        filepath = os.path.join(TEMPLATES_DIR, "report.md.j2")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_markdownlint_config_exists(self):
        filepath = os.path.join(AUDITGEN_DIR, ".markdownlint.json")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"


class TestRecordsYaml:
    """Test the records.yaml file content."""

    def test_records_yaml_has_47_entries(self):
        """Verify records.yaml contains exactly 47 audit records."""
        filepath = os.path.join(DATA_DIR, "records.yaml")
        result = subprocess.run(
            ["grep", "-c", "record_id:", filepath],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip())
        assert count == 47, f"Expected 47 records in records.yaml, found {count}"

    def test_records_yaml_is_valid_yaml(self):
        """Verify records.yaml is valid YAML."""
        filepath = os.path.join(DATA_DIR, "records.yaml")
        with open(filepath, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, "records.yaml is empty or invalid"
                assert isinstance(data, list), "records.yaml should contain a list of records"
            except yaml.YAMLError as e:
                pytest.fail(f"records.yaml is not valid YAML: {e}")

    def test_record_31_has_action_type_typo(self):
        """Verify the bug: record 31 (0-indexed) has 'action_type' instead of 'action'."""
        filepath = os.path.join(DATA_DIR, "records.yaml")
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        assert len(data) > 31, f"records.yaml has fewer than 32 entries"
        record_31 = data[31]

        # The bug: record 31 has "action_type" instead of "action"
        has_action_type = "action_type" in record_31
        has_action = "action" in record_31

        assert has_action_type and not has_action, (
            f"Record 31 should have 'action_type' (typo) instead of 'action'. "
            f"Found: action_type={has_action_type}, action={has_action}"
        )


class TestSchemaYaml:
    """Test the schema.yaml file content."""

    def test_schema_yaml_is_valid_yaml(self):
        """Verify schema.yaml is valid YAML."""
        filepath = os.path.join(AUDITGEN_DIR, "schema.yaml")
        with open(filepath, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, "schema.yaml is empty or invalid"
            except yaml.YAMLError as e:
                pytest.fail(f"schema.yaml is not valid YAML: {e}")

    def test_schema_does_not_require_action(self):
        """Verify the bug: schema.yaml does NOT require 'action' field."""
        filepath = os.path.join(AUDITGEN_DIR, "schema.yaml")
        with open(filepath, 'r') as f:
            schema = yaml.safe_load(f)

        # Navigate to find the required array - could be at root or in items for array schema
        required_fields = []
        if "required" in schema:
            required_fields = schema["required"]
        elif "items" in schema and "required" in schema["items"]:
            required_fields = schema["items"]["required"]

        assert "action" not in required_fields, (
            f"Schema should NOT require 'action' field (this is the bug). "
            f"Required fields: {required_fields}"
        )

    def test_schema_has_action_in_properties(self):
        """Verify schema.yaml has 'action' listed in properties."""
        filepath = os.path.join(AUDITGEN_DIR, "schema.yaml")
        with open(filepath, 'r') as f:
            schema = yaml.safe_load(f)

        properties = {}
        if "properties" in schema:
            properties = schema["properties"]
        elif "items" in schema and "properties" in schema["items"]:
            properties = schema["items"]["properties"]

        assert "action" in properties, (
            f"Schema should have 'action' in properties. Found: {list(properties.keys())}"
        )


class TestTemplate:
    """Test the Jinja2 template file."""

    def test_template_uses_record_action(self):
        """Verify template uses {{ record.action }} syntax."""
        filepath = os.path.join(TEMPLATES_DIR, "report.md.j2")
        with open(filepath, 'r') as f:
            content = f.read()

        assert "record.action" in content, (
            "Template should reference record.action field"
        )


class TestMarkdownLintConfig:
    """Test the markdownlint configuration."""

    def test_markdownlint_config_is_valid_json(self):
        """Verify .markdownlint.json is valid JSON."""
        filepath = os.path.join(AUDITGEN_DIR, ".markdownlint.json")
        with open(filepath, 'r') as f:
            try:
                config = json.load(f)
                assert config is not None, ".markdownlint.json is empty"
            except json.JSONDecodeError as e:
                pytest.fail(f".markdownlint.json is not valid JSON: {e}")


class TestPythonEnvironment:
    """Test Python and required packages are installed."""

    def test_python3_available(self):
        """Verify Python 3 is available."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not available"
        assert "Python 3" in result.stdout, f"Expected Python 3, got: {result.stdout}"

    def test_pyyaml_installed(self):
        """Verify pyyaml is installed."""
        result = subprocess.run(
            ["python3", "-c", "import yaml"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"pyyaml is not installed: {result.stderr}"

    def test_jinja2_installed(self):
        """Verify jinja2 is installed."""
        result = subprocess.run(
            ["python3", "-c", "import jinja2"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"jinja2 is not installed: {result.stderr}"

    def test_jsonschema_installed(self):
        """Verify jsonschema is installed."""
        result = subprocess.run(
            ["python3", "-c", "import jsonschema"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"jsonschema is not installed: {result.stderr}"


class TestMarkdownLintCLI:
    """Test markdownlint-cli is installed."""

    def test_markdownlint_available(self):
        """Verify markdownlint command is available."""
        result = subprocess.run(
            ["which", "markdownlint"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "markdownlint-cli is not installed or not in PATH"


class TestGenerateScript:
    """Test the generate.py script structure."""

    def test_generate_py_is_readable(self):
        """Verify generate.py is readable and contains expected references."""
        filepath = os.path.join(AUDITGEN_DIR, "generate.py")
        with open(filepath, 'r') as f:
            content = f.read()

        # Should reference the data file
        assert "records.yaml" in content or "records" in content, (
            "generate.py should reference records.yaml or records"
        )

        # Should reference schema
        assert "schema" in content.lower(), (
            "generate.py should reference schema for validation"
        )


class TestOutputDirectoryState:
    """Test the output directory initial state."""

    def test_output_directory_is_empty_or_no_report(self):
        """Verify output directory exists (report may or may not exist initially)."""
        # The output directory should exist
        assert os.path.isdir(OUTPUT_DIR), f"Output directory {OUTPUT_DIR} does not exist"


class TestBugReproduction:
    """Test that the bug can be reproduced - generate.py runs but linter fails."""

    def test_generate_py_runs_successfully(self):
        """Verify generate.py executes without Python errors (exit 0)."""
        result = subprocess.run(
            ["python3", "generate.py"],
            cwd=AUDITGEN_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"generate.py should run successfully (exit 0). "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_output_file_created(self):
        """Verify output file is created after running generate.py."""
        # First run generate.py
        subprocess.run(
            ["python3", "generate.py"],
            cwd=AUDITGEN_DIR,
            capture_output=True,
            text=True
        )

        output_file = os.path.join(OUTPUT_DIR, "audit_report.md")
        assert os.path.isfile(output_file), (
            f"Output file {output_file} should be created after running generate.py"
        )

    def test_markdownlint_fails_on_output(self):
        """Verify markdownlint fails on the generated output (the bug symptom)."""
        # First run generate.py
        subprocess.run(
            ["python3", "generate.py"],
            cwd=AUDITGEN_DIR,
            capture_output=True,
            text=True
        )

        output_file = os.path.join(OUTPUT_DIR, "audit_report.md")

        # Now run markdownlint
        result = subprocess.run(
            ["markdownlint", output_file],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0, (
            "markdownlint should FAIL on the generated output (this is the bug). "
            "If it passes, the bug may have already been fixed."
        )
