"""Unit tests for YouTube-specific publishing behavior: visibility validation, the Made for
Kids declaration, the required upload-terms acknowledgment, and OAuth scope minimization.

No credentials, browser profiles, network access, or live accounts anywhere in this file.
"""
from __future__ import annotations

import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from auth.publish_youtube import SCOPES, UPLOAD_TERMS_NOTICE, publish_youtube


@pytest.fixture
def no_api(monkeypatch):
    """Patch _load_credentials so any test that regresses past the safety/compliance gates
    would fail loudly (a call here means credentials were loaded, which means an API call
    was about to happen) instead of silently trying real network I/O."""
    mock = MagicMock(name="_load_credentials", side_effect=AssertionError(
        "credentials were loaded -- this should not happen for a validate-only call"
    ))
    monkeypatch.setattr("auth.publish_youtube._load_credentials", mock, raising=False)
    return mock


def test_default_call_is_dry_run_and_touches_no_api(no_api, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    result = publish_youtube(str(video), title="t")
    assert result["dry_run"] is True
    assert result["platform"] == "youtube"
    no_api.assert_not_called()


def test_dry_run_wins_over_confirm_publish(no_api, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    result = publish_youtube(str(video), title="t", dry_run=True, confirm_publish=True)
    assert result["dry_run"] is True
    no_api.assert_not_called()


def test_invalid_visibility_rejected(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    with pytest.raises(SystemExit):
        publish_youtube(str(video), title="t", visibility="bogus")


def test_missing_video_path_rejected():
    with pytest.raises(SystemExit):
        publish_youtube("does_not_exist.mp4", title="t")


def test_real_publish_requires_upload_terms_acknowledgment(no_api, tmp_path):
    """confirm_publish=True alone must not be enough -- the YouTube-specific requirement is
    separate and enforced before credentials are ever loaded."""
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    with pytest.raises(SystemExit, match="acknowledge-upload-terms"):
        publish_youtube(str(video), title="t", confirm_publish=True)
    no_api.assert_not_called()


def test_real_publish_requires_made_for_kids_declaration(no_api, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    with pytest.raises(SystemExit, match="made-for-kids"):
        publish_youtube(
            str(video), title="t", confirm_publish=True, acknowledge_upload_terms=True
        )
    no_api.assert_not_called()


def test_dry_run_never_requires_made_for_kids_or_upload_terms(no_api, tmp_path):
    """A dry run validates inputs; it must never fail on the two real-upload-only
    requirements, since it never gets far enough to need them."""
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    result = publish_youtube(str(video), title="t")  # no made_for_kids, no ack, no confirm
    assert result["dry_run"] is True


def test_upload_terms_notice_matches_required_wording():
    """The exact wording required by the YouTube API Services Terms of Service, Section
    9.1(i). If this drifts, it needs to be a deliberate, reviewed change -- not a typo."""
    assert "By clicking 'upload,'" in UPLOAD_TERMS_NOTICE
    assert "https://www.youtube.com/t/terms" in UPLOAD_TERMS_NOTICE
    assert "copyright" in UPLOAD_TERMS_NOTICE
    assert "privacy" in UPLOAD_TERMS_NOTICE


def test_notice_is_printed_even_when_ack_already_supplied(no_api, tmp_path, capsys):
    """The notice must not be something the flag merely suppresses -- it has to actually
    appear in this run's own output even when --acknowledge-upload-terms (or
    acknowledge_upload_terms=True) is already set on the very first call, not just on a
    prior failed attempt. Verified by capturing real stdout, not by reading the exception
    message."""
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    with pytest.raises(AssertionError):  # _load_credentials mock fires once past both gates
        publish_youtube(
            str(video),
            title="t",
            confirm_publish=True,
            acknowledge_upload_terms=True,
            made_for_kids=False,
        )
    captured = capsys.readouterr()
    assert UPLOAD_TERMS_NOTICE in captured.out


def test_notice_is_printed_before_the_made_for_kids_check_too(no_api, tmp_path, capsys):
    """Even if made_for_kids is still missing, the notice must already have been printed --
    ordering matters: show the notice first, then gate on acknowledgment and declaration."""
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    with pytest.raises(SystemExit, match="made-for-kids"):
        publish_youtube(
            str(video), title="t", confirm_publish=True, acknowledge_upload_terms=True
        )
    captured = capsys.readouterr()
    assert UPLOAD_TERMS_NOTICE in captured.out


def test_cli_made_for_kids_flags_are_mutually_exclusive():
    """--made-for-kids and --not-made-for-kids together must be rejected by argparse itself
    -- exactly one, never both, never inferred. Run as a real subprocess so this exercises
    the actual CLI parser, not a hand-rolled copy of it."""
    result = subprocess.run(
        [sys.executable, "-m", "auth.publish_youtube", "nonexistent.mp4",
         "--title", "t", "--made-for-kids", "--not-made-for-kids"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "not allowed with argument" in result.stderr


def test_cli_made_for_kids_and_not_made_for_kids_each_work_standalone():
    """Each flag alone must parse cleanly (still hits the missing-file check downstream,
    which is fine -- this only verifies the flags themselves parse and resolve correctly)."""
    for flag, expect_snippet in (("--made-for-kids", "not found"), ("--not-made-for-kids", "not found")):
        result = subprocess.run(
            [sys.executable, "-m", "auth.publish_youtube", "nonexistent.mp4", "--title", "t", flag],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert expect_snippet in result.stdout + result.stderr


def test_scopes_are_minimal():
    """Only the scopes publishing and doctor.py's channel check actually use -- the broad
    manage scope must not be requested. See CHANGELOG.md / PRIVACY.md for why."""
    assert set(SCOPES) == {
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
    }
    assert "https://www.googleapis.com/auth/youtube" not in SCOPES


def test_setup_oauth_scopes_match_publish_scopes():
    """auth.setup_youtube_oauth.SCOPES must match auth.publish_youtube.SCOPES exactly, or
    token refresh raises a 'scope has changed' error -- this is a real, documented failure
    mode, not a style preference."""
    from auth.setup_youtube_oauth import SCOPES as setup_scopes

    assert setup_scopes == SCOPES


def test_doctor_channel_check_scopes_match_publish_scopes():
    """doctor.py's channel-verification call must request the same scopes as the real
    publisher, or it can misreport whether a token will actually work. Checked by source
    inspection rather than invocation, since the Google client imports are local to the
    function (not module-level names) and there's no real token to check against here."""
    import inspect

    import doctor

    source = inspect.getsource(doctor._check_channel)
    assert "https://www.googleapis.com/auth/youtube.upload" in source
    assert "https://www.googleapis.com/auth/youtube.readonly" in source
    # The broad manage scope (bare ".../auth/youtube", no suffix) must not appear as its own
    # scope entry -- only as a substring of the two narrower scopes above.
    without_narrow_scopes = source.replace(
        "https://www.googleapis.com/auth/youtube.upload", ""
    ).replace("https://www.googleapis.com/auth/youtube.readonly", "")
    assert "https://www.googleapis.com/auth/youtube\"" not in without_narrow_scopes
