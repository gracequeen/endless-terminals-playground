I'm a security engineer and I just finished rotating a bunch of service account credentials across our infrastructure. My manager wants me to document everything I did in a specific markdown format that our security wiki can ingest, and it needs to pass our team's markdown linter before I can submit it.

Here's the situation: I have a directory at /home/user/credential-rotation containing several log files from the rotation process:

- `aws-rotation.log` - contains entries about AWS IAM key rotations
- `db-rotation.log` - contains entries about database password rotations  
- `api-keys.log` - contains entries about third-party API key rotations

Each log file has entries in the format:
```
[TIMESTAMP] SERVICE_NAME | OLD_KEY_ID | NEW_KEY_ID | STATUS | ROTATED_BY
```

I need you to:

1. Parse all three log files and generate a consolidated markdown document at `/home/user/credential-rotation/ROTATION_REPORT.md`

2. The markdown document must follow this exact structure:

```markdown
# Credential Rotation Report

**Generated:** YYYY-MM-DD HH:MM:SS
**Total Credentials Rotated:** N

## Summary by Category

| Category | Count | Success | Failed |
|----------|-------|---------|--------|
| AWS IAM | X | Y | Z |
| Database | X | Y | Z |
| API Keys | X | Y | Z |

## Detailed Rotation Log

### AWS IAM Credentials

| Service | Old Key ID | New Key ID | Status | Rotated By |
|---------|------------|------------|--------|------------|
| ... | ... | ... | ... | ... |

### Database Credentials

| Service | Old Key ID | New Key ID | Status | Rotated By |
|---------|------------|------------|--------|------------|
| ... | ... | ... | ... | ... |

### API Keys

| Service | Old Key ID | New Key ID | Status | Rotated By |
|---------|------------|------------|--------|------------|
| ... | ... | ... | ... | ... |

## Failed Rotations

> **Action Required:** The following credentials failed rotation and need manual intervention.

- SERVICE_NAME (CATEGORY): REASON
...

## Sign-off

- [ ] All successful rotations verified
- [ ] Failed rotations escalated
- [ ] Old credentials scheduled for deletion
```

3. The tables must be sorted alphabetically by service name within each category.

4. The "Failed Rotations" section should only list entries where STATUS was "FAILED". If there are no failures, that section should instead contain: `> No failed rotations. All credentials rotated successfully.`

5. Install and run `markdownlint-cli` on the generated report. Fix any linting errors. The final document must pass `markdownlint /home/user/credential-rotation/ROTATION_REPORT.md` with exit code 0.

6. Create a lint results file at `/home/user/credential-rotation/lint-results.txt` containing the output of running markdownlint on your final document (should be empty or show no errors).

The timestamp in the "Generated" field should reflect when you actually generated the report. Use 24-hour time format.
