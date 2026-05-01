# test_final_state.py
"""
Tests to validate the final state of the operating system / filesystem
AFTER the student has completed the CSV sorting task.
"""

import os
import subprocess
import pytest


class TestFinalState:
    """Validate the final state after the task is performed."""

    def test_output_file_exists(self):
        """Verify /home/user/data/orders_sorted.csv file exists."""
        output_file = "/home/user/data/orders_sorted.csv"
        assert os.path.isfile(output_file), (
            f"Output file {output_file} does not exist. "
            "The sorted CSV file was not created."
        )

    def test_output_file_is_readable(self):
        """Verify /home/user/data/orders_sorted.csv is readable."""
        output_file = "/home/user/data/orders_sorted.csv"
        assert os.access(output_file, os.R_OK), (
            f"Output file {output_file} is not readable"
        )

    def test_output_file_line_count(self):
        """Verify orders_sorted.csv has 50,001 lines (1 header + 50,000 data rows)."""
        output_file = "/home/user/data/orders_sorted.csv"

        with open(output_file, "r", encoding="utf-8") as f:
            line_count = sum(1 for _ in f)

        assert line_count == 50001, (
            f"Expected 50001 lines in {output_file}, but found {line_count}. "
            "Some rows may have been dropped or duplicated."
        )

    def test_header_row_preserved(self):
        """Verify the header row is exactly the same as the original."""
        original_file = "/home/user/data/orders.csv"
        output_file = "/home/user/data/orders_sorted.csv"
        expected_header = "order_id,customer_id,order_date,total_amount,status"

        with open(output_file, "r", encoding="utf-8") as f:
            output_header = f.readline().rstrip("\n\r")

        assert output_header == expected_header, (
            f"Header row mismatch. Expected: '{expected_header}', "
            f"but found: '{output_header}'. "
            "The header must be the first line of the sorted file."
        )

    def test_header_matches_original(self):
        """Verify the header row matches the original file's header."""
        original_file = "/home/user/data/orders.csv"
        output_file = "/home/user/data/orders_sorted.csv"

        with open(original_file, "r", encoding="utf-8") as f:
            original_header = f.readline().rstrip("\n\r")

        with open(output_file, "r", encoding="utf-8") as f:
            output_header = f.readline().rstrip("\n\r")

        assert output_header == original_header, (
            f"Header in sorted file does not match original. "
            f"Original: '{original_header}', Sorted: '{output_header}'"
        )

    def test_sort_order_descending_first_100_rows(self):
        """Verify rows 2-100 are sorted by total_amount in descending order."""
        output_file = "/home/user/data/orders_sorted.csv"

        with open(output_file, "r", encoding="utf-8") as f:
            # Skip header
            f.readline()

            previous_amount = None
            for i, line in enumerate(f):
                if i >= 99:  # Check first 99 data rows (rows 2-100)
                    break

                cols = line.rstrip("\n\r").split(",")
                try:
                    current_amount = float(cols[3])
                except (ValueError, IndexError) as e:
                    pytest.fail(
                        f"Row {i+2}: Unable to parse total_amount from '{cols}': {e}"
                    )

                if previous_amount is not None:
                    assert current_amount <= previous_amount, (
                        f"Sort order violation at row {i+2}: "
                        f"total_amount {current_amount} > previous {previous_amount}. "
                        "Rows must be sorted by total_amount in DESCENDING order."
                    )
                previous_amount = current_amount

    def test_sort_order_descending_sample_throughout(self):
        """Verify sort order is correct by sampling throughout the file."""
        output_file = "/home/user/data/orders_sorted.csv"

        amounts = []
        with open(output_file, "r", encoding="utf-8") as f:
            # Skip header
            f.readline()

            for i, line in enumerate(f):
                # Sample every 500th row to check sort order throughout
                if i % 500 == 0:
                    cols = line.rstrip("\n\r").split(",")
                    try:
                        amounts.append(float(cols[3]))
                    except (ValueError, IndexError):
                        pass

        # Verify sampled amounts are in descending order
        for i in range(1, len(amounts)):
            assert amounts[i] <= amounts[i-1], (
                f"Sort order violation in sampled data: "
                f"amount at sample {i} ({amounts[i]}) > previous ({amounts[i-1]}). "
                "The file is not properly sorted by total_amount descending."
            )

    def test_all_columns_preserved(self):
        """Verify all 5 columns are present in the output."""
        output_file = "/home/user/data/orders_sorted.csv"

        with open(output_file, "r", encoding="utf-8") as f:
            # Check header
            header = f.readline().rstrip("\n\r")
            header_cols = header.split(",")
            assert len(header_cols) == 5, (
                f"Header has {len(header_cols)} columns, expected 5. "
                f"Columns found: {header_cols}"
            )

            # Check first 50 data rows
            for i, line in enumerate(f):
                if i >= 50:
                    break
                cols = line.rstrip("\n\r").split(",")
                assert len(cols) == 5, (
                    f"Row {i+2} has {len(cols)} columns, expected 5. "
                    "No columns should be added, removed, or reordered."
                )

    def test_original_file_unchanged(self):
        """Verify the original orders.csv file is unchanged."""
        original_file = "/home/user/data/orders.csv"

        # Check file exists
        assert os.path.isfile(original_file), (
            f"Original file {original_file} no longer exists! "
            "The original file should be preserved."
        )

        # Check line count
        with open(original_file, "r", encoding="utf-8") as f:
            line_count = sum(1 for _ in f)

        assert line_count == 50001, (
            f"Original file {original_file} has {line_count} lines, expected 50001. "
            "The original file should not be modified."
        )

        # Check header
        with open(original_file, "r", encoding="utf-8") as f:
            header = f.readline().rstrip("\n\r")

        expected_header = "order_id,customer_id,order_date,total_amount,status"
        assert header == expected_header, (
            f"Original file header changed. Expected: '{expected_header}', "
            f"Found: '{header}'"
        )

    def test_data_integrity_no_rows_lost(self):
        """Verify no data rows were lost during sorting."""
        original_file = "/home/user/data/orders.csv"
        output_file = "/home/user/data/orders_sorted.csv"

        # Count data rows (excluding header) in both files
        with open(original_file, "r", encoding="utf-8") as f:
            original_count = sum(1 for _ in f) - 1  # Subtract header

        with open(output_file, "r", encoding="utf-8") as f:
            output_count = sum(1 for _ in f) - 1  # Subtract header

        assert output_count == original_count, (
            f"Data row count mismatch. Original: {original_count}, "
            f"Sorted: {output_count}. No rows should be dropped or duplicated."
        )

    def test_output_file_utf8_encoding(self):
        """Verify orders_sorted.csv is UTF-8 encoded."""
        output_file = "/home/user/data/orders_sorted.csv"

        try:
            with open(output_file, "r", encoding="utf-8") as f:
                # Read entire file to verify UTF-8 encoding
                f.read()
        except UnicodeDecodeError as e:
            pytest.fail(f"Output file {output_file} is not valid UTF-8: {e}")

    def test_first_data_row_has_highest_total_amount(self):
        """Verify the first data row has one of the highest total_amount values."""
        output_file = "/home/user/data/orders_sorted.csv"

        with open(output_file, "r", encoding="utf-8") as f:
            # Skip header
            f.readline()

            # Get first data row's total_amount
            first_line = f.readline().rstrip("\n\r")
            first_amount = float(first_line.split(",")[3])

            # Check that no subsequent row has a higher amount
            for i, line in enumerate(f):
                cols = line.rstrip("\n\r").split(",")
                try:
                    amount = float(cols[3])
                    assert amount <= first_amount, (
                        f"Row {i+3} has total_amount {amount} which is greater than "
                        f"first data row's amount {first_amount}. "
                        "The file is not sorted in descending order."
                    )
                except (ValueError, IndexError):
                    continue

    def test_last_data_row_has_lowest_total_amount(self):
        """Verify the last data row has one of the lowest total_amount values."""
        output_file = "/home/user/data/orders_sorted.csv"

        # Get the last line's total_amount
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_line = lines[-1].rstrip("\n\r")
            last_amount = float(last_line.split(",")[3])

            # Sample first 100 data rows and verify they're >= last amount
            for i, line in enumerate(lines[1:101]):  # Skip header, check first 100
                cols = line.rstrip("\n\r").split(",")
                try:
                    amount = float(cols[3])
                    assert amount >= last_amount, (
                        f"Row {i+2} has total_amount {amount} which is less than "
                        f"last row's amount {last_amount}. "
                        "The file is not sorted in descending order."
                    )
                except (ValueError, IndexError):
                    continue
