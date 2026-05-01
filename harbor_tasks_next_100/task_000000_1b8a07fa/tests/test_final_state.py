# test_final_state.py
"""
Tests to validate the final state of the system after the student has
bumped the solver timeout in /home/user/pipeline/optim.cfg from 30 to 120.
"""

import os
import configparser
import subprocess
import pytest


class TestFinalState:
    """Tests to verify the final state after the task is performed."""

    CONFIG_PATH = "/home/user/pipeline/optim.cfg"

    def test_config_file_exists(self):
        """Verify that the config file still exists."""
        assert os.path.exists(self.CONFIG_PATH), \
            f"Config file {self.CONFIG_PATH} does not exist"

    def test_config_file_is_file(self):
        """Verify that the config path is a regular file."""
        assert os.path.isfile(self.CONFIG_PATH), \
            f"{self.CONFIG_PATH} exists but is not a regular file"

    def test_config_is_valid_ini(self):
        """Verify that the config file is still valid INI format."""
        config = configparser.ConfigParser()
        try:
            config.read(self.CONFIG_PATH)
        except configparser.Error as e:
            pytest.fail(f"Config file {self.CONFIG_PATH} is not valid INI format: {e}")

    def test_timeout_sec_is_120(self):
        """Verify that timeout_sec is now set to 120."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('solver', 'timeout_sec'), \
            "timeout_sec option not found in [solver] section"
        value = config.get('solver', 'timeout_sec')
        assert value == '120', \
            f"timeout_sec should be '120', but found '{value}'"

    def test_timeout_sec_is_integer_120(self):
        """Verify that timeout_sec can be parsed as integer 120."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        value = config.getint('solver', 'timeout_sec')
        assert value == 120, \
            f"timeout_sec should be integer 120, but found {value}"

    def test_grep_exact_match_timeout_sec_120(self):
        """Anti-shortcut: grep must find exactly one line with timeout_sec = 120."""
        result = subprocess.run(
            ['grep', '-E', r'^timeout_sec\s*=\s*120$', self.CONFIG_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"grep did not find 'timeout_sec = 120' in {self.CONFIG_PATH}"
        lines = result.stdout.strip().split('\n')
        assert len(lines) == 1, \
            f"Expected exactly one line matching 'timeout_sec = 120', found {len(lines)}"

    def test_general_section_exists(self):
        """Verify that [general] section still exists."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert 'general' in config.sections(), \
            f"[general] section not found in {self.CONFIG_PATH}"

    def test_solver_section_exists(self):
        """Verify that [solver] section still exists."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert 'solver' in config.sections(), \
            f"[solver] section not found in {self.CONFIG_PATH}"

    def test_cache_section_exists(self):
        """Verify that [cache] section still exists."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert 'cache' in config.sections(), \
            f"[cache] section not found in {self.CONFIG_PATH}"

    def test_general_log_level_unchanged(self):
        """Verify that log_level in [general] is unchanged."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('general', 'log_level'), \
            "log_level option not found in [general] section"
        assert config.get('general', 'log_level') == 'info', \
            f"log_level should be 'info', found '{config.get('general', 'log_level')}'"

    def test_general_output_dir_unchanged(self):
        """Verify that output_dir in [general] is unchanged."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('general', 'output_dir'), \
            "output_dir option not found in [general] section"
        assert config.get('general', 'output_dir') == '/tmp/optim_out', \
            f"output_dir should be '/tmp/optim_out', found '{config.get('general', 'output_dir')}'"

    def test_solver_algorithm_unchanged(self):
        """Verify that algorithm in [solver] is unchanged."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('solver', 'algorithm'), \
            "algorithm option not found in [solver] section"
        assert config.get('solver', 'algorithm') == 'simplex', \
            f"algorithm should be 'simplex', found '{config.get('solver', 'algorithm')}'"

    def test_solver_max_iterations_unchanged(self):
        """Verify that max_iterations in [solver] is unchanged."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('solver', 'max_iterations'), \
            "max_iterations option not found in [solver] section"
        assert config.get('solver', 'max_iterations') == '10000', \
            f"max_iterations should be '10000', found '{config.get('solver', 'max_iterations')}'"

    def test_cache_enabled_unchanged(self):
        """Verify that enabled in [cache] is unchanged."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('cache', 'enabled'), \
            "enabled option not found in [cache] section"
        assert config.get('cache', 'enabled') == 'true', \
            f"cache enabled should be 'true', found '{config.get('cache', 'enabled')}'"

    def test_cache_path_unchanged(self):
        """Verify that path in [cache] is unchanged."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('cache', 'path'), \
            "path option not found in [cache] section"
        assert config.get('cache', 'path') == '/var/cache/optim', \
            f"cache path should be '/var/cache/optim', found '{config.get('cache', 'path')}'"

    def test_no_extra_sections_added(self):
        """Verify that no extra sections were added."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        expected_sections = {'general', 'solver', 'cache'}
        actual_sections = set(config.sections())
        assert actual_sections == expected_sections, \
            f"Expected sections {expected_sections}, found {actual_sections}"

    def test_no_extra_options_in_general(self):
        """Verify that no extra options were added to [general]."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        expected_options = {'log_level', 'output_dir'}
        actual_options = set(config.options('general'))
        assert actual_options == expected_options, \
            f"Expected options in [general]: {expected_options}, found {actual_options}"

    def test_no_extra_options_in_solver(self):
        """Verify that no extra options were added to [solver]."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        expected_options = {'algorithm', 'timeout_sec', 'max_iterations'}
        actual_options = set(config.options('solver'))
        assert actual_options == expected_options, \
            f"Expected options in [solver]: {expected_options}, found {actual_options}"

    def test_no_extra_options_in_cache(self):
        """Verify that no extra options were added to [cache]."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        expected_options = {'enabled', 'path'}
        actual_options = set(config.options('cache'))
        assert actual_options == expected_options, \
            f"Expected options in [cache]: {expected_options}, found {actual_options}"
