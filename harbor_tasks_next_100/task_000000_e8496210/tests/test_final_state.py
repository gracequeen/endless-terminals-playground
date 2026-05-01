# test_final_state.py
"""
Tests to validate the final state after the student has generated an SSH keypair
for the data server (ed25519, no passphrase, saved to /home/user/.ssh/dataserver_key).
"""

import os
import stat
import subprocess
import pytest


class TestPrivateKeyExists:
    """Verify the private key file exists and has correct properties."""

    def test_private_key_exists(self):
        """The private key file must exist."""
        private_key = "/home/user/.ssh/dataserver_key"
        assert os.path.exists(private_key), f"Private key {private_key} does not exist"

    def test_private_key_is_file(self):
        """The private key must be a regular file."""
        private_key = "/home/user/.ssh/dataserver_key"
        assert os.path.isfile(private_key), f"{private_key} exists but is not a regular file"

    def test_private_key_permissions(self):
        """The private key must have permissions 600 or stricter."""
        private_key = "/home/user/.ssh/dataserver_key"
        st = os.stat(private_key)
        mode = stat.S_IMODE(st.st_mode)
        # 600 = 0o600, stricter would be 0o400 or 0o000
        # Check that group and other have no permissions, and owner has at most rw
        assert mode <= 0o600, f"Private key has permissions {oct(mode)}, expected 0o600 or stricter"
        # Also ensure no group/other permissions
        assert (mode & 0o077) == 0, f"Private key has group/other permissions {oct(mode)}, should have none"

    def test_private_key_is_openssh_format(self):
        """The private key must start with OpenSSH private key header."""
        private_key = "/home/user/.ssh/dataserver_key"
        with open(private_key, "r") as f:
            content = f.read()
        assert content.startswith("-----BEGIN OPENSSH PRIVATE KEY-----"), \
            "Private key does not start with '-----BEGIN OPENSSH PRIVATE KEY-----'"


class TestPublicKeyExists:
    """Verify the public key file exists and has correct properties."""

    def test_public_key_exists(self):
        """The public key file must exist."""
        public_key = "/home/user/.ssh/dataserver_key.pub"
        assert os.path.exists(public_key), f"Public key {public_key} does not exist"

    def test_public_key_is_file(self):
        """The public key must be a regular file."""
        public_key = "/home/user/.ssh/dataserver_key.pub"
        assert os.path.isfile(public_key), f"{public_key} exists but is not a regular file"

    def test_public_key_is_ed25519(self):
        """The public key must be of type ssh-ed25519."""
        public_key = "/home/user/.ssh/dataserver_key.pub"
        with open(public_key, "r") as f:
            content = f.read()
        assert content.startswith("ssh-ed25519 "), \
            f"Public key does not start with 'ssh-ed25519 '. Key type appears to be wrong. Content starts with: {content[:50]}"


class TestKeyIsEd25519:
    """Verify the key is actually ed25519 type (anti-shortcut guard)."""

    def test_public_key_contains_ed25519(self):
        """The public key file must contain ssh-ed25519."""
        public_key = "/home/user/.ssh/dataserver_key.pub"
        result = subprocess.run(
            ["grep", "-q", "ssh-ed25519", public_key],
            capture_output=True
        )
        assert result.returncode == 0, \
            "Public key does not contain 'ssh-ed25519'. The key must be ed25519 type, not rsa/ecdsa."


class TestNoPassphrase:
    """Verify the private key has no passphrase."""

    def test_private_key_no_passphrase(self):
        """The private key must have no passphrase (can be read with empty passphrase)."""
        private_key = "/home/user/.ssh/dataserver_key"
        result = subprocess.run(
            ["ssh-keygen", "-y", "-P", "", "-f", private_key],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Private key appears to have a passphrase or is invalid. ssh-keygen -y -P '' failed with: {result.stderr}"
        # The output should be the public key starting with ssh-ed25519
        assert "ssh-ed25519" in result.stdout, \
            f"ssh-keygen -y output does not contain 'ssh-ed25519'. Output: {result.stdout}"


class TestSSHDirectoryInvariants:
    """Verify the .ssh directory invariants are maintained."""

    def test_ssh_directory_permissions_unchanged(self):
        """The /home/user/.ssh directory must still have permissions 700."""
        ssh_dir = "/home/user/.ssh"
        st = os.stat(ssh_dir)
        mode = stat.S_IMODE(st.st_mode)
        assert mode == 0o700, f"{ssh_dir} has permissions {oct(mode)}, expected 0o700 (700)"

    def test_ssh_directory_only_contains_keypair(self):
        """The /home/user/.ssh directory must only contain the keypair files."""
        ssh_dir = "/home/user/.ssh"
        contents = set(os.listdir(ssh_dir))
        expected = {"dataserver_key", "dataserver_key.pub"}
        assert contents == expected, \
            f"{ssh_dir} contains unexpected files. Found: {contents}, expected only: {expected}"


class TestKeyPairMatches:
    """Verify that the public and private keys are a matching pair."""

    def test_keypair_matches(self):
        """The public key derived from private key must match the .pub file."""
        private_key = "/home/user/.ssh/dataserver_key"
        public_key = "/home/user/.ssh/dataserver_key.pub"

        # Get public key from private key
        result = subprocess.run(
            ["ssh-keygen", "-y", "-P", "", "-f", private_key],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to derive public key from private key: {result.stderr}"

        derived_pub = result.stdout.strip()

        # Read the stored public key
        with open(public_key, "r") as f:
            stored_pub = f.read().strip()

        # The key data should match (first two fields: type and base64 data)
        derived_parts = derived_pub.split()[:2]
        stored_parts = stored_pub.split()[:2]

        assert derived_parts == stored_parts, \
            "Public key file does not match the public key derived from the private key. Keys may not be a matching pair."
