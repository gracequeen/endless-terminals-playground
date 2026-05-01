Rotating creds for the batch processor and something's weird — updated the service account key in /home/user/batch/config/credentials.json (new key id is `sa-batch-7f2a`) but jobs are failing auth against the internal API. Logs at /home/user/batch/logs/runner.log just say "403 Forbidden" with a request id, nothing about which credential it's actually trying to use.

The processor itself is /home/user/batch/runner.py and it definitely reads from that credentials.json on startup — I watched it parse the file. But somewhere between config load and the actual API call something's going sideways. Old key (`sa-batch-4e1c`) was revoked at 14:00 UTC today so anything still trying to use it would fail.

Need the auth working again. The API endpoint at localhost:9100 is up and accepts the new key — tested with curl manually and it's fine.
