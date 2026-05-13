#!/bin/bash
# Auto-generated solve script
set -e

ls -la /home/user/netmon/
ls -la /home/user/netmon/scripts/
cat /home/user/netmon/scripts/check_ping.sh
cat /home/user/netmon/scripts/check_ports.sh
cat /home/user/netmon/aggregate.py
cat /home/user/netmon/hosts.conf
sed -i 's/with open("results\/status.json", "w") as f$/with open("results\/status.json", "w") as f:/' /home/user/netmon/aggregate.py
cat /home/user/netmon/aggregate.py
cat > /home/user/netmon/Makefile << 'EOF'
# Makefile for network monitoring stack

# Check that hosts.conf exists before doing anything
ifeq (,$(wildcard hosts.conf))
$(error hosts.conf not found - cannot proceed without configuration file)
endif

.PHONY: report clean check-ping check-ports

# Main target: generate the full status report
report: results/status.json

# Aggregate results into JSON report
results/status.json: results/ping.txt results/ports.txt
	python3 aggregate.py

# Run ping checks
results/ping.txt: hosts.conf scripts/check_ping.sh
	./scripts/check_ping.sh

# Run port checks
results/ports.txt: hosts.conf scripts/check_ports.sh
	./scripts/check_ports.sh

# Convenience targets
check-ping: results/ping.txt

check-ports: results/ports.txt

# Clean up results
clean:
	rm -rf results/
EOF
cat /home/user/netmon/Makefile
cd /home/user/netmon && make report
cat /home/user/netmon/results/status.json
cd /home/user/netmon && mv hosts.conf hosts.conf.bak && make report 2>&1; mv hosts.conf.bak hosts.conf
cat /home/user/netmon/results/ping.txt && echo "---" && cat /home/user/netmon/results/ports.txt
