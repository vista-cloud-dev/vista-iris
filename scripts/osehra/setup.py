"""VistA site-build steps, driven over an interactive `iris session`.

Cleaned, IRIS-only Python 3 fork of WorldVistA/VistA `Python/vista/OSEHRASetup.py`
(submodule pin b7aecb9), per spec docs/vista-iris-container-spec-v2.md §5 / §5.4.

Each function reproduces a *proven* OSEHRA write/wait sequence verbatim; the
only edits are mechanical cleaning:
  * ``if VistA.type == 'cache'`` branches -> always the IRIS (Cache-compatible)
    path; ``sys.platform == 'win32'`` branches -> the POSIX path;
  * dropped the ``TestHelper`` / CSV dependency (patients are passed in-line);
  * Python 3 syntax.
The single *addition* is setupHL7Listener() (spec §8 step 8) -- VistA's HL7 MLLP
listener on a published port, which upstream OSEHRA does not configure. It is
flagged UNVERIFIED below.
"""
import datetime
import re
import time
from tempfile import gettempdir

from helper import PROMPT

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


def startFileman(VistA):
    # Start FileMan as the programmer user; XUMF=1 permits editing Kernel files.
    VistA.wait(PROMPT)
    VistA.write('S DUZ=1 S XUMF=1 D Q^DI')
    VistA.wait('Select OPTION:')


def signonZU(VistA, acc_code, ver_code):
    # Sign a user into the ZU menu; forces a verify-code change if prompted.
    VistA.wait(PROMPT, 60)
    VistA.write('D ^ZU')
    VistA.wait('ACCESS CODE:')
    VistA.write(acc_code)
    VistA.wait('VERIFY CODE:')
    VistA.write(ver_code)
    index = VistA.multiwait(['TYPE NAME', 'verify code:'])
    if index == 1:
        VistA.write(ver_code)
        VistA.wait('VERIFY CODE:')
        VistA.write(ver_code + "!")
        VistA.wait('right:')
        VistA.write(ver_code + "!")
        VistA.wait('TYPE NAME:')
    VistA.write('')


def initializeFileman(VistA, site_name, site_number):
    # Initialize FileMan (DINIT) and set the MUMPS OPERATING SYSTEM to CACHE --
    # the Cache-compatible interface IRIS presents (replaces the manual
    # ^ZTMGRSET "system type 3" step). ^ZUSET renames the ZU* routines.
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

    UNVERIFIED / least-tested step: upstream OSEHRA only autostarts the Link
    Manager (HL AUTOSTART LINK MANAGER), it does not create a listening logical
    link. This drives the HL7 "LLP" edit dialog (option HL EDIT LOGICAL LINKS,
    via the Link Edit/HLLP setup) to define a single-listener TCP link on the
    published port. Confirm the prompt sequence against the HL7 package version
    in the pinned FOIA VistA-M before relying on it; adjust as needed.
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


def startTaskMan(VistA):
    # Cold-boot TaskMan; this fires the scheduled STARTUP options (XWB
    # listener, HL7 Link Manager) on every boot.
    VistA.wait(PROMPT)
    VistA.write('DO ^ZTMB')


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


def setupNursLocation(VistA, unit_name):
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE:')
    VistA.write('NURS LOCATION')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('')
    VistA.wait('NURSING UNIT NAME')
    VistA.write(unit_name)
    VistA.wait('Are you adding')
    VistA.write('Y')
    VistA.wait('Are you adding')
    VistA.write('Y')
    VistA.wait('PRODUCT LINE')
    VistA.write('NURSING')
    VistA.wait('CARE SETTING')
    VistA.write('INPATIENT')
    VistA.wait('UNIT TYPE')
    VistA.write('CLINICAL')
    VistA.wait('INPATIENT DSS DEPARTMENT')
    VistA.write('')
    VistA.wait('PATIENT CARE FLAG')
    VistA.write('A')
    VistA.wait('INACTIVE FLAG')
    VistA.write('A')
    VistA.wait('MAS WARD')
    VistA.write('')
    VistA.wait('AMIS BED SECTION')
    VistA.write('')
    VistA.wait('PROFESSIONAL PERCENTAGE')
    VistA.write('')
    VistA.wait('UNIT EXPERIENCE')
    VistA.write('')
    VistA.wait('POC DATA ENTRY PERSONNEL')
    VistA.write('')
    VistA.wait('POC DATA APPROVAL PERSONNEL')
    VistA.write('')
    VistA.wait('SERVICE DATE')
    VistA.write('')
    VistA.wait('SERVICE DATE')
    VistA.write('')
    VistA.wait('STATUS')
    VistA.write('')
    VistA.wait('NURSING UNIT NAME')
    VistA.write('')
    VistA.wait('Select OPTION')
    VistA.write('')


