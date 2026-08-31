"""Unit tests for TikTok-specific publishing behavior: visibility/privacy-level mapping, the
unaudited-app notice, and OAuth scope consistency between setup and publish.

No credentials, browser profiles, network access, or live accounts anywhere in this file.
"""
from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import MagicMock

import pytest

from auth.publish_tiktok import (
    MAX_CHUNK_SIZE,
    MIN_CHUNK_SIZE,
    SCOPES,
    UNAUDITED_APP_NOTICE,
    UNAUDITED_PRIVATE_ACCOUNT_REQUIRED_CODE,
    VALID_VISIBILITY,
    VISIBILITY_TO_PRIVACY_LEVEL,
    _api_post_json,
    _compute_chunking,
    check_publish_status,
    publish_tiktok,
)


@pytest.fixture
def no_api(monkeypatch):
    """Patch _load_token so any test that regresses past the safety gate would fail loudly (a
    call here means a token was about to be loaded, which means an API call was about to
    happen) instead of silently trying real network I/O."""
    mock = MagicMock(name="_load_token", side_effect=AssertionError(
        "a token was loaded -- this should not happen for a validate-only call"
    ))
    monkeypatch.setattr("auth.publish_tiktok._load_token", mock, raising=False)
    return mock


def test_default_call_is_dry_run_and_touches_no_api(no_api, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    result = publish_tiktok(str(video), title="t")
    assert result["dry_run"] is True
    assert result["platform"] == "tiktok"
    no_api.assert_not_called()


def test_dry_run_wins_over_confirm_publish(no_api, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    result = publish_tiktok(str(video), title="t", dry_run=True, confirm_publish=True)
    assert result["dry_run"] is True
    no_api.assert_not_called()


def test_invalid_visibility_rejected(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    with pytest.raises(SystemExit):
        publish_tiktok(str(video), title="t", visibility="bogus")


def test_missing_video_path_rejected():
    with pytest.raises(SystemExit):
        publish_tiktok("does_not_exist.mp4", title="t")


def test_visibility_maps_to_correct_privacy_levels():
    """Every friendly --visibility value must map to a real TikTok privacy_level, and the
    default must be the most restrictive one -- matching what an unaudited app is forced to
    anyway, and the "default to private" convention every other publisher here follows."""
    assert VISIBILITY_TO_PRIVACY_LEVEL == {
        "private": "SELF_ONLY",
        "followers": "FOLLOWER_OF_CREATOR",
        "friends": "MUTUAL_FOLLOW_FRIENDS",
        "public": "PUBLIC_TO_EVERYONE",
    }
    assert VALID_VISIBILITY == set(VISIBILITY_TO_PRIVACY_LEVEL)


def test_dry_run_result_includes_privacy_level_and_unaudited_note(no_api, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    result = publish_tiktok(str(video), title="t", visibility="public")
    assert result["privacy_level"] == "PUBLIC_TO_EVERYONE"
    assert "unaudited" in result["message"].lower() or "audit" in result["message"].lower()


def test_notice_is_printed_before_token_is_loaded(no_api, tmp_path, capsys):
    """The unaudited-app notice must actually appear in this run's own output on every
    real-publish attempt, before a token is ever loaded -- verified by capturing real stdout,
    not by reading an exception message. Mirrors auth.publish_youtube's equivalent test."""
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a real video, just needs to exist")
    with pytest.raises(AssertionError):  # _load_token mock fires once past the safety gate
        publish_tiktok(str(video), title="t", confirm_publish=True)
    captured = capsys.readouterr()
    assert UNAUDITED_APP_NOTICE in captured.out


def test_scopes_are_minimal():
    """Only video.publish is requested -- no broader TikTok scope than publishing needs."""
    assert SCOPES == ["video.publish"]


def test_setup_oauth_scopes_match_publish_scopes():
    from auth.setup_tiktok_oauth import SCOPES as setup_scopes

    assert setup_scopes == SCOPES


def test_small_video_is_always_a_single_chunk():
    """Regression test for a live 400 ("the total chunk count is invalid") caused by chunking a
    video under TikTok's 64 MiB single-chunk threshold. Even if a caller passes a tiny chunk_size,
    a video at or under MAX_CHUNK_SIZE must still come back as exactly one chunk."""
    small_size = 15 * 1024 * 1024  # 15 MiB -- comfortably under the 64 MiB threshold
    effective_chunk, total_chunk_count = _compute_chunking(small_size, chunk_size=1024 * 1024)
    assert total_chunk_count == 1
    assert effective_chunk == small_size


def test_video_exactly_at_threshold_is_a_single_chunk():
    effective_chunk, total_chunk_count = _compute_chunking(MAX_CHUNK_SIZE, chunk_size=MAX_CHUNK_SIZE)
    assert total_chunk_count == 1
    assert effective_chunk == MAX_CHUNK_SIZE


def test_large_video_is_split_into_clamped_chunks():
    large_size = MAX_CHUNK_SIZE * 3 + 1  # just over 3 full chunks
    effective_chunk, total_chunk_count = _compute_chunking(large_size, chunk_size=MAX_CHUNK_SIZE)
    assert effective_chunk == MAX_CHUNK_SIZE
    assert total_chunk_count == 4  # 3 full chunks + a small remainder chunk
    assert (total_chunk_count - 1) * effective_chunk < large_size <= total_chunk_count * effective_chunk


def test_large_video_chunk_size_is_clamped_between_min_and_max():
    large_size = MAX_CHUNK_SIZE * 2
    # a chunk_size below MIN_CHUNK_SIZE must be clamped up, not honored as-is
    effective_chunk, _ = _compute_chunking(large_size, chunk_size=1024)
    assert effective_chunk == MIN_CHUNK_SIZE
    # a chunk_size above MAX_CHUNK_SIZE must be clamped down, not honored as-is
    effective_chunk, _ = _compute_chunking(large_size, chunk_size=MAX_CHUNK_SIZE * 10)
    assert effective_chunk == MAX_CHUNK_SIZE


def test_unaudited_private_account_error_is_explained(monkeypatch):
    """Regression test for a live 403 (unaudited_client_can_only_post_to_private_accounts):
    confirmed 2026-08-17 that an unaudited app can only publish at all when the connected TikTok
    account is set to Private -- this must surface as an actionable message, not a raw JSON dump,
    and must not touch the network (urlopen is mocked)."""
    body = json.dumps(
        {"error": {"code": UNAUDITED_PRIVATE_ACCOUNT_REQUIRED_CODE, "message": "..."}}
    ).encode("utf-8")

    def fake_urlopen(req, timeout=30):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", hdrs=None, fp=io.BytesIO(body))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    with pytest.raises(RuntimeError) as exc_info:
        _api_post_json("https://open.tiktokapis.com/v2/post/publish/video/init/", "token", {})

    message = str(exc_info.value)
    assert "Private account" in message or "private" in message.lower()
    assert "Settings and privacy" in message


def test_check_publish_status_wires_token_and_publish_id_through(monkeypatch):
    """Regression test for a real publish_id that came back 'PROCESSING_UPLOAD' right after
    upload (a transient state) and never actually appeared in the TikTok app -- the original code
    only ever checked status once, immediately post-upload, with no way to check again later.
    check_publish_status must load the current token and query STATUS_FETCH_URL with exactly the
    given publish_id, returning whatever TikTok's API reports right now."""
    fake_token = {"access_token": "tok123"}
    monkeypatch.setattr("auth.publish_tiktok._load_token", lambda: fake_token)
    monkeypatch.setattr("auth.publish_tiktok._refresh_token_if_needed", lambda t: t)

    captured = {}

    def fake_api_post_json(url, access_token, body):
        captured["url"] = url
        captured["access_token"] = access_token
        captured["body"] = body
        return {"data": {"status": "PUBLISH_COMPLETE"}, "error": {"code": "ok"}}

    monkeypatch.setattr("auth.publish_tiktok._api_post_json", fake_api_post_json)

    result = check_publish_status("v_pub_file~v2-1.example")

    assert result["publish_id"] == "v_pub_file~v2-1.example"
    assert result["status_response"]["data"]["status"] == "PUBLISH_COMPLETE"
    assert captured["access_token"] == "tok123"
    assert captured["body"] == {"publish_id": "v_pub_file~v2-1.example"}
    assert "status/fetch" in captured["url"]


def test_doctor_registers_tiktok_without_treating_it_as_a_browser_platform():
    """TikTok, like YouTube, uses OAuth + an API and never touches a browser profile -- it must
    not be listed alongside the Chrome-session platforms, but it must have its own check group."""
    import doctor

    assert "tiktok" not in doctor.BROWSER_PLATFORMS
    assert "tiktok" in doctor.GROUPS


def test_doctor_refreshes_token_before_checking_creator_info(monkeypatch, tmp_path):
    """Codex-reported regression: doctor.py's TikTok check used to send the stored access_token
    straight to TikTok's API without ever refreshing it first -- unlike auth.publish_tiktok
    itself, which always refreshes an expired token before a real call. A perfectly healthy,
    refreshable token would report "unreachable" here for the mundane reason that its short-lived
    access_token had simply expired, even though a real publish would have refreshed and
    succeeded. check_tiktok must call _refresh_token_if_needed before the creator-info check."""
    import doctor

    token_path = tmp_path / "token.json"
    stale_token = {
        "access_token": "stale",
        "refresh_token": "refresh-me",
        "scopes": ["video.publish"],
    }
    token_path.write_text(json.dumps(stale_token), encoding="utf-8")
    monkeypatch.setattr(doctor, "TIKTOK_TOKEN", token_path)
    monkeypatch.setattr(doctor, "REPO_ROOT", tmp_path)

    refreshed_token = {**stale_token, "access_token": "fresh"}
    refresh_mock = MagicMock(return_value=refreshed_token)
    monkeypatch.setattr("auth.publish_tiktok._refresh_token_if_needed", refresh_mock)

    creator_info_mock = MagicMock()
    monkeypatch.setattr(doctor, "_check_tiktok_creator_info", creator_info_mock)

    doctor.check_tiktok()

    refresh_mock.assert_called_once_with(stale_token)
    creator_info_mock.assert_called_once()
    # The (possibly refreshed) token, not the stale one straight off disk, must reach the
    # creator-info check.
    assert creator_info_mock.call_args[0][1] == refreshed_token
