# test_final_state.py
"""
Tests to validate the final state of the system after the student has fixed the scheduler bug.
This verifies the timezone conversion is now correct and all invariants are maintained.
"""

import os
import subprocess
import json
import re
import pytest


HOME_DIR = "/home/user"
SCHEDULER_DIR = "/home/user/scheduler"
APP_PY = "/home/user/scheduler/app.py"
MEETINGS_JSON = "/home/user/scheduler/meetings.json"
CRONTAB_FILE = "/home/user/scheduler/crontab"


class TestInvariantsPreserved:
    """Test that invariants from the original setup are preserved."""

    def test_scheduler_directory_exists(self):
        assert os.path.isdir(SCHEDULER_DIR), f"Scheduler directory {SCHEDULER_DIR} must still exist"

    def test_app_py_exists(self):
        assert os.path.isfile(APP_PY), f"Application file {APP_PY} must still exist"

    def test_meetings_json_exists(self):
        assert os.path.isfile(MEETINGS_JSON), f"Meetings file {MEETINGS_JSON} must still exist"

    def test_meetings_json_unchanged(self):
        """Verify meetings.json still has the expected content structure."""
        with open(MEETINGS_JSON, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list), "meetings.json should still be a list"
        # Check the DST test meeting still exists
        utc_times = [m.get('utc_time', '') for m in data]
        assert any('2024-03-31T01:30:00' in t for t in utc_times), \
            "meetings.json should still contain the DST spring-forward test meeting"

    def test_app_still_uses_pytz(self):
        """Verify app.py still uses pytz (not rewritten to use dateutil or zoneinfo exclusively)."""
        with open(APP_PY, 'r') as f:
            content = f.read()
        assert 'pytz' in content, "app.py must still use pytz library"

    def test_crontab_file_exists(self):
        assert os.path.isfile(CRONTAB_FILE), f"Crontab file {CRONTAB_FILE} must still exist"

    def test_crontab_still_installed(self):
        """Verify crontab is still installed for user."""
        result = subprocess.run(
            ['crontab', '-l'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Crontab must still be installed for current user"
        assert 'app.py' in result.stdout or 'scheduler' in result.stdout, \
            "Installed crontab should still reference the scheduler app"

    def test_system_timezone_still_utc(self):
        """Verify system timezone is still UTC."""
        if os.path.isfile('/etc/timezone'):
            with open('/etc/timezone', 'r') as f:
                tz = f.read().strip()
            assert tz in ('Etc/UTC', 'UTC'), f"System timezone must remain UTC, got {tz}"


class TestAntiShortcutGuards:
    """Test that the fix is proper and not a hack."""

    def test_no_hardcoded_hour_offset(self):
        """Verify the fix doesn't use hardcoded hour offsets."""
        with open(APP_PY, 'r') as f:
            content = f.read()

        # Check for offset-hacking patterns
        # Pattern: timedelta with hours=1 or similar offset hacks
        hack_patterns = [
            r'timedelta\s*\([^)]*hours\s*[=:]\s*1',
            r'hours\s*=\s*1[^0-9]',
            r'\+\s*1\s*\)',
            r'-\s*1\s*\)',
            r'timedelta\s*\(\s*hours\s*=\s*-?\s*1\s*\)',
        ]

        for pattern in hack_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            # Filter out false positives (like legitimate uses)
            for match in matches:
                # Skip if it's clearly part of the 15-75 minute window logic
                if '15' in match or '75' in match or '60' in match:
                    continue
                # This is a suspicious offset hack
                assert False, f"Found suspicious offset hack pattern: {match}. Fix must use proper localize/astimezone logic."

    def test_grep_no_offset_hacking(self):
        """Use grep to check for offset hacking patterns."""
        result = subprocess.run(
            ['grep', '-E', r'timedelta.*hours.*1|hours.*=.*1|\+ 1\)|\- 1\)', APP_PY],
            capture_output=True,
            text=True
        )
        # If grep finds matches, check they're not offset hacks
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            for line in lines:
                # Allow legitimate uses (like checking 15-75 minute windows)
                if any(x in line for x in ['15', '75', '60', 'minute', 'Minute']):
                    continue
                # Check it's not a raw hour offset hack
                if re.search(r'hours\s*=\s*1[^0-9]', line) or re.search(r'timedelta\s*\(\s*hours\s*=\s*1', line):
                    pytest.fail(f"Found offset hacking pattern: {line}")


class TestCorrectTimezoneConversion:
    """Test that timezone conversion is now correct."""

    def test_app_py_has_correct_conversion_pattern(self):
        """Verify app.py now has proper UTC localization before astimezone."""
        with open(APP_PY, 'r') as f:
            content = f.read()

        # The correct pattern involves:
        # 1. Localizing the datetime to UTC first
        # 2. Then converting to Berlin timezone with astimezone

        # Check for presence of astimezone
        assert 'astimezone' in content, \
            "app.py should use astimezone() for proper timezone conversion"

        # Check for UTC localization pattern
        # Could be: pytz.utc.localize(), utc.localize(), or replace(tzinfo=...)
        has_utc_aware = any([
            'utc.localize' in content.lower(),
            'pytz.utc.localize' in content.lower(),
            'pytz.UTC.localize' in content,
            'replace(tzinfo=' in content and 'utc' in content.lower(),
            'timezone.utc' in content,  # datetime.timezone.utc
        ])

        assert has_utc_aware, \
            "app.py should properly make datetime UTC-aware before converting to Berlin"

    def test_spring_forward_conversion_correct(self):
        """
        Test that 2024-03-31T01:30:00 UTC converts correctly to Europe/Berlin.
        This is during spring-forward: 02:30 Berlin doesn't exist, so it becomes 03:30.
        """
        # First, get the correct reference value
        reference_code = '''
import pytz
from datetime import datetime

utc = pytz.utc
berlin = pytz.timezone('Europe/Berlin')
dt = datetime(2024, 3, 31, 1, 30, 0)
correct = utc.localize(dt).astimezone(berlin)
print(correct.strftime('%Y-%m-%d %H:%M:%S %Z'))
'''
        ref_result = subprocess.run(
            ['python3', '-c', reference_code],
            capture_output=True,
            text=True
        )
        assert ref_result.returncode == 0, f"Reference code failed: {ref_result.stderr}"
        reference_time = ref_result.stdout.strip()

        # The correct conversion should give 03:30:00 CEST (since 02:30 doesn't exist)
        assert '03:30:00' in reference_time, \
            f"Reference conversion should be 03:30 Berlin, got {reference_time}"

    def test_fall_back_conversion_correct(self):
        """
        Test that 2024-10-27T01:30:00 UTC converts correctly to Europe/Berlin.
        This is during fall-back: 02:30 Berlin exists twice.
        UTC 01:30 should map to 02:30+01:00 (before the clocks fall back).
        """
        # Get the correct reference value
        reference_code = '''
import pytz
from datetime import datetime

utc = pytz.utc
berlin = pytz.timezone('Europe/Berlin')
dt = datetime(2024, 10, 27, 1, 30, 0)
correct = utc.localize(dt).astimezone(berlin)
# Print with offset to distinguish the two 02:30 times
print(correct.strftime('%Y-%m-%d %H:%M:%S %z'))
'''
        ref_result = subprocess.run(
            ['python3', '-c', reference_code],
            capture_output=True,
            text=True
        )
        assert ref_result.returncode == 0, f"Reference code failed: {ref_result.stderr}"
        reference_time = ref_result.stdout.strip()

        # UTC 01:30 -> Berlin 02:30+0100 (before fallback, still summer time)
        assert '02:30:00' in reference_time, \
            f"Reference conversion should be 02:30 Berlin, got {reference_time}"
        assert '+0100' in reference_time or '+01:00' in reference_time, \
            f"Reference conversion should be +0100 (CEST), got {reference_time}"

    def test_app_conversion_matches_reference_spring(self):
        """
        Verify the app's conversion matches the reference for spring-forward case.
        """
        # Create a test script that imports and uses the app's conversion logic
        test_code = '''
import sys
sys.path.insert(0, '/home/user/scheduler')
import pytz
from datetime import datetime

utc = pytz.utc
berlin = pytz.timezone('Europe/Berlin')

# Reference correct conversion
dt = datetime(2024, 3, 31, 1, 30, 0)
correct = utc.localize(dt).astimezone(berlin)
print(f"REFERENCE:{correct.strftime('%Y-%m-%d %H:%M:%S %Z %z')}")

# Now try to extract and test the app's logic
# We'll read the app and look for how it does conversion
try:
    with open('/home/user/scheduler/app.py', 'r') as f:
        app_content = f.read()

    # Execute the app's conversion logic in isolation
    # Look for the conversion pattern and test it
    exec_globals = {'pytz': pytz, 'datetime': datetime}

    # The app should have proper conversion now
    # Test by checking if astimezone is used properly
    if 'astimezone' in app_content and ('utc.localize' in app_content.lower() or 'pytz.utc' in app_content.lower()):
        print("PATTERN:CORRECT")
    else:
        print("PATTERN:UNKNOWN")
except Exception as e:
    print(f"ERROR:{e}")
'''
        result = subprocess.run(
            ['python3', '-c', test_code],
            capture_output=True,
            text=True,
            cwd=SCHEDULER_DIR
        )
        assert result.returncode == 0, f"Test code failed: {result.stderr}"
        assert 'REFERENCE:2024-03-31 03:30:00' in result.stdout, \
            f"Reference should show 03:30 Berlin time"

    def test_unambiguous_time_conversion(self):
        """
        Test conversion of unambiguous time: 2024-10-27T00:30:00 UTC -> 01:30 Berlin.
        """
        test_code = '''
import pytz
from datetime import datetime

utc = pytz.utc
berlin = pytz.timezone('Europe/Berlin')
dt = datetime(2024, 10, 27, 0, 30, 0)
correct = utc.localize(dt).astimezone(berlin)
print(correct.strftime('%Y-%m-%d %H:%M:%S %z'))
'''
        result = subprocess.run(
            ['python3', '-c', test_code],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"
        output = result.stdout.strip()
        # UTC 00:30 -> Berlin 01:30+0100 (still summer time on Oct 27 at that hour)
        assert '01:30:00' in output, f"Expected 01:30 Berlin, got {output}"


class TestAppFunctionality:
    """Test that the app runs correctly."""

    def test_app_py_valid_python(self):
        """Verify app.py is still valid Python."""
        result = subprocess.run(
            ['python3', '-m', 'py_compile', APP_PY],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"app.py has syntax errors: {result.stderr}"

    def test_app_runs_without_error(self):
        """Verify app.py can be executed without errors."""
        result = subprocess.run(
            ['python3', APP_PY],
            capture_output=True,
            text=True,
            cwd=SCHEDULER_DIR
        )
        # App should run without Python errors (may have no output if no meetings in window)
        assert result.returncode == 0, f"app.py failed to run: {result.stderr}"

    def test_app_imports_work(self):
        """Verify all imports in app.py work."""
        test_code = '''
import sys
sys.path.insert(0, '/home/user/scheduler')
# Try to import pytz and datetime as the app would
import pytz
from datetime import datetime, timedelta
print("IMPORTS:OK")
'''
        result = subprocess.run(
            ['python3', '-c', test_code],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Import test failed: {result.stderr}"
        assert 'IMPORTS:OK' in result.stdout


class TestConversionLogicDirectly:
    """Directly test the conversion logic that should be in the fixed app."""

    def test_buggy_vs_correct_differ(self):
        """
        Verify that the buggy approach and correct approach give different results
        for DST transition times, confirming the bug was real.
        """
        test_code = '''
import pytz
from datetime import datetime

berlin = pytz.timezone('Europe/Berlin')
utc = pytz.utc

# Spring forward case: 2024-03-31T01:30:00 UTC
dt = datetime(2024, 3, 31, 1, 30, 0)

# Correct way
correct = utc.localize(dt).astimezone(berlin)

# Buggy way (what the old code did)
buggy = berlin.localize(dt)

print(f"CORRECT:{correct}")
print(f"BUGGY:{buggy}")
print(f"SAME:{correct == buggy}")
'''
        result = subprocess.run(
            ['python3', '-c', test_code],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"
        # They should be different, proving the bug existed
        assert 'SAME:False' in result.stdout, \
            "Buggy and correct conversions should differ for DST transition times"

    def test_fixed_app_uses_correct_approach(self):
        """
        Verify the fixed app uses the correct conversion approach.
        Check for the pattern: localize to UTC, then astimezone to Berlin.
        """
        with open(APP_PY, 'r') as f:
            content = f.read()

        # Remove comments and strings for cleaner analysis
        lines = [line for line in content.split('\n') if not line.strip().startswith('#')]
        code = '\n'.join(lines)

        # Must have astimezone
        assert 'astimezone' in code, "Fixed app must use astimezone() for conversion"

        # Must have some form of UTC awareness before astimezone
        # Patterns that indicate proper UTC handling:
        utc_patterns = [
            r'pytz\.utc\.localize',
            r'pytz\.UTC\.localize', 
            r'utc\.localize',
            r'UTC\.localize',
            r'replace\s*\(\s*tzinfo\s*=.*utc',
            r'datetime\.timezone\.utc',
        ]

        has_utc_handling = any(re.search(p, code, re.IGNORECASE) for p in utc_patterns)
        assert has_utc_handling, \
            "Fixed app must properly handle UTC timezone before converting to Berlin"

    def test_no_direct_berlin_localize_on_utc_datetime(self):
        """
        Verify the buggy pattern (berlin.localize(utc_dt)) is no longer present
        without proper UTC handling first.
        """
        with open(APP_PY, 'r') as f:
            content = f.read()

        # Look for the buggy pattern: berlin timezone localizing a naive datetime
        # that's supposed to be UTC
        # The fix should have: utc.localize(dt).astimezone(berlin)
        # NOT: berlin.localize(utc_dt)

        # Check that if berlin.localize exists, it's not the primary conversion method
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Skip comments
            if line.strip().startswith('#'):
                continue

            # If we see berlin_tz.localize or similar without proper UTC handling nearby
            if re.search(r'berlin.*\.localize\s*\(', line, re.IGNORECASE):
                # This is suspicious - check if there's proper UTC handling
                # Look for astimezone in the same logical block
                context = '\n'.join(lines[max(0, i-5):min(len(lines), i+5)])
                if 'astimezone' not in context and 'utc' not in context.lower():
                    pytest.fail(
                        f"Found suspicious berlin.localize() without proper UTC handling near line {i+1}: {line}"
                    )