def setupStrepTest(VistA):
    # Make a STREPTOZYME lab test orderable at VISTA HEALTH CARE, then build a
    # quick order + order set for it (used by CPRS ordering demos/tests).
    startFileman(VistA)
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('ACCESSION\r1')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('.4\r')
    VistA.wait('Select ACCESSION AREA')
    VistA.write('CHEMISTRY')
    VistA.wait('NUMERIC IDENTIFIER')
    VistA.write('CH\r')
    VistA.wait('OPTION')
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('LABORATORY TEST')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('ACCESSION AREA\r\r')
    VistA.wait('Select LABORATORY TEST NAME')
    VistA.write('STREPTOZYME')
    VistA.wait('Select INSTITUTION')
    VistA.write('VISTA HEALTH CARE')
    VistA.wait('ACCESSION AREA')
    VistA.write('CHEMISTRY')
    VistA.wait('Select LABORATORY TEST NAME')
    VistA.write('')
    VistA.wait('OPTION')
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('ADMINISTRATION SCHEDULE')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('PACKAGE PREFIX\r')
    VistA.wait('Select ADMINISTRATION SCHEDULE NAME')
    VistA.write('ONCE')
    VistA.wait('P')
    VistA.write('LR')
    VistA.wait('ADMINISTRATION SCHEDULE')
    VistA.write('')
    VistA.wait('Select OPTION')
    VistA.write('')
    VistA.wait(PROMPT)
    VistA.write('K  D ^XUP')
    VistA.wait('Access Code')
    VistA.write('SM1234')
    index = VistA.multiwait(['Select OPTION NAME', 'TERMINAL TYPE NAME'])
    if index == 1:
        VistA.write('C-VT220')
        VistA.wait('Select OPTION NAME')
    VistA.write('Systems Manager Menu')
    VistA.wait('Systems Manager Menu')
    VistA.write('CPRS Configuration')
    VistA.wait('CPRS Configuration')
    VistA.write('MM')
    VistA.wait('Order Menu Management')
    VistA.write('QO')
    VistA.wait('Select QUICK ORDER NAME')
    VistA.write('LRZ STREP TEST')
    VistA.wait('Are you adding')
    VistA.write('Y')
    VistA.wait('TYPE OF QUICK ORDER')
    VistA.write('LAB\r')
    VistA.wait('DISPLAY TEXT')
    VistA.write('STREP TEST')
    VistA.wait('VERIFY ORDER')
    VistA.write('Y')
    VistA.wait('DESCRIPTION')
    VistA.write('N\r')
    VistA.wait('Lab Test')
    VistA.write('STREP\r2')
    VistA.wait('Collected By')
    VistA.write('SP')
    VistA.wait('Collection Sample')
    VistA.write('SWAB\r')
    VistA.wait('Collection Date/Time')
    VistA.write('TODAY\r')
    VistA.wait('How often')
    VistA.write('ONCE')
    VistA.wait('PLACE//')
    VistA.write('\r\r')
    VistA.wait('Option')
    VistA.write('ST')
    VistA.wait('Select ORDER SET NAME')
    VistA.write('STREP TEST')
    VistA.wait('Are you adding')
    VistA.write('Y')
    VistA.wait('Do you wish to copy')
    VistA.write('No\r')
    VistA.wait('DISPLAY TEXT')
    VistA.write('Strep Test\r\r\r')
    VistA.wait('COMPONENT SEQUENCE')
    VistA.write('10\r')
    VistA.wait('ITEM:')
    VistA.write('LRZ STREP TEST\r\r\r\r')
    VistA.wait('Systems Manager Menu')
    VistA.write('')
    VistA.wait('Do you really')
    VistA.write('Y')


