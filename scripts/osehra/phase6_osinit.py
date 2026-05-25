#!/usr/bin/env python3
"""Phase 6 -- device interface init + FileMan re-init (spec v3 §7 Phase 6).

Was ``01_osinit.py``. Sets the TELNET/TRM device $I entries and the MPI local
site number, then runs DINIT (MUMPS OPERATING SYSTEM -> CACHE) + ^ZUSET.
(``^ZTMGRSET`` system-type setup already ran in Phase 5.)

Run via: ``python -m osehra osinit``.
"""
from . import config, session, state, steps_osinit
from .helper import PROMPT

NAME = "osinit"


def run():
    V = session.connect_with_retry("phase6_osinit.log")
    if state.phase_done(V, NAME):
        print("[phase6] OS-interface init already done -- skipping")
        session.release(V)
        return

    # --- Device file: set $I for the TELNET and TRM console devices ---
    V.write('S DUZ=1')
    V.wait(PROMPT)
    V.write('D Q^DI')
    V.wait('Select OPTION:')
    V.write('1')
    V.wait_re('INPUT TO WHAT FILE')
    V.write('DEVICE')
    V.wait('EDIT WHICH FIELD')
    V.write('$I')
    V.wait('THEN EDIT FIELD:')
    V.write('')
    V.wait('Select DEVICE NAME:')
    V.write('TELNET')
    V.wait('CHOOSE 1-2:')
    V.write('1')
    V.wait('$I: ')
    V.write('|TNT|')
    V.wait('Select DEVICE NAME:')
    V.write('TRM')
    V.wait('$I: ')
    V.write('|TRM|:|')
    V.wait('Select DEVICE NAME:')
    V.write('')
    V.wait('Select OPTION:')
    V.write('')

    # --- MPI local site number ---
    steps_osinit.addMPILocalNumber(V)

    # --- FileMan re-init + OS routine rename (DINIT + ZUSET) ---
    V.wait(PROMPT)
    steps_osinit.initializeFileman(V, config.DOMAIN, config.SITE_NUMBER)

    V.wait(PROMPT)
    state.mark_done(V, NAME)
    session.release(V)
