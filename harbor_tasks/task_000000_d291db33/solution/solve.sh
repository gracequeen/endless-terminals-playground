#!/bin/bash
# Auto-generated solve script
set -e

mkdir -p /home/user/bin
cat > /home/user/bin/sync-docs.sh << 'EOF'
#!/bin/bash
# Sync docs from remote-docs to local-docs
# Preserves timestamps and permissions, skips files > 50MB

rsync -av --max-size=50M /home/user/remote-docs/ /home/user/local-docs/
EOF
chmod +x /home/user/bin/sync-docs.sh
ls -l /home/user/bin/sync-docs.sh && cat /home/user/bin/sync-docs.sh
