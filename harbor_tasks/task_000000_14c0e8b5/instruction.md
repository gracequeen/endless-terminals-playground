Security scan dumps a JSON config at /home/user/audit/firewall_rules.json and a CSV of active connections at /home/user/audit/connections.csv every hour. Need a script at /home/user/audit/check.py that cross-references them and flags any connection whose destination port isn't explicitly allowed by an inbound rule for that source CIDR.

Thing is, the JSON uses CIDR notation for sources (like "10.0.0.0/8") but the CSV has actual IPs. And some rules have port ranges ("1024-65535") while others are single ports. Output should be lines like "BLOCKED: 10.2.3.4:8443 not allowed from 10.0.0.0/8" for anything that doesn't match.

Ran a test earlier and it flagged literally everything — pretty sure my CIDR matching was off, maybe also how I was parsing the port ranges. The tricky bit is the rules can overlap (more specific CIDR should win if it exists, I think?) and there's a default-deny implicit at the end.
