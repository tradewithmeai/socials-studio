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
# CI smoke-tests this script on macos-latest (see
# .github/workflows/build-installers.yml) -- silent install, verify expected
# files exist, verify a reinstall doesn't touch profiles/. That's real,
# automated coverage, but it is not the same as a person running this on
# their own Mac. See README.md's Testing status section for the current,
# honest label -- do not treat this as verified on real hardware until a
# human confirms it.
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

# Find a python3 that is ACTUALLY 3.10+, not just named as if it might be --
# a distro's plain `python3` can resolve to something older, and trusting
# the name alone would silently accept it.
PYTHON_BIN=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo ""
    echo "No Python 3.10+ was found on this Mac (checked python3.10 through"
    echo "python3.13, and plain python3 -- rejecting anything older than 3.10)."
    echo "This installer does not set up Python for you on macOS -- install one"
    echo "yourself from https://www.python.org/downloads/macos/ (or via"
    echo "Homebrew: brew install python@3.12), then run this installer again."
    echo ""
    exit 1
fi

echo "Using $(command -v "$PYTHON_BIN") to set up Socials Studio's environment..."
# bootstrap.py exits non-zero when Claude Code isn't found yet -- that's a
# real, expected first-run state (the user hasn't installed it yet), not a
# fatal installer error. Don't let `set -e` abort the rest of this script
# (installing the launcher below) just because of that.
bootstrap_status=0
"$PYTHON_BIN" "$DEST/installer/bootstrap.py" --project-dir "$DEST" || bootstrap_status=$?

cp "$SCRIPT_DIR/SocialsStudio.command" "$DEST/SocialsStudio.command"
chmod +x "$DEST/SocialsStudio.command"

echo ""
if [ "$bootstrap_status" -ne 0 ]; then
    echo "Setup finished with an action still needed (see above, usually installing"
    echo "Claude Code). Once that's done, double-click $DEST/SocialsStudio.command"
    echo "to launch Socials Studio."
else
    echo "Done. Double-click $DEST/SocialsStudio.command to launch Socials Studio,"
    echo "or drag it to your Dock/Applications folder first."
fi
