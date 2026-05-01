# test_final_state.py
"""
Tests to validate the final state after the student completes the task.
Verifies that no process is listening on port 8443 and the busy-loop python3 process is killed.
"""

import subprocess
import pytest


def test_no_listener_on_port_8443_ss():
    """Verify that no process is listening on port 8443 using ss command."""
    result = subprocess.run(
        ["ss", "-tlnp"],
        capture_output=True,
        text=True
    )

    lines_with_8443 = [line for line in result.stdout.splitlines() if "8443" in line]

    assert len(lines_with_8443) == 0, (
        f"Port 8443 still has a listener. The process should have been killed.\n"
        f"Lines containing 8443:\n" + "\n".join(lines_with_8443) + "\n"
        f"Full ss -tlnp output:\n{result.stdout}"
    )


def test_no_listener_on_port_8443_lsof():
    """Verify that no process is listening on port 8443 using lsof command."""
    result = subprocess.run(
        ["lsof", "-i", ":8443"],
        capture_output=True,
        text=True
    )

    # lsof returns non-zero when no matching processes found, which is expected
    # If it returns 0 with output, there's still something listening
    if result.returncode == 0 and result.stdout.strip():
        pytest.fail(
            f"lsof still shows a process on port 8443. The process should have been killed.\n"
            f"lsof -i :8443 output:\n{result.stdout}"
        )


def test_busy_loop_python_process_killed():
    """Verify that the specific busy-loop python3 socket process is no longer running."""
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )

    # Look for the specific pattern of the busy-loop process
    suspicious_processes = []
    for line in result.stdout.splitlines():
        # Check for python3 processes that involve socket and bind with 8443
        if "python3" in line and "socket" in line and "8443" in line:
            suspicious_processes.append(line)
        # Also check for the exec while True pattern
        elif "python3" in line and "while True" in line:
            suspicious_processes.append(line)

    assert len(suspicious_processes) == 0, (
        f"The busy-loop python3 process appears to still be running.\n"
        f"Suspicious processes found:\n" + "\n".join(suspicious_processes)
    )


def test_no_python_socket_8443_process():
    """Verify no python process is bound to port 8443 using multiple methods."""
    # Method 1: Check with ss
    ss_result = subprocess.run(
        ["ss", "-tlnp", "sport", "=", ":8443"],
        capture_output=True,
        text=True
    )

    # Filter for actual listener lines (not header)
    listener_lines = [
        line for line in ss_result.stdout.splitlines() 
        if "LISTEN" in line and "8443" in line
    ]

    assert len(listener_lines) == 0, (
        f"Still found listener on port 8443.\n"
        f"Listener lines: {listener_lines}"
    )


def test_port_8443_is_free():
    """Comprehensive check that port 8443 is completely free."""
    # Try multiple approaches to ensure port is free

    # Approach 1: ss with grep
    ss_result = subprocess.run(
        "ss -tlnp | grep 8443",
        shell=True,
        capture_output=True,
        text=True
    )

    # grep returns 1 when no match found, which is what we want
    if ss_result.returncode == 0 and ss_result.stdout.strip():
        pytest.fail(
            f"Port 8443 is not free. ss -tlnp | grep 8443 shows:\n{ss_result.stdout}"
        )

    # Approach 2: netstat if available
    netstat_result = subprocess.run(
        "netstat -tlnp 2>/dev/null | grep 8443",
        shell=True,
        capture_output=True,
        text=True
    )

    if netstat_result.returncode == 0 and netstat_result.stdout.strip():
        pytest.fail(
            f"Port 8443 is not free. netstat shows:\n{netstat_result.stdout}"
        )


def test_no_orphaned_agent_processes():
    """Verify no new processes started by the agent remain running after task completion."""
    # Check that no suspicious python busy-loop processes exist
    result = subprocess.run(
        ["pgrep", "-af", "python3.*socket.*8443"],
        capture_output=True,
        text=True
    )

    # pgrep returns 1 when no processes match, which is expected
    if result.returncode == 0 and result.stdout.strip():
        pytest.fail(
            f"Found orphaned python3 process that should have been killed:\n{result.stdout}"
        )
