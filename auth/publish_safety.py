"""Shared safe-by-default gate for every publisher in this repo.

The problem this exists to fix: before this module, every `publish_<platform>.py` defaulted
`dry_run` to `False`. Calling the *library function* with no arguments beyond the required ones --
exactly what happens if any caller (a script, a test, an agent that forgot the flag) doesn't pass
`dry_run=True` explicitly -- published or uploaded for real, immediately, with no confirmation.
YouTube's `--visibility` defaulting to `private` did not fix this: private-by-default only matters
if you already remembered to make it a dry run in the first place.

The fix: publishing for real now requires an explicit, positive opt-in -- `confirm_publish=True`
in a library call, or `--confirm-publish` on the CLI. Everything else -- calling with no flags at
all, or passing `dry_run=True` -- validates only and touches no browser, no API, no network call
to a platform. `dry_run=True` always wins if both are passed, so there's no way to accidentally
force a real publish through a script that still passes `dry_run=True` out of old habit.

Every publisher module uses this the same way:

    from auth.publish_safety import should_publish

    def publish_thing(..., dry_run: bool = False, confirm_publish: bool = False) -> dict:
        do_publish = should_publish(dry_run=dry_run, confirm_publish=confirm_publish)
        ...
        if not do_publish:
            return {"dry_run": True, ...}
        ...  # the real thing, only reachable when do_publish is True
"""

from __future__ import annotations


def should_publish(*, dry_run: bool, confirm_publish: bool) -> bool:
    """True only when the caller explicitly asked for a real publish and did not also ask for
    a dry run. This is the one place that decision is made -- every publisher calls this instead
    of re-implementing the same `if dry_run: ... else: ...` logic five slightly different ways.
    """
    if dry_run:
        return False
    return bool(confirm_publish)


NOT_PUBLISHED_NOTE = (
    "No confirm_publish=True (or --confirm-publish on the CLI) was given, so this was a "
    "validate-only run by default -- nothing was launched, posted, or uploaded."
)