def registerVitalsCPRS(VistA):
    VistA.wait(PROMPT, 60)
    VistA.write('S GMVDLL="5.0.38.3"')
    VistA.wait(PROMPT, 60)
    VistA.write('D EN^XPAR("SYS","GMV DLL VERSION",GMVDLL,1)')
    VistA.wait(PROMPT, 60)
    VistA.write('S GMVGUI="VITALSMANAGER.EXE:5.0.38.3"')
    VistA.wait(PROMPT, 60)
    VistA.write('D EN^XPAR("SYS","GMV GUI VERSION",GMVGUI,1)')
    VistA.wait(PROMPT, 60)
    VistA.write('S GMVGUI="VITALS.EXE:5.0.38.3"')
    VistA.wait(PROMPT, 60)
    VistA.write('D EN^XPAR("SYS","GMV GUI VERSION",GMVGUI,1)')


def removeCAPRILogin(VistA):
    VistA.wait(PROMPT, 60)
    VistA.write('D EN^XPAR("SYS","XU522",1,"Y")')


def _addUser(VistA, name, init, SSN, sex, AC, VC1, screenman, keys, first=False):
    # Shared NEW PERSON creation via USER MANAGEMENT > ADD. `screenman` is the
    # verbatim ScreenMan keystroke blob; `keys` is the list of security keys.
    if first:
        VistA.write('USER MANAGEMENT')
    else:
        VistA.wait('Systems Manager Menu')
        VistA.write('User Management')
    VistA.wait('User Management')
    VistA.write('ADD')
    VistA.wait('name')
    VistA.write(name + '\rY')
    VistA.wait('INITIAL:')
    VistA.write(init)
    VistA.wait('SSN:')
    VistA.write(SSN)
    VistA.wait('SEX:')
    VistA.write(sex)
    VistA.wait('NPI')
    VistA.write('')
    VistA.wait('NAME COMPONENTS')
    VistA.write(screenman)
    VistA.wait('User Account Access Letter')
    VistA.write('NO')
    VistA.wait('wish to allocate security keys?')
    VistA.write('Y')
    for i, key in enumerate(keys):
        VistA.wait('Allocate key' if i == 0 else 'Another key')
        VistA.write(key)
    VistA.wait('Another key')
    VistA.write('')
    VistA.wait('Another holder')
    VistA.write('')
    VistA.wait('Do you wish to proceed')
    VistA.write('Yes')
    VistA.wait('add this user to mail groups')
    VistA.write('NO')
    VistA.wait('User Management')
    VistA.write('')


def addDoctor(VistA, name, init, SSN, sex, AC, VC1):
    screenman = '\r\r\r\r\r^PRIMARY MENU OPTION\rXUCOR\r^SECONDARY MENU OPTIONS\rPSB GUI CONTEXT\rY\r\r\r\rGMPL MGT MENU\rY\r\r\r\rOR CPRS GUI CHART\rY\r\r\r\rGMV V/M GUI\rY\r\r\r\r^Want to edit ACCESS CODE\rY\r' + AC + '\r' + AC + '\r^Want to edit VERIFY CODE\rY\r' + VC1 + '\r' + VC1 + '\rVISTA HEALTH CARE\rY\r\r\r\r\r^SERVICE/SECTION\rIRM\r^Language\r\r767\rY\rY\rT-1\r\r^RESTRICT PATIENT SELECTION\r0\r\rCOR\rY\rT-1\r\r^MULTIPLE SIGN-ON\r1\r1\r99\r^\rS\rE'
    keys = ['PROVIDER\r1', 'GMV MANAGER', 'LRLAB', 'LRVERIFY', 'ORES',
            'SD SUPERVISOR', 'SDWL PARAMETER', 'SDWL MENU', 'PSB MANAGER']
    _addUser(VistA, name, init, SSN, sex, AC, VC1, screenman, keys, first=True)


