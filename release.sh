#!/usr/bin/env bash
set -euo pipefail

# release.sh - Commit VERSION, create annotated tag and push
# Usage: ./release.sh [--dry-run] [--no-push]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$SCRIPT_DIR/VERSION"

if [[ ! -f "$VERSION_FILE" ]]; then
    echo "VERSION file not found in $SCRIPT_DIR"
    exit 1
fi

VERSION="$(head -n1 "$VERSION_FILE" | tr -d '\r\n')"
TAG="v$VERSION"

DRY_RUN=0
NO_PUSH=0
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        --no-push) NO_PUSH=1; shift ;;
        -h|--help) echo "Usage: $0 [--dry-run] [--no-push]"; exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Ensure we are inside a git repo
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "This script must be run inside a git working tree."
    exit 1
fi

echo "Preparing release $TAG (from $VERSION_FILE)"

if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] git add VERSION"
    echo "[DRY-RUN] git commit -m 'Bump version to $TAG'"
    echo "[DRY-RUN] git tag -a $TAG -m 'Release $TAG'"
    echo "[DRY-RUN] git push origin HEAD"
    echo "[DRY-RUN] git push origin $TAG"
    exit 0
fi

# Stage and commit VERSION (if changed)
if git diff --quiet -- "$VERSION_FILE"; then
    echo "No changes to $VERSION_FILE to commit. Skipping commit."
else
    git add "$VERSION_FILE"
    git commit -m "Bump version to $TAG"
fi

# Create annotated tag (overwrite if exists)
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "Tag $TAG already exists locally. Deleting and recreating."
    git tag -d "$TAG"
fi

git tag -a "$TAG" -m "Release $TAG"

echo "Created tag $TAG"

if [[ $NO_PUSH -eq 1 ]]; then
    echo "Skipping push due to --no-push."
    exit 0
fi

# Push changes and tag
git push origin HEAD
# Push tag
git push origin "$TAG"

echo "Pushed tag $TAG to origin."
