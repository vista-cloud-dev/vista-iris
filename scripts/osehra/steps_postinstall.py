"""Phase 7 (post-install / site configuration) steps.

Verbatim from the former ``setup.py`` (cleaned IRIS-only OSEHRA fork): HFS dir,
resource-usage logging, intro text, device fixups, DOMAIN christening, box:volume
+ RPC Broker (XWB) listener port into #8994.1, volume set, TaskMan STARTUP
scheduling (as *dormant* config), re-index, CAPRI login, System Manager, and
institution/division/MAS parameters.

Two hard rules preserved from the original (spec v3 §7 Phase 7):
  * TaskMan is NOT cold-started here (``D ^ZTMB`` would spawn ~37 persistent
    processes and exhaust the 8-unit Community license -- log E16). The RPC
    Broker is started at boot by the ``%ZSTART`` hook (Phase 9), one process.
  * The HL7 ``#870`` MLLP listener is DEFERRED (``setupHL7Listener`` below is a
    clearly-marked, unverified stub and is not called -- log E7).
"""
import datetime
import time
from tempfile import gettempdir

from .helper import PROMPT
from .steps_fileman import reindexFile, startFileman

introText = """**************************************************
  *  Welcome to VistA
  **************************************************
  *
  * Use the following credentials for Robert Alexander
  *   Access:  fakedoc1
  *   Verify:  1Doc!@#$
  *   Electronic Signature: ROBA123
  *
  * Use the following credentials for Mary Smith (Nurse)
  *   Access:  fakenurse1
  *   Verify:  1Nur!@#$
  *   Electronic Signature: MARYS123
  *
  * Use the following credentials for Joe Clerk (Clerk)
  *   Access:  fakeclerk1
  *   Verify:  1Cle!@#$
  *   Electronic Signature: CLERKJ123
  *
  * This instance was built from VistA-M %s on %s
  * TEST SYSTEM -- fictitious data only, not for production or real PHI.
  **************************************************
"""


def setupPrimaryHFSDir(VistA, hfs_dir):
    # Set the PRIMARY HFS DIRECTORY in Kernel System Parameters.
    if hfs_dir == "@" or hfs_dir == '':
        hfs_dir = gettempdir()
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('KERNEL SYSTEM PARAMETERS')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('PRIMARY HFS DIRECTORY')
    VistA.wait('THEN EDIT FIELD')
    VistA.write('')
    VistA.wait('DOMAIN NAME')
    VistA.write('`1')
    VistA.wait('PRIMARY HFS DIRECTORY')
    VistA.write(hfs_dir.rstrip('/') or '/')
    index = VistA.multiwait(['SURE YOU WANT TO DELETE', 'DOMAIN NAME', 'PRIMARY HFS DIRECTORY'])
    if index == 0:
        VistA.write('Y')
        VistA.wait('DOMAIN NAME')
    if index == 2:
        VistA.write('')
        VistA.wait('DOMAIN NAME')
    VistA.write('')
    VistA.wait('Select OPTION:')
    VistA.write('')


def removeResourceUsageLogging(VistA):
    # Disable Resource Usage logging (VOLUME SET + Kernel System Parameters).
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('VOLUME SET')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('LINK ACCESS')
    VistA.wait('THEN EDIT FIELD')
    VistA.write('')
    VistA.wait('VOLUME SET')
    VistA.write('`1')
    VistA.wait('LINK ACCESS')
    VistA.write('NO')
    VistA.wait('VOLUME SET')
    VistA.write('')
    VistA.wait('Select OPTION:')
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('KERNEL SYSTEM PARAMETERS')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('LOG RESOURCE USAGE')
    VistA.wait('THEN EDIT FIELD')
    VistA.write('')
    VistA.wait('DOMAIN NAME')
    VistA.write('`1')
    VistA.wait('LOG RESOURCE USAGE')
    VistA.write('NO')
    VistA.wait('DOMAIN NAME')
    VistA.write('')
    VistA.wait('Select OPTION:')
    VistA.write('')


