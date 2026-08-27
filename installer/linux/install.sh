#!/usr/bin/env bash
# Socials Studio installer (Linux).
#
# Plain shell script, not a compiled/opaque binary -- stages the repository
# source onto disk exactly as it is in the repo, then runs
# installer/bootstrap.py to prepare a Python virtual environment. Never logs
# into a platform, never publishes anything, never collects a credential.
#
# CI smoke-tests this script on ubuntu-24.04 (see
# .github/workflows/build-installers.yml) -- silent install, verify expected
# files exist, verify a reinstall doesn't touch profiles/. A separate,
# independent manual test on real Ubuntu 24.04 x64 hardware has also
# confirmed source install, venv creation, dependency install, the
# launcher/desktop entry, and byte-for-byte profiles/ preservation on
# reinstall -- see README.md's Testing status section for the exact,
# current label. Real browser login / publishing has not been tested
# through this package on any Linux machine yet.
#
# Usage (once downloaded/extracted):
#   ./install.sh [destination-directory]
# Defaults to ~/.local/share/socials-studio if no destination is given.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEST="${1:-$HOME/.local/share/socials-studio}"

echo "Installing Socials Studio to: $DEST"
mkdir -p "$DEST"

# Exclude profiles/ so an existing install's saved logins/tokens are never
# overwritten by a reinstall or upgrade.
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
    echo "No Python 3.10+ was found (checked python3.10 through python3.13, and"
    echo "plain python3 -- rejecting anything older than 3.10)."
    echo "This installer does not set up Python for you on Linux -- install one"
    echo "yourself with your distribution's package manager, e.g.:"
    echo "  Debian/Ubuntu:  sudo apt install python3 python3-venv python3-pip"
    echo "  Fedora:         sudo dnf install python3"
    echo "  Arch:           sudo pacman -S python"
    echo "Then run this installer again."
    echo ""
    exit 1
fi

echo "Using $(command -v "$PYTHON_BIN") to set up Socials Studio's environment..."
"$PYTHON_BIN" "$DEST/installer/bootstrap.py" --project-dir "$DEST"

cp "$SCRIPT_DIR/socials-studio-launch.sh" "$DEST/socials-studio-launch.sh"
chmod +x "$DEST/socials-studio-launch.sh"

DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
sed "s|__EXEC_PATH__|$DEST/socials-studio-launch.sh|" \
    "$SCRIPT_DIR/socials-studio.desktop" > "$DESKTOP_DIR/socials-studio.desktop"

echo ""
echo "Done. Run $DEST/socials-studio-launch.sh, or look for \"Socials Studio\""
echo "in your applications menu."
