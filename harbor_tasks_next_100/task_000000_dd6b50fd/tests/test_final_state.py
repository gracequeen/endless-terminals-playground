# test_final_state.py
"""
Tests to validate the final state after the student has fixed the auditgen compliance doc generator.
The fix should address the data or schema issue so that:
1. python generate.py exits 0
2. output/audit_report.md exists
3. markdownlint passes on the output
4. All 47 records are present
5. The fix is proper (not a workaround like disabling linter rules or template hacks)
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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "audit_report.md")
SCHEMA_FILE = os.path.join(AUDITGEN_DIR, "schema.yaml")
RECORDS_FILE = os.path.join(DATA_DIR, "records.yaml")
TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "report.md.j2")
LINT_CONFIG_FILE = os.path.join(AUDITGEN_DIR, ".markdownlint.json")


class TestGenerateScriptExecution:
    """Test that generate.py runs successfully."""

    def test_generate_py_exits_zero(self):
        """Verify python generate.py exits with code 0."""
        result = subprocess.run(
            ["python3", "generate.py"],
            cwd=AUDITGEN_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"generate.py should exit with code 0. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}, stdout: {result.stdout}"
        )

    def test_output_file_exists(self):
        """Verify output/audit_report.md exists after running generate.py."""
        # Run generate.py first
        subprocess.run(
            ["python3", "generate.py"],
            cwd=AUDITGEN_DIR,
            capture_output=True,
            text=True
        )

        assert os.path.isfile(OUTPUT_FILE), (
            f"Output file {OUTPUT_FILE} should exist after running generate.py"
        )


class TestMarkdownLintPasses:
    """Test that markdownlint passes on the generated output."""

    def test_markdownlint_exits_zero(self):
        """Verify markdownlint output/audit_report.md exits with code 0."""
        # First ensure generate.py has run
        subprocess.run(
            ["python3", "generate.py"],
            cwd=AUDITGEN_DIR,
            capture_output=True,
            text=True
        )

        result = subprocess.run(
            ["markdownlint", OUTPUT_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"markdownlint should pass on {OUTPUT_FILE}. "
            f"Exit code: {result.returncode}, stdout: {result.stdout}, stderr: {result.stderr}"
        )


class TestAllRecordsPresent:
    """Test that all 47 records are still present and rendered."""

    def test_records_yaml_has_47_entries(self):
        """Verify records.yaml still contains exactly 47 audit records."""
        result = subprocess.run(
            ["grep", "-c", "record_id:", RECORDS_FILE],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip())
        assert count == 47, (
            f"Expected 47 records in records.yaml, found {count}. "
            "Records should not be deleted as a fix."
        )

    def test_output_contains_47_records(self):
        """Verify the output markdown contains all 47 records."""
        # Run generate.py first
        subprocess.run(
            ["python3", "generate.py"],
            cwd=AUDITGEN_DIR,
            capture_output=True,
            text=True
        )

        with open(OUTPUT_FILE, 'r') as f:
            content = f.read()

        # Load records to get their IDs
        with open(RECORDS_FILE, 'r') as f:
            records = yaml.safe_load(f)

        assert len(records) == 47, f"Expected 47 records in YAML, found {len(records)}"

        # Check that each record_id appears in the output
        missing_records = []
        for record in records:
            record_id = record.get('record_id', '')
            if str(record_id) not in content:
                missing_records.append(record_id)

        assert len(missing_records) == 0, (
            f"The following record IDs are missing from the output: {missing_records}"
        )


class TestProperFix:
    """Test that the fix is proper and not a workaround."""

    def test_record_31_has_action_field(self):
        """Verify record 31 now has a proper 'action' field (not 'action_type')."""
        with open(RECORDS_FILE, 'r') as f:
            records = yaml.safe_load(f)

        record_31 = records[31]
        has_action = "action" in record_31
        action_value = record_31.get("action", "")

        # Either the data was fixed (action field exists and is non-empty)
        # OR the schema now requires action (tested separately)
        assert has_action, (
            f"Record 31 should have an 'action' field. "
            f"Found keys: {list(record_31.keys())}"
        )
        assert action_value and str(action_value).strip(), (
            f"Record 31's 'action' field should be non-empty. "
            f"Found: '{action_value}'"
        )

    def test_schema_requires_action_or_data_fixed(self):
        """Verify either schema requires 'action' OR all records have 'action' field."""
        with open(SCHEMA_FILE, 'r') as f:
            schema = yaml.safe_load(f)

        # Find required fields in schema
        required_fields = []
        if "required" in schema:
            required_fields = schema["required"]
        elif "items" in schema and "required" in schema["items"]:
            required_fields = schema["items"]["required"]

        schema_requires_action = "action" in required_fields

        # Check all records have action field
        with open(RECORDS_FILE, 'r') as f:
            records = yaml.safe_load(f)

        all_have_action = all("action" in record for record in records)
        all_actions_non_empty = all(
            record.get("action", "").strip() if isinstance(record.get("action"), str) 
            else record.get("action") is not None
            for record in records
        )

        # At least one of these should be true for a proper fix
        assert schema_requires_action or (all_have_action and all_actions_non_empty), (
            f"Fix should either: "
            f"1) Add 'action' to schema required fields (currently: {required_fields}), OR "
            f"2) Ensure all records have non-empty 'action' field. "
            f"Schema requires action: {schema_requires_action}, "
            f"All records have action: {all_have_action}"
        )

    def test_template_unchanged(self):
        """Verify the template still uses {{ record.action }} without default filter workaround."""
        with open(TEMPLATE_FILE, 'r') as f:
            content = f.read()

        # Template should still reference record.action
        assert "record.action" in content, (
            "Template should still reference record.action"
        )

        # Check for anti-pattern: adding default('') or similar to hide missing fields
        # This would be a workaround, not a fix
        import re
        # Look for patterns like {{ record.action | default('') }} or {{ record.action | default("") }}
        default_pattern = re.compile(r'record\.action\s*\|\s*default\s*\(')

        assert not default_pattern.search(content), (
            "Template should not use default() filter on record.action as a workaround. "
            "The fix should be in the data or schema, not hiding missing fields."
        )

    def test_markdownlint_config_unchanged(self):
        """Verify .markdownlint.json rules are unchanged (MD032 not disabled)."""
        with open(LINT_CONFIG_FILE, 'r') as f:
            config = json.load(f)

        # MD032 should not be disabled
        md032_disabled = config.get("MD032") is False or config.get("blanks-around-lists") is False

        assert not md032_disabled, (
            "MD032/blanks-around-lists should not be disabled in .markdownlint.json. "
            "The fix should address the root cause, not disable the linter rule."
        )

    def test_no_action_type_in_records(self):
        """Verify 'action_type' typo has been corrected (should not exist in any record)."""
        with open(RECORDS_FILE, 'r') as f:
            records = yaml.safe_load(f)

        records_with_action_type = [
            i for i, record in enumerate(records) 
            if "action_type" in record
        ]

        assert len(records_with_action_type) == 0, (
            f"Found 'action_type' (typo) in records at indices: {records_with_action_type}. "
            "This should be renamed to 'action'."
        )


class TestGenerateScriptIntegrity:
    """Test that generate.py still validates against schema."""

    def test_generate_py_references_schema(self):
        """Verify generate.py still references schema for validation."""
        generate_path = os.path.join(AUDITGEN_DIR, "generate.py")
        with open(generate_path, 'r') as f:
            content = f.read()

        # Should still reference schema validation
        assert "schema" in content.lower(), (
            "generate.py should still reference schema for validation"
        )

        # Should still read from records.yaml
        assert "records" in content.lower(), (
            "generate.py should still read from records.yaml"
        )

    def test_generate_py_not_hardcoded(self):
        """Verify generate.py doesn't have hardcoded action values as a workaround."""
        generate_path = os.path.join(AUDITGEN_DIR, "generate.py")
        with open(generate_path, 'r') as f:
            content = f.read()

        # Check for suspicious patterns that might indicate hardcoding
        # This is a heuristic check
        import re

        # Look for patterns like record['action'] = 'something' or record["action"] = "something"
        hardcode_pattern = re.compile(r"record\s*\[\s*['\"]action['\"]\s*\]\s*=")

        # This is a soft check - we're looking for obvious hardcoding
        matches = hardcode_pattern.findall(content)

        # Allow if it's part of legitimate processing, but flag if it looks like a workaround
        # We'll check if there's assignment with a literal string
        literal_assignment = re.compile(r"record\s*\[\s*['\"]action['\"]\s*\]\s*=\s*['\"][^'\"]+['\"]")
        literal_matches = literal_assignment.findall(content)

        assert len(literal_matches) == 0, (
            f"generate.py appears to hardcode action values: {literal_matches}. "
            "The fix should be in the data or schema, not hardcoding values in the script."
        )


