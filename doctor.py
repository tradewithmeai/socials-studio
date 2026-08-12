#!/usr/bin/env python3
"""Check the setup that actually breaks, and say exactly how to fix it.

    python doctor.py              # run every check
    python doctor.py --youtube    # one group: sessions | youtube | media | repo
    python doctor.py --quiet      # only failures and warnings

Written because the same handful of misconfigurations get rediscovered by hand, one
person at a time. A written guide describes the setup and goes stale silently; these
checks interrogate the real machine, so they cannot drift out of step with it.

Nothing here launches a browser, publishes anything, or spends money. Safe to run
any time, including before you have set anything up.

Exit codes: 0 = no failures (warnings allowed) · 1 = at least one FAIL · 2 = interrupted.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
PROFILES_DIR = REPO_ROOT / "profiles"
YOUTUBE_TOKEN = PROFILES_DIR / "youtube" / "token.json"

# Platforms that use a saved browser session. YouTube is deliberately absent: it uses
# OAuth + the official Data API and never touches a browser profile. X is also absent:
# it's not presented as a supported platform in this release (auth/publish_x.py and its
# login machinery are untouched and functional -- see .claude/dormant/README.md).
BROWSER_PLATFORMS = ["instagram", "bluesky", "linkedin"]

PASS, WARN, FAIL, SKIP = "PASS", "WARN", "FAIL", "SKIP"
_MARK = {PASS: "[ok]  ", WARN: "[warn]", FAIL: "[FAIL]", SKIP: "[skip]"}

results: list[tuple[str, str, str, str]] = []  # (group, status, title, detail)


def record(group: str, status: str, title: str, detail: str = "") -> None:
    results.append((group, status, title, detail))


def run(cmd: list[str], timeout: int = 25) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, "not found"
    except subprocess.TimeoutExpired:
        return 124, "timed out"
    except OSError as e:
        return 126, str(e)


# ---------------------------------------------------------------- saved sessions

def check_sessions() -> None:
    """Each browser platform keeps its own profile under profiles/<platform>/."""
    g = "sessions"

    try:
        import playwright  # noqa: F401
        record(g, PASS, "Playwright installed", "")
    except ImportError:
        record(g, FAIL, "Playwright installed",
               "Not importable. Every browser publisher needs it.\n"
               "    Fix: pip install -r requirements.txt")
        return

    if not PROFILES_DIR.exists():
        record(g, FAIL, "Any platform connected",
               "No profiles/ directory — nothing is connected yet.\n"
               "    Fix: python -m auth.login_wizard --platform bluesky   (and the same for each platform)\n"
               "    That opens a plain Chrome window for you to sign in by hand. Automation cannot\n"
               "    log in for you: attempting it trips anti-automation defences.")
        return

    connected = 0
    for name in BROWSER_PLATFORMS:
        profile = PROFILES_DIR / name
        if not profile.exists():
            record(g, WARN, f"{name} session",
                   f"Not connected. Fix: python -m auth.login_wizard --platform {name}")
            continue

        cookies = _find_cookie_store(profile)
        if cookies is None:
            record(g, FAIL, f"{name} session",
                   "Profile directory exists but has no cookie store — the sign-in did not\n"
                   f"    complete. Fix: python -m auth.login_wizard --platform {name}")
            continue

        size = cookies.stat().st_size
        if size < 20_000:
            record(g, WARN, f"{name} session",
                   f"Cookie store is only {size:,} B, which looks like an incomplete sign-in.\n"
                   "    Expect this platform to hit a login wall when publishing.")
        else:
            connected += 1
            age_days = (datetime.now() - datetime.fromtimestamp(cookies.stat().st_mtime)).days
            note = f"Cookie store present ({size:,} B, last written {age_days}d ago)."
            if age_days > 120:
                note += "\n    Sessions do expire — if publishing hits a login wall, re-run the wizard."
            record(g, PASS, f"{name} session", note)

    if connected:
        record(g, PASS, "At least one platform connected", f"{connected} of {len(BROWSER_PLATFORMS)}.")

    _check_profile_locks(g)


def _find_cookie_store(profile: Path) -> Path | None:
    """Chrome's layout varies by version; check both known locations."""
    for rel in (Path("Default") / "Network" / "Cookies", Path("Default") / "Cookies"):
        p = profile / rel
        if p.exists():
            return p
    return None


