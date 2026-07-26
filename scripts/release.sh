#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: scripts/release.sh <version, e.g. 0.1.2>}"
TAG="v$VERSION"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree not clean. Commit or stash changes first." >&2
  exit 1
fi

VERSION="$VERSION" python3 - <<'EOF'
import os, re

version = os.environ["VERSION"]
with open("pyproject.toml") as f:
    content = f.read()
content = re.sub(r'(?m)^version = ".*"', f'version = "{version}"', content, count=1)
with open("pyproject.toml", "w") as f:
    f.write(content)
EOF

git add pyproject.toml
git commit -m "chore: release $TAG"
git tag "$TAG"
git push origin HEAD
git push origin "$TAG"

echo "Pushed $TAG — CI will build, test, and publish to PyPI."