def setupIntroText(VistA, introTextSHA):
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('KERNEL SYSTEM PARAMETERS')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('INTRO MESSAGE')
    VistA.wait('THEN EDIT FIELD')
    VistA.write('')
    VistA.wait('DOMAIN NAME')
    VistA.write('`1')
    index = VistA.multiwait(['EDIT Option', '1>$'])
    if index == 0:
        VistA.write('D')
        VistA.wait('Delete from line')
        VistA.write('1')
        VistA.wait('thru')
        VistA.write('')
        VistA.wait('OK TO REMOVE')
        VistA.write('Y')
        VistA.wait('ARE YOU SURE')
        VistA.write('Y')
        VistA.wait('EDIT Option')
        VistA.write('A')
        VistA.wait('Add lines')
    VistA.write((introText % (introTextSHA, datetime.date.today())) + '\r')
    VistA.wait('EDIT Option')
    VistA.write('')
    VistA.wait('DOMAIN NAME')
    VistA.write('')
    VistA.wait('Select OPTION:')
    VistA.write('')


def configureNULLDevice(VistA):
    # Point the NULL device at the POSIX path and disable sign-on.
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('DEVICE')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('$I\rSIGN-ON/SYSTEM DEVICE\r')
    VistA.wait('NAME:')
    VistA.write('NULL\r1')
    VistA.wait('//')
    VistA.write('/dev/null\rNO\r')
    VistA.wait('Select OPTION')
    VistA.write('')


def configureConsoleDevice(VistA):
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('DEVICE')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('$I\rSIGN-ON/SYSTEM DEVICE\r')
    VistA.wait('NAME:')
    VistA.write('/dev/tty')
    VistA.wait('//')
    VistA.write('')
    VistA.wait('SYSTEM DEVICE')
    VistA.write('Y')
    index = VistA.multiwait(['SYSTEM DEVICE', 'DEVICE NAME'])
    if index == 0:
        VistA.write('^')
        VistA.wait('Select DEVICE')
    VistA.write('')
    VistA.wait('Select OPTION')
    VistA.write('')


def configureHFSDevice(VistA):
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('DEVICE')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('OPEN PARAMETERS')
    VistA.wait_re('then edit field')
    VistA.write('ASK PARAMETERS')
    VistA.wait_re('then edit field')
    VistA.write('SUBTYPE')
    VistA.wait_re('then edit field')
    VistA.write('')
    VistA.wait('NAME:')
    VistA.write('HFS')
    VistA.wait('OPEN PARAMETERS')
    VistA.write('"NWS"')
    VistA.wait('ASK PARAMETERS')
    VistA.write('1')
    VistA.wait('SUBTYPE')
    VistA.write('P-OTHER')
    index = VistA.multiwait(['CHOOSE', 'DEVICE NAME'])
    if index == 0:
        VistA.write('1')
        VistA.wait('Select DEVICE')
    VistA.write('')
    VistA.wait('Select OPTION')
    VistA.write('')


def setupVistADomain(VistA, site_name):
    # Add the site to the DOMAIN file, christen it, and point Kernel System
    # Parameters (#8989.3) + RPC Broker Site Parameters (#8994.1) at it.
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('DOMAIN\r')
    VistA.wait('Select DOMAIN NAME')
    VistA.write(site_name)
    index = VistA.multiwait(["Are you adding", "NAME"])
    if index == 0:
        VistA.write('Y')
    else:
        VistA.write('')
    VistA.wait('FLAGS')
    VistA.write('^\r\r')
    VistA.wait(PROMPT, 60)
    VistA.write('D CHRISTEN^XMUDCHR')
    VistA.wait('Are you sure you want to change the name of this facility?')
    VistA.write('Yes')
    VistA.wait('Select DOMAIN NAME')
    VistA.write(site_name)
    VistA.wait('PARENT')
    VistA.write('')
    VistA.wait('TIME ZONE')
    VistA.write(time.strftime('%Z').replace(' Time', ''))
    index = VistA.multiwait([VistA.prompt, 'TIME ZONE'])
    if index == 1:
        VistA.write('EST')
        VistA.wait(PROMPT, 60)
    VistA.IEN('DOMAIN', site_name)
    VistA.wait(PROMPT, 60)
    VistA.write('S $P(^XWB(8994.1,1,0),"^")=' + VistA.IENumber)
    VistA.write('S $P(^XTV(8989.3,1,0),"^")=' + VistA.IENumber)
    reindexFile(VistA, "8989.3")
    reindexFile(VistA, "8994.1")