def addNurse(VistA, name, init, SSN, sex, AC, VC1):
    screenman = '\r\r\r\r\r^PRIMARY MENU OPTION\rXUCOR\r^SECONDARY MENU OPTIONS\rPSB GUI CONTEXT\rY\r\r\r\rGMPL MGT MENU\rY\r\r\r\rOR CPRS GUI CHART\rY\r\r\r\rGMV V/M GUI\rY\r\r\r\r^Want to edit ACCESS CODE\rY\r' + AC + '\r' + AC + '\r^Want to edit VERIFY CODE\rY\r' + VC1 + '\r' + VC1 + '\rVISTA HEALTH CARE\rY\r\r\r\r\r^SERVICE/SECTION\rIRM\r^Language\r\r289\rY\rY\rT-1\r\r^RESTRICT PATIENT SELECTION\r0\r\rCOR\rY\rT-1\r\r^MULTIPLE SIGN-ON\r1\r1\r99\r^\rS\rE'
    keys = ['PSB MANAGER', 'PROVIDER\r1', 'ORELSE\r']
    _addUser(VistA, name, init, SSN, sex, AC, VC1, screenman, keys)


def addClerk(VistA, name, init, SSN, sex, AC, VC1):
    screenman = '\r\r\r\r\r^PRIMARY MENU OPTION\rXUCOR\r^SECONDARY MENU OPTIONS\rGMPL DATA ENTRY\rY\r\r\r\rOR CPRS GUI CHART\rY\r\r\r\rGMV V/M GUI\rY\r\r\r\r^Want to edit ACCESS CODE\rY\r' + AC + '\r' + AC + '\r^Want to edit VERIFY CODE\rY\r' + VC1 + '\r' + VC1 + '\rVISTA HEALTH CARE\rY\r\r\r\r\r^SERVICE/SECTION\rIRM\r^RESTRICT PATIENT SELECTION\r0\r\rCOR\rY\rT-1\r\r^MULTIPLE SIGN-ON\r1\r1\r99\r^\rS\rE'
    keys = ['ORELSE']
    _addUser(VistA, name, init, SSN, sex, AC, VC1, screenman, keys)


def setNonExpiringCodes(VistA, nameArray):
    startFileman(VistA)
    VistA.write('ENTER')
    VistA.wait('Input to what File')
    VistA.write('NEW PERSON')
    VistA.wait_re('EDIT WHICH FIELD')
    VistA.write('7.2')
    VistA.wait('THEN EDIT')
    VistA.write('')
    for name in nameArray:
        VistA.wait('NEW PERSON NAME')
        VistA.write(name)
        VistA.wait('VERIFY CODE never expires')
        VistA.write('Y')
    VistA.wait('NEW PERSON NAME')
    VistA.write('')
    VistA.wait_re('Select OPTION')
    VistA.write('')


def setupElectronicSignature(VistA, AC, VC1, VC2, sigcode):
    VistA.wait(PROMPT, 60)
    VistA.write('D ^ZU')
    VistA.wait('ACCESS CODE:')
    VistA.write(AC)
    VistA.wait('VERIFY CODE:')
    VistA.write(VC1)
    VistA.wait('verify code:')
    VistA.write(VC1)
    VistA.wait('VERIFY CODE:')
    VistA.write(VC2)
    VistA.wait('right:')
    VistA.write(VC2)
    VistA.wait('TYPE NAME')
    VistA.write('')
    VistA.wait('Core Applications')
    VistA.write("USER's TOOLBOX")
    VistA.wait('Toolbox')
    VistA.write('ELE')
    VistA.wait('INITIAL')
    VistA.write('')
    VistA.wait('SIGNATURE BLOCK PRINTED NAME')
    VistA.write('')
    VistA.wait('SIGNATURE BLOCK TITLE')
    VistA.write('\r\r\r')
    VistA.wait('SIGNATURE CODE')
    VistA.write(sigcode)
    VistA.wait('SIGNATURE CODE FOR VERIFICATION')
    VistA.write(sigcode)
    VistA.wait('Toolbox')
    VistA.write('\r\r\r')


