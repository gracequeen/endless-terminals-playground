Trying to profile startup latency on our Go service at /home/user/profilesvc — need it listening on :8080 so I can hit it with wrk. But `go run main.go` just hangs for like 20 seconds then dies with some bind error. Weird because nothing else is using 8080 (checked with ss). Config's in config.yaml, pretty vanilla setup afaict. Was working yesterday before someone "cleaned up" the repo, not sure what changed.

Just need the server actually starting and responding on 8080 so I can get my latency numbers.
