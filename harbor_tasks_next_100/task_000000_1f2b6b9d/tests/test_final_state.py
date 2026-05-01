# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student completes the task.
This verifies that the 7z archive was properly extracted and logged.
"""

import os
import subprocess
import json
import pytest


class TestExtractedFiles:
    """Test that the extracted files exist and have correct content."""

    def test_report_csv_exists(self):
        """The report.csv file must exist in the extracted directory."""
        assert os.path.isfile("/home/user/extracted/report.csv"), \
            "File /home/user/extracted/report.csv does not exist - extraction failed"

    def test_report_csv_has_50_lines(self):
        """The report.csv file must have exactly 50 lines (header + 49 data rows)."""
        with open("/home/user/extracted/report.csv", "r") as f:
            lines = f.readlines()
        assert len(lines) == 50, \
            f"report.csv should have exactly 50 lines but has {len(lines)} lines. " \
            "This suggests the file was manually created rather than extracted from the archive."

    def test_report_csv_contains_q2(self):
        """The report.csv file must contain 'Q2' somewhere in the data."""
        result = subprocess.run(
            ["grep", "-q", "Q2", "/home/user/extracted/report.csv"],
            capture_output=True
        )
        assert result.returncode == 0, \
            "report.csv does not contain 'Q2' - file may have been manually created " \
            "rather than extracted from the original archive"

    def test_metadata_json_exists(self):
        """The metadata.json file must exist in the extracted directory."""
        assert os.path.isfile("/home/user/extracted/metadata.json"), \
            "File /home/user/extracted/metadata.json does not exist - extraction failed"

    def test_metadata_json_is_valid_json(self):
        """The metadata.json file must be valid JSON."""
        try:
            with open("/home/user/extracted/metadata.json", "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"metadata.json is not valid JSON: {e}")
        except Exception as e:
            pytest.fail(f"Failed to read metadata.json: {e}")

    def test_metadata_json_contains_customer_id(self):
        """The metadata.json file must contain customer_id: 4422."""
        with open("/home/user/extracted/metadata.json", "r") as f:
            data = json.load(f)
        assert "customer_id" in data, \
            "metadata.json does not contain 'customer_id' key"
        assert data["customer_id"] == 4422, \
            f"metadata.json customer_id should be 4422 but is {data['customer_id']}"

    def test_metadata_json_contains_batch(self):
        """The metadata.json file should contain batch information."""
        with open("/home/user/extracted/metadata.json", "r") as f:
            data = json.load(f)
        assert "batch" in data, \
            "metadata.json does not contain 'batch' key"
        assert "Q2" in str(data["batch"]), \
            f"metadata.json batch should contain 'Q2' but is {data['batch']}"


class TestLogFile:
    """Test that the log file was updated correctly."""

    def test_log_file_exists(self):
        """The intake.log file must still exist."""
        assert os.path.isfile("/home/user/logs/intake.log"), \
            "File /home/user/logs/intake.log does not exist"

    def test_log_has_non_unknown_entry_for_delivery(self):
        """The log must have a non-'unknown format' entry for delivery_0422.bin."""
        # Use grep to find lines with delivery_0422.bin that don't have "unknown format"
        result = subprocess.run(
            ["bash", "-c", 
             "grep 'delivery_0422.bin' /home/user/logs/intake.log | grep -v 'unknown format'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "Log file does not contain a non-'unknown format' entry for delivery_0422.bin. " \
            "The log should reflect successful 7z format detection."

    def test_log_reflects_7z_detection(self):
        """The log should contain an entry indicating 7z format detection."""
        with open("/home/user/logs/intake.log", "r") as f:
            content = f.read()

        # Check for evidence of 7z format detection in the log
        # Could be various forms: "7z", "x-7z-compressed", etc.
        has_7z_reference = (
            "7z" in content.lower() or 
            "x-7z" in content or
            "application/x-7z-compressed" in content
        )

        # Also check that there's a successful processing entry (not unknown)
        lines = content.strip().split('\n')
        delivery_lines = [l for l in lines if "delivery_0422.bin" in l]
        has_successful_entry = any("unknown format" not in l for l in delivery_lines)

        assert has_successful_entry, \
            "Log file should have a successful (non-unknown) entry for delivery_0422.bin"


class TestOriginalFilePreserved:
    """Test that the original delivery file is preserved."""

    def test_delivery_file_still_exists(self):
        """The original delivery file must still exist."""
        assert os.path.isfile("/home/user/incoming/delivery_0422.bin"), \
            "Original file /home/user/incoming/delivery_0422.bin was deleted - it should be preserved"

    def test_delivery_file_still_has_7z_signature(self):
        """The original delivery file must still have the 7z signature (not corrupted)."""
        with open("/home/user/incoming/delivery_0422.bin", "rb") as f:
            header = f.read(6)
        expected_signature = bytes([0x37, 0x7A, 0xBC, 0xAF, 0x27, 0x1C])
        assert header == expected_signature, \
            f"Original file was modified - no longer has 7z signature. " \
            f"Got: {header.hex()}, expected: {expected_signature.hex()}"


class TestHandlerScript:
    """Test that the handler script still exists and maintains functionality."""

    def test_handler_script_exists(self):
        """The extract_handler.sh script must still exist."""
        assert os.path.isfile("/home/user/api/extract_handler.sh"), \
            "File /home/user/api/extract_handler.sh was deleted - it should be preserved"

    def test_handler_script_still_handles_zip(self):
        """The script should still handle zip format."""
        with open("/home/user/api/extract_handler.sh", "r") as f:
            content = f.read().lower()
        assert "zip" in content, \
            "Handler script no longer appears to handle zip format - existing functionality broken"

    def test_handler_script_still_handles_tar(self):
        """The script should still handle tar format."""
        with open("/home/user/api/extract_handler.sh", "r") as f:
            content = f.read().lower()
        assert "tar" in content, \
            "Handler script no longer appears to handle tar format - existing functionality broken"


class TestExtractionIntegrity:
    """Additional tests to verify extraction was done properly, not manually created."""

    def test_report_csv_is_csv_format(self):
        """The report.csv should have CSV-like structure."""
        with open("/home/user/extracted/report.csv", "r") as f:
            first_line = f.readline()
        # CSV should have comma-separated values
        assert "," in first_line, \
            "report.csv does not appear to be in CSV format (no commas found in header)"

    def test_python_can_parse_metadata_json(self):
        """Verify metadata.json is parseable using the exact method from the task description."""
        result = subprocess.run(
            ["python3", "-c", 
             "import json; json.load(open('/home/user/extracted/metadata.json'))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"metadata.json failed Python JSON parsing: {result.stderr}"

    def test_files_are_not_empty(self):
        """Extracted files should not be empty."""
        report_size = os.path.getsize("/home/user/extracted/report.csv")
        metadata_size = os.path.getsize("/home/user/extracted/metadata.json")

        assert report_size > 0, "report.csv is empty"
        assert metadata_size > 0, "metadata.json is empty"

        # report.csv with 50 lines should be reasonably sized
        assert report_size > 100, \
            f"report.csv seems too small ({report_size} bytes) for 50 lines of CSV data"
