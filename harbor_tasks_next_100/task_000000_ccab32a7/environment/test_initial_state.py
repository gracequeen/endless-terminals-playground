# test_initial_state.py
"""
Tests to validate the initial state of the operating system / filesystem
BEFORE the student performs the CSV sorting task.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Validate the initial state before the task is performed."""

    def test_data_directory_exists(self):
        """Verify /home/user/data/ directory exists."""
        data_dir = "/home/user/data"
        assert os.path.isdir(data_dir), f"Directory {data_dir} does not exist"

    def test_data_directory_is_writable(self):
        """Verify /home/user/data/ directory is writable."""
        data_dir = "/home/user/data"
        assert os.access(data_dir, os.W_OK), f"Directory {data_dir} is not writable"

    def test_orders_csv_exists(self):
        """Verify /home/user/data/orders.csv file exists."""
        orders_file = "/home/user/data/orders.csv"
        assert os.path.isfile(orders_file), f"File {orders_file} does not exist"

    def test_orders_csv_is_readable(self):
        """Verify /home/user/data/orders.csv is readable."""
        orders_file = "/home/user/data/orders.csv"
        assert os.access(orders_file, os.R_OK), f"File {orders_file} is not readable"

    def test_orders_csv_line_count(self):
        """Verify orders.csv has 50,001 lines (1 header + 50,000 data rows)."""
        orders_file = "/home/user/data/orders.csv"
        result = subprocess.run(
            ["wc", "-l"],
            stdin=open(orders_file, "r"),
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip())
        assert line_count == 50001, (
            f"Expected 50001 lines in {orders_file}, but found {line_count}"
        )

    def test_orders_csv_header_row(self):
        """Verify the header row has the expected columns."""
        orders_file = "/home/user/data/orders.csv"
        expected_header = "order_id,customer_id,order_date,total_amount,status"

        with open(orders_file, "r", encoding="utf-8") as f:
            header = f.readline().rstrip("\n\r")

        assert header == expected_header, (
            f"Expected header: '{expected_header}', but found: '{header}'"
        )

    def test_orders_csv_has_five_columns(self):
        """Verify each row has exactly 5 columns."""
        orders_file = "/home/user/data/orders.csv"

        with open(orders_file, "r", encoding="utf-8") as f:
            # Check header
            header = f.readline().rstrip("\n\r")
            header_cols = len(header.split(","))
            assert header_cols == 5, f"Header has {header_cols} columns, expected 5"

            # Check first 100 data rows
            for i, line in enumerate(f):
                if i >= 100:
                    break
                cols = len(line.rstrip("\n\r").split(","))
                assert cols == 5, f"Row {i+2} has {cols} columns, expected 5"

    def test_total_amount_column_is_numeric(self):
        """Verify total_amount column contains numeric values."""
        orders_file = "/home/user/data/orders.csv"

        with open(orders_file, "r", encoding="utf-8") as f:
            # Skip header
            f.readline()

            # Check first 100 data rows
            for i, line in enumerate(f):
                if i >= 100:
                    break
                cols = line.rstrip("\n\r").split(",")
                total_amount = cols[3]  # 4th column (0-indexed: 3)
                try:
                    float(total_amount)
                except ValueError:
                    pytest.fail(
                        f"Row {i+2}: total_amount '{total_amount}' is not numeric"
                    )

    def test_orders_csv_utf8_encoding(self):
        """Verify orders.csv is UTF-8 encoded."""
        orders_file = "/home/user/data/orders.csv"

        try:
            with open(orders_file, "r", encoding="utf-8") as f:
                # Read entire file to verify UTF-8 encoding
                f.read()
        except UnicodeDecodeError as e:
            pytest.fail(f"File {orders_file} is not valid UTF-8: {e}")

    def test_orders_csv_unix_line_endings(self):
        """Verify orders.csv uses Unix line endings (LF, not CRLF)."""
        orders_file = "/home/user/data/orders.csv"

        with open(orders_file, "rb") as f:
            content = f.read(10000)  # Check first 10KB

        # Check for Windows line endings
        if b"\r\n" in content:
            pytest.fail(f"File {orders_file} contains Windows line endings (CRLF)")

    def test_coreutils_sort_available(self):
        """Verify 'sort' command is available."""
        result = subprocess.run(
            ["which", "sort"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "'sort' command is not available"

    def test_coreutils_head_available(self):
        """Verify 'head' command is available."""
        result = subprocess.run(
            ["which", "head"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "'head' command is not available"

    def test_coreutils_tail_available(self):
        """Verify 'tail' command is available."""
        result = subprocess.run(
            ["which", "tail"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "'tail' command is not available"

    def test_coreutils_awk_available(self):
        """Verify 'awk' command is available."""
        result = subprocess.run(
            ["which", "awk"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "'awk' command is not available"

    def test_coreutils_sed_available(self):
        """Verify 'sed' command is available."""
        result = subprocess.run(
            ["which", "sed"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "'sed' command is not available"

    def test_output_file_does_not_exist(self):
        """Verify the output file does not exist yet (clean state)."""
        output_file = "/home/user/data/orders_sorted.csv"
        assert not os.path.exists(output_file), (
            f"Output file {output_file} already exists - initial state should be clean"
        )
