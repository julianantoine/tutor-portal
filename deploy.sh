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

git add -A
git diff --cached --quiet || git commit -q -m "$MSG"

# the version marker travels inside the image (the Dockerfile copies backend/),
# so the running container can say which commit it is
echo "$(git rev-parse --short HEAD)" > backend/VERSION
git add backend/VERSION
git diff --cached --quiet || git commit -q -m "Record build $(git rev-parse --short HEAD)"

SHA=$(git rev-parse --short HEAD)
git push -q origin main
echo "pushed $SHA to $(git remote get-url origin | sed 's#.*github.com/##; s#\.git$##')"

railway up --detach >/dev/null 2>&1
echo "build started — waiting for $LIVE to report $SHA"

for _ in $(seq 1 40); do
  RESP=$(curl -s --max-time 15 "$LIVE/api/health" || true)
  case "$RESP" in
    *"\"version\":\"$SHA\""*)
      echo "LIVE: $LIVE now running $SHA"
      echo "$RESP"
      exit 0 ;;
  esac
  sleep 15
done

echo "LIVE SITE IS NOT ON $SHA YET — still building, or the build failed. Check:" >&2
echo "  railway logs" >&2
exit 1
