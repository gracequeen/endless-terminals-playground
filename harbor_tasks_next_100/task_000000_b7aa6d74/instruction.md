Compliance audit script at /home/user/audit/collect.py is supposed to pull metrics from three internal services (auth, billing, inventory) running on localhost and produce a consolidated JSON report. The services are up and responding — I can curl them individually — but the script keeps timing out after about 30 seconds and the report comes out with all nulls for the service data.

Thing is, the timeouts are weird. Each service responds in under 100ms when I hit them manually, and the script's timeout is set to 5 seconds per service, so even worst case it should finish in 15 seconds not 30. And the logs just say "timeout" three times, nothing more specific.

Need this actually pulling real data from all three services into /home/user/audit/report.json. The report structure is fine, just needs the actual values instead of nulls.
