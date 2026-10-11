#!/usr/bin/env bash
#
# Ship the Tutor Portal: commit, push to GitHub, update the live site.
#
# Railway is NOT wired to GitHub on this account (the Railway GitHub App is not
# authorised), so a push on its own does NOT deploy. This script is the one
# command that makes a change live, and it does not claim success until the
# running site actually answers.
#
#   ./deploy.sh "what changed"
#
set -euo pipefail
cd "$(dirname "$0")"

MSG="${1:-update $(date '+%Y-%m-%d %H:%M')}"
LIVE="https://app.collegegradelifter.com"

git add -A
if git diff --cached --quiet; then
  echo "nothing to commit"
else
  git commit -q -m "$MSG"
  echo "committed $(git rev-parse --short HEAD)"
fi

git push -q origin main
echo "pushed to $(git remote get-url origin | sed 's#.*github.com/##; s#\.git$##')"

railway up --detach >/dev/null 2>&1
echo "deploy started — waiting for $LIVE to answer"

# the edge answers 502 while the old container is torn down and the new one
# starts, so retry rather than reporting the first failure
for _ in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$LIVE/api/health" || true)
  if [ "$code" = "200" ]; then
    echo "LIVE: $LIVE  (health 200, $(git rev-parse --short HEAD))"
    exit 0
  fi
  sleep 10
done

echo "DEPLOY DID NOT COME UP — run 'railway logs' and check" >&2
exit 1
