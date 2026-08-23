#!/usr/bin/env bash
# Socials Studio installer (macOS).
#
# This is a plain shell script, not a compiled/opaque binary -- it stages
# the repository source (Markdown skills, Python code, everything Claude
# Code reads) onto disk exactly as it is in the repo, then runs
# installer/bootstrap.py to prepare a Python virtual environment. It never
# logs into a platform, never publishes anything, never collects a
# credential.
#
# Has NOT been run on a real Mac as part of this change -- see the PR notes
# for what still needs human testing before this ships as verified.
#
# Usage (once downloaded/extracted):
#   ./install.sh [destination-directory]
# Defaults to ~/Applications/SocialsStudio if no destination is given.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEST="${1:-$HOME/Applications/SocialsStudio}"

echo "Installing Socials Studio to: $DEST"
mkdir -p "$DEST"

# Copy the plain repo source, excluding profiles/ so an existing install's
# saved logins/tokens are never overwritten by a reinstall or upgrade.
rsync -a --exclude 'profiles/' --exclude '.git/' "$REPO_ROOT/" "$DEST/"
mkdir -p "$DEST/profiles"

PYTHON_BIN=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo ""
    echo "Python 3.10+ was not found on this Mac."
    echo "Install it from https://www.python.org/downloads/macos/ (or via"
    echo "Homebrew: brew install python@3.12), then run this installer again."
    echo ""
    exit 1
fi

echo "Using $(command -v "$PYTHON_BIN") to set up Socials Studio's environment..."
"$PYTHON_BIN" "$DEST/installer/bootstrap.py" --project-dir "$DEST"

cp "$SCRIPT_DIR/SocialsStudio.command" "$DEST/SocialsStudio.command"
chmod +x "$DEST/SocialsStudio.command"

echo ""
echo "Done. Double-click $DEST/SocialsStudio.command to launch Socials Studio,"
echo "or drag it to your Dock/Applications folder first."
