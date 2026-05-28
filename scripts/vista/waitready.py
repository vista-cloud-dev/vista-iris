#!/usr/bin/env python3
"""Readiness gate (pre-Phase 6) -- wait until the VISTA database is writable.

Run via ``python -m vista waitready`` immediately after ``iris start ... quietly``
and before the interactive phases. ``iris start`` may return while the database
is still mounting/recovering (read-only for a beat); the first FileMan write in
Phase 6 then hits ``<PROTECT>`` and the install dies (observed in CI). This gate
blocks on a write probe until the database accepts it, so the phases that follow
never race a cold mount. Idempotent and safe to re-run.
"""
from . import session

NAME = "waitready"


def run():
    with session.open_session("waitready.log") as v:
        session.wait_until_writable(v)
    print("[waitready] VISTA database is writable")
