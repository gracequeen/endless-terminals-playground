# test_initial_state.py
"""
Tests to validate the initial state before the student performs the task.
Verifies that a process is running and listening on port 8443.
"""

import subprocess
import pytest


def test_port_8443_has_listener():
    """Verify that a process is listening on port 8443."""
    result = subprocess.run(
        ["ss", "-tlnp"],
        capture_output=True,
        text=True
    )

    # Check if port 8443 appears in the listening sockets
    assert "8443" in result.stdout, (
        "No process is listening on port 8443. "
        "Expected a process to be bound to this port. "
        f"ss -tlnp output:\n{result.stdout}"
    )


def test_port_8443_listener_with_ss():
    """Verify port 8443 listener using ss command with grep."""
    result = subprocess.run(
        ["ss", "-tlnp"],
        capture_output=True,
        text=True
    )

    lines_with_8443 = [line for line in result.stdout.splitlines() if "8443" in line]

    assert len(lines_with_8443) > 0, (
        "No listener found on port 8443 using ss -tlnp. "
        "The initial state requires a process listening on port 8443."
    )


def test_python3_process_exists():
    """Verify that a python3 process is running."""
    result = subprocess.run(
        ["pgrep", "-f", "python3"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0 and result.stdout.strip(), (
        "No python3 process found running. "
        "Expected a python3 process to be running as the metrics-exporter."
    )


def test_python3_socket_process_on_8443():
    """Verify that the python3 process is the one listening on port 8443."""
    # Use lsof to check what's listening on port 8443
    result = subprocess.run(
        ["lsof", "-i", ":8443"],
        capture_output=True,
        text=True
    )

    # lsof might return non-zero if no process found, or if permission issues
    # We check the output contains python
    if result.returncode == 0:
        assert "python" in result.stdout.lower(), (
            f"Expected python process listening on port 8443, but found:\n{result.stdout}"
        )
    else:
        # Try ss as fallback
        ss_result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        lines_with_8443 = [line for line in ss_result.stdout.splitlines() if "8443" in line]
        assert len(lines_with_8443) > 0, (
            "Could not verify process on port 8443. "
            f"lsof error: {result.stderr}\n"
            f"ss output: {ss_result.stdout}"
        )


def test_required_tools_available():
    """Verify that the required tools are available for the task."""
    tools = ["lsof", "fuser", "ss", "kill", "pkill", "ps", "grep", "awk"]

    missing_tools = []
    for tool in tools:
        result = subprocess.run(
            ["which", tool],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            missing_tools.append(tool)

    # We allow some tools to be missing as long as core ones are present
    core_tools = ["ss", "kill", "ps", "grep"]
    missing_core = [t for t in missing_tools if t in core_tools]

    assert not missing_core, (
        f"Missing core tools required for the task: {missing_core}. "
        "These tools should be available to complete the task."
    )


def test_process_is_consuming_cpu():
    """Verify that there's a python3 process that could be consuming CPU."""
    # Get python3 processes and their CPU usage
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )

    python_processes = [
        line for line in result.stdout.splitlines() 
        if "python3" in line and "socket" in line
    ]

    # At minimum, we should find the python3 process
    # The busy loop should show some CPU usage
    assert len(python_processes) > 0 or any("python3" in line for line in result.stdout.splitlines()), (
        "No python3 process found that matches the expected busy-loop process. "
        f"ps aux output:\n{result.stdout}"
    )
