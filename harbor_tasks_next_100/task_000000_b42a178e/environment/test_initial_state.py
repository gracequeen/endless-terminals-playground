# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the Redis password rotation task.
"""

import os
import pytest


class TestInitialState:
    """Validate the initial state before password rotation."""

    DOCKER_COMPOSE_PATH = "/home/user/app/docker-compose.yml"
    OLD_PASSWORD = "hunter2"

    def test_app_directory_exists(self):
        """Verify /home/user/app directory exists."""
        app_dir = "/home/user/app"
        assert os.path.isdir(app_dir), (
            f"Directory {app_dir} does not exist. "
            "The app directory must exist before performing the task."
        )

    def test_docker_compose_file_exists(self):
        """Verify docker-compose.yml file exists."""
        assert os.path.isfile(self.DOCKER_COMPOSE_PATH), (
            f"File {self.DOCKER_COMPOSE_PATH} does not exist. "
            "The docker-compose.yml file must exist before performing the task."
        )

    def test_docker_compose_file_is_writable(self):
        """Verify docker-compose.yml file is writable."""
        assert os.access(self.DOCKER_COMPOSE_PATH, os.W_OK), (
            f"File {self.DOCKER_COMPOSE_PATH} is not writable. "
            "The file must be writable to update the password."
        )

    def test_docker_compose_file_is_readable(self):
        """Verify docker-compose.yml file is readable."""
        assert os.access(self.DOCKER_COMPOSE_PATH, os.R_OK), (
            f"File {self.DOCKER_COMPOSE_PATH} is not readable. "
            "The file must be readable to perform the task."
        )

    def test_old_password_exists_in_file(self):
        """Verify the old password 'hunter2' exists in the docker-compose.yml."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        assert self.OLD_PASSWORD in content, (
            f"The old password '{self.OLD_PASSWORD}' was not found in "
            f"{self.DOCKER_COMPOSE_PATH}. The file should contain the old "
            "password that needs to be rotated."
        )

    def test_old_password_appears_twice(self):
        """Verify the old password appears exactly twice (redis command and app env)."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        count = content.count(self.OLD_PASSWORD)
        assert count == 2, (
            f"Expected the old password '{self.OLD_PASSWORD}' to appear exactly "
            f"2 times in {self.DOCKER_COMPOSE_PATH}, but found {count} occurrences. "
            "The password should be in both the redis service command and app service environment."
        )

    def test_redis_service_requirepass_exists(self):
        """Verify the redis service has --requirepass in its command."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        assert "--requirepass" in content, (
            f"The '--requirepass' flag was not found in {self.DOCKER_COMPOSE_PATH}. "
            "The redis service should have a --requirepass argument in its command."
        )

    def test_redis_password_env_var_exists(self):
        """Verify the REDIS_PASSWORD environment variable exists in the file."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        assert "REDIS_PASSWORD=" in content, (
            f"The 'REDIS_PASSWORD=' environment variable was not found in "
            f"{self.DOCKER_COMPOSE_PATH}. The app service should have a "
            "REDIS_PASSWORD environment variable."
        )

    def test_file_contains_version(self):
        """Verify the docker-compose file has a version field."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        assert "version:" in content, (
            f"The 'version:' field was not found in {self.DOCKER_COMPOSE_PATH}. "
            "The file should be a valid docker-compose.yml with a version field."
        )

    def test_file_contains_services(self):
        """Verify the docker-compose file has a services section."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        assert "services:" in content, (
            f"The 'services:' section was not found in {self.DOCKER_COMPOSE_PATH}. "
            "The file should be a valid docker-compose.yml with a services section."
        )

    def test_redis_service_exists(self):
        """Verify the redis service is defined in the file."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        assert "redis:" in content, (
            f"The 'redis:' service was not found in {self.DOCKER_COMPOSE_PATH}. "
            "The file should contain a redis service definition."
        )

    def test_app_service_exists(self):
        """Verify the app service is defined in the file."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        assert "app:" in content, (
            f"The 'app:' service was not found in {self.DOCKER_COMPOSE_PATH}. "
            "The file should contain an app service definition."
        )

    def test_file_is_valid_yaml_structure(self):
        """Basic check that the file has proper YAML-like structure."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        # Check for basic expected content
        expected_elements = [
            "redis:7-alpine",
            "myapp:latest",
            "REDIS_HOST=redis",
            "REDIS_PORT=6379",
            "6379:6379",
            "depends_on:"
        ]

        for element in expected_elements:
            assert element in content, (
                f"Expected element '{element}' not found in {self.DOCKER_COMPOSE_PATH}. "
                "The file should contain the expected docker-compose structure."
            )
