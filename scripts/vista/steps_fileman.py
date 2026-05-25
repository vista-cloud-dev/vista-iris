"""Shared FileMan navigation primitives used by Phases 6, 7 and 8.

Verbatim from the former ``setup.py`` (cleaned IRIS-only WorldVistA fork) -- the
write/wait sequences are unchanged; only their home moved so each phase imports
exactly what it needs without pulling in a monolith.
"""
from .helper import PROMPT


def startFileman(VistA):
    # Start FileMan as the programmer user; XUMF=1 permits editing Kernel files.
    VistA.wait(PROMPT)
    VistA.write('S DUZ=1 S XUMF=1 D Q^DI')
    VistA.wait('Select OPTION:')


def reindexFile(VistA, fileNo):
    startFileman(VistA)
    VistA.write('UTILITY')
    VistA.wait('UTILITY OPTION')
    VistA.write('RE')
    VistA.wait_re('MODIFY WHAT FILE')
    VistA.write(fileNo)
    VistA.wait('PARTICULAR INDEX')
    VistA.write('NO')
    VistA.wait('EXISTING')
    VistA.write('Y')
    VistA.wait('RE-CROSS-REFERENCE')
    VistA.write('Y')
    index = VistA.multiwait(['UTILITY OPTION', 'Start Time'])
    if index == 1:
        VistA.write('')
        VistA.wait('UTILITY OPTION')
    VistA.write('')
    VistA.wait('Select OPTION')
    VistA.write('')
