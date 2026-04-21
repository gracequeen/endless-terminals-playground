FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update apt cache and install required tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    apt-utils \
    && rm -rf /var/lib/apt/lists/*

# Update apt cache again to ensure it's available for the task
RUN apt-get update

# Install pytest
RUN pip3 install pytest

# Create home directory with proper permissions
RUN mkdir -p /home/user/migration && chmod 0777 /home/user && chmod 0777 /home/user/migration

# Create installed_packages.txt with the 31 packages
RUN cat <<EOF > /home/user/migration/installed_packages.txt
curl
wget
vim
nano
git
htop
tree
ncdu
jq
python3
python3-pip
nodejs
npm
nginx
apache2
mysql-client
postgresql-client
redis-tools
netcat-openbsd
tcpdump
strace
lsof
dnsutils
iputils-ping
ca-certificates
openssl
libssl3
zlib1g
libc6
coreutils
bash
EOF

# Create required_packages.txt with the 9 packages
RUN cat <<EOF > /home/user/migration/required_packages.txt
curl
python3
python3-pip
jq
nginx
ca-certificates
openssl
bash
coreutils
EOF

# Set proper permissions on the files
RUN chmod 0644 /home/user/migration/installed_packages.txt && \
    chmod 0644 /home/user/migration/required_packages.txt

# Create a non-root user
RUN useradd -m -d /home/user -s /bin/bash user || true

# Make sure user owns the migration directory
RUN chown -R user:user /home/user

# Set working directory
WORKDIR /home/user

# Switch to non-root user
USER user
