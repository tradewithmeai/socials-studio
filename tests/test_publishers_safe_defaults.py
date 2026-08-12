"""Unit tests covering the browser-based publishers' safe-by-default behavior.

No credentials, browser profiles, network access, or live accounts anywhere in this file.
`sync_playwright` and `ensure_chrome_installed` are patched in every test so that even a
regression in the safety gate could never launch a real browser -- the assertion is not just
"the function returned a dry-run dict," it's "the thing that would launch a browser was never
even called."
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from auth.publish_bluesky import publish_bluesky
from auth.publish_instagram import publish_instagram
from auth.publish_linkedin import publish_linkedin
from auth.publish_x import publish_x

# (module path for patching, callable, args-builder given a valid media path)
# publish_instagram takes the media path positionally; the others take post text positionally
# with media as an optional keyword.
TEXT_PUBLISHERS = [
    ("auth.publish_x", publish_x, "x"),
    ("auth.publish_bluesky", publish_bluesky, "bluesky"),
    ("auth.publish_linkedin", publish_linkedin, "linkedin"),
]


@pytest.fixture
def no_browser(monkeypatch):
    """Patch sync_playwright and ensure_chrome_installed everywhere they're imported, and
    return the mocks so a test can assert they were never called."""
    mocks = {}
    for mod_path in ("auth.publish_x", "auth.publish_bluesky", "auth.publish_linkedin", "auth.publish_instagram"):
        sp = MagicMock(name=f"{mod_path}.sync_playwright")
        ec = MagicMock(name=f"{mod_path}.ensure_chrome_installed")
        monkeypatch.setattr(f"{mod_path}.sync_playwright", sp, raising=False)
        monkeypatch.setattr(f"{mod_path}.ensure_chrome_installed", ec, raising=False)
        mocks[mod_path] = {"sync_playwright": sp, "ensure_chrome_installed": ec}
    return mocks


@pytest.mark.parametrize("mod_path,fn,platform", TEXT_PUBLISHERS)
def test_default_call_is_dry_run_and_touches_no_browser(no_browser, mod_path, fn, platform):
    result = fn("hello world")
    assert result["dry_run"] is True
    assert result["platform"] == platform
    no_browser[mod_path]["sync_playwright"].assert_not_called()
    no_browser[mod_path]["ensure_chrome_installed"].assert_not_called()


@pytest.mark.parametrize("mod_path,fn,platform", TEXT_PUBLISHERS)
def test_explicit_dry_run_touches_no_browser(no_browser, mod_path, fn, platform):
    result = fn("hello world", dry_run=True)
    assert result["dry_run"] is True
    no_browser[mod_path]["sync_playwright"].assert_not_called()


@pytest.mark.parametrize("mod_path,fn,platform", TEXT_PUBLISHERS)
def test_dry_run_wins_over_confirm_publish(no_browser, mod_path, fn, platform):
    """Passing both flags together must never publish -- dry_run is the override."""
    result = fn("hello world", dry_run=True, confirm_publish=True)
    assert result["dry_run"] is True
    no_browser[mod_path]["sync_playwright"].assert_not_called()


@pytest.mark.parametrize("mod_path,fn,platform", TEXT_PUBLISHERS)
def test_confirm_publish_without_session_fails_safe_before_touching_browser(no_browser, mod_path, fn, platform):
    """confirm_publish=True with no saved session must raise before ever reaching
    sync_playwright -- there's nothing to publish to, so it should fail fast, not launch
    a browser and then fail."""
    with patch(f"{mod_path}.PROFILES_DIR") as fake_profiles_dir:
        fake_profiles_dir.__truediv__.return_value.exists.return_value = False
        with pytest.raises(SystemExit):
            fn("hello world", confirm_publish=True)
    no_browser[mod_path]["sync_playwright"].assert_not_called()


@pytest.mark.parametrize("mod_path,fn,platform", TEXT_PUBLISHERS)
def test_empty_text_rejected_regardless_of_flags(no_browser, mod_path, fn, platform):
    with pytest.raises(SystemExit):
        fn("   ")
    with pytest.raises(SystemExit):
        fn("   ", confirm_publish=True)


@pytest.mark.parametrize("mod_path,fn,platform", TEXT_PUBLISHERS)
def test_mutually_exclusive_video_and_image(no_browser, mod_path, fn, platform, tmp_path):
    video = tmp_path / "clip.mp4"
    image = tmp_path / "photo.jpg"
    video.write_bytes(b"not a real video, just needs to exist")
    image.write_bytes(b"not a real image, just needs to exist")
    with pytest.raises(SystemExit):
        fn("hello world", video_path=str(video), image_path=str(image))


@pytest.mark.parametrize("mod_path,fn,platform", TEXT_PUBLISHERS)
def test_missing_media_path_rejected(no_browser, mod_path, fn, platform, tmp_path):
    missing = tmp_path / "does_not_exist.mp4"
    with pytest.raises(SystemExit):
        fn("hello world", video_path=str(missing))


# --- Instagram: media path is positional and required, not optional like the text platforms ---


def test_instagram_default_call_is_dry_run_and_touches_no_browser(no_browser, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    result = publish_instagram(str(video))
    assert result["dry_run"] is True
    assert result["platform"] == "instagram"
    no_browser["auth.publish_instagram"]["sync_playwright"].assert_not_called()


def test_instagram_dry_run_wins_over_confirm_publish(no_browser, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    result = publish_instagram(str(video), dry_run=True, confirm_publish=True)
    assert result["dry_run"] is True
    no_browser["auth.publish_instagram"]["sync_playwright"].assert_not_called()


def test_instagram_missing_media_path_rejected(no_browser, tmp_path):
    missing = tmp_path / "does_not_exist.mp4"
    with pytest.raises(SystemExit):
        publish_instagram(str(missing))


def test_instagram_confirm_publish_without_session_fails_safe(no_browser, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    with patch("auth.publish_instagram.PROFILES_DIR") as fake_profiles_dir:
        fake_profiles_dir.__truediv__.return_value.exists.return_value = False
        with pytest.raises(SystemExit):
            publish_instagram(str(video), confirm_publish=True)
    no_browser["auth.publish_instagram"]["sync_playwright"].assert_not_called()