class TestOutputQuality:
    """Test the quality of the generated output."""

    def test_output_is_valid_markdown_table(self):
        """Verify the output contains a properly formatted markdown table."""
        # Run generate.py first
        subprocess.run(
            ["python3", "generate.py"],
            cwd=AUDITGEN_DIR,
            capture_output=True,
            text=True
        )

        with open(OUTPUT_FILE, 'r') as f:
            content = f.read()

        # Should contain table structure with pipes
        assert "|" in content, "Output should contain markdown table with pipe characters"

        # Should not have empty cells (double pipes with only whitespace)
        import re
        # Pattern for empty cells: | followed by only whitespace then |
        empty_cell_pattern = re.compile(r'\|\s*\|')

        # Find lines with table content (containing |)
        table_lines = [line for line in content.split('\n') if '|' in line and not line.strip().startswith('|---')]

        for line in table_lines:
            # Skip header separator lines
            if re.match(r'^[\s|:-]+$', line):
                continue
            # Check for empty cells (but allow header separator which has |---|)
            if empty_cell_pattern.search(line) and '---' not in line:
                # This might be a false positive, let's be more careful
                # Split by | and check for empty segments
                parts = line.split('|')
                empty_parts = [p for p in parts[1:-1] if not p.strip()]  # Exclude first/last empty from split
                assert len(empty_parts) == 0, (
                    f"Found empty table cell in line: '{line}'. "
                    "All action fields should be populated."
                )

    def test_output_ends_with_newline(self):
        """Verify output file ends with a newline (MD047 compliance)."""
        # Run generate.py first
        subprocess.run(
            ["python3", "generate.py"],
            cwd=AUDITGEN_DIR,
            capture_output=True,
            text=True
        )

        with open(OUTPUT_FILE, 'r') as f:
            content = f.read()

        assert content.endswith('\n'), (
            "Output file should end with a newline (MD047 compliance)"
        )
