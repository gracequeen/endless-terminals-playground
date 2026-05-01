FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/firewall && chmod 0777 /home/user/firewall

RUN cat > /home/user/firewall/policy.conf << 'EOF'
# Approved inbound ports
ALLOWED_PORTS=22,80,443
# Last reviewed: 2024-01-15
EOF

RUN chmod 0666 /home/user/firewall/policy.conf

RUN cat > /home/user/firewall/current_rules.txt << 'EOF'
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -p tcp --dport 22 -j ACCEPT
-A INPUT -p tcp --dport 80 -j ACCEPT
-A INPUT -p tcp --dport 443 -j ACCEPT
-A INPUT -p tcp --dport 3306 -j ACCEPT
-A INPUT -p tcp --dport 6379 -j ACCEPT
COMMIT
EOF

RUN chmod 0666 /home/user/firewall/current_rules.txt

RUN cat > /home/user/firewall/apply_rules.sh << 'EOF'
#!/bin/bash
# apply_rules.sh - Apply firewall rules from current_rules.txt
# This script reads the iptables rules from current_rules.txt and applies them
# Usage: sudo ./apply_rules.sh
#
# Note: Requires root privileges to modify iptables

RULES_FILE="$(dirname "$0")/current_rules.txt"

if [ ! -f "$RULES_FILE" ]; then
    echo "Error: Rules file not found at $RULES_FILE"
    exit 1
fi

echo "Applying firewall rules from $RULES_FILE..."
iptables-restore < "$RULES_FILE"
echo "Firewall rules applied successfully."
EOF

RUN chmod 0755 /home/user/firewall/apply_rules.sh

RUN useradd -m -d /home/user -s /bin/bash user || true

RUN chown -R user:user /home/user/firewall

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
