"""Lightweight consistency checks between what the code actually does and what the docs
claim it does. Not exhaustive -- these catch the specific regressions this hardening pass
was written to prevent (X quietly reappearing as "supported", the platform lists drifting
apart across files) without trying to parse markdown properly.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_login_wizard_list_includes_all_platforms():
    """auth.login_wizard's --list output is driven by auth.platforms' dormant flag -- this
    confirms no platform is currently marked dormant, so all five browser-session platforms
    (including X and the experimental Facebook extra) are on the CLI's own advertised list,
    not just a doc claim."""
    from auth.platforms import PLATFORMS

    dormant_keys = {key for key, cfg in PLATFORMS.items() if cfg.dormant}
    assert not dormant_keys, f"expected no dormant platforms, found: {dormant_keys}"

    # Simulate the same filter login_wizard.main() applies, without needing to invoke argparse.
    listed_keys = {key for key, cfg in PLATFORMS.items() if not cfg.dormant}
    assert listed_keys == {"instagram", "bluesky", "linkedin", "x", "facebook"}


def test_doctor_browser_platforms_includes_x():
    import doctor

    assert "x" in doctor.BROWSER_PLATFORMS


def test_readme_supported_platforms_table_includes_x():
    readme = _read("README.md")
    # Find the "Supported platforms" section's table specifically, not the whole file.
    section = readme.split("## Supported platforms", 1)[1].split("## Publishing safety", 1)[0]
    assert "X (Twitter)" in section


def test_roadmap_now_section_lists_x_as_shipped():
    """The 'Now' section must list X alongside the platforms that actually ship, the way
    "Login wizard: X, Bluesky, LinkedIn, Instagram" lists the real ones -- and must not carry
    stale "not presented as a supported platform" language."""
    roadmap = _read("ROADMAP.md")
    now_section = roadmap.split("## Now", 1)[1].split("## Next", 1)[0]
    assert re.search(r"(Login wizard|Publish):.*\bX\b", now_section)
    assert "not presented as a supported platform" not in now_section


def test_issue_templates_include_x():
    for name in ("bug_report.md", "beta_testing.md"):
        content = _read(f".github/ISSUE_TEMPLATE/{name}")
        assert re.search(r"\bX\b", content), name


def test_active_x_skills_exist():
    """X's onboarding, publishing, and troubleshooting guidance must be active, discoverable
    skills (directory + SKILL.md), not left as dormant, undiscoverable files."""
    onboard = REPO_ROOT / ".claude" / "skills" / "onboard-x" / "SKILL.md"
    publish = REPO_ROOT / ".claude" / "skills" / "publish-x" / "SKILL.md"
    assert onboard.is_file(), "onboard-x skill is missing"
    assert publish.is_file(), "publish-x skill is missing"
    assert "name: onboard-x" in onboard.read_text(encoding="utf-8")
    assert "name: publish-x" in publish.read_text(encoding="utf-8")

    troubleshooting = _read(".claude/skills/troubleshoot-publishing/SKILL.md")
    assert re.search(r"\bX\b", troubleshooting), "troubleshoot-publishing has no X recovery guidance"


def test_no_stale_x_dormant_claims():
    """No active, tracked doc should still claim X is unsupported or dormant -- these are the
    exact phrases that described the pre-correction state and must not survive it."""
    skip_dirs = {".claude/dormant", ".git", ".venv", "__pycache__", ".pytest_cache", "exported-docs"}
    stale_phrases = [
        "not presented as a supported platform",
        "dormant=True",
    ]
    hits = []
    for suffix in ("*.md", "*.py", "*.html"):
        for path in REPO_ROOT.rglob(suffix):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if any(rel.startswith(d) for d in skip_dirs) or path.name == Path(__file__).name:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for phrase in stale_phrases:
                if phrase in text:
                    hits.append(f"{rel}: contains {phrase!r}")
    assert not hits, "stale X-unsupported/dormant claims found:\n" + "\n".join(hits)


def test_privacy_and_security_docs_exist_and_are_linked_from_readme():
    assert (REPO_ROOT / "PRIVACY.md").is_file()
    assert (REPO_ROOT / "SECURITY.md").is_file()
    readme = _read("README.md")
    assert "PRIVACY.md" in readme
    assert "SECURITY.md" in readme


def test_changelog_exists_and_mentions_current_version():
    changelog = _read("CHANGELOG.md")
    assert "v0.1.0-beta.2" in changelog


def test_no_stale_made_for_kids_single_flag_syntax():
    """The real interface is two mutually exclusive flags, --made-for-kids /
    --not-made-for-kids -- never a single flag that takes a true/false value. That older
    single-flag form (`--made-for-kids {true,false}`, or `--made-for-kids false` as a literal
    value-taking example) was replaced everywhere once; this test is here so it can't quietly
    come back in a future doc edit or error message without failing CI.

    Scans every actively-shipped .md/.py/.html/.yml file (skips .claude/dormant/, which is
    deliberately preserved historical material, and this test file's own docstring/source)."""
    stale_patterns = [
        re.compile(r"--made-for-kids\s*\{true,false\}", re.IGNORECASE),
        re.compile(r"--made-for-kids\s+(true|false)\b", re.IGNORECASE),
        re.compile(r"made_for_kids\s*\{true,false\}", re.IGNORECASE),
    ]
    skip_dirs = {".claude/dormant", ".git", ".venv", "__pycache__", ".pytest_cache"}
    skip_files = {Path(__file__).name}
    hits = []
    for suffix in ("*.md", "*.py", "*.html", "*.yml", "*.yaml"):
        for path in REPO_ROOT.rglob(suffix):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if any(rel.startswith(d) for d in skip_dirs) or path.name in skip_files:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern in stale_patterns:
                if pattern.search(text):
                    hits.append(f"{rel}: matched {pattern.pattern}")
    assert not hits, "stale --made-for-kids {true,false} syntax found:\n" + "\n".join(hits)