def _check_profile_locks(g: str) -> None:
    """A held profile reads as 'logged out' but is really a stale process."""
    if os.name != "nt":
        return
    rc, out = run(["powershell", "-NoProfile", "-Command",
                   "@(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
                   "Where-Object { $_.CommandLine -like '*\\profiles\\*' }).Count"], timeout=30)
    if rc != 0:
        return
    try:
        n = int((out.strip().splitlines() or ["0"])[-1])
    except ValueError:
        return
    if n:
        record(g, WARN, "No stale browser holding a profile",
               f"{n} chrome process(es) appear to hold a profile directory.\n"
               "    Only ONE process can use a profile at a time. If a publish reports the profile is\n"
               "    in use, that is this — a stale process, NOT an auth failure. Close the other run\n"
               "    first; don't kill blind while a publish may be in flight.")
    else:
        record(g, PASS, "No stale browser holding a profile", "")


# ---------------------------------------------------------------- youtube oauth

def check_youtube() -> None:
    g = "youtube"

    if not YOUTUBE_TOKEN.exists():
        record(g, WARN, "YouTube connected",
               "No token yet. YouTube uses OAuth + the Data API, never a browser.\n"
               "    Fix: python -m auth.setup_youtube_oauth\n"
               "    At the consent screen, sign in as the account that OWNS THE CHANNEL — which is\n"
               "    often NOT the account that owns the Google Cloud project.")
        return

    try:
        tok = json.loads(YOUTUBE_TOKEN.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        record(g, FAIL, "YouTube token readable", f"{YOUTUBE_TOKEN} could not be parsed: {e}")
        return
    record(g, PASS, "YouTube token present", str(YOUTUBE_TOKEN.relative_to(REPO_ROOT)))

    if not tok.get("refresh_token"):
        record(g, FAIL, "Refresh token stored",
               "No refresh_token — the token expires within the hour and cannot renew itself.\n"
               "    Fix: re-run python -m auth.setup_youtube_oauth")
    else:
        record(g, PASS, "Refresh token stored", "")

    if "https://www.googleapis.com/auth/youtube.upload" not in set(tok.get("scopes") or []):
        record(g, FAIL, "Upload scope granted",
               "youtube.upload missing — this token can read but never publish.\n"
               "    Fix: re-run setup and accept all requested permissions.")
    else:
        record(g, PASS, "Upload scope granted", "")

    _check_token_age(g, tok)
    _check_channel(g)


def _check_token_age(g: str, tok: dict) -> None:
    """A grant that keeps dying after ~a week means the OAuth app is still in Testing."""
    raw = tok.get("expiry")
    if not raw:
        return
    try:
        exp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return
    days = (datetime.now(timezone.utc) - exp).days
    if days > 7:
        record(g, WARN, "Token freshness",
               f"Access token expired {days} days ago. Normal in itself — it refreshes on use — BUT\n"
               "    if uploads start failing about a week after each re-auth, the OAuth app is still\n"
               "    in 'Testing' mode, where Google expires REFRESH tokens after 7 days.\n"
               "    Fix: Google Cloud Console -> OAuth consent screen -> PUBLISH APP.")


def _check_channel(g: str) -> None:
    """The two-account trap: authorising as the app owner only 401s at upload time."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as e:
        record(g, SKIP, "Token points at your channel",
               f"Dependency missing ({e.name}). Fix: pip install -r requirements.txt")
        return

    # Must match auth.publish_youtube.SCOPES exactly.
    scopes = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
    ]
    try:
        creds = Credentials.from_authorized_user_file(str(YOUTUBE_TOKEN), scopes)
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
        items = yt.channels().list(part="id,snippet", mine=True).execute().get("items", [])
    except Exception as e:  # network, auth, quota — report, never crash
        record(g, WARN, "Token points at your channel",
               f"Could not verify against the API: {type(e).__name__}: {str(e)[:160]}")
        return

    if not items:
        record(g, FAIL, "Token points at your channel",
               "The token authenticates but owns ZERO channels. Uploads will fail with\n"
               "    401 youtubeSignupRequired — an error that never mentions accounts, which is what\n"
               "    makes it expensive to debug. You authorised as the wrong Google account.\n"
               "    Fix: delete profiles/youtube/token.json, re-run setup, sign in as the CHANNEL OWNER.")
    else:
        snippet = items[0].get("snippet", {})
        record(g, PASS, "Token points at your channel",
               f"{snippet.get('title', '?')} ({items[0].get('id')})"
               " — confirm that is the channel you publish to.")


# ---------------------------------------------------------------- media tooling

def check_media() -> None:
    g = "media"
    exe = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not exe:
        record(g, WARN, "ffmpeg available",
               "Not found. Only needed to inspect or convert video before posting — checking a reel's\n"
               "    first frame is not black, or building a vertical cut. Publishing works without it.")
        return
    record(g, PASS, "ffmpeg available", exe)
    if not (shutil.which("ffprobe") or shutil.which("ffprobe.exe")):
        record(g, WARN, "ffprobe available", "ffmpeg is present but ffprobe is not.")


# ---------------------------------------------------------------- repo hygiene

def check_repo() -> None:
    g = "repo"

    rc, _ = run(["git", "-C", str(REPO_ROOT), "rev-parse", "--git-dir"])
    if rc != 0:
        record(g, SKIP, "Secrets are ignored by git", "Not a git repository.")
        return

    # profiles/ holds live logged-in cookies and the YouTube token. Committing it would
    # hand over the accounts themselves.
    rc, out = run(["git", "-C", str(REPO_ROOT), "ls-files", "profiles"])
    tracked = [ln for ln in out.splitlines() if ln.strip()]
    if tracked:
        record(g, FAIL, "Session data is not committed",
               f"{len(tracked)} file(s) under profiles/ are TRACKED BY GIT. That directory holds live\n"
               "    login cookies and your YouTube token — committing it hands over the accounts.\n"
               "    Fix: git rm -r --cached profiles, confirm profiles/ is in .gitignore, and treat\n"
               "    those sessions as compromised (sign out everywhere, re-run the login wizard).\n"
               "    Note: removing a file from the tree does NOT remove it from history.")
    else:
        record(g, PASS, "Session data is not committed", "profiles/ is not tracked.")

    for name in (".env", "client_secret.json", "credentials.json"):
        p = REPO_ROOT / name
        if not p.exists():
            continue
        rc, _ = run(["git", "-C", str(REPO_ROOT), "ls-files", "--error-unmatch", name])
        if rc == 0:
            record(g, FAIL, f"{name} not committed",
                   f"{name} is tracked by git and carries credentials. Untrack it and rotate them.")


# ---------------------------------------------------------------- output

GROUPS = {"sessions": check_sessions, "youtube": check_youtube,
          "media": check_media, "repo": check_repo}


def main() -> int:
    # Windows consoles often default to a legacy codepage (cp1252) that cannot
    # encode the em dashes used throughout this file's output, rendering them
    # as "?" or "" instead of erroring outright. Force UTF-8 so the output is
    # legible everywhere, matching the encoding="utf-8" fix already applied to
    # subprocess calls in auth/chrome_setup.py for the same underlying reason.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in GROUPS:
        ap.add_argument(f"--{name}", action="store_true", help=f"run only the {name} checks")
    ap.add_argument("--quiet", action="store_true", help="show only warnings and failures")
    args = ap.parse_args()

    chosen = [n for n in GROUPS if getattr(args, n)] or list(GROUPS)
    for name in chosen:
        try:
            GROUPS[name]()
        except Exception as e:  # a broken check must not hide the others
            record(name, WARN, f"{name} checks incomplete", f"{type(e).__name__}: {e}")

    width = max((len(t) for _, _, t, _ in results), default=0)
    current = None
    for group, status, title, detail in results:
        if status == PASS and args.quiet:
            continue
        if group != current:
            print(f"\n{group.upper()}")
            current = group
        first = detail.splitlines()[0] if detail else ""
        print(f"  {_MARK[status]} {title.ljust(width)}" + (f"   {first}" if first else ""))
        for line in detail.splitlines()[1:]:
            print(f"         {line}")

    n_fail = sum(1 for _, s, _, _ in results if s == FAIL)
    n_warn = sum(1 for _, s, _, _ in results if s == WARN)
    n_pass = sum(1 for _, s, _, _ in results if s == PASS)

    # The number of checks that run is NOT fixed -- it depends on what's
    # already connected (e.g. a fresh clone with nothing set up sees far
    # fewer checks than a fully-connected one, since per-platform checks
    # like "token points at your channel" only exist once there's a token to
    # check). Always state the total alongside the breakdown so a first-run
    # agent or user can tell "5 checks, none of them failures" apart from
    # "5 of some larger unstated total, might be missing checks."
    print(f"\n{len(results)} checks run: {n_pass} passed, {n_warn} warning(s), {n_fail} failure(s).")
    if n_fail:
        print("Fix the failures above before publishing — each one has a concrete next step.")
    elif n_warn:
        print("Nothing blocking. Warnings are worth reading before you rely on this.")
    else:
        print("Setup looks good.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