def setupBoxVolPair(VistA, volume_set, site_name, tcp_port):
    # Rename the TaskMan Site Parameters box-volume pair, then write the RPC
    # Broker (XWB) LISTENER for the local domain on tcp_port (the RPC port,
    # 9430). On IRIS this also queues the listener under the Listener Starter.
    VistA.getenv(volume_set)
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('14.7')
    VistA.wait('ALL//')
    VistA.write('BOX-VOLUME')
    VistA.wait_re('Then edit field')
    VistA.write('Manager Startup Delay')
    VistA.wait_re('Then edit field')
    VistA.write('')
    VistA.wait('Select TASKMAN SITE PARAMETERS BOX-VOLUME PAIR:')
    VistA.write('`1')
    VistA.wait('PAIR')
    VistA.write(VistA.boxvol)
    VistA.wait('Manager Startup')
    VistA.write('1')
    VistA.wait('Select TASKMAN SITE PARAMETERS BOX-VOLUME PAIR:')
    VistA.write('')
    VistA.wait('Select OPTION')
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('8994.1')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('LISTENER')
    VistA.wait('SUB-FIELD')
    VistA.write('')
    VistA.wait('THEN EDIT FIELD')
    VistA.write('')
    VistA.wait('Select RPC BROKER SITE PARAMETERS DOMAIN NAME')
    VistA.write(site_name)
    VistA.wait('OK')
    VistA.write('Y')
    VistA.wait('BOX-VOLUME PAIR')
    VistA.write(VistA.boxvol)
    VistA.wait('OK')
    VistA.write('Y')
    index = VistA.multiwait(['BOX-VOLUME', 'Select PORT'])
    if index == 0:
        VistA.write('')
        VistA.wait('Select PORT')
    VistA.write(tcp_port + '\rY')
    VistA.write('1\r1\r1\r')
    VistA.wait('Select OPTION')
    VistA.write('')


def setupVolumeSet(VistA, site_name, volume_set, namespace=""):
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('14.5\r')
    VistA.wait('Select VOLUME SET')
    VistA.write('`1')
    VistA.wait('VOLUME SET:')
    VistA.write(volume_set + '\r\r\r\r\r')
    VistA.wait('TASKMAN FILES UCI')
    VistA.write(namespace + '\r\r\r\r\r\r')
    VistA.wait('Select OPTION')
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('KERNEL SYSTEM PARAMETERS\rVOLUME SET\r\r')
    VistA.wait('Select KERNEL SYSTEM PARAMETERS DOMAIN NAME:')
    VistA.write(site_name + '\r')
    VistA.wait('VOLUME SET')
    VistA.write(volume_set)
    index = VistA.multiwait(['Are you adding', 'VOLUME SET'])
    if index == 0:
        VistA.write('Y')
    elif index == 1:
        VistA.write('')
    VistA.wait('MAX SIGNON ALLOWED')
    VistA.write('500')
    VistA.wait('LOG SYSTEM RT')
    VistA.write('N')
    VistA.wait('VOLUME SET')
    VistA.write('\r\r')


def scheduleOption(VistA, optionName, scheduleValue, scheduleTime="0030"):
    # Schedule a TaskMan option (STARTUP, or a recurring frequency).
    VistA.wait(PROMPT)
    VistA.write('S DUZ=1 D ^XUP')
    VistA.wait('Select OPTION NAME')
    VistA.write('EVE\r1')
    VistA.wait('Systems Manager Menu')
    VistA.write('Taskman Management')
    VistA.wait('Select Taskman Management')
    VistA.write('SCHED')
    VistA.wait('reschedule:')
    VistA.write(optionName + '\rY')
    VistA.wait('COMMAND:')
    if scheduleValue == 'STARTUP':
        VistA.write('\r^SPECIAL QUEUEING\rSTARTUP')
    else:
        VistA.write('^RESCHEDULING FREQUENCY\r%s' % scheduleValue)
        VistA.write('^QUEUED TO RUN AT WHAT TIME\rT+1@%s' % scheduleTime)
        VistA.write('^')
    VistA.write('S\rE')
    VistA.wait('reschedule:')
    VistA.write('')
    VistA.wait('Select Taskman Management')
    VistA.write('')
    VistA.wait('Systems Manager Menu')
    VistA.write('')
    VistA.wait('Do you really want to halt')
    VistA.write('Y')


