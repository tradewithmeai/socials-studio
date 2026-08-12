"""Unit tests for the shared safe-by-default gate (auth/publish_safety.py).

No credentials, browser profiles, network access, or live accounts anywhere in this file.
"""
from __future__ import annotations

from auth.publish_safety import NOT_PUBLISHED_NOTE, should_publish


def test_default_is_safe():
    """Neither flag given -> validate only."""
    assert should_publish(dry_run=False, confirm_publish=False) is False


def test_confirm_publish_alone_allows_real_action():
    assert should_publish(dry_run=False, confirm_publish=True) is True


def test_dry_run_alone_is_safe():
    assert should_publish(dry_run=True, confirm_publish=False) is False


def test_dry_run_wins_over_confirm_publish():
    """The one case that matters most: a caller can never accidentally force a real
    publish through code that still passes dry_run=True out of old habit, even if it
    also (mistakenly, or via some other code path) passes confirm_publish=True."""
    assert should_publish(dry_run=True, confirm_publish=True) is False


def test_not_published_note_is_non_empty_string():
    assert isinstance(NOT_PUBLISHED_NOTE, str)
    assert len(NOT_PUBLISHED_NOTE) > 0
