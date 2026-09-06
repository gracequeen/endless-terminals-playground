#!/usr/bin/env bash
# Per-image backup of the 89 terminal-bench-2-1 task images to ~/tb2_1_images_backup/.
# Each image is saved individually (gzipped) so it does not block behind a running
# eval on the shared Docker daemon, and the backup is resumable (skips images whose
# tarball already exists). Restore with scripts/restore_tb_images.sh.
#
#   bash scripts/backup_tb_images.sh
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
REFS="$REPO/scripts/tb2_1_image_refs.txt"
DEST="${1:-$HOME/tb2_1_images_backup/images}"

[[ -f "$REFS" ]] || { echo "ref list not found: $REFS" >&2; exit 1; }
mkdir -p "$DEST"
cp "$REFS" "$DEST/../image_refs.txt" 2>/dev/null || true

total=$(grep -c . "$REFS")
i=0; saved=0; skipped=0; failed=0
declare -a FAILED=()
while IFS= read -r ref; do
  [[ -z "$ref" ]] && continue
  i=$((i+1))
  # filename-safe: alexgshaw/foo:tag -> foo__tag.tar.gz
  fname="$(echo "$ref" | sed -E 's#^[^/]+/##; s#[:/]#__#g').tar.gz"
  out="$DEST/$fname"
  if [[ -s "$out" ]]; then
    skipped=$((skipped+1)); printf "[%2d/%d] have  %s\n" "$i" "$total" "$fname"; continue
  fi
  printf "[%2d/%d] save  %s ... " "$i" "$total" "$fname"
  if docker save "$ref" | gzip > "$out" 2>/dev/null && [[ -s "$out" ]]; then
    saved=$((saved+1)); echo "ok ($(du -h "$out" | cut -f1))"
  else
    failed=$((failed+1)); rm -f "$out"; echo "FAILED"; FAILED+=("$ref")
  fi
done < "$REFS"

echo
echo "Backup done: saved=$saved skipped=$skipped failed=$failed of $total -> $DEST"
if (( failed > 0 )); then
  printf 'FAILED: %s\n' "${FAILED[@]}"
  exit 1
fi
echo "All $total images backed up. Total size: $(du -sh "$DEST" | cut -f1)"