def setupHL7Listener(VistA, hl7_port, link_name="VISTA-MLLP"):
    """Configure an HL7 (HL package) MLLP listener on hl7_port -- spec §8 step 8.

    DEFERRED / UNVERIFIED -- NOT CALLED by Phase 7 (log E7). Upstream OSEHRA only
    autostarts the Link Manager (HL AUTOSTART LINK MANAGER); it does not create a
    listening logical link. This would drive the HL7 "LLP" edit dialog (option
    HL EDIT LOGICAL LINKS) to define a single-listener TCP link on the published
    port -- but that option is a full-screen List Manager UI that pexpect cannot
    drive reliably, so the listener on port 5026 is left unbacked. Replacing this
    with a programmatic HL LOGICAL LINK (#870) FileMan/global approach is tracked
    as Deferred (spec v3 §13). Kept here as a clearly-marked stub; do not enable
    without first confirming the prompt sequence against the pinned HL7 version.
    """
    VistA.wait(PROMPT, 60)
    VistA.write('S DUZ=1 D ^XUP')
    VistA.wait('Select OPTION NAME')
    VistA.write('HL EDIT LOGICAL LINKS\r')
    VistA.wait('Select HL LOGICAL LINK NODE:')
    VistA.write(link_name)
    index = VistA.multiwait(['Are you adding', 'NODE:'])
    if index == 0:
        VistA.write('Y')
    VistA.wait('LLP TYPE:')
    VistA.write('TCP')
    # ScreenMan LLP parameters: SINGLE LISTENER on hl7_port.
    VistA.wait('TCP/IP SERVICE TYPE:')
    VistA.write('SINGLE LISTENER')
    VistA.wait('TCP/IP PORT')
    VistA.write(str(hl7_port))
    VistA.write('\r^\rS\rE')
    VistA.wait('Select OPTION NAME')
    VistA.write('')
    VistA.wait('halt')
    VistA.write('Y')


def addSystemManager(VistA):
    VistA.wait(PROMPT, 60)
    VistA.write('S DUZ=1 D ^XUP')
    VistA.wait('Select OPTION NAME')
    VistA.write('EVE\r1')
    VistA.wait('Systems Manager Menu')
    VistA.write('USER MANAGEMENT')
    VistA.wait('User Management')
    VistA.write('ADD')
    VistA.wait('Enter NEW PERSON')
    VistA.write('MANAGER,SYSTEM')
    index = VistA.multiwait(['Are you adding', 'Want to reactivate'])
    if index == 0:
        VistA.write('Y')
        VistA.wait('INITIAL:')
        VistA.write('SM')
        VistA.wait('SSN:')
        VistA.write('000000001')
        VistA.wait('SEX:')
        VistA.write('M')
        VistA.wait('NPI')
        VistA.write('')
        VistA.wait('NAME COMPONENTS')
    VistA.write('\r\r\r\r\r^PRIMARY MENU OPTION\rEVE\r1\r^Want to edit ACCESS CODE\rY\rSM1234\rSM1234\r^Want to edit VERIFY CODE\rY\rSM1234!!\rSM1234!!\r^SECONDARY MENU OPTIONS\rOR PARAM COORDINATOR MENU\rY\r\r\r\rTIU IRM MAINTENANCE MENU\rY\r\r\r\rXPAR MENU TOOLS\rY\r\r\r\rDG REGISTER PATIENT\rY\r\r\r\r^MULTIPLE SIGN-ON\r1\r1\r99\r^SERVICE/SECTION\rIRM\rS\rE')
    VistA.wait('User Account Access Letter')
    VistA.write('NO')
    VistA.wait('wish to allocate security keys?')
    VistA.write('Y')
    VistA.wait('Allocate key')
    VistA.write('XUMGR')
    VistA.wait('Another key')
    VistA.write('XUPROG\r1')
    VistA.wait('Another key')
    VistA.write('XUPROGMODE')
    VistA.wait('Another key')
    VistA.write('SD SUPERVISOR')
    VistA.wait('Another key')
    VistA.write('SDWL PARAMETER')
    VistA.wait('Another key')
    VistA.write('SDWL MENU')
    VistA.wait('Another key')
    VistA.write('')
    VistA.wait('Another holder')
    VistA.write('')
    VistA.wait('YES//')
    VistA.write('')
    VistA.wait('mail groups?')
    VistA.write('\r')
    VistA.wait('Systems Manager Menu')
    VistA.write('\rY')
    VistA.wait(PROMPT, 60)
    VistA.IEN('NEW PERSON', 'MANAGER,SYSTEM')
    VistA.wait(PROMPT, 60)
    VistA.write('S DUZ=' + VistA.IENumber + ' S $P(^VA(200,DUZ,0),"^",4)="@"')


