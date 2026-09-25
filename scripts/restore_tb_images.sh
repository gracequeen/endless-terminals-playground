#!/usr/bin/env bash
# Restore terminal-bench-2-1 task images from the per-image backup created by
# scripts/backup_tb_images.sh. Loads each *.tar.gz that isn't already present in
# the local Docker image cache. No Docker Hub / network needed.
#
#   bash scripts/restore_tb_images.sh
set -uo pipefail

SRC="${1:-$HOME/tb2_1_images_backup/images}"
[[ -d "$SRC" ]] || { echo "backup dir not found: $SRC" >&2; exit 1; }

total=$(ls "$SRC"/*.tar.gz 2>/dev/null | wc -l)
i=0; loaded=0; failed=0
for f in "$SRC"/*.tar.gz; do
  [[ -e "$f" ]] || continue
  i=$((i+1))
  printf "[%2d/%d] load %s ... " "$i" "$total" "$(basename "$f")"
  if gunzip -c "$f" | docker load >/dev/null 2>&1; then
    loaded=$((loaded+1)); echo "ok"
  else
    failed=$((failed+1)); echo "FAILED"
  fi
done
echo
echo "Restore done: loaded=$loaded failed=$failed of $total from $SRC"
