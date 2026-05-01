# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the Redis password rotation task.
"""

import os
import yaml
import pytest


class TestFinalState:
    """Validate the final state after password rotation."""

    DOCKER_COMPOSE_PATH = "/home/user/app/docker-compose.yml"
    OLD_PASSWORD = "hunter2"
    NEW_PASSWORD = "Kj9$mP2x!vL4"

    def test_docker_compose_file_exists(self):
        """Verify docker-compose.yml file still exists."""
        assert os.path.isfile(self.DOCKER_COMPOSE_PATH), (
            f"File {self.DOCKER_COMPOSE_PATH} does not exist. "
            "The docker-compose.yml file must still exist after the task."
        )

    def test_old_password_not_in_file(self):
        """Verify the old password 'hunter2' is no longer in the file."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        assert self.OLD_PASSWORD not in content, (
            f"The old password '{self.OLD_PASSWORD}' was still found in "
            f"{self.DOCKER_COMPOSE_PATH}. All occurrences of the old password "
            "should be replaced with the new password."
        )

    def test_new_password_appears_twice(self):
        """Verify the new password appears exactly twice (redis command and app env)."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        count = content.count(self.NEW_PASSWORD)
        assert count == 2, (
            f"Expected the new password '{self.NEW_PASSWORD}' to appear exactly "
            f"2 times in {self.DOCKER_COMPOSE_PATH}, but found {count} occurrences. "
            "The password should be in both the redis service command and app service environment."
        )

    def test_redis_requirepass_has_new_password(self):
        """Verify the redis service command has --requirepass with the new password."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        expected_requirepass = f"--requirepass {self.NEW_PASSWORD}"
        assert expected_requirepass in content, (
            f"The redis service command should contain '{expected_requirepass}' "
            f"but it was not found in {self.DOCKER_COMPOSE_PATH}. "
            "Make sure the --requirepass argument uses the new password."
        )

    def test_redis_password_env_has_new_password(self):
        """Verify the REDIS_PASSWORD environment variable has the new password."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            content = f.read()

        expected_env = f"REDIS_PASSWORD={self.NEW_PASSWORD}"
        assert expected_env in content, (
            f"The app service environment should contain '{expected_env}' "
            f"but it was not found in {self.DOCKER_COMPOSE_PATH}. "
            "Make sure the REDIS_PASSWORD environment variable uses the new password."
        )

    def test_file_is_valid_yaml(self):
        """Verify the file is still valid YAML."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(
                    f"File {self.DOCKER_COMPOSE_PATH} is not valid YAML: {e}. "
                    "The file must remain valid YAML after the password rotation."
                )

        assert data is not None, (
            f"File {self.DOCKER_COMPOSE_PATH} parsed as empty YAML. "
            "The file should contain valid docker-compose content."
        )

    def test_version_preserved(self):
        """Verify the version field is preserved."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            data = yaml.safe_load(f)

        assert 'version' in data, (
            f"The 'version' field is missing from {self.DOCKER_COMPOSE_PATH}. "
            "The file structure should be preserved."
        )
        assert data['version'] == '3.8', (
            f"Expected version '3.8' but found '{data.get('version')}'. "
            "The version should remain unchanged."
        )

    def test_services_section_preserved(self):
        """Verify the services section exists."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            data = yaml.safe_load(f)

        assert 'services' in data, (
            f"The 'services' section is missing from {self.DOCKER_COMPOSE_PATH}. "
            "The file structure should be preserved."
        )

    def test_redis_service_preserved(self):
        """Verify the redis service configuration is preserved (except password)."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            data = yaml.safe_load(f)

        services = data.get('services', {})
        assert 'redis' in services, (
            f"The 'redis' service is missing from {self.DOCKER_COMPOSE_PATH}. "
            "The redis service should still exist."
        )

        redis = services['redis']
        assert redis.get('image') == 'redis:7-alpine', (
            f"Expected redis image 'redis:7-alpine' but found '{redis.get('image')}'. "
            "The redis image should remain unchanged."
        )
        assert redis.get('ports') == ['6379:6379'], (
            f"Expected redis ports ['6379:6379'] but found '{redis.get('ports')}'. "
            "The redis ports should remain unchanged."
        )

    def test_app_service_preserved(self):
        """Verify the app service configuration is preserved (except password)."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            data = yaml.safe_load(f)

        services = data.get('services', {})
        assert 'app' in services, (
            f"The 'app' service is missing from {self.DOCKER_COMPOSE_PATH}. "
            "The app service should still exist."
        )

        app = services['app']
        assert app.get('image') == 'myapp:latest', (
            f"Expected app image 'myapp:latest' but found '{app.get('image')}'. "
            "The app image should remain unchanged."
        )
        assert app.get('depends_on') == ['redis'], (
            f"Expected depends_on ['redis'] but found '{app.get('depends_on')}'. "
            "The depends_on should remain unchanged."
        )

    def test_app_environment_other_vars_preserved(self):
        """Verify other environment variables in app service are preserved."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            data = yaml.safe_load(f)

        app = data.get('services', {}).get('app', {})
        environment = app.get('environment', [])

        # Convert to a dict-like structure for easier checking
        env_dict = {}
        for item in environment:
            if '=' in item:
                key, value = item.split('=', 1)
                env_dict[key] = value

        assert env_dict.get('REDIS_HOST') == 'redis', (
            f"Expected REDIS_HOST=redis but found '{env_dict.get('REDIS_HOST')}'. "
            "The REDIS_HOST environment variable should remain unchanged."
        )
        assert env_dict.get('REDIS_PORT') == '6379', (
            f"Expected REDIS_PORT=6379 but found '{env_dict.get('REDIS_PORT')}'. "
            "The REDIS_PORT environment variable should remain unchanged."
        )

    def test_app_environment_has_new_password(self):
        """Verify the REDIS_PASSWORD env var in app service has new password."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            data = yaml.safe_load(f)

        app = data.get('services', {}).get('app', {})
        environment = app.get('environment', [])

        # Find REDIS_PASSWORD
        redis_password = None
        for item in environment:
            if item.startswith('REDIS_PASSWORD='):
                redis_password = item.split('=', 1)[1]
                break

        assert redis_password == self.NEW_PASSWORD, (
            f"Expected REDIS_PASSWORD={self.NEW_PASSWORD} but found "
            f"REDIS_PASSWORD={redis_password}. "
            "The REDIS_PASSWORD environment variable should have the new password."
        )

    def test_redis_command_has_new_password(self):
        """Verify the redis service command has the new password."""
        with open(self.DOCKER_COMPOSE_PATH, 'r') as f:
            data = yaml.safe_load(f)

        redis = data.get('services', {}).get('redis', {})
        command = redis.get('command', '')

        # Command could be a string or a list
        if isinstance(command, list):
            command = ' '.join(command)

        assert f"--requirepass {self.NEW_PASSWORD}" in command, (
            f"Expected redis command to contain '--requirepass {self.NEW_PASSWORD}' "
            f"but found command: '{command}'. "
            "The redis service command should use the new password."
        )
        assert self.OLD_PASSWORD not in command, (
            f"The old password '{self.OLD_PASSWORD}' was found in the redis command. "
            "The old password should be replaced with the new password."
        )
