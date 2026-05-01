# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the disk usage analysis task.
"""

import os
import pytest
import subprocess


# Expected locale directories
EXPECTED_LOCALES = [
    "en_US", "es_ES", "fr_FR", "de_DE", "ja_JP", 
    "zh_CN", "ko_KR", "pt_BR", "it_IT", "ru_RU", 
    "nl_NL", "pl_PL", "sv_SE", "ar_SA", "th_TH"
]

TRANSLATIONS_DIR = "/home/user/translations"
HOME_DIR = "/home/user"
OUTPUT_FILE = "/home/user/locale_sizes.txt"


class TestInitialState:
    """Test the initial state before the task is performed."""

    def test_home_directory_exists(self):
        """Verify /home/user exists."""
        assert os.path.isdir(HOME_DIR), f"Home directory {HOME_DIR} does not exist"

    def test_home_directory_writable(self):
        """Verify /home/user is writable."""
        assert os.access(HOME_DIR, os.W_OK), f"Home directory {HOME_DIR} is not writable"

    def test_translations_directory_exists(self):
        """Verify /home/user/translations exists."""
        assert os.path.isdir(TRANSLATIONS_DIR), f"Translations directory {TRANSLATIONS_DIR} does not exist"

    def test_all_locale_directories_exist(self):
        """Verify all 15 expected locale subdirectories exist."""
        missing_locales = []
        for locale in EXPECTED_LOCALES:
            locale_path = os.path.join(TRANSLATIONS_DIR, locale)
            if not os.path.isdir(locale_path):
                missing_locales.append(locale)

        assert not missing_locales, (
            f"Missing locale directories in {TRANSLATIONS_DIR}: {missing_locales}"
        )

    def test_exactly_15_locale_directories(self):
        """Verify there are exactly 15 subdirectories (the expected locales)."""
        subdirs = [
            d for d in os.listdir(TRANSLATIONS_DIR) 
            if os.path.isdir(os.path.join(TRANSLATIONS_DIR, d))
        ]
        assert len(subdirs) == 15, (
            f"Expected 15 locale subdirectories, found {len(subdirs)}: {subdirs}"
        )

    def test_locale_directories_have_content(self):
        """Verify each locale directory has some content (not empty)."""
        empty_locales = []
        for locale in EXPECTED_LOCALES:
            locale_path = os.path.join(TRANSLATIONS_DIR, locale)
            if os.path.isdir(locale_path):
                contents = os.listdir(locale_path)
                if not contents:
                    empty_locales.append(locale)

        assert not empty_locales, (
            f"Empty locale directories found: {empty_locales}"
        )

    def test_locale_directories_contain_translation_files(self):
        """Verify locale directories contain .po or .mo translation files."""
        locales_without_translations = []
        for locale in EXPECTED_LOCALES:
            locale_path = os.path.join(TRANSLATIONS_DIR, locale)
            if os.path.isdir(locale_path):
                has_translation_files = False
                for root, dirs, files in os.walk(locale_path):
                    for f in files:
                        if f.endswith('.po') or f.endswith('.mo'):
                            has_translation_files = True
                            break
                    if has_translation_files:
                        break
                if not has_translation_files:
                    locales_without_translations.append(locale)

        assert not locales_without_translations, (
            f"Locale directories without .po or .mo files: {locales_without_translations}"
        )

    def test_translations_total_size_approximately_2gb(self):
        """Verify total size of translations is approximately 2GB (within reasonable range)."""
        result = subprocess.run(
            ["du", "-sb", TRANSLATIONS_DIR],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to get size of {TRANSLATIONS_DIR}"

        size_bytes = int(result.stdout.split()[0])
        size_gb = size_bytes / (1024 ** 3)

        # Allow range of 1.5GB to 2.5GB
        assert 1.5 <= size_gb <= 2.5, (
            f"Total translations size is {size_gb:.2f}GB, expected approximately 2GB"
        )

    def test_output_file_does_not_exist(self):
        """Verify the output file does not exist initially."""
        assert not os.path.exists(OUTPUT_FILE), (
            f"Output file {OUTPUT_FILE} already exists - it should not exist before the task"
        )

    def test_du_command_available(self):
        """Verify du command is available."""
        result = subprocess.run(
            ["which", "du"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "du command is not available"

    def test_sort_command_available(self):
        """Verify sort command is available."""
        result = subprocess.run(
            ["which", "sort"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "sort command is not available"

    def test_large_locales_exist_and_are_large(self):
        """Verify zh_CN and ja_JP are among the largest directories."""
        large_locales = ["zh_CN", "ja_JP"]

        for locale in large_locales:
            locale_path = os.path.join(TRANSLATIONS_DIR, locale)
            result = subprocess.run(
                ["du", "-sb", locale_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Failed to get size of {locale_path}"

            size_bytes = int(result.stdout.split()[0])
            size_mb = size_bytes / (1024 ** 2)

            # These should be 300-400MB each
            assert size_mb >= 250, (
                f"{locale} directory is only {size_mb:.0f}MB, expected 300-400MB"
            )
