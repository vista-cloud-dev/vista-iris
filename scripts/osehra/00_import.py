#!/usr/bin/env python3
"""Step 0 -- routine + global import and OS manager setup (spec v2 §8 steps 3-5).

Forked from OSEHRA RoutineImport.py.in + GlobalImport.py.in (cache path, which
is the correct one for IRIS). Imports routines.ro via `^%RI`, loads the globals
via `LIST^ZGI(globals.lst)`, then runs `^ZTMGRSET` choosing system type "3"
(= Cache (VMS, NT, Linux), OpenM-NT -- the Cache-compatible interface IRIS
presents) and renames the FileMan routines.

routines.ro / globals.lst are produced by prepare.py at build time.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
from helper import PROMPT  # noqa: E402

BUILD = os.environ.get("VISTA_BUILD_DIR", "/tmp/vista-build")
RO_FILE = os.path.join(BUILD, "routines.ro")
GLOBALS_LST = os.path.join(BUILD, "globals.lst")

V = config.connect("00_import.log")

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
V.write('h')
