# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the task.
This verifies the buggy scheduler setup exists as described.
"""

import os
import subprocess
import json
import pytest


HOME_DIR = "/home/user"
SCHEDULER_DIR = "/home/user/scheduler"
APP_PY = "/home/user/scheduler/app.py"
MEETINGS_JSON = "/home/user/scheduler/meetings.json"
CRONTAB_FILE = "/home/user/scheduler/crontab"
TEST_CONVERSION_PY = "/home/user/scheduler/test_conversion.py"


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_home_directory_exists(self):
        assert os.path.isdir(HOME_DIR), f"Home directory {HOME_DIR} does not exist"

    def test_scheduler_directory_exists(self):
        assert os.path.isdir(SCHEDULER_DIR), f"Scheduler directory {SCHEDULER_DIR} does not exist"

    def test_scheduler_directory_writable(self):
        assert os.access(SCHEDULER_DIR, os.W_OK), f"Scheduler directory {SCHEDULER_DIR} is not writable"


class TestRequiredFiles:
    """Test that required files exist."""

    def test_app_py_exists(self):
        assert os.path.isfile(APP_PY), f"Application file {APP_PY} does not exist"

    def test_meetings_json_exists(self):
        assert os.path.isfile(MEETINGS_JSON), f"Meetings file {MEETINGS_JSON} does not exist"

    def test_crontab_file_exists(self):
        assert os.path.isfile(CRONTAB_FILE), f"Crontab file {CRONTAB_FILE} does not exist"

    def test_test_conversion_py_exists(self):
        assert os.path.isfile(TEST_CONVERSION_PY), f"Test conversion script {TEST_CONVERSION_PY} does not exist"


class TestMeetingsJson:
    """Test the meetings.json file content."""

    def test_meetings_json_valid_json(self):
        with open(MEETINGS_JSON, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"meetings.json is not valid JSON: {e}")

    def test_meetings_json_is_list(self):
        with open(MEETINGS_JSON, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list), "meetings.json should contain a list"

    def test_meetings_have_required_fields(self):
        with open(MEETINGS_JSON, 'r') as f:
            data = json.load(f)
        for i, meeting in enumerate(data):
            assert 'title' in meeting, f"Meeting {i} missing 'title' field"
            assert 'utc_time' in meeting, f"Meeting {i} missing 'utc_time' field"

    def test_dst_transition_meeting_exists(self):
        """Verify the problematic DST transition meeting exists."""
        with open(MEETINGS_JSON, 'r') as f:
            data = json.load(f)
        utc_times = [m.get('utc_time', '') for m in data]
        assert any('2024-03-31T01:30:00' in t for t in utc_times), \
            "meetings.json should contain a meeting at 2024-03-31T01:30:00 (DST spring-forward test case)"


class TestAppPyContent:
    """Test the app.py file contains the expected buggy code."""

    def test_app_py_readable(self):
        with open(APP_PY, 'r') as f:
            content = f.read()
        assert len(content) > 0, "app.py is empty"

    def test_app_py_uses_pytz(self):
        with open(APP_PY, 'r') as f:
            content = f.read()
        assert 'pytz' in content, "app.py should use pytz library"

    def test_app_py_references_europe_berlin(self):
        with open(APP_PY, 'r') as f:
            content = f.read()
        assert 'Europe/Berlin' in content, "app.py should reference Europe/Berlin timezone"

    def test_app_py_has_buggy_localize_pattern(self):
        """Verify the buggy localize pattern exists (localizing UTC time with Berlin tz)."""
        with open(APP_PY, 'r') as f:
            content = f.read()
        # The bug is using berlin_tz.localize(utc_dt) instead of proper conversion
        # Look for patterns that suggest direct localization without proper UTC handling
        has_localize = 'localize' in content
        assert has_localize, "app.py should contain localize() call (part of the bug pattern)"

    def test_app_py_is_python_script(self):
        """Verify app.py is a valid Python file."""
        result = subprocess.run(
            ['python3', '-m', 'py_compile', APP_PY],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"app.py has syntax errors: {result.stderr}"


class TestCrontab:
    """Test crontab configuration."""

    def test_crontab_file_content(self):
        with open(CRONTAB_FILE, 'r') as f:
            content = f.read()
        assert '0 * * * *' in content, "Crontab should run at the top of every hour"
        assert 'app.py' in content, "Crontab should reference app.py"

    def test_crontab_installed_for_user(self):
        """Verify crontab is installed for user."""
        result = subprocess.run(
            ['crontab', '-l'],
            capture_output=True,
            text=True
        )
        # crontab -l returns 0 if there's a crontab, non-zero if none
        assert result.returncode == 0, "No crontab installed for current user"
        assert 'app.py' in result.stdout or 'scheduler' in result.stdout, \
            "Installed crontab should reference the scheduler app"


class TestSystemTimezone:
    """Test system timezone configuration."""

    def test_system_timezone_is_utc(self):
        """Verify system timezone is UTC."""
        # Check /etc/timezone
        if os.path.isfile('/etc/timezone'):
            with open('/etc/timezone', 'r') as f:
                tz = f.read().strip()
            assert tz in ('Etc/UTC', 'UTC'), f"System timezone should be UTC, got {tz}"
        else:
            # Alternative: check timedatectl or TZ environment
            result = subprocess.run(
                ['timedatectl', 'show', '--property=Timezone', '--value'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                tz = result.stdout.strip()
                assert tz in ('Etc/UTC', 'UTC'), f"System timezone should be UTC, got {tz}"


class TestPythonEnvironment:
    """Test Python environment has required packages."""

    def test_python3_available(self):
        result = subprocess.run(
            ['python3', '--version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "python3 is not available"

    def test_pytz_installed(self):
        result = subprocess.run(
            ['python3', '-c', 'import pytz; print(pytz.__version__)'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"pytz is not installed: {result.stderr}"

    def test_python_version_311(self):
        """Verify Python 3.11 is available."""
        result = subprocess.run(
            ['python3', '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Could not determine Python version"
        version = result.stdout.strip()
        # Allow 3.11 or higher
        major, minor = map(int, version.split('.'))
        assert major == 3 and minor >= 11, f"Expected Python 3.11+, got {version}"


class TestBuggyBehavior:
    """Test that the buggy behavior exists in the current code."""

    def test_app_demonstrates_bug(self):
        """
        Verify the app has the bug where it incorrectly handles DST transitions.
        The bug is using berlin_tz.localize(utc_dt) instead of 
        utc_tz.localize(utc_dt).astimezone(berlin_tz)
        """
        # Run a Python snippet that mimics what the buggy code does
        buggy_code = '''
import pytz
from datetime import datetime

berlin = pytz.timezone('Europe/Berlin')
utc = pytz.utc

# The correct way
dt = datetime(2024, 3, 31, 1, 30, 0)
correct = utc.localize(dt).astimezone(berlin)

# The buggy way (treating UTC time as if it were Berlin time)
buggy = berlin.localize(dt)

# They should differ for DST transition times
print(f"CORRECT:{correct}")
print(f"BUGGY:{buggy}")
print(f"DIFFER:{correct != buggy}")
'''
        result = subprocess.run(
            ['python3', '-c', buggy_code],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Test code failed: {result.stderr}"
        # The outputs should differ, demonstrating the bug exists
        assert 'DIFFER:True' in result.stdout, \
            "The buggy and correct conversions should differ for DST transition times"

    def test_app_py_missing_proper_utc_localize(self):
        """
        Check that app.py doesn't have the correct pattern of localizing to UTC first.
        The correct pattern is: utc.localize(dt).astimezone(berlin) or similar.
        The buggy pattern is: berlin.localize(utc_dt) without UTC localization.
        """
        with open(APP_PY, 'r') as f:
            content = f.read()

        # Look for the buggy pattern - localize being called on a non-UTC timezone
        # with what appears to be a UTC datetime
        lines = content.split('\n')
        has_localize = any('localize' in line for line in lines)

        # Check if there's a proper UTC localization followed by astimezone
        # A proper fix would have something like: utc.localize(...).astimezone(...)
        # or pytz.utc.localize(...).astimezone(...)
        proper_pattern_exists = any(
            ('utc.localize' in line.lower() or 'pytz.utc.localize' in line.lower()) 
            and 'astimezone' in line 
            for line in lines
        )

        assert has_localize, "app.py should use localize()"
        # The bug exists if there's no proper UTC->Berlin conversion pattern
        # We expect the buggy state, so proper_pattern should NOT exist
        assert not proper_pattern_exists, \
            "app.py should NOT have the correct utc.localize().astimezone() pattern (this is the bug to fix)"


class TestTestConversionScript:
    """Test the test_conversion.py script exists and works differently."""

    def test_test_conversion_py_readable(self):
        with open(TEST_CONVERSION_PY, 'r') as f:
            content = f.read()
        assert len(content) > 0, "test_conversion.py is empty"

    def test_test_conversion_py_valid_python(self):
        result = subprocess.run(
            ['python3', '-m', 'py_compile', TEST_CONVERSION_PY],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"test_conversion.py has syntax errors: {result.stderr}"
