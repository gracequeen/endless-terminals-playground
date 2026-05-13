#!/bin/bash
# Auto-generated solve script
set -e

cat /home/user/.rsyncrc
echo '--archive' > /home/user/.rsyncrc
cat /home/user/.rsyncrc
ls -la /home/user/project/ 2>/dev/null | head -20
rsync --dry-run -v /home/user/project/ /home/user/backup/
rsync --dry-run -av /home/user/project/ /home/user/backup/
cat /home/user/.rsyncrc