def createClinic(VistA, name, abbrv, service):
    # Build a minimal scheduling clinic via SDBUILD.
    VistA.wait(PROMPT)
    VistA.write('W $$NOSEND^VAFHUTL')
    VistA.wait('0')
    VistA.write('S DUZ=1 D ^XUP')
    VistA.wait('OPTION NAME:')
    VistA.write('SDBUILD')
    VistA.wait('CLINIC NAME:')
    VistA.write(name)
    VistA.wait('Are you adding')
    VistA.write('Y')
    VistA.wait('NAME')
    VistA.write('')
    VistA.wait('ABBREVIATION')
    VistA.write(abbrv)
    while True:
        index = VistA.multiwait(['SERVICE', 'CLINIC MEETS', 'PATIENT FRIENDLY NAME', 'ALLOW DIRECT PATIENT', 'DISPLAY CLIN APPT'])
        if index == 0:
            break
        if index == 2:
            VistA.write('')
        else:
            VistA.write('Y')
    VistA.write(service)
    VistA.wait('NON-COUNT CLINIC')
    VistA.write('N')
    VistA.wait('STOP CODE NUMBER')
    VistA.write('301\r\r')
    VistA.wait('TELEPHONE')
    VistA.write('555-555-1414\r\r\r\r\r\r\r\r\r\r\r')
    index = VistA.multiwait(['ALLOWABLE CONSECUTIVE NO-SHOWS', 'WORKLOAD VALIDATION'])
    if index == 1:
        VistA.write('')
        VistA.wait('ALLOWABLE CONSECUTIVE NO-SHOWS')
    VistA.write('0')
    VistA.wait('FUTURE BOOKING')
    VistA.write('90')
    VistA.wait('HOUR CLINIC DISPLAY BEGINS')
    VistA.write('8\r')
    VistA.wait('AUTO-REBOOK')
    VistA.write('90\r\r\r\r\r')
    VistA.wait('MAXIMUM')
    VistA.write('0\r')
    VistA.wait('LENGTH OF APP')
    VistA.write('30')
    VistA.wait('VARIABLE')
    VistA.write('Yes')
    VistA.wait('DISPLAY INCREMENTS PER HOUR')
    VistA.write('2')
    dates = ['JUL 2,2012', 'JUL 3,2012', 'JUL 4,2012', 'JUL 5,2012', 'JUL 6,2012']
    for date in dates:
        VistA.wait('AVAILABILITY DATE')
        VistA.write(date)
        VistA.wait('TIME')
        VistA.write('0800-1200\r4')
        VistA.wait('TIME')
        VistA.write('1230-1500\r4')
        VistA.wait('TIME')
        VistA.write('')
        VistA.wait('PATTERN OK')
        VistA.write('Yes')
    VistA.wait('AVAILABILITY DATE')
    VistA.write('')
    VistA.wait('CLINIC NAME:')
    VistA.write('')


def setupWard(VistA, division, institution, ward_name, clinic_name, order,
              specialty='Cardiac Surgery', bed_array=(("1-A", "testBed1"),)):
    VistA.wait(PROMPT)
    VistA.write('S DUZ=1 D ^XUP')
    VistA.wait('OPTION NAME:')
    VistA.write('WARD DEFINITION ENTRY')
    VistA.wait('NAME:')
    VistA.write(ward_name)
    VistA.wait('No//')
    VistA.write('YES')
    VistA.wait('POINTER:')
    VistA.write(clinic_name)
    VistA.wait('ORDER:')
    VistA.write(order)
    VistA.wait(ward_name)
    VistA.write('')
    VistA.wait('WRISTBAND:')
    VistA.write('YES')
    VistA.wait('DIVISION:')
    VistA.write(division)
    VistA.wait('INSTITUTION:')
    VistA.write(institution)
    VistA.wait('6100')
    VistA.write('')
    VistA.wait('BEDSECTION:')
    VistA.write('bedselect')
    VistA.wait('SPECIALTY:')
    VistA.write(specialty)
    VistA.wait('SERVICE:')
    VistA.write('S')
    VistA.wait('LOCATION:')
    VistA.write('north')
    VistA.wait('WARD:')
    VistA.write('1')
    VistA.wait('DATE:')
    VistA.write('T')
    VistA.wait('No//')
    VistA.write('YES')
    VistA.wait('BEDS:')
    VistA.write('20')
    VistA.wait('ILL:')
    VistA.write('1')
    VistA.wait('SYNONYM:')
    VistA.write('')
    VistA.wait('G&L ORDER:')
    VistA.write('')
    VistA.wait('TOTALS:')
    VistA.write('')
    VistA.wait('NAME:')
    VistA.write('')
    addBedsToWard(VistA, ward_name, bed_array)


