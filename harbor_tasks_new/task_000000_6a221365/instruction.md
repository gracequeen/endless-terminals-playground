I'm a compliance analyst and I need to process our transaction audit logs to generate a clean audit trail for regulators. The raw logs are in /home/user/audit/raw_transactions.jsonl — each line is a JSON object representing a transaction event. However, the data is messy: some lines are malformed JSON, some have missing required fields, and some have invalid data types.

Here's what I need:

1. Parse /home/user/audit/raw_transactions.jsonl and process each transaction record. Valid records must have these required fields with correct types:
   - `transaction_id` (string, must match pattern `TXN-[0-9]{8}`)
   - `timestamp` (string, ISO 8601 format like `2024-01-15T14:30:00Z`)
   - `account_id` (string, non-empty)
   - `amount` (number, can be positive or negative)
   - `currency` (string, exactly 3 uppercase letters)
   - `status` (string, one of: "completed", "pending", "failed", "reversed")

2. For each valid transaction, compute a SHA-256 hash of the canonical form: `{transaction_id}|{timestamp}|{account_id}|{amount}|{currency}|{status}` (amount should be formatted to exactly 2 decimal places, like `100.00` or `-50.25`).

3. Write successfully processed transactions to /home/user/audit/clean_audit.jsonl — one JSON object per line, sorted by timestamp ascending. Each output record must have exactly these fields:
   - All original required fields
   - `integrity_hash` (the SHA-256 hex digest you computed)
   - `processed_at` (current UTC timestamp when you process it, ISO 8601 format)

4. Write all errors to /home/user/audit/error_log.jsonl — one JSON object per line, in the order encountered. Each error record must have:
   - `line_number` (integer, 1-indexed line from the input file)
   - `error_type` (string, one of: "malformed_json", "missing_field", "invalid_format", "invalid_value")
   - `error_detail` (string, brief description like "missing field: account_id" or "invalid currency format: usd")
   - `raw_content` (string, the original line from the input file, truncated to 200 characters max)

5. Generate a summary report at /home/user/audit/processing_summary.txt with exactly this format:
```
AUDIT PROCESSING SUMMARY
========================
Input file: /home/user/audit/raw_transactions.jsonl
Total lines processed: <N>
Valid transactions: <N>
Failed records: <N>
Success rate: <X.XX>%

Errors by type:
  malformed_json: <N>
  missing_field: <N>
  invalid_format: <N>
  invalid_value: <N>

Processing completed at: <ISO 8601 UTC timestamp>
```

The error counts in the summary must match the number of corresponding entries in error_log.jsonl. If an error type has zero occurrences, still include it with count 0.
