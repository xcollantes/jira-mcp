#!/bin/bash
# Bump version in __version__.py and README.md badge.
# Usage: ./bump_version.sh <new_version>
# Example: ./bump_version.sh 0.2.3

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <new_version>"
    echo "Example: $0 0.2.3"
    exit 1
fi

NEW_VERSION="$1"

echo "Update __version__.py."
sed -i '' "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/__version__.py

echo "Update README.md version badge."
sed -i '' "s/Version-[0-9]*\.[0-9]*\.[0-9]*/Version-$NEW_VERSION/" README.md

echo "Update server.json version for MCP registry."
sed -i '' "s/\"version\": \"[0-9]*\.[0-9]*\.[0-9]*/\"version\": \"$NEW_VERSION/" server.json

echo "Version bumped to $NEW_VERSION"
echo "Updated files:"
echo "  - src/__version__.py"
echo "  - README.md"
echo "  - server.json"

echo "Remember to create tag and push it to the repository:"
echo ""
echo "git tag v$NEW_VERSION"
echo "git push origin v$NEW_VERSION"
