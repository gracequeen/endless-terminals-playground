FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install pytest
RUN pip3 install pytest

# Install Node.js (using NodeSource repository for a recent version)
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Create home directory with appropriate permissions
RUN mkdir -p /home/user && chmod 0777 /home/user

# Create credential-rotation directory
RUN mkdir -p /home/user/credential-rotation && chmod 0777 /home/user/credential-rotation

# Create aws-rotation.log
RUN cat <<EOF > /home/user/credential-rotation/aws-rotation.log
[2024-01-15 09:23:45] payment-service | AKIA3EXAMPLE1OLD | AKIA3EXAMPLE1NEW | SUCCESS | jsmith
[2024-01-15 09:24:12] user-auth-api | AKIA3EXAMPLE2OLD | AKIA3EXAMPLE2NEW | SUCCESS | jsmith
[2024-01-15 09:25:33] analytics-pipeline | AKIA3EXAMPLE3OLD | AKIA3EXAMPLE3NEW | FAILED | jsmith
[2024-01-15 09:26:01] notification-worker | AKIA3EXAMPLE4OLD | AKIA3EXAMPLE4NEW | SUCCESS | mwilliams
[2024-01-15 09:27:18] backup-service | AKIA3EXAMPLE5OLD | AKIA3EXAMPLE5NEW | SUCCESS | mwilliams
EOF

# Create db-rotation.log
RUN cat <<EOF > /home/user/credential-rotation/db-rotation.log
[2024-01-15 10:01:22] postgres-primary | db_old_hash_001 | db_new_hash_001 | SUCCESS | jsmith
[2024-01-15 10:02:45] mysql-reporting | db_old_hash_002 | db_new_hash_002 | SUCCESS | jsmith
[2024-01-15 10:03:58] redis-cache | db_old_hash_003 | db_new_hash_003 | FAILED | mwilliams
[2024-01-15 10:05:12] mongodb-sessions | db_old_hash_004 | db_new_hash_004 | SUCCESS | mwilliams
EOF

# Create api-keys.log
RUN cat <<EOF > /home/user/credential-rotation/api-keys.log
[2024-01-15 11:00:05] stripe-payments | sk_old_stripe123 | sk_new_stripe456 | SUCCESS | jsmith
[2024-01-15 11:01:33] sendgrid-email | SG.old_key_abc | SG.new_key_xyz | SUCCESS | jsmith
[2024-01-15 11:02:44] twilio-sms | twilio_old_sid | twilio_new_sid | SUCCESS | mwilliams
[2024-01-15 11:03:22] datadog-monitoring | dd_old_api_key | dd_new_api_key | FAILED | mwilliams
[2024-01-15 11:04:01] github-actions | ghp_oldtoken123 | ghp_newtoken456 | SUCCESS | jsmith
EOF

# Set permissions on log files
RUN chmod 0666 /home/user/credential-rotation/*.log

# Set working directory
WORKDIR /home/user

# Default command
CMD ["/bin/bash"]
