Running a user-audit scan at /home/user/audit — it's supposed to check our user database against a known-breached-credentials list and flag any accounts that need forced password resets. The scanner at scan.py keeps reporting zero compromised accounts, which would be great except I *know* there are matches — I manually spot-checked a few hashes from the breach dump against our user table and found at least one hit.

The breach list is at /home/user/audit/breach_hashes.txt, our user DB is the sqlite file at /home/user/audit/users.db (table `accounts`, columns `uid`, `email`, `password_hash`). Scanner should output matching uids to /home/user/audit/compromised_uids.txt, one per line.

Something's off in how it's comparing hashes but I can't figure out what — the formats look the same to me.
