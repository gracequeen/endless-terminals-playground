#!/usr/bin/env bash
# Pre-pull terminal-bench-2-1 task images (environment + verifier) so the eval
# runs from a warm cache and does not pull mid-run.
#
# WHY: docker cleanup / prune evicted the cached images, and anonymous Docker Hub
# pulls hit the rate limit. Run `docker login` FIRST (authenticated pull limit is
# far higher), then run this script once. After images are cached they persist and
# no further pulls are needed unless the image cache is pruned or tags change.
#
#   docker login          # do this first (higher authenticated pull limit)
#   bash scripts/prepull_tb_images.sh
#
# The ref list (scripts/tb2_1_image_refs.txt) is the authoritative image set for the
# 89 terminal-bench-2-1 tasks: one image per task, alexgshaw/<task>:20251031 (no
# separate verifier image). Task membership was resolved from the Harbor registry
# (PackageDatasetClient) and the images extracted from those 89 tasks' task.toml.
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
REFS="$REPO/scripts/tb2_1_image_refs.txt"

[[ -f "$REFS" ]] || { echo "ref list not found: $REFS" >&2; exit 1; }

total=$(wc -l < "$REFS")
echo "Pre-pulling $total terminal-bench images (skips any already cached)..."
echo "If you see 'toomanyrequests', run 'docker login' and re-run this script."
echo

i=0; pulled=0; skipped=0; failed=0
declare -a FAILED_REFS=()
while IFS= read -r ref; do
  [[ -z "$ref" ]] && continue
  i=$((i+1))
  # already present? (match by full repo@digest or repo:tag)
  if docker image inspect "$ref" >/dev/null 2>&1; then
    skipped=$((skipped+1))
    printf "[%3d/%d] cached   %s\n" "$i" "$total" "${ref##*:}"
    continue
  fi
  printf "[%3d/%d] pulling  %s ... " "$i" "$total" "${ref##*/}"
  if docker pull "$ref" >/dev/null 2>&1; then
    pulled=$((pulled+1)); echo "ok"
  else
    failed=$((failed+1)); echo "FAILED"; FAILED_REFS+=("$ref")
  fi
done < "$REFS"

echo
echo "Done: pulled=$pulled skipped(cached)=$skipped failed=$failed of $total"
if (( failed > 0 )); then
  echo "Failed refs (likely rate-limited — run 'docker login' and re-run):"
  printf '  %s\n' "${FAILED_REFS[@]}"
  exit 1
fi
echo "All images cached. Safe to launch the eval."
