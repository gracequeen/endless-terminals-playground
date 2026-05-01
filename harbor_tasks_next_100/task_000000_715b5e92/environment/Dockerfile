FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/user

RUN apt-get update && apt-get install -y \
    gnupg \
    bash \
    python3 \
    python3-pip \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user
RUN mkdir -p /var/backups/encrypted && chmod 0755 /var/backups/encrypted
RUN mkdir -p /home/user/backup-verify && chmod 0777 /home/user/backup-verify
RUN mkdir -p /home/user/.gnupg && chmod 0700 /home/user/.gnupg

# Create GPG keys and setup
RUN gpg --batch --gen-key <<KEYEOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Subkey-Type: RSA
Subkey-Length: 2048
Name-Real: Backup System
Name-Email: backup@example.com
Expire-Date: 0
%commit
KEYEOF

RUN gpg --batch --gen-key <<KEYEOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Name-Real: Old Signing Key
Name-Email: sign@example.com
Expire-Date: 0
%commit
KEYEOF

RUN gpg --batch --gen-key <<KEYEOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Name-Real: New Signing Key
Name-Email: sign-new@example.com
Expire-Date: 0
%commit
KEYEOF

# Get key IDs and rename them to match expected IDs in the task
RUN BACKUP_KEY=$(gpg --list-secret-keys --keyid-format long | grep -A1 "Backup System" | head -1 | awk '{print $1}' | cut -d'/' -f2) && \
    OLD_SIGN_KEY=$(gpg --list-secret-keys --keyid-format long | grep -A1 "Old Signing Key" | head -1 | awk '{print $1}' | cut -d'/' -f2) && \
    NEW_SIGN_KEY=$(gpg --list-secret-keys --keyid-format long | grep -A1 "New Signing Key" | head -1 | awk '{print $1}' | cut -d'/' -f2) && \
    echo "BACKUP_KEY=$BACKUP_KEY" > /tmp/keyids && \
    echo "OLD_SIGN_KEY=$OLD_SIGN_KEY" >> /tmp/keyids && \
    echo "NEW_SIGN_KEY=$NEW_SIGN_KEY" >> /tmp/keyids

# Create test backup content
RUN mkdir -p /tmp/backup-content && \
    echo "This is test backup data from 2024-01-15" > /tmp/backup-content/data-old.txt && \
    tar -cf /tmp/backup-2024-01-15.tar -C /tmp/backup-content data-old.txt && \
    echo "This is test backup data from 2024-01-20" > /tmp/backup-content/data-new.txt && \
    tar -cf /tmp/backup-2024-01-20.tar -C /tmp/backup-content data-new.txt

# Encrypt backups with the Backup System key
RUN . /tmp/keyids && \
    gpg --batch --yes --trust-model always -r "Backup System" --encrypt --output /var/backups/encrypted/backup-2024-01-15.tar.gpg /tmp/backup-2024-01-15.tar && \
    gpg --batch --yes --trust-model always -r "Backup System" --encrypt --output /var/backups/encrypted/backup-2024-01-20.tar.gpg /tmp/backup-2024-01-20.tar

# Sign old backup with old signing key
RUN . /tmp/keyids && \
    gpg --batch --yes --detach-sign --local-user "Old Signing Key" --output /var/backups/encrypted/backup-2024-01-15.tar.sig /tmp/backup-2024-01-15.tar

# Sign new backup with new signing key
RUN . /tmp/keyids && \
    gpg --batch --yes --detach-sign --local-user "New Signing Key" --output /var/backups/encrypted/backup-2024-01-20.tar.sig /tmp/backup-2024-01-20.tar

# Set trust on old signing key to ultimate (so it works)
RUN OLD_FPR=$(gpg --fingerprint "Old Signing Key" | grep -A1 "pub" | tail -1 | tr -d ' ') && \
    echo "${OLD_FPR}:6:" | gpg --import-ownertrust

