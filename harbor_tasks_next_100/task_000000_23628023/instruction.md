Getting paged about /home/user/services/auth-gateway — it's been restarting every few minutes since around 2am. Logs are in /var/log/auth-gateway/ but there's a lot of noise in there from normal operation. The service itself is a Go binary that reads config from /home/user/services/auth-gateway/config.yaml and talks to a redis instance on localhost:6379.

Pretty sure redis is fine — I can connect manually and PING it. So it's something in the gateway itself. Need the service actually staying up, not crash-looping.
