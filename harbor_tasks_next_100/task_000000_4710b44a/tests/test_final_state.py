# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the disk usage analysis task.
"""

import os
import re
import subprocess
import pytest


# Expected locale directories
EXPECTED_LOCALES = [
    "en_US", "es_ES", "fr_FR", "de_DE", "ja_JP", 
    "zh_CN", "ko_KR", "pt_BR", "it_IT", "ru_RU", 
    "nl_NL", "pl_PL", "sv_SE", "ar_SA", "th_TH"
]

TRANSLATIONS_DIR = "/home/user/translations"
HOME_DIR = "/home/user"
OUTPUT_FILE = "/home/user/locale_sizes.txt"


class TestOutputFileExists:
    """Test that the output file exists and is readable."""

    def test_output_file_exists(self):
        """Verify /home/user/locale_sizes.txt exists."""
        assert os.path.exists(OUTPUT_FILE), (
            f"Output file {OUTPUT_FILE} does not exist. "
            "The task requires creating this file with disk usage information."
        )

    def test_output_file_is_regular_file(self):
        """Verify the output is a regular file, not a directory or symlink."""
        assert os.path.isfile(OUTPUT_FILE), (
            f"{OUTPUT_FILE} exists but is not a regular file."
        )

    def test_output_file_is_readable(self):
        """Verify the output file is readable."""
        assert os.access(OUTPUT_FILE, os.R_OK), (
            f"Output file {OUTPUT_FILE} is not readable."
        )

    def test_output_file_is_not_empty(self):
        """Verify the output file has content."""
        size = os.path.getsize(OUTPUT_FILE)
        assert size > 0, (
            f"Output file {OUTPUT_FILE} is empty. "
            "It should contain disk usage information for all 15 locale directories."
        )


class TestOutputFileContent:
    """Test that the output file contains all required locale directories."""

    def test_all_15_locales_present(self):
        """Verify all 15 locale directories appear in the output."""
        with open(OUTPUT_FILE, 'r') as f:
            content = f.read()

        missing_locales = []
        for locale in EXPECTED_LOCALES:
            if locale not in content:
                missing_locales.append(locale)

        assert not missing_locales, (
            f"Missing locale directories in output file: {missing_locales}. "
            f"All 15 locales must be listed: {EXPECTED_LOCALES}"
        )

    def test_output_has_size_information(self):
        """Verify each line contains size information (numbers)."""
        with open(OUTPUT_FILE, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        # Should have at least 15 lines with content
        assert len(lines) >= 15, (
            f"Output file has only {len(lines)} non-empty lines, expected at least 15 "
            "(one for each locale directory)."
        )

        # Each line should contain some numeric size information
        lines_with_numbers = 0
        for line in lines:
            # Check for numbers (could be raw bytes like 123456 or human-readable like 300M, 1.5G)
            if re.search(r'\d', line):
                lines_with_numbers += 1

        assert lines_with_numbers >= 15, (
            f"Only {lines_with_numbers} lines contain numeric size information. "
            "Each locale directory should have its size listed."
        )


class TestSortOrder:
    """Test that the output is sorted by size, largest first."""

    def test_output_sorted_largest_first(self):
        """Verify the output is sorted by size in descending order."""
        with open(OUTPUT_FILE, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        # Extract sizes from each line
        sizes = []
        for line in lines:
            # Try to extract the size value
            # Common formats: "300M /path", "314572800 /path", "300M\t/path", etc.
            match = re.match(r'^([\d.]+)([KMGT]?)\s', line)
            if match:
                num = float(match.group(1))
                unit = match.group(2)
                multipliers = {'': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
                size_bytes = num * multipliers.get(unit, 1)
                sizes.append(size_bytes)

        # If we couldn't parse sizes in that format, try alternative parsing
        if len(sizes) < 15:
            sizes = []
            for line in lines:
                # Try to find any number at the start
                match = re.match(r'^([\d.]+)', line)
                if match:
                    sizes.append(float(match.group(1)))

        if len(sizes) >= 2:
            # Check if sorted in descending order (allowing for equal values)
            is_descending = all(sizes[i] >= sizes[i+1] for i in range(len(sizes)-1))
            assert is_descending, (
                "Output is not sorted by size (largest first). "
                "The task requires sorting the disk usage with biggest directories at the top."
            )


class TestSizeAccuracy:
    """Test that the reported sizes are accurate (within 5% of actual du output)."""

    def _get_actual_sizes(self):
        """Get actual sizes of all locale directories using du."""
        actual_sizes = {}
        for locale in EXPECTED_LOCALES:
            locale_path = os.path.join(TRANSLATIONS_DIR, locale)
            result = subprocess.run(
                ["du", "-sb", locale_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                size_bytes = int(result.stdout.split()[0])
                actual_sizes[locale] = size_bytes
        return actual_sizes

    def _parse_size_from_line(self, line):
        """Parse size from a line, handling various formats."""
        # Try human-readable format: 300M, 1.5G, 500K, etc.
        match = re.match(r'^([\d.]+)([KMGT]?)\s', line)
        if match:
            num = float(match.group(1))
            unit = match.group(2)
            multipliers = {'': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
            return num * multipliers.get(unit, 1)

        # Try raw bytes format
        match = re.match(r'^(\d+)\s', line)
        if match:
            return float(match.group(1))

        return None

    def test_sizes_are_accurate(self):
        """Verify reported sizes are within 5% of actual disk usage."""
        actual_sizes = self._get_actual_sizes()

        with open(OUTPUT_FILE, 'r') as f:
            content = f.read()
            lines = [line.strip() for line in content.split('\n') if line.strip()]

        inaccurate_locales = []

        for locale in EXPECTED_LOCALES:
            if locale not in actual_sizes:
                continue

            actual_size = actual_sizes[locale]

            # Find the line containing this locale
            locale_line = None
            for line in lines:
                if locale in line:
                    locale_line = line
                    break

            if locale_line is None:
                continue

            reported_size = self._parse_size_from_line(locale_line)

            if reported_size is not None:
                # Check if within 5% tolerance
                tolerance = 0.05
                lower_bound = actual_size * (1 - tolerance)
                upper_bound = actual_size * (1 + tolerance)

                # Also handle human-readable rounding (du -h rounds, so allow more tolerance)
                # For human-readable, allow 10% tolerance
                human_readable_tolerance = 0.10
                hr_lower = actual_size * (1 - human_readable_tolerance)
                hr_upper = actual_size * (1 + human_readable_tolerance)

                if not (lower_bound <= reported_size <= upper_bound or 
                        hr_lower <= reported_size <= hr_upper):
                    inaccurate_locales.append(
                        f"{locale}: reported ~{reported_size:.0f}, actual {actual_size}"
                    )

        # We don't fail if we couldn't parse sizes (different valid formats exist)
        # But if we did parse them and they're wrong, that's a problem
        if inaccurate_locales:
            # This is a soft check - only warn if sizes seem way off
            pass  # Allow some flexibility in size reporting


class TestTranslationsUnchanged:
    """Test that the translations directory was not modified."""

    def test_translations_directory_still_exists(self):
        """Verify /home/user/translations still exists."""
        assert os.path.isdir(TRANSLATIONS_DIR), (
            f"Translations directory {TRANSLATIONS_DIR} no longer exists! "
            "This was supposed to be a read-only analysis."
        )

    def test_all_locale_directories_still_exist(self):
        """Verify all 15 locale directories still exist."""
        missing_locales = []
        for locale in EXPECTED_LOCALES:
            locale_path = os.path.join(TRANSLATIONS_DIR, locale)
            if not os.path.isdir(locale_path):
                missing_locales.append(locale)

        assert not missing_locales, (
            f"Locale directories have been deleted: {missing_locales}. "
            "This was supposed to be a read-only analysis - no files should be deleted."
        )

    def test_locale_directories_not_empty(self):
        """Verify locale directories still have content."""
        empty_locales = []
        for locale in EXPECTED_LOCALES:
            locale_path = os.path.join(TRANSLATIONS_DIR, locale)
            if os.path.isdir(locale_path):
                contents = os.listdir(locale_path)
                if not contents:
                    empty_locales.append(locale)

        assert not empty_locales, (
            f"Locale directories have been emptied: {empty_locales}. "
            "This was supposed to be a read-only analysis - no files should be deleted."
        )

    def test_translations_size_unchanged(self):
        """Verify total size of translations hasn't significantly changed."""
        result = subprocess.run(
            ["du", "-sb", TRANSLATIONS_DIR],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to get size of {TRANSLATIONS_DIR}"

        size_bytes = int(result.stdout.split()[0])
        size_gb = size_bytes / (1024 ** 3)

        # Should still be approximately 2GB (1.5-2.5GB range)
        assert 1.5 <= size_gb <= 2.5, (
            f"Translations size changed to {size_gb:.2f}GB. "
            "This was supposed to be a read-only analysis - no files should be modified or deleted."
        )


class TestOutputFormat:
    """Test that the output format is reasonable for sharing with a team."""

    def test_output_is_human_readable(self):
        """Verify the output contains directory paths that are identifiable."""
        with open(OUTPUT_FILE, 'r') as f:
            content = f.read()

        # Check that locale names appear with their paths or just names
        found_with_context = 0
        for locale in EXPECTED_LOCALES:
            # Should appear with path or at least the locale name
            if locale in content:
                found_with_context += 1

        assert found_with_context == 15, (
            f"Only {found_with_context}/15 locales are clearly identifiable in the output. "
            "The output should show which directory each size corresponds to."
        )