def addBedsToWard(VistA, ward_name, bed_array):
    VistA.wait(PROMPT)
    VistA.write('S DUZ=1 D ^XUP')
    VistA.wait('OPTION NAME:')
    VistA.write('ADT SYSTEM')
    VistA.wait('Option:')
    VistA.write('ADD')
    for sitem in bed_array:
        VistA.wait('NAME:')
        VistA.write(sitem[0])
        VistA.wait('No//')
        VistA.write('yes')
        VistA.wait('NAME:')
        VistA.write('')
        VistA.wait('DESCRIPTION:')
        VistA.write(sitem[1])
        VistA.wait('No//')
        VistA.write('yes')
        VistA.wait('ASSIGN:')
        VistA.write(ward_name)
        VistA.wait('No//')
        VistA.write('yes')
        VistA.wait('ASSIGN:')
        VistA.write('')
    VistA.wait('NAME:')
    VistA.write('')
    VistA.wait('Option:')
    VistA.write('')
    VistA.wait('YES//')
    VistA.write('')


def modifyDVBParams(VistA):
    VistA.wait(PROMPT)
    VistA.write('D ^XUP')
    VistA.wait('NAME:')
    VistA.write('ZZFILEMAN')
    VistA.wait('OPTION:')
    VistA.write('1')
    VistA.wait_re('INPUT TO WHAT FILE')
    VistA.write('395')
    VistA.wait('EDIT WHICH FIELD')
    VistA.write('ALL')
    VistA.wait('Select DVB PARAMETERS ONE:')
    VistA.write('1')
    VistA.wait('No//')
    VistA.write('yes')
    VistA.wait('SCREENS?:')
    VistA.write('NO')
    VistA.wait('DAY:')
    VistA.write('^NEW IDCU INTERFACE')
    VistA.wait('INTERFACE:')
    VistA.write('0')
    VistA.wait('Difference:')
    VistA.write('')
    VistA.wait('DIVISION:')
    VistA.write('YES')
    VistA.wait('GROUP:')
    VistA.write('^')
    VistA.wait('Select DVB PARAMETERS ONE:')
    VistA.write('')
    VistA.wait('OPTION:')
    VistA.write('')


def addAllergiesPermission(VistA):
    VistA.wait('Systems Manager Menu')
    VistA.write('CPRS Configuration')
    VistA.wait('CPRS Configuration')
    VistA.write('GUI PARAMETERS')
    VistA.wait('GUI Parameters')
    VistA.write('GUI Mark Allergy Entered in Error')
    VistA.wait('Enter selection')
    VistA.write('4\rY\r\r')


def addTemplatePermission(VistA, init):
    VistA.wait('Systems Manager Menu')
    VistA.write('TIU Maintenance')
    VistA.wait('TIU Maintenance')
    VistA.write('User Class Management')
    VistA.wait('User Class Management')
    VistA.write('List Membership by User')
    VistA.wait('Select USER')
    VistA.write(init + '\rAdd\rClinical Coordinator\rT-1\r\r\r')
    VistA.wait('Option')
    VistA.write('\r')


