"""Regression checks for installer/windows/setup.iss.

Plain text assertions against the .iss source -- no Inno Setup compiler
required. Guards against the desktop-shortcut privilege bug found on the
first real Windows 11 hardware test of PR #7: PrivilegesRequired=lowest
means Setup never runs elevated, but {commondesktop} (the shared, all-users
desktop) can require administrator rights to write to -- confirmed live,
"IPersistFile::Save failed; code 0x80070005. Access is denied." targeting
"C:\\Users\\Public\\Desktop\\Socials Studio.lnk". {userdesktop} (the current
user's own desktop) never has that problem.

Also guards against a Codex-reported regression: setup.iss's MyAppVersion
(baked into the built .exe as its AppVersion) was left at "0.1.0-beta.3"
after v0.1.0-beta.4 was tagged and released, so the advertised beta.4
download would have installed and registered itself as beta.3 -- misleading
for version reporting and upgrade diagnosis. There's no single VERSION file
in this repo; the version string is repeated across a few files, so this
test cross-checks setup.iss against docs/index.html's machine-readable
JSON-LD softwareVersion field rather than introducing new shared state.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SETUP_ISS = (REPO_ROOT / "installer" / "windows" / "setup.iss").read_text(encoding="utf-8")
DOCS_INDEX_HTML = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")


def test_privileges_required_is_lowest():
    """A lowest-privilege install must never need an admin elevation prompt --
    this is the assumption every other check in this file depends on."""
    assert "PrivilegesRequired=lowest" in SETUP_ISS


def test_no_commondesktop_reference_in_any_run_entry():
    """{commondesktop} writes to the shared, all-users desktop, which can
    require administrator rights -- incompatible with
    PrivilegesRequired=lowest. Only the explanatory code comment may mention
    the token; no [Icons]/[Run] entry may use it as a real destination."""
    for line in SETUP_ISS.splitlines():
        stripped = line.strip()
        if stripped.startswith(";") or stripped.startswith("//"):
            continue
        assert "{commondesktop}" not in line, (
            f"Found a live (non-comment) {{commondesktop}} reference, which can "
            f"require admin rights under PrivilegesRequired=lowest: {line!r}"
        )


def test_desktop_shortcut_uses_userdesktop():
    """The optional desktop shortcut must target the current user's own
    desktop, not the shared public one."""
    assert r"{userdesktop}\Socials Studio" in SETUP_ISS


def test_desktop_shortcut_is_optional_and_targets_launch_bat():
    """The desktop shortcut entry must stay gated behind the optional
    `desktopicon` task, launch {app}\\launch.bat, and use {app} as its
    working directory -- unchanged behaviour, just a different destination."""
    icons_section = SETUP_ISS.split("[Icons]", 1)[1].split("[Tasks]", 1)[0]
    desktop_lines = [
        line
        for line in icons_section.splitlines()
        if r"{userdesktop}" in line and not line.strip().startswith(";")
    ]
    assert len(desktop_lines) == 1
    line = desktop_lines[0]
    assert r'Filename: "{app}\launch.bat"' in line
    assert r'WorkingDir: "{app}"' in line
    assert "Tasks: desktopicon" in line


def test_desktopicon_task_still_declared():
    """The `desktopicon` task itself (which makes the shortcut opt-in, not
    automatic) must still exist."""
    assert 'Name: "desktopicon"' in SETUP_ISS


def test_installer_version_matches_docs_index_software_version():
    """Regression test for the Codex-reported version-drift bug: setup.iss's
    MyAppVersion is baked into the built .exe's AppVersion (visible in
    Windows' Programs & Features / installer properties). If it isn't bumped
    alongside a release, the advertised binary silently installs and
    registers itself as an older version. docs/index.html's JSON-LD
    softwareVersion field is a machine-readable version marker already
    expected to track the current release, so cross-checking against it
    catches this drift without introducing a new shared VERSION file."""
    iss_match = re.search(r'#define MyAppVersion "([^"]+)"', SETUP_ISS)
    assert iss_match, "MyAppVersion not found in setup.iss"

    docs_match = re.search(r'"softwareVersion":\s*"([^"]+)"', DOCS_INDEX_HTML)
    assert docs_match, "softwareVersion not found in docs/index.html"

    assert iss_match.group(1) == docs_match.group(1), (
        f"installer/windows/setup.iss's MyAppVersion ({iss_match.group(1)!r}) does not match "
        f"docs/index.html's softwareVersion ({docs_match.group(1)!r}) -- the built Windows "
        "installer would install and register itself as the wrong version."
    )
