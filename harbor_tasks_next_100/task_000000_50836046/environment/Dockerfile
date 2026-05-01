FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    bash \
    iptables \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/firewall && chmod 0777 /home/user && chmod 0777 /home/user/firewall

RUN cat > /home/user/firewall/rules.conf << 'EOF'
# Default policies
default_input: drop
default_output: accept

# Allow established connections
allow in state established,related

# SSH access
allow in tcp 22 from any

# Block known bad subnet
deny in from 10.80.0.0/16

# Monitoring access
allow in tcp 9100 from 10.80.4.0/24

# Web traffic
allow in tcp 80 from any
allow in tcp 443 from any
EOF

RUN chmod 0666 /home/user/firewall/rules.conf

RUN cat > /home/user/firewall/apply.sh << 'EOFSCRIPT'
#!/bin/bash

# Firewall rule applier script
# Reads rules.conf and generates iptables commands
# Running in dry-run mode - writes to applied.log instead of executing

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_FILE="$SCRIPT_DIR/rules.conf"
OUTPUT_LOG="$SCRIPT_DIR/applied.log"

if [[ ! -f "$RULES_FILE" ]]; then
    echo "Error: rules.conf not found"
    exit 1
fi

# Clear output log
> "$OUTPUT_LOG"

echo "# Firewall rules applied at $(date)" >> "$OUTPUT_LOG"
echo "# Dry-run mode - showing what would be executed" >> "$OUTPUT_LOG"
echo "" >> "$OUTPUT_LOG"

while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip comments and empty lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue

    # Parse default policies
    if [[ "$line" =~ ^default_input:[[:space:]]*(.+)$ ]]; then
        policy="${BASH_REMATCH[1]}"
        policy_upper=$(echo "$policy" | tr '[:lower:]' '[:upper:]')
        echo "iptables -P INPUT $policy_upper" >> "$OUTPUT_LOG"
        continue
    fi

    if [[ "$line" =~ ^default_output:[[:space:]]*(.+)$ ]]; then
        policy="${BASH_REMATCH[1]}"
        policy_upper=$(echo "$policy" | tr '[:lower:]' '[:upper:]')
        echo "iptables -P OUTPUT $policy_upper" >> "$OUTPUT_LOG"
        continue
    fi

    # Parse allow in state established,related
    if [[ "$line" =~ ^allow[[:space:]]+in[[:space:]]+state[[:space:]]+(.+)$ ]]; then
        states="${BASH_REMATCH[1]}"
        states_upper=$(echo "$states" | tr '[:lower:]' '[:upper:]')
        echo "iptables -A INPUT -m state --state $states_upper -j ACCEPT" >> "$OUTPUT_LOG"
        continue
    fi

    # Parse allow in tcp PORT from CIDR/any
    if [[ "$line" =~ ^allow[[:space:]]+in[[:space:]]+tcp[[:space:]]+([0-9]+)[[:space:]]+from[[:space:]]+(.+)$ ]]; then
        port="${BASH_REMATCH[1]}"
        source="${BASH_REMATCH[2]}"
        if [[ "$source" == "any" ]]; then
            echo "iptables -A INPUT -p tcp --dport $port -j ACCEPT" >> "$OUTPUT_LOG"
        else
            echo "iptables -A INPUT -p tcp --dport $port -s $source -j ACCEPT" >> "$OUTPUT_LOG"
        fi
        continue
    fi

    # Parse deny in from CIDR
    if [[ "$line" =~ ^deny[[:space:]]+in[[:space:]]+from[[:space:]]+(.+)$ ]]; then
        source="${BASH_REMATCH[1]}"
        echo "iptables -A INPUT -s $source -j DROP" >> "$OUTPUT_LOG"
        continue
    fi

done < "$RULES_FILE"

echo "" >> "$OUTPUT_LOG"
echo "# End of rules" >> "$OUTPUT_LOG"

echo "Rules applied successfully"
exit 0
EOFSCRIPT

RUN chmod 0755 /home/user/firewall/apply.sh

RUN cat > /home/user/firewall/conn.log << 'EOF'
[2024-01-15 14:32:17] incoming connection from 10.80.4.17:48832 to :9100
[2024-01-15 14:32:17] matched rule: deny in from 10.80.0.0/16
[2024-01-15 14:32:17] action: DROP
EOF

RUN chmod 0666 /home/user/firewall/conn.log

RUN chown -R 1000:1000 /home/user/firewall

WORKDIR /home/user

CMD ["/bin/bash"]
