#!/usr/bin/env bash
#
# Ship the Tutor Portal: commit, push to GitHub, update the live site.
#
# Railway is NOT wired to GitHub on this account (the Railway GitHub App is not
# authorised), so a push on its own does NOT deploy. This is the one command that
# makes a change live.
#
# It does not trust a 200 from /api/health. During a rollout the PREVIOUS
# container is still answering, so a health check passes while the new build is
# still building — this waits until the live site reports the exact commit that
# was just pushed.
#
#   ./deploy.sh "what changed"
#
set -euo pipefail
cd "$(dirname "$0")"

MSG="${1:-update $(date '+%Y-%m-%d %H:%M')}"
LIVE="https://app.collegegradelifter.com"

# A unique id for THIS deploy, written into the image (the Dockerfile copies
# backend/) and then waited for on the live site. It must NOT be derived from the
# commit hash and then re-read after committing: writing the file changes the
# tree, so the commit the image is built from is not the hash written into it.
# That mistake made this script report failure on a deploy that had succeeded.
DEPLOY_ID="$(date -u +%Y%m%d-%H%M%S)-$(git rev-parse --short HEAD)"
echo "$DEPLOY_ID" > backend/VERSION

git add -A
git diff --cached --quiet || git commit -q -m "$MSG"

git push -q origin main
echo "pushed $(git rev-parse --short HEAD) to $(git remote get-url origin | sed 's#.*github.com/##; s#\.git$##')"

railway up --detach >/dev/null 2>&1
echo "build started — waiting for $LIVE to report $DEPLOY_ID"

for _ in $(seq 1 40); do
  RESP=$(curl -s --max-time 15 "$LIVE/api/health" || true)
  case "$RESP" in
    *"\"version\":\"$DEPLOY_ID\""*)
      echo "LIVE: $LIVE now running $DEPLOY_ID  (commit $(git rev-parse --short HEAD))"
      echo "$RESP"
      exit 0 ;;
  esac
  sleep 15
done

echo "LIVE SITE IS NOT ON $DEPLOY_ID YET — still building, or the build failed. Check:" >&2
echo "  railway logs" >&2
exit 1
