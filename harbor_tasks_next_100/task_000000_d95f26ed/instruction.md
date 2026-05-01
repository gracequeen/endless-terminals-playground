Got a runaway process eating CPU on port 8443 — it's the old metrics-exporter that should've been killed when we rotated pods. Just need it dead so the new one can bind.
