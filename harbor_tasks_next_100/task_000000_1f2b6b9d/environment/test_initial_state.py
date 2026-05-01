# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student performs the task.
This verifies the environment matches the expected initial conditions for the 7z archive extraction task.
"""

import os
import subprocess
import pytest


class TestInitialDirectoryStructure:
    """Test that required directories exist."""

    def test_incoming_directory_exists(self):
        """The /home/user/incoming/ directory must exist."""
        assert os.path.isdir("/home/user/incoming"), \
            "Directory /home/user/incoming/ does not exist"

    def test_extracted_directory_exists(self):
        """The /home/user/extracted/ directory must exist."""
        assert os.path.isdir("/home/user/extracted"), \
            "Directory /home/user/extracted/ does not exist"

    def test_extracted_directory_is_empty(self):
        """The /home/user/extracted/ directory must be empty initially."""
        contents = os.listdir("/home/user/extracted")
        assert len(contents) == 0, \
            f"Directory /home/user/extracted/ should be empty but contains: {contents}"

    def test_logs_directory_exists(self):
        """The /home/user/logs/ directory must exist."""
        assert os.path.isdir("/home/user/logs"), \
            "Directory /home/user/logs/ does not exist"

    def test_api_directory_exists(self):
        """The /home/user/api/ directory must exist."""
        assert os.path.isdir("/home/user/api"), \
            "Directory /home/user/api/ does not exist"


class TestDeliveryFile:
    """Test the delivery_0422.bin file exists and is a valid 7z archive."""

    def test_delivery_file_exists(self):
        """The delivery file must exist."""
        assert os.path.isfile("/home/user/incoming/delivery_0422.bin"), \
            "File /home/user/incoming/delivery_0422.bin does not exist"

    def test_delivery_file_has_7z_signature(self):
        """The delivery file must have the 7z magic bytes signature."""
        with open("/home/user/incoming/delivery_0422.bin", "rb") as f:
            header = f.read(6)
        # 7z signature: 37 7A BC AF 27 1C
        expected_signature = bytes([0x37, 0x7A, 0xBC, 0xAF, 0x27, 0x1C])
        assert header == expected_signature, \
            f"File does not have 7z signature. Got: {header.hex()}, expected: {expected_signature.hex()}"

    def test_delivery_file_detected_as_7z(self):
        """The file command should detect this as a 7z archive."""
        result = subprocess.run(
            ["file", "--mime-type", "-b", "/home/user/incoming/delivery_0422.bin"],
            capture_output=True,
            text=True
        )
        mime_type = result.stdout.strip()
        assert "7z" in mime_type.lower() or "x-7z" in mime_type, \
            f"File not detected as 7z archive. Detected mime type: {mime_type}"


class TestLogFile:
    """Test the intake.log file exists with expected initial content."""

    def test_log_file_exists(self):
        """The intake.log file must exist."""
        assert os.path.isfile("/home/user/logs/intake.log"), \
            "File /home/user/logs/intake.log does not exist"

    def test_log_file_contains_unknown_format_entry(self):
        """The log file must contain the 'unknown format - skipped' entry."""
        with open("/home/user/logs/intake.log", "r") as f:
            content = f.read()
        assert "delivery_0422.bin" in content, \
            "Log file does not contain entry for delivery_0422.bin"
        assert "unknown format - skipped" in content, \
            "Log file does not contain 'unknown format - skipped' message"


class TestExtractHandlerScript:
    """Test the extract_handler.sh script exists and has expected structure."""

    def test_handler_script_exists(self):
        """The extract_handler.sh script must exist."""
        assert os.path.isfile("/home/user/api/extract_handler.sh"), \
            "File /home/user/api/extract_handler.sh does not exist"

    def test_handler_script_is_readable(self):
        """The extract_handler.sh script must be readable."""
        assert os.access("/home/user/api/extract_handler.sh", os.R_OK), \
            "File /home/user/api/extract_handler.sh is not readable"

    def test_handler_script_is_writable(self):
        """The extract_handler.sh script must be writable (so agent can modify it)."""
        assert os.access("/home/user/api/extract_handler.sh", os.W_OK), \
            "File /home/user/api/extract_handler.sh is not writable"

    def test_handler_script_uses_file_command(self):
        """The script should use 'file --mime-type' for detection."""
        with open("/home/user/api/extract_handler.sh", "r") as f:
            content = f.read()
        assert "file" in content and "mime" in content.lower(), \
            "Script does not appear to use 'file --mime-type' for format detection"

    def test_handler_script_handles_zip(self):
        """The script should have a case handler for zip files."""
        with open("/home/user/api/extract_handler.sh", "r") as f:
            content = f.read()
        assert "zip" in content.lower(), \
            "Script does not appear to handle zip format"

    def test_handler_script_handles_tar(self):
        """The script should have a case handler for tar files."""
        with open("/home/user/api/extract_handler.sh", "r") as f:
            content = f.read()
        assert "tar" in content.lower(), \
            "Script does not appear to handle tar format"

    def test_handler_script_does_not_handle_7z(self):
        """The script should NOT have a case handler for 7z files initially."""
        with open("/home/user/api/extract_handler.sh", "r") as f:
            content = f.read()
        # Check that there's no 7z handling - this is the problem the student needs to fix
        assert "7z" not in content and "p7zip" not in content, \
            "Script already appears to handle 7z format - initial state should NOT handle 7z"


class TestSystemTools:
    """Test that required and expected system tools are available."""

    def test_unzip_available(self):
        """unzip must be available."""
        result = subprocess.run(["which", "unzip"], capture_output=True)
        assert result.returncode == 0, \
            "unzip is not installed/available"

    def test_tar_available(self):
        """tar must be available."""
        result = subprocess.run(["which", "tar"], capture_output=True)
        assert result.returncode == 0, \
            "tar is not installed/available"

    def test_gzip_available(self):
        """gzip must be available."""
        result = subprocess.run(["which", "gzip"], capture_output=True)
        assert result.returncode == 0, \
            "gzip is not installed/available"

    def test_file_command_available(self):
        """file command must be available."""
        result = subprocess.run(["which", "file"], capture_output=True)
        assert result.returncode == 0, \
            "file command is not installed/available"

    def test_7z_not_installed(self):
        """7z/p7zip should NOT be installed initially."""
        result = subprocess.run(["which", "7z"], capture_output=True)
        assert result.returncode != 0, \
            "7z is already installed - initial state should NOT have 7z installed"

    def test_apt_available(self):
        """apt/apt-get must be available for package installation."""
        result = subprocess.run(["which", "apt-get"], capture_output=True)
        assert result.returncode == 0, \
            "apt-get is not available for package installation"


class TestWritePermissions:
    """Test that required paths are writable."""

    def test_extracted_directory_writable(self):
        """The /home/user/extracted/ directory must be writable."""
        assert os.access("/home/user/extracted", os.W_OK), \
            "Directory /home/user/extracted/ is not writable"

    def test_logs_directory_writable(self):
        """The /home/user/logs/ directory must be writable."""
        assert os.access("/home/user/logs", os.W_OK), \
            "Directory /home/user/logs/ is not writable"

    def test_api_directory_writable(self):
        """The /home/user/api/ directory must be writable."""
        assert os.access("/home/user/api", os.W_OK), \
            "Directory /home/user/api/ is not writable"

    def test_log_file_writable(self):
        """The intake.log file must be writable."""
        assert os.access("/home/user/logs/intake.log", os.W_OK), \
            "File /home/user/logs/intake.log is not writable"
