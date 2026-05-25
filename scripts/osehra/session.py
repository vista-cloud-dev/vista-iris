"""Centralized connection discipline for the VistA install phases.

IRIS Community caps concurrent license-consuming processes (8 units; spec v3
§9.1). The install opens many short `iris session` connections, so two rules,
learned the hard way (log E8), are enforced here in ONE place and used by every
phase:

  1. **Release cleanly.** A session that has entered a menu must climb back to
     the programmer prompt, ``halt``, and wait for EOF so IRIS deregisters its
     license slot *synchronously*. Force-closing leaves the slot held and the
     next connect hits ``<LICENSE LIMIT EXCEEDED>``.
  2. **One connection at a time.** Open a connection, do the work, release it,
     then open the next -- never overlap.

Promoted from the former ``config.connect`` and ``03_sampledata.py``'s local
``_connect``/``_release`` so the discipline can't drift between phases. Use
:func:`open_session` (a context manager) so a phase can't forget to release.
"""
import contextlib
import os
import sys
import time

import pexpect

from . import config
from .helper import ConnectToMUMPS


def connect(logname):
    """Spawn an ``iris session``, sign in if prompted, and return at the prompt.

    A local ``iris session`` may drop straight to the namespace prompt (OS
    authentication) or ask for credentials, depending on IRIS security. After
    sign-in we emit a bare CR so exactly one fresh prompt is pending -- the
    OSEHRA steps assume each is entered at a prompt, and the first one is
    wait-first (harmless to write-first steps, whose next non-prompt match skips
    this extra prompt).
    """
    v = ConnectToMUMPS(os.path.join(config.LOG_DIR, logname),
                       config.INSTANCE, config.NAMESPACE)
    idx = v.multiwait(["Username:", v.prompt], 120)
    if idx == 0:
        v.write(config.USERNAME)
        v.wait("Password")
        v.write(config.PASSWORD)
        v.wait(v.prompt, 120)
    v.write("")
    return v


def connect_with_retry(logname, attempts=12, pause=15):
    """Connect, retrying through a transient ``<LICENSE LIMIT EXCEEDED>`` (E8).

    A just-released session takes a moment to free its license slot, so a fresh
    connect can transiently fail; retry with a pause until a slot frees up
    instead of aborting the build.
    """
    last = None
    for attempt in range(attempts):
        try:
            return connect(logname)
        except Exception as exc:  # noqa: BLE001 -- retry on any connect failure
            last = exc
            sys.stderr.write("connect retry %d for %s: %s\n"
                             % (attempt + 1, logname, exc))
            time.sleep(pause)
    raise last


def release(v):
    """Climb out of any menu, halt cleanly, and wait for EOF (frees the slot).

    Sends a burst of ``^`` to escape any menu/login back to the programmer
    prompt, then ``h`` to halt; waiting for EOF lets IRIS deregister the license
    synchronously. Bounded (no multiwait loop) so it can never hang the build;
    harmless at a bare programmer prompt (the stray ``^`` lines just re-prompt).
    """
    if v is None:
        return
    try:
        for _ in range(10):
            v.write("^")
        v.write("h")
        v.connection.expect(pexpect.EOF, timeout=25)
    except Exception:  # noqa: BLE001 -- release is best-effort
        pass
    try:
        v.connection.close(force=True)
    except Exception:  # noqa: BLE001
        pass
    time.sleep(3)


@contextlib.contextmanager
def open_session(logname):
    """Context manager: ``connect_with_retry`` on enter, ``release`` on exit.

    Open ONE at a time (Community license). Usage::

        with session.open_session("phase7.log") as v:
            ...drive the dialog with v...
    """
    v = connect_with_retry(logname)
    try:
        yield v
    finally:
        release(v)