# Make sure new signing key has unknown trust (the bug)
# By default it will have unknown trust, but let's be explicit
RUN NEW_FPR=$(gpg --fingerprint "New Signing Key" | grep -A1 "pub" | tail -1 | tr -d ' ') && \
    echo "${NEW_FPR}:2:" | gpg --import-ownertrust

# Set file timestamps so 2024-01-20 is clearly newer
RUN touch -d "2024-01-15 12:00:00" /var/backups/encrypted/backup-2024-01-15.tar.gpg && \
    touch -d "2024-01-15 12:00:00" /var/backups/encrypted/backup-2024-01-15.tar.sig && \
    touch -d "2024-01-20 02:00:00" /var/backups/encrypted/backup-2024-01-20.tar.gpg && \
    touch -d "2024-01-20 02:00:00" /var/backups/encrypted/backup-2024-01-20.tar.sig

# Store key fingerprints for the check script to potentially use
RUN gpg --fingerprint "New Signing Key" | grep -A1 "pub" | tail -1 | tr -d ' ' > /tmp/new_sign_fpr

# Create the check.sh script
RUN cat > /home/user/backup-verify/check.sh << 'SCRIPTEOF'
#!/bin/bash

BACKUP_DIR="/var/backups/encrypted"
SENTINEL="/home/user/backup-verify/.last-verified"

# Find the newest .gpg file
newest_gpg=$(ls -t "$BACKUP_DIR"/*.gpg 2>/dev/null | head -1)

if [ -z "$newest_gpg" ]; then
    echo "verification failed"
    exit 1
fi

# Derive the tar filename and sig filename
basename_gpg=$(basename "$newest_gpg" .gpg)
tarfile="/tmp/${basename_gpg}"
sigfile="${BACKUP_DIR}/${basename_gpg}.sig"

if [ ! -f "$sigfile" ]; then
    echo "verification failed"
    exit 1
fi

# Decrypt the backup
gpg --batch --yes --decrypt --output "$tarfile" "$newest_gpg" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "verification failed"
    exit 1
fi

# Verify the signature with status output
status=$(gpg --verify --status-fd 1 "$sigfile" "$tarfile" 2>&1)

if ! echo "$status" | grep -q "GOODSIG"; then
    echo "verification failed"
    rm -f "$tarfile"
    exit 1
fi

if echo "$status" | grep -q "TRUST_UNDEFINED\|TRUST_NEVER"; then
    echo "verification failed"
    rm -f "$tarfile"
    exit 1
fi

# All checks passed
rm -f "$tarfile"
touch "$SENTINEL"
exit 0
SCRIPTEOF

RUN chmod +x /home/user/backup-verify/check.sh

# Copy GPG directory to user home and set permissions
RUN cp -r /root/.gnupg/* /home/user/.gnupg/ && \
    chmod 0700 /home/user/.gnupg && \
    chmod 0600 /home/user/.gnupg/* 2>/dev/null || true && \
    chmod 0700 /home/user/.gnupg/private-keys-v1.d 2>/dev/null || true && \
    chmod 0600 /home/user/.gnupg/private-keys-v1.d/* 2>/dev/null || true

# Store the key IDs in a way that matches the task description
RUN NEW_KEY_LONG=$(gpg --list-keys --keyid-format long "New Signing Key" | grep "pub" | head -1 | sed 's/.*\/\([A-F0-9]*\).*/\1/') && \
    echo "New signing key ID: $NEW_KEY_LONG" && \
    sed -i "s/$NEW_KEY_LONG/22222222$NEW_KEY_LONG/g" /home/user/.gnupg/pubring.kbx 2>/dev/null || true

# Actually we need to work with the keys as they are - let's export info for tests
RUN gpg --list-keys --keyid-format long > /home/user/.gnupg/keylist.txt

# Set proper ownership for everything
RUN chown -R 1000:1000 /home/user

# Make backup directory readable but not writable by user
RUN chmod 755 /var/backups/encrypted && \
    chmod 644 /var/backups/encrypted/*

# Clean up temp files
RUN rm -rf /tmp/backup-content /tmp/backup-*.tar /tmp/keyids

WORKDIR /home/user
USER 1000

CMD ["/bin/bash"]
