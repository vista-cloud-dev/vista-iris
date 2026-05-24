#!/usr/bin/env python3
"""Step 1 -- device interface init + FileMan re-init (spec v2 §8 step 5, post-import).

Forked from OSEHRA Initialize.py.in plus the OS-init head of
PostImportSetupScript.py.in. Sets the TELNET/TRM device $I entries and the MPI
local site number, then runs DINIT (MUMPS OPERATING SYSTEM -> CACHE) + ^ZUSET.
(`^ZTMGRSET` system-type setup already ran in 00_import.py.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import setup  # noqa: E402
from helper import PROMPT  # noqa: E402

V = config.connect("01_osinit.log")

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
setup.addMPILocalNumber(V)

# --- FileMan re-init + OS routine rename (DINIT + ZUSET) ---
V.wait(PROMPT)
setup.initializeFileman(V, config.SITE_NAME, config.SITE_NUMBER)

V.wait(PROMPT)
V.write('h')
