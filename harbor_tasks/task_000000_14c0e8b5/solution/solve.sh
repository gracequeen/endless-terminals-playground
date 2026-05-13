#!/bin/bash
# Auto-generated solve script
set -e

cat /home/user/audit/firewall_rules.json
cat /home/user/audit/connections.csv
cat > /home/user/audit/check.py << 'EOF'
#!/usr/bin/env python3
"""
Cross-reference firewall rules (JSON) with active connections (CSV).
Flags connections whose destination port isn't allowed by inbound rules.
"""

import json
import csv
import ipaddress
from pathlib import Path

AUDIT_DIR = Path("/home/user/audit")
RULES_FILE = AUDIT_DIR / "firewall_rules.json"
CONNECTIONS_FILE = AUDIT_DIR / "connections.csv"


def load_rules(filepath):
    """Load firewall rules from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get('rules', []), data.get('default_action', 'deny')


def load_connections(filepath):
    """Load active connections from CSV file."""
    connections = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            connections.append(row)
    return connections


def parse_port_spec(port_spec):
    """
    Parse a port specification which can be:
    - Single port: "443" -> (443, 443)
    - Port range: "8000-9000" -> (8000, 9000)
    Returns tuple (start_port, end_port)
    """
    port_spec = str(port_spec).strip()
    if '-' in port_spec:
        parts = port_spec.split('-')
        return (int(parts[0]), int(parts[1]))
    else:
        port = int(port_spec)
        return (port, port)


def port_matches(dest_port, port_spec):
    """Check if destination port matches the rule's port specification."""
    try:
        dest_port = int(dest_port)
        start_port, end_port = parse_port_spec(port_spec)
        return start_port <= dest_port <= end_port
    except (ValueError, TypeError):
        return False


def ip_in_cidr(ip_str, cidr_str):
    """Check if an IP address is within a CIDR block."""
    try:
        ip = ipaddress.ip_address(ip_str)
        network = ipaddress.ip_network(cidr_str, strict=False)
        return ip in network
    except ValueError:
        return False


def get_cidr_prefix_length(cidr_str):
    """Get the prefix length of a CIDR (higher = more specific)."""
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        return network.prefixlen
    except ValueError:
        return -1


def check_connection(src_ip, dest_port, rules, default_action):
    """
    Check if a connection is allowed by the firewall rules.
    
    Returns tuple: (is_allowed, matching_cidr or None)
    
    Logic:
    - Find all rules where source IP matches the CIDR
    - Sort by specificity (most specific CIDR first)
    - For each matching rule, check if port matches
    - If port matches, return the rule's action
    - If no rule matches, return default action
    """
    # Find all rules where the source IP is in the CIDR
    matching_rules = []
    for rule in rules:
        cidr = rule.get('source_cidr', '')
        if ip_in_cidr(src_ip, cidr):
            prefix_len = get_cidr_prefix_length(cidr)
            matching_rules.append((prefix_len, rule))
    
    # Sort by prefix length descending (most specific first)
    matching_rules.sort(key=lambda x: x[0], reverse=True)
    
    # Check rules in order of specificity
    for prefix_len, rule in matching_rules:
        rule_port = rule.get('dest_port', '')
        if port_matches(dest_port, rule_port):
            action = rule.get('action', 'deny')
            cidr = rule.get('source_cidr', '')
            return (action == 'allow', cidr)
    
    # No matching rule found - apply default action
    # Find the most specific CIDR that matched the IP (for reporting)
    if matching_rules:
        most_specific_cidr = matching_rules[0][1].get('source_cidr', 'unknown')
    else:
        most_specific_cidr = '0.0.0.0/0'  # Implicit "any"
    
    return (default_action == 'allow', most_specific_cidr)


def main():
    # Load data
    rules, default_action = load_rules(RULES_FILE)
    connections = load_connections(CONNECTIONS_FILE)
    
    # Check each connection
    for conn in connections:
        src_ip = conn.get('src_ip', '')
        dest_port = conn.get('dest_port', '')
        
        is_allowed, matching_cidr = check_connection(src_ip, dest_port, rules, default_action)
        
        if not is_allowed:
            print(f"BLOCKED: {src_ip}:{dest_port} not allowed from {matching_cidr}")


if __name__ == '__main__':
    main()
EOF
python3 /home/user/audit/check.py
chmod +x /home/user/audit/check.py && ls -la /home/user/audit/
head -50 /home/user/audit/check.py
