# test_final_state.py
"""
Tests to validate the final state after the student has fixed the load testing
latency report bugs. The p50 must be less than p99, percentiles must be computed
correctly, and the mock server must still be running.
"""

import os
import subprocess
import json
import re
import pytest


LOADTEST_DIR = "/home/user/loadtest"


class TestMockServerStillRunning:
    """Verify the mock server is still running after the fix."""

    def test_port_9222_is_listening(self):
        """Port 9222 should still be listening on 127.0.0.1."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        output = result.stdout
        listening = "127.0.0.1:9222" in output or "0.0.0.0:9222" in output or ":9222" in output

        assert listening, (
            "No process is listening on port 9222. "
            "The mock server must still be running on 127.0.0.1:9222 after the fix.\n"
            f"Current listening ports:\n{output}"
        )

    def test_mock_server_responds_to_http(self):
        """The mock server should still respond to HTTP GET requests."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--connect-timeout", "2", "http://127.0.0.1:9222/"],
            capture_output=True,
            text=True
        )
        http_code = result.stdout.strip()
        assert http_code == "200", (
            f"Mock server at 127.0.0.1:9222 returned HTTP {http_code}, expected 200. "
            "The mock server must still be running after the fix."
        )


class TestBenchmarkExecution:
    """Test that the benchmark runs successfully and produces correct output."""

    def _run_benchmark(self):
        """Helper to run the benchmark and return the result."""
        result = subprocess.run(
            ["./run_bench.sh"],
            cwd=LOADTEST_DIR,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout for 200 requests with ~100ms each
        )
        return result

    def _extract_percentile_from_output(self, output, label):
        """Extract a percentile value from the output given a label like 'p50' or 'p99'."""
        # Look for patterns like "p50: 123.45" or "p50 = 123.45" or "p50  123.45ms"
        patterns = [
            rf'{label}\s*[:=]?\s*(\d+\.?\d*)',
            rf'{label}\s+(\d+\.?\d*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None

    def test_benchmark_exits_successfully(self):
        """./run_bench.sh should exit with code 0."""
        result = self._run_benchmark()
        assert result.returncode == 0, (
            f"./run_bench.sh exited with code {result.returncode}, expected 0.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    def test_output_contains_p50_and_p99(self):
        """The output should contain both p50 and p99 labels."""
        result = self._run_benchmark()
        output = result.stdout.lower()

        assert "p50" in output, (
            "Output does not contain 'p50' label.\n"
            f"stdout:\n{result.stdout}"
        )
        assert "p99" in output, (
            "Output does not contain 'p99' label.\n"
            f"stdout:\n{result.stdout}"
        )

    def test_p50_less_than_p99_run1(self):
        """First run: p50 must be less than p99."""
        result = self._run_benchmark()
        assert result.returncode == 0, f"Benchmark failed: {result.stderr}"

        p50 = self._extract_percentile_from_output(result.stdout, "p50")
        p99 = self._extract_percentile_from_output(result.stdout, "p99")

        assert p50 is not None, (
            f"Could not extract p50 value from output.\nstdout:\n{result.stdout}"
        )
        assert p99 is not None, (
            f"Could not extract p99 value from output.\nstdout:\n{result.stdout}"
        )
        assert p50 < p99, (
            f"p50 ({p50}) must be less than p99 ({p99}). "
            "This is a fundamental property of percentiles.\n"
            f"stdout:\n{result.stdout}"
        )

    def test_p50_less_than_p99_run2(self):
        """Second run: p50 must be less than p99."""
        result = self._run_benchmark()
        assert result.returncode == 0, f"Benchmark failed: {result.stderr}"

        p50 = self._extract_percentile_from_output(result.stdout, "p50")
        p99 = self._extract_percentile_from_output(result.stdout, "p99")

        assert p50 is not None, (
            f"Could not extract p50 value from output.\nstdout:\n{result.stdout}"
        )
        assert p99 is not None, (
            f"Could not extract p99 value from output.\nstdout:\n{result.stdout}"
        )
        assert p50 < p99, (
            f"p50 ({p50}) must be less than p99 ({p99}). "
            "This is a fundamental property of percentiles.\n"
            f"stdout:\n{result.stdout}"
        )

    def test_p50_less_than_p99_run3(self):
        """Third run: p50 must be less than p99."""
        result = self._run_benchmark()
        assert result.returncode == 0, f"Benchmark failed: {result.stderr}"

        p50 = self._extract_percentile_from_output(result.stdout, "p50")
        p99 = self._extract_percentile_from_output(result.stdout, "p99")

        assert p50 is not None, (
            f"Could not extract p50 value from output.\nstdout:\n{result.stdout}"
        )
        assert p99 is not None, (
            f"Could not extract p99 value from output.\nstdout:\n{result.stdout}"
        )
        assert p50 < p99, (
            f"p50 ({p50}) must be less than p99 ({p99}). "
            "This is a fundamental property of percentiles.\n"
            f"stdout:\n{result.stdout}"
        )


class TestStatsJsonCorrectness:
    """Verify that stats.json contains correctly computed percentiles."""

    def _run_benchmark_and_get_stats(self):
        """Run benchmark and return the stats.json content."""
        result = subprocess.run(
            ["./run_bench.sh"],
            cwd=LOADTEST_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, f"Benchmark failed: {result.stderr}"

        stats_path = os.path.join(LOADTEST_DIR, "stats.json")
        assert os.path.isfile(stats_path), (
            f"stats.json not found at {stats_path} after running benchmark."
        )

        with open(stats_path, "r") as f:
            return json.load(f)

    def test_stats_json_has_percentiles(self):
        """stats.json should contain p50 and p99 keys."""
        stats = self._run_benchmark_and_get_stats()

        # Check for p50 and p99 keys (case-insensitive check)
        keys_lower = {k.lower(): k for k in stats.keys()}

        assert "p50" in keys_lower, (
            f"stats.json does not contain 'p50' key. Keys found: {list(stats.keys())}"
        )
        assert "p99" in keys_lower, (
            f"stats.json does not contain 'p99' key. Keys found: {list(stats.keys())}"
        )

    def test_stats_json_p50_in_valid_range(self):
        """p50 should be in the valid range (50-150ms based on server delay)."""
        stats = self._run_benchmark_and_get_stats()

        # Find p50 key (case-insensitive)
        p50_key = None
        for k in stats.keys():
            if k.lower() == "p50":
                p50_key = k
                break

        assert p50_key is not None, "p50 key not found in stats.json"

        p50_value = stats[p50_key]
        # Allow some tolerance for timing variations
        assert 40 <= p50_value <= 160, (
            f"p50 value ({p50_value}ms) is outside expected range [40, 160]ms. "
            "The mock server has 50-150ms delay, so p50 should be around 100ms."
        )

    def test_stats_json_p99_greater_than_p50(self):
        """p99 in stats.json must be >= p50."""
        stats = self._run_benchmark_and_get_stats()

        # Find keys (case-insensitive)
        p50_key = None
        p99_key = None
        for k in stats.keys():
            if k.lower() == "p50":
                p50_key = k
            elif k.lower() == "p99":
                p99_key = k

        assert p50_key is not None, "p50 key not found in stats.json"
        assert p99_key is not None, "p99 key not found in stats.json"

        p50_value = stats[p50_key]
        p99_value = stats[p99_key]

        assert p99_value >= p50_value, (
            f"In stats.json, p99 ({p99_value}) must be >= p50 ({p50_value}). "
            "This is mathematically required for percentiles."
        )


class TestStringSortingRemoved:
    """Verify that the string sorting bug has been fixed in aggregate.py."""

    def test_no_string_sorting_in_aggregate(self):
        """aggregate.py should not sort latencies as strings."""
        aggregate_path = os.path.join(LOADTEST_DIR, "aggregate.py")
        assert os.path.isfile(aggregate_path), f"{aggregate_path} does not exist"

        with open(aggregate_path, "r") as f:
            content = f.read()

        # Check for common string sorting patterns that would be bugs
        # Pattern 1: sort with key=str
        # Pattern 2: sorted(..., key=str)
        # Pattern 3: sorting without converting to float/int first

        bad_patterns = [
            r'sort\s*\([^)]*key\s*=\s*str',
            r'sorted\s*\([^)]*key\s*=\s*str',
        ]

        for pattern in bad_patterns:
            match = re.search(pattern, content)
            assert match is None, (
                f"Found potential string sorting bug in aggregate.py: {match.group(0)}\n"
                "Latencies must be sorted as numbers, not strings."
            )


class TestClientMakesRealRequests:
    """Verify that client.py still makes real HTTP requests."""

    def test_client_uses_http_library(self):
        """client.py should use an HTTP library to make requests."""
        client_path = os.path.join(LOADTEST_DIR, "client.py")
        assert os.path.isfile(client_path), f"{client_path} does not exist"

        with open(client_path, "r") as f:
            content = f.read()

        has_http = (
            "requests" in content or
            "urllib" in content or
            "http.client" in content or
            "httpx" in content
        )
        assert has_http, (
            "client.py does not appear to use an HTTP library. "
            "It must make real HTTP requests, not use fake/stubbed data."
        )

    def test_client_targets_localhost_9222(self):
        """client.py should target 127.0.0.1:9222 or localhost:9222."""
        client_path = os.path.join(LOADTEST_DIR, "client.py")
        with open(client_path, "r") as f:
            content = f.read()

        targets_correct_host = (
            "127.0.0.1:9222" in content or
            "localhost:9222" in content or
            "9222" in content
        )
        assert targets_correct_host, (
            "client.py does not appear to target port 9222. "
            "It must make requests to the mock server on 127.0.0.1:9222."
        )


class TestMinimumRequestCount:
    """Verify that the benchmark still performs at least 100 requests."""

    def test_raw_timings_has_sufficient_entries(self):
        """After a run, raw_timings.csv should have at least 100 entries."""
        # Run the benchmark first
        result = subprocess.run(
            ["./run_bench.sh"],
            cwd=LOADTEST_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, f"Benchmark failed: {result.stderr}"

        raw_timings_path = os.path.join(LOADTEST_DIR, "raw_timings.csv")
        assert os.path.isfile(raw_timings_path), (
            f"raw_timings.csv not found at {raw_timings_path}"
        )

        with open(raw_timings_path, "r") as f:
            lines = f.readlines()

        # Count non-empty, non-header lines
        data_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

        # If there's a header, subtract 1
        # Check if first line looks like a header
        if data_lines and not re.match(r'^\d', data_lines[0].strip()):
            data_lines = data_lines[1:]

        assert len(data_lines) >= 100, (
            f"raw_timings.csv has only {len(data_lines)} data entries. "
            "The benchmark must perform at least 100 requests per run."
        )


class TestReportOutputToStdout:
    """Verify that the report is printed to stdout, not redirected to a file."""

    def test_report_goes_to_stdout(self):
        """The benchmark output should contain the report on stdout."""
        result = subprocess.run(
            ["./run_bench.sh"],
            cwd=LOADTEST_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, f"Benchmark failed: {result.stderr}"

        # The stdout should contain p50 and p99 values
        stdout_lower = result.stdout.lower()
        assert "p50" in stdout_lower and "p99" in stdout_lower, (
            "Report output (containing p50 and p99) not found in stdout. "
            "The report must be printed to stdout, not redirected to a file.\n"
            f"stdout:\n{result.stdout}"
        )


class TestReportLabelsCorrect:
    """Verify that report.py prints the correct labels with correct values."""

    def test_report_labels_match_stats_json(self):
        """The p50 label in output should match p50 value in stats.json."""
        # Run benchmark
        result = subprocess.run(
            ["./run_bench.sh"],
            cwd=LOADTEST_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, f"Benchmark failed: {result.stderr}"

        # Read stats.json
        stats_path = os.path.join(LOADTEST_DIR, "stats.json")
        with open(stats_path, "r") as f:
            stats = json.load(f)

        # Get p50 and p99 from stats.json
        p50_json = None
        p99_json = None
        for k, v in stats.items():
            if k.lower() == "p50":
                p50_json = v
            elif k.lower() == "p99":
                p99_json = v

        assert p50_json is not None, "p50 not found in stats.json"
        assert p99_json is not None, "p99 not found in stats.json"

        # Extract values from stdout
        output = result.stdout

        # Find p50 value in output
        p50_match = re.search(r'p50\s*[:=]?\s*(\d+\.?\d*)', output, re.IGNORECASE)
        p99_match = re.search(r'p99\s*[:=]?\s*(\d+\.?\d*)', output, re.IGNORECASE)

        assert p50_match is not None, f"Could not find p50 in output:\n{output}"
        assert p99_match is not None, f"Could not find p99 in output:\n{output}"

        p50_output = float(p50_match.group(1))
        p99_output = float(p99_match.group(1))

        # The values should match (with some tolerance for rounding)
        assert abs(p50_output - p50_json) < 1.0, (
            f"p50 in output ({p50_output}) does not match p50 in stats.json ({p50_json}). "
            "The labels may still be swapped in report.py."
        )
        assert abs(p99_output - p99_json) < 1.0, (
            f"p99 in output ({p99_output}) does not match p99 in stats.json ({p99_json}). "
            "The labels may still be swapped in report.py."
        )
