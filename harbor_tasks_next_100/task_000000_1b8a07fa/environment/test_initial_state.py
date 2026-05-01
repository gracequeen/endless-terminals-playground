# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs
the task of bumping the solver timeout in /home/user/pipeline/optim.cfg from 30 to 120.
"""

import os
import configparser
import pytest


class TestInitialState:
    """Tests to verify the initial state before the task is performed."""

    CONFIG_PATH = "/home/user/pipeline/optim.cfg"

    def test_config_file_exists(self):
        """Verify that the config file exists."""
        assert os.path.exists(self.CONFIG_PATH), \
            f"Config file {self.CONFIG_PATH} does not exist"

    def test_config_file_is_file(self):
        """Verify that the config path is a regular file."""
        assert os.path.isfile(self.CONFIG_PATH), \
            f"{self.CONFIG_PATH} exists but is not a regular file"

    def test_config_file_is_readable(self):
        """Verify that the config file is readable."""
        assert os.access(self.CONFIG_PATH, os.R_OK), \
            f"Config file {self.CONFIG_PATH} is not readable"

    def test_config_file_is_writable(self):
        """Verify that the config file is writable."""
        assert os.access(self.CONFIG_PATH, os.W_OK), \
            f"Config file {self.CONFIG_PATH} is not writable"

    def test_config_is_valid_ini(self):
        """Verify that the config file is valid INI format."""
        config = configparser.ConfigParser()
        try:
            config.read(self.CONFIG_PATH)
        except configparser.Error as e:
            pytest.fail(f"Config file {self.CONFIG_PATH} is not valid INI format: {e}")

    def test_general_section_exists(self):
        """Verify that [general] section exists."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert 'general' in config.sections(), \
            f"[general] section not found in {self.CONFIG_PATH}"

    def test_solver_section_exists(self):
        """Verify that [solver] section exists."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert 'solver' in config.sections(), \
            f"[solver] section not found in {self.CONFIG_PATH}"

    def test_cache_section_exists(self):
        """Verify that [cache] section exists."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert 'cache' in config.sections(), \
            f"[cache] section not found in {self.CONFIG_PATH}"

    def test_timeout_sec_exists_in_solver(self):
        """Verify that timeout_sec option exists in [solver] section."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('solver', 'timeout_sec'), \
            f"timeout_sec option not found in [solver] section of {self.CONFIG_PATH}"

    def test_timeout_sec_initial_value_is_30(self):
        """Verify that timeout_sec is initially set to 30."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        value = config.get('solver', 'timeout_sec')
        assert value == '30', \
            f"timeout_sec should be '30' initially, but found '{value}'"

    def test_general_section_has_log_level(self):
        """Verify that [general] section has log_level setting."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('general', 'log_level'), \
            "log_level option not found in [general] section"
        assert config.get('general', 'log_level') == 'info', \
            f"log_level should be 'info', found '{config.get('general', 'log_level')}'"

    def test_general_section_has_output_dir(self):
        """Verify that [general] section has output_dir setting."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('general', 'output_dir'), \
            "output_dir option not found in [general] section"
        assert config.get('general', 'output_dir') == '/tmp/optim_out', \
            f"output_dir should be '/tmp/optim_out', found '{config.get('general', 'output_dir')}'"

    def test_solver_section_has_algorithm(self):
        """Verify that [solver] section has algorithm setting."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('solver', 'algorithm'), \
            "algorithm option not found in [solver] section"
        assert config.get('solver', 'algorithm') == 'simplex', \
            f"algorithm should be 'simplex', found '{config.get('solver', 'algorithm')}'"

    def test_solver_section_has_max_iterations(self):
        """Verify that [solver] section has max_iterations setting."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('solver', 'max_iterations'), \
            "max_iterations option not found in [solver] section"
        assert config.get('solver', 'max_iterations') == '10000', \
            f"max_iterations should be '10000', found '{config.get('solver', 'max_iterations')}'"

    def test_cache_section_has_enabled(self):
        """Verify that [cache] section has enabled setting."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('cache', 'enabled'), \
            "enabled option not found in [cache] section"
        assert config.get('cache', 'enabled') == 'true', \
            f"cache enabled should be 'true', found '{config.get('cache', 'enabled')}'"

    def test_cache_section_has_path(self):
        """Verify that [cache] section has path setting."""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        assert config.has_option('cache', 'path'), \
            "path option not found in [cache] section"
        assert config.get('cache', 'path') == '/var/cache/optim', \
            f"cache path should be '/var/cache/optim', found '{config.get('cache', 'path')}'"

    def test_pipeline_directory_exists(self):
        """Verify that the pipeline directory exists."""
        pipeline_dir = "/home/user/pipeline"
        assert os.path.isdir(pipeline_dir), \
            f"Pipeline directory {pipeline_dir} does not exist"
