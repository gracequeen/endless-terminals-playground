Service mesh headache — we've got three services in /home/user/mesh that are supposed to chain together: gateway (port 8080) → auth (port 8081) → backend (port 8082). Gateway accepts requests, forwards to auth for token validation, auth calls backend for the actual data, response bubbles back up. All three start fine with the launcher script and I can curl each one individually on their ports, but when I hit the gateway endpoint it times out after 30 seconds with a 504.

Weirdest part: I added debug logging and auth *does* receive the forwarded request from gateway, and backend *does* receive the request from auth. So traffic is flowing. But somewhere the response chain is breaking. Checked for firewall stuff, nothing. All three are just Flask apps, nothing fancy.

Been staring at this for two hours, feels like something obvious I'm missing. Need the full chain working — `curl localhost:8080/data` should return the JSON from backend.
