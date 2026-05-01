ETL job at /home/user/pipeline/ingest.py started failing this morning with some pandas error about datetime parsing — was working fine last week. We didn't change the script, just updated dependencies Friday for an unrelated fix. The source CSV at /home/user/data/events.csv hasn't changed either afaik.

Need it running again — should produce /home/user/output/daily_summary.parquet with the aggregated event counts by date. Pretty sure it's something dumb but I've been staring at it for an hour.
