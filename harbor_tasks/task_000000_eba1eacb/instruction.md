Been setting up a small monitoring stack in /home/user/netmon — got a few shell scripts that ping hosts and check port status, plus a python script that aggregates the results into a json report. Right now I'm running them manually one by one which is dumb.

Need a Makefile that ties it together. Should have a `report` target that runs the checks then builds the aggregated json. The scripts depend on a config file /home/user/netmon/hosts.conf being present — make should bail early if it's missing rather than letting the scripts fail cryptically. Oh and the ping script writes to results/ping.txt, port checker writes to results/ports.txt, then aggregate.py reads both of those and spits out results/status.json.

Pretty sure there's also something wrong with aggregate.py — was getting some error last time I ran it but didn't write it down. Might need a quick fix there too.