def createOrderMenu(VistA):
    # Build the ORZ GEN MED WRITE ORDERS LIST menu and point ORWDX WRITE ORDERS
    # LIST at it system-wide. (Verbatim from upstream; long but deterministic.)
    VistA.wait('Systems Manager Menu')
    VistA.write('CPRS Configuration')
    VistA.wait('CPRS Configuration')
    VistA.write('MM')
    VistA.wait('Order Menu Management')
    VistA.write('MN')
    VistA.wait('ORDER MENU:')
    VistA.write('ORZ GEN MED WRITE ORDERS LIST')
    VistA.wait('Are you adding')
    VistA.write('Y')
    VistA.wait('Do you wish to copy an existing menu')
    VistA.write('N')
    VistA.wait('DISPLAY TEXT')
    VistA.write('')
    VistA.wait('Edit')
    VistA.write('N')
    VistA.wait('COLUMN WIDTH')
    VistA.write('80')
    VistA.wait('MNEMONIC WIDTH')
    VistA.write('')
    VistA.wait('PATH SWITCH')
    VistA.write('')
    VistA.wait('ENTRY ACTION')
    VistA.write('')
    VistA.wait('EXIT ACTION')
    VistA.write('')
    VistA.wait('Action')
    VistA.write('Add')
    VistA.wait('Add')
    VistA.write('Menu Items')
    items = [
        ('OR ADD MENU CLINICIAN', '1'), ('GMRAOR ALLERGY ENTER/EDIT', '2'),
        ('FHW1', '3'), ('PSJ OR PAT OE', '4'), ('PSH OERR', '5'),
        ('PSO OERR', '6'), ('PSJI OR PAT FLUID OE', '7'),
        ('LR OTHER LAB TESTS', '8'), ('RA OERR EXAM', '9'),
        ('GMRCOR CONSULT', '10'), ('GMRCOR REQUEST', '11'),
    ]
    for item, row in items:
        VistA.wait('ITEM')
        VistA.write(item)
        VistA.wait('ROW')
        VistA.write(row)
        VistA.wait('COLUMN')
        VistA.write('1')
        VistA.wait('DISPLAY TEXT')
        VistA.write('')
        VistA.wait('MNEMONIC')
        VistA.write('')
    # 'Vitals' menu name is ambiguous -> CHOOSE prompt.
    VistA.wait('ITEM')
    VistA.write('GMRVOR')
    VistA.wait('CHOOSE')
    VistA.write('1')
    VistA.wait('ROW')
    VistA.write('12')
    VistA.wait('COLUMN')
    VistA.write('1')
    VistA.wait('DISPLAY TEXT')
    VistA.write('')
    VistA.wait('MNEMONIC')
    VistA.write('')
    for item, row in [('OR GXTEXT WORD PROCESSING ORDER', '13'), ('LRZ STREP TEST', '14')]:
        VistA.wait('ITEM')
        VistA.write(item)
        VistA.wait('ROW')
        VistA.write(row)
        VistA.wait('COLUMN')
        VistA.write('1')
        VistA.wait('DISPLAY TEXT')
        VistA.write('')
        VistA.wait('MNEMONIC')
        VistA.write('')
    VistA.wait('ITEM')
    VistA.write('')
    VistA.wait('Action')
    VistA.write('Quit')
    VistA.wait('Order Menu Management')
    VistA.write('General Parameter Tools')
    VistA.wait('General Parameter Tools')
    VistA.write('EP')
    VistA.wait('PARAMETER DEFINITION NAME')
    VistA.write('ORWDX WRITE ORDERS LIST')
    VistA.wait('selection')
    VistA.write('8')
    VistA.wait('Order Dialog')
    VistA.write('ORZ GEN MED WRITE ORDERS LIST')
    VistA.write('\r\r\r\r')


