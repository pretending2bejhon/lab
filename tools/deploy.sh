#!/bin/bash
# Deploy .output/public to the gh-pages branch of pretending2bejhon/lab (served at jhonalbert.com/lab/).
# Usage: bash tools/deploy.sh "<commit message>"
set -euo pipefail
cd "$(dirname "$0")/.."
MSG="${1:-deploy}"
test -f .output/public/index.html || { echo "no build: run npx nuxi generate first"; exit 1; }
test -f .output/public/.nojekyll || { echo ".nojekyll missing from the build"; exit 1; }
WT=.gh-pages-wt
rm -rf "$WT"
if git show-ref --verify --quiet refs/heads/gh-pages; then
  git worktree add "$WT" gh-pages >/dev/null
else
  git worktree add --detach "$WT" >/dev/null
  (cd "$WT" && git checkout --orphan gh-pages >/dev/null 2>&1 && git rm -rfq . >/dev/null 2>&1 || true)
fi
find "$WT" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R .output/public/. "$WT"/
(cd "$WT" && git add -A . && git -c user.name="Jhon" -c user.email="$(git config user.email)" commit -qm "$MSG" && git push -q origin gh-pages)
git worktree remove --force "$WT"
echo "pushed gh-pages: $(git rev-parse --short gh-pages)"
