Load testing our internal API and getting bizarre latency numbers — p99 is fine but p50 is somehow *worse* than p99 in the report, which makes no sense statistically. The test harness is at /home/user/loadtest and `./run_bench.sh` does a batch of requests against the mock server, then spits out a latency report to stdout. Mock server's already running on 127.0.0.1:9222.

Something's off in either the measurement, the aggregation, or the reporting — not sure which. Need the p50 and p99 to actually reflect reality so I can trust the numbers before we present to infra team tomorrow.