def addPatient(VistA, patients):
    """Register fictitious patients via the ADT Register-a-Patient menu.

    `patients` is a list of dicts with keys: fullname, sex, dob, ssn, type,
    veteran, service, twin, cityob, stateob. (Upstream read these from a CSV;
    inlined here to drop the TestHelper/CSV dependency.)
    """
    for patient_data in patients:
        VistA.write('L  S DUZ=1 D ^XUP')
        VistA.wait('Select OPTION NAME')
        VistA.write('Core Applications\r')
        VistA.wait('Select Core Applications')
        VistA.write('ADT Manager Menu')
        while True:
            index = VistA.multiwait(['to continue', 'Select ADT Manager Menu', 'Select Registration Menu'])
            if index == 0:
                VistA.write('')
            elif index == 1:
                VistA.write('Registration Menu')
            elif index == 2:
                VistA.write('Register a Patient')
                break
        index = VistA.multiwait(['PATIENT NAME', 'Select 1010 printer'])
        if index == 1:
            VistA.write('NULL')
            VistA.wait('PATIENT NAME')
        VistA.write(patient_data['fullname'].strip())
        index = VistA.multiwait(['ARE YOU ADDING', 'Enterprise Search'])
        VistA.write('Y')
        if index == 1:
            while True:
                index = VistA.multiwait(['FAMILY', 'GIVEN', 'MIDDLE NAME', 'PREFIX', 'SUFFIX',
                                         'DEGREE', 'SOCIAL SECURITY', 'DATE OF BIRTH', 'SEX',
                                         'MAIDEN NAME', 'CITY', 'STATE', 'MULTIPLE BIRTH',
                                         'PHONE NUMBER', 'ARE YOU ADDING'])
                if index == 14:
                    VistA.write('Y')
                    break
                elif index == 6:
                    VistA.write(patient_data['ssn'])
                elif index == 7:
                    VistA.write(patient_data['dob'].strip())
                elif index == 8:
                    VistA.write(patient_data['sex'].strip())
                else:
                    VistA.write('')
            VistA.wait('to continue')
            VistA.write('')
            VistA.wait('MULTIPLE BIRTH INDICATOR')
            VistA.write('')
            VistA.wait('MAIDEN NAME:')
            VistA.write('')
        else:
            VistA.wait('SEX')
            VistA.write(patient_data['sex'].strip())
            VistA.wait('DATE OF BIRTH')
            VistA.write(patient_data['dob'].strip())
            VistA.wait('SOCIAL SECURITY NUMBER')
            VistA.write(patient_data['ssn'])
            VistA.wait('TYPE')
            VistA.write(patient_data['type'].strip())
            VistA.wait('PATIENT VETERAN')
            VistA.write(patient_data['veteran'].strip())
            VistA.wait('SERVICE CONNECTED')
            VistA.write(patient_data['service'].strip())
            VistA.wait('MULTIPLE BIRTH INDICATOR')
            VistA.write(patient_data['twin'].strip())
            index = VistA.multiwait(['Do you still', 'FAMILY'])
            if index == 0:
                VistA.write('Y')
                VistA.wait('FAMILY')
            VistA.write('^\r')
            VistA.wait('MAIDEN NAME:')
            VistA.write('')
        VistA.wait('[CITY]')
        VistA.write(patient_data['cityob'].strip())
        VistA.wait('[STATE]')
        VistA.write(patient_data['stateob'].strip())
        VistA.wait('ALIAS')
        VistA.write('')
        while True:
            waitIndex = VistA.multiwait(['Patient Data', 'to exit:'])
            if waitIndex == 0:
                break
            VistA.write('')
        VistA.write('Y')
        index = VistA.multiwait(['QUIT', 'Do you want to edit'])
        if index == 1:
            VistA.write('N')
            VistA.wait('QUIT')
        VistA.write('^')
        VistA.wait('condition')
        VistA.write('N')
        VistA.wait('today')
        VistA.write('N')
        VistA.wait('Registration login')
        VistA.write('NOW')
        VistA.wait('TYPE OF BENEFIT')
        VistA.write('3')
        VistA.wait('TYPE OF CARE')
        VistA.write('5')
        VistA.wait('REGISTRATION ELIGIBILITY CODE')
        VistA.write('')
        VistA.wait('NEED RELATED TO AN ACCIDENT')
        VistA.write('N')
        VistA.wait('NEED RELATED TO OCCUPATION')
        VistA.write('N')
        index = VistA.multiwait(['VA Patient Enrollment', 'PRINT 10'])
        if index == 0:
            VistA.write('No')
            VistA.wait('as soon as available')
            VistA.write('No')
            VistA.wait('PRINT 10')
        VistA.write('N')
        VistA.wait('ROUTING SLIP')
        VistA.write('N')
        VistA.wait_re('SELECT PATIENT NAME')
        VistA.write('^')
        while True:
            index = VistA.multiwait(['to halt', 'Core Applications', 'to continue',
                                     'Select ADT Manager Menu', 'Registration Menu'])
            VistA.write('')
            if index == 0:
                break
        VistA.wait(PROMPT)
