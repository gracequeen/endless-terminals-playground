FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    iptables \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/firewall/rules.d && chmod -R 0777 /home/user/firewall

RUN cat > /home/user/firewall/rules.sh << 'EOF'
#!/bin/bash
# Main firewall rules

iptables -F
iptables -X

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow established connections
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# Source additional rule files
for f in /home/user/firewall/rules.d/*.conf; do
    source "$f"
done

# Allow internal subnets to reach wiki
iptables -A FORWARD -s 10.0.10.0/24 -d 192.168.1.80 -p tcp --dport 8080 -j ACCEPT
iptables -A FORWARD -s 10.0.20.0/24 -d 192.168.1.80 -p tcp --dport 8080 -j ACCEPT
iptables -A FORWARD -s 10.0.30.0/24 -d 192.168.1.80 -p tcp --dport 8080 -j ACCEPT
iptables -A FORWARD -s 10.0.40.0/24 -d 192.168.1.80 -p tcp --dport 8080 -j ACCEPT
# 10.0.50.0/24 - need to check if this was ever added
iptables -A FORWARD -s 10.0.60.0/24 -d 192.168.1.80 -p tcp --dport 8080 -j ACCEPT
EOF

RUN chmod 0777 /home/user/firewall/rules.sh

RUN cat > /home/user/firewall/rules.d/ratelimit.conf << 'EOF'
# Rate limiting rules - added by JT, March
# Block repeat offenders from specific subnets

# Temp block on 10.0.50.0/24 due to abuse incident - REMOVE AFTER INVESTIGATION
iptables -A FORWARD -s 10.0.50.0/24 -d 192.168.1.0/24 -j DROP

# Rate limit other subnets
iptables -A FORWARD -s 10.0.70.0/24 -d 192.168.1.0/24 -m limit --limit 100/min -j ACCEPT
EOF

RUN chmod 0777 /home/user/firewall/rules.d/ratelimit.conf

RUN cat > /home/user/firewall/rules.d/logging.conf << 'EOF'
# Log dropped packets for debugging
iptables -A FORWARD -j LOG --log-prefix "FW_DROP: " --log-level 4
EOF

RUN chmod 0777 /home/user/firewall/rules.d/logging.conf

RUN cat > /home/user/firewall/changelog.txt << 'EOF'
2024-01-15: Initial setup - MR
2024-03-08: Added ratelimit.conf, temp block on 50 subnet - JT
2024-03-22: Tuned logging - JT
EOF

RUN chmod 0777 /home/user/firewall/changelog.txt

RUN useradd -m -d /home/user -s /bin/bash user || true
RUN chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
