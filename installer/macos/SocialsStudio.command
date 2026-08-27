#!/usr/bin/env bash
# Socials Studio launcher (macOS). Double-click this file in Finder.
#
# Opens Terminal in the install directory and starts Claude Code there.
# Never logs into a platform, publishes anything, or re-runs setup -- that
# already happened once, when install.sh ran.

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v claude >/dev/null 2>&1; then
    echo ""
    echo "Claude Code was not found on PATH."
    echo "Install it from https://claude.com/claude-code, sign in with a"
    echo "qualifying Claude account, then run this launcher again."
    echo ""
    read -r -p "Press Enter to close..."
    exit 1
fi

echo "Starting Socials Studio..."
echo ""
claude
