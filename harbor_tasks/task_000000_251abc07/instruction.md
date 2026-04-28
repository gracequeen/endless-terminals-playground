Need to filter /var/log/app/access.log down to only requests that hit our internal API endpoints — anything matching `/api/v[0-9]+/internal/` — and dump those lines to /home/user/internal_hits.log. But here's the thing: we're also seeing a ton of health check spam from the load balancer that I want excluded, those come from 10.0.0.0/8 range and hit `/health` or `/ready`. So internal API calls yes, but not if they're from the 10.x.x.x health probes.

Also the timestamps in that log are in that annoying Apache combined format with the brackets, would be nice if the output had them as ISO 8601 instead (like 2024-01-15T14:30:22). Rest of the line can stay as-is.

Log's about 50k lines so nothing crazy but I don't want to sit here doing it by hand.