def addInstitution(VistA, inst_name, station_number):
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE:')
    VistA.write('4')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('STATION NUMBER')
    VistA.wait('THEN EDIT FIELD')
    VistA.write('')
    VistA.wait('Select INSTITUTION NAME:')
    VistA.write(inst_name)
    index = VistA.multiwait(['Are you adding', 'STATION NUMBER'])
    if index == 0:
        VistA.write('Y')
        VistA.wait('STATION NUMBER:')
    VistA.write(station_number)
    VistA.wait('Select INSTITUTION NAME:')
    VistA.write('')
    VistA.wait('Select OPTION:')
    VistA.write('')


def addDivision(VistA, div_name, facility_number, station_number):
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE:')
    VistA.write('40.8')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('FACILITY NUMBER')
    VistA.wait('THEN EDIT FIELD')
    VistA.write('INSTITUTION FILE POINTER')
    VistA.wait('THEN EDIT FIELD')
    VistA.write('')
    VistA.wait('DIVISION NAME')
    VistA.write(div_name)
    VistA.wait('Are you adding')
    VistA.write('Y')
    VistA.wait('MEDICAL CENTER DIVISION NUM:')
    VistA.write('')
    VistA.wait('FACILITY NUMBER')
    VistA.write(facility_number)
    VistA.write('')
    VistA.wait('INSTITUTION FILE POINTER')
    VistA.write(station_number)
    VistA.wait('DIVISION NAME')
    VistA.write('')
    VistA.wait('Select OPTION')
    VistA.write('')


def addtoMASParameter(VistA, institution, medical_center):
    VistA.wait(PROMPT)
    VistA.write('D ^XUP')
    VistA.write('1')
    VistA.wait('Select OPTION NAME')
    VistA.write('ADT SYSTEM')
    VistA.wait('ADT System Definition Menu')
    VistA.write('MAS Parameter Entry')
    VistA.wait('Enter 1-3 to EDIT, or RETURN to QUIT')
    VistA.write('1')
    VistA.wait('MEDICAL CENTER NAME')
    VistA.write(medical_center)
    VistA.wait('AFFILIATED')
    VistA.write('NO')
    VistA.wait('MULTIDIVISION MED CENTER')
    VistA.write('NO')
    VistA.wait('NURSING HOME WARDS')
    VistA.write('')
    VistA.wait('DOMICILIARY WARDS')
    VistA.write('')
    VistA.wait('SYSTEM TIMEOUT')
    VistA.write('30')
    VistA.wait('AUTOMATIC PTF MESSAGES')
    VistA.write('')
    VistA.wait('PRINT PTF MESSAGES')
    VistA.write('')
    VistA.wait('DEFAULT PTF MESSAGE PRINTER')
    VistA.write('')
    VistA.wait('SHOW STATUS SCREEN')
    VistA.write('YES')
    VistA.wait('USE HIGH INTENSITY ON SCREENS')
    VistA.write('^^')
    VistA.wait('Enter 1-3 to EDIT, or RETURN to QUIT')
    VistA.write('2')
    VistA.wait('DAYS TO UPDATE MEDICAID')
    VistA.write('365')
    VistA.wait('DAYS TO MAINTAIN G&L CORR')
    VistA.write('30')
    VistA.wait('TIME FOR LATE DISPOSITION')
    VistA.write('30')
    VistA.wait('SUPPLEMENTAL 10/10')
    VistA.write('0')
    VistA.wait(':')
    VistA.write('^ASK DEVICE IN REGISTRATION')
    VistA.wait('ASK DEVICE IN REGISTRATION')
    VistA.write('YES')
    VistA.wait('DAYS TO MAINTAIN SENSITIVITY')
    VistA.write('30')
    VistA.wait(':')
    VistA.write('^^')
    VistA.wait('Enter 1-3 to EDIT, or RETURN to QUIT')
    VistA.write('3')
    VistA.wait(':')
    VistA.write('^INSTITUTION FILE POINTER')
    VistA.wait('INSTITUTION FILE POINTER')
    VistA.write(institution)
    VistA.wait(':')
    VistA.write('^^')
    VistA.wait('Enter 1-3 to EDIT, or RETURN to QUIT')
    VistA.write('')
    VistA.wait('ADT System Definition Menu')
    VistA.write('')
    VistA.wait('YES//')
    VistA.write('')
    VistA.wait(PROMPT)
    VistA.write('')


def removeCAPRILogin(VistA):
    VistA.wait(PROMPT, 60)
    VistA.write('D EN^XPAR("SYS","XU522",1,"Y")')
