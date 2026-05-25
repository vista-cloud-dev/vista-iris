#!/usr/bin/env python3
"""Phase 5 -- routine + global import and OS manager setup (spec v3 §7 Phase 5).

Was ``00_import.py``. Imports ``routines.ro`` via ``^%RI``, loads the globals via
``LIST^ZGI(globals.lst)``, then runs ``^ZTMGRSET`` choosing system type 3
(= Cache (VMS, NT, Linux), OpenM-NT -- the Cache-compatible interface IRIS
presents) and renames the FileMan routines. routines.ro / globals.lst are
produced by ``prepare.py`` at build time.

This is the expensive, cached layer; the idempotency guard makes a re-run a safe
no-op so iterating later phases (or re-running standalone) never re-imports.
Run via: ``python -m vista import``.
"""
import os

from . import config, session, state
from .helper import PROMPT

BUILD = os.environ.get("VISTA_BUILD_DIR", "/tmp/vista-build")
RO_FILE = os.path.join(BUILD, "routines.ro")
GLOBALS_LST = os.path.join(BUILD, "globals.lst")

NAME = "import"


def run():
    V = session.connect("phase5_import.log")
    if state.phase_done(V, NAME):
        print("[phase5] routines/globals already imported -- skipping")
        session.release(V)
        return
    # The guard's last wait_re leaves a trailing unmatched prompt, exactly like
    # connect() does, so the write-first ^%RI sequence proceeds unchanged.

    # --- Routines: ^%RI reads the .ro transfer file ---
    V.write('D ^%RI')
    V.wait('Device:')
    V.write(RO_FILE)
    V.wait('"R" =>')
    V.write('')
    V.wait('No =>')
    V.write('YES')          # override existing routines
    V.wait('<0>')
    V.write('')
    V.wait('Routine Input Option:')
    V.write('All Routines')
    V.wait('No =>')
    V.write('YES')
    V.wait('Yes =>')
    V.write('')
    V.wait('Yes =>')
    V.write('')
    V.wait(PROMPT, 3600)    # the FOIA routine set is large

    # --- Globals: LIST^ZGI loads each .zwr listed in globals.lst (absolute paths) ---
    V.write('D LIST^ZGI("%s")' % GLOBALS_LST)
    V.wait(PROMPT, 3600)

    # --- OS manager setup: ^ZTMGRSET, system type 3 (Cache-compatible, IRIS) ---
    V.write('D ^ZTMGRSET')
    while True:
        idx = V.multiwait(['Should I continue?', 'System:'])
        if idx == 0:
            V.write('YES')
            continue
        break
    V.write('3')
    V.wait('NAME OF')
    V.write(config.NAMESPACE)
    V.wait('PRODUCTION')
    V.write(config.NAMESPACE)
    V.wait('NAME OF')
    V.write(config.NAMESPACE)
    V.wait('Want to rename the FileMan routines: No//')
    V.write('YES')
    V.wait(PROMPT, 300)
    state.mark_done(V, NAME)
    session.release(V)
