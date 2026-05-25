"""Phase 6 (OS-interface init) steps -- verbatim from the former ``setup.py``.

The MPI local site number and the FileMan re-init (``^DINIT`` -> MUMPS OPERATING
SYSTEM = CACHE, + ``^ZUSET``). ``^ZTMGRSET`` system-type setup already ran in
Phase 5 (the two coexist; spec v3 §7 Phase 6 reconciliation).
"""
import re

from .helper import PROMPT
from .steps_fileman import startFileman


def addMPILocalNumber(VistA):
    VistA.wait(PROMPT)
    VistA.write("W $$SITE^VASITE($$DT^XLFDT)")
    VistA.wait(PROMPT)
    localNum = re.search(r"\^([0-9]+)\W", VistA.lastconnection).groups()[0]
    VistA.write("")
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('MASTER PATIENT INDEX (LOCAL')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('')
    VistA.wait('MASTER PATIENT INDEX (LOCAL')
    VistA.write('`1')
    VistA.wait('SITE ID NUMBER')
    VistA.write(localNum)
    VistA.wait('LAST NUMBER')
    VistA.write('^')
    VistA.wait('MASTER PATIENT INDEX (LOCAL')
    VistA.write('')
    VistA.wait('Select OPTION:')
    VistA.write('')


def initializeFileman(VistA, site_name, site_number):
    # Initialize FileMan (DINIT) and set the MUMPS OPERATING SYSTEM to CACHE
    # (the Cache-compatible interface IRIS presents). ^ZUSET renames the ZU*
    # routines. (^ZTMGRSET system-type setup already ran in Phase 5.)
    VistA.write('D ^DINIT')
    VistA.wait('Initialize VA FileMan now?')
    VistA.write('Yes')
    VistA.wait('SITE NAME:')
    VistA.write(site_name)
    VistA.wait('SITE NUMBER')
    VistA.write(site_number)
    VistA.wait('Do you want to change the MUMPS OPERATING SYSTEM File?')
    VistA.write('Yes')
    VistA.wait('TYPE OF MUMPS SYSTEM YOU ARE USING')
    VistA.write('CACHE')
    VistA.wait(PROMPT, 60)
    VistA.write('D ^ZUSET')
    VistA.wait('Rename')
    VistA.write('Yes')
