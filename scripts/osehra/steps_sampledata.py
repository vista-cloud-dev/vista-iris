"""Phase 8 (Tier-1 sample data) steps.

Verbatim from the former ``setup.py`` + the ``Clinic`` builder from
``03_sampledata.py`` (cleaned IRIS-only OSEHRA fork): a NURS location, an
orderable STREPTOZYME test + quick order, scheduling clinics, an inpatient ward
with beds, the clinical users (doctor/nurse/clerk) with access/verify codes and
e-signatures, the write-orders menu, and the fictitious patients (filed via
``UPDATE^DIE`` -- never the registration menu, which hangs on the MVI; log E9).

All identities are CLEARLY FICTITIOUS -- no real PHI.
"""
from .helper import PROMPT
from .steps_fileman import startFileman


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
    # No trailing CR on the last key: _addUser already runs the uniform
    # "Another key" -> "" cycle, so an extra CR would desync the dialog.
    keys = ['PSB MANAGER', 'PROVIDER\r1', 'ORELSE']
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
    """Create the sample patients directly in PATIENT (#2) via FileMan DBS.

    A standalone instance has no Master Patient Index, so the interactive
    "Register a Patient" menu blocks on "Searching the MVI..." (the Enterprise
    Search is gated by the MPIFXMLP routine, which is present once VistA-M is
    loaded). UPDATE^DIE files each entry directly with the file's seven required
    identifiers (.02 SEX, .03 DOB, .09 SSN, .301 SERVICE CONNECTED?, 391 TYPE,
    1901 VETERAN) -- deterministic and MVI-free. Enough to look the patient up
    and use it in CPRS; full registration (eligibility/enrollment) is deferred.

    `patients` is a list of dicts with keys: fullname, sex, dob, ssn, service,
    veteran (type/twin/cityob/stateob are accepted but unused here).
    """
    VistA.wait(PROMPT, 60)
    # Resolve the PATIENT TYPE (#391) pointer once (391 is a required identifier).
    VistA.write('S DIC=391,DIC(0)="M",X="NSC VETERAN" D ^DIC S DGTYPE=+Y')
    VistA.wait(PROMPT)
    for p in patients:
        name = p['fullname'].strip()
        VistA.write('S X="' + p['dob'].strip() + '",%DT="" D ^%DT S DGDOB=Y')
        VistA.wait(PROMPT)
        VistA.write('K FDA,DGIEN,DGERR')
        VistA.wait(PROMPT)
        VistA.write('S FDA(2,"+1,",.01)="' + name + '",FDA(2,"+1,",.02)="'
                    + p['sex'].strip()[0] + '",FDA(2,"+1,",.03)=DGDOB,FDA(2,"+1,",.09)="'
                    + p['ssn'].strip() + '"')
        VistA.wait(PROMPT)
        VistA.write('S FDA(2,"+1,",.301)="' + p.get('service', 'N').strip()
                    + '",FDA(2,"+1,",391)=DGTYPE,FDA(2,"+1,",1901)="'
                    + p.get('veteran', 'Y').strip() + '"')
        VistA.wait(PROMPT)
        VistA.write('D UPDATE^DIE("","FDA","DGIEN","DGERR")')
        VistA.wait(PROMPT)
        VistA.write('W !,"PATIENT ",$S(+$G(DGIEN(1)):"ADDED DFN="_DGIEN(1),'
                    '1:"FAILED: "_$G(DGERR("DIERR",1,"TEXT",1)))," (' + name + ')",!')
        VistA.wait(PROMPT)


class Clinic(object):
    """A scheduling clinic built via the SDBUILD option (from ClinicSetup.py.in)."""

    def __init__(self, cname, cabr, cstarttime, ctime, cdate, cslots, cservice,
                 ctype, cxray, cprofiles, ccico, cproviders, cdiagnosisICD10,
                 cdiagnosis, cvarlen, cstopcode):
        self.cname = cname
        self.cabr = cabr
        self.cstarttime = cstarttime
        self.ctime = ctime
        self.cdate = cdate
        self.cslots = cslots
        self.cservice = cservice
        self.ctype = ctype
        self.cxray = cxray
        self.cprofiles = cprofiles
        self.ccico = ccico
        self.cproviders = cproviders
        self.cdiagnosis = cdiagnosis
        self.cdiagnosisICD10 = cdiagnosisICD10
        self.cvarlen = cvarlen
        self.cstopcode = cstopcode

    def setup(self, VistA):
        VistA.write('W $$NOSEND^VAFHUTL')
        VistA.wait('0')
        VistA.write('S DUZ=1 D ^XUP')
        VistA.wait('OPTION NAME:')
        VistA.write('SDBUILD')
        VistA.wait('CLINIC NAME:')
        VistA.write(self.cname)
        VistA.wait('LOCATION?')
        VistA.write('Yes')
        VistA.wait('NAME:')
        VistA.write('')
        VistA.wait('ABBREVIATION')
        VistA.write(self.cabr)
        while True:
            index = VistA.multiwait(['SERVICE', 'CLINIC MEETS', 'PATIENT FRIENDLY NAME',
                                     'ALLOW DIRECT PATIENT', 'DISPLAY CLIN APPT'])
            if index == 0:
                break
            if index == 2:
                VistA.write('')
            else:
                VistA.write('Y')
        VistA.write(self.cservice)
        VistA.wait('CLINIC?')
        VistA.write('N')
        VistA.wait('NUMBER:')
        VistA.write(self.cstopcode)
        VistA.wait('TYPE:')
        VistA.write(self.ctype)
        VistA.wait('MEDS?')
        VistA.write('')
        VistA.wait('TELEPHONE')
        VistA.write('')
        VistA.wait('FILMS?')
        VistA.write(self.cxray)
        VistA.wait('PROFILES?')
        VistA.write(self.cprofiles)
        for _ in range(0, 4):
            VistA.wait('LETTER:')
            VistA.write('')
        VistA.wait('TIME:')
        VistA.write(self.ccico)
        for provider in self.cproviders:
            VistA.wait('Select PROVIDER')
            VistA.write(provider)
            VistA.wait('new PROVIDER')
            VistA.write('Yes')
            VistA.wait('DEFAULT PROVIDER')
            VistA.write('')
        VistA.wait('PROVIDER')
        VistA.write('')
        VistA.wait('PRACTITIONER?')
        VistA.write('')
        for diag in self.cdiagnosis:
            VistA.wait('Select DIAGNOSIS')
            VistA.write(diag)
            index = VistA.multiwait(['\\?\\?', 'OK'])
            if index == 1:
                VistA.write('')
                VistA.wait('new DIAGNOSIS')
                VistA.write('Yes')
                VistA.wait('DEFAULT DIAGNOSIS')
                VistA.write('')
            else:
                for diag10 in self.cdiagnosisICD10:
                    VistA.wait('Select DIAGNOSIS')
                    VistA.write(diag)
                    index = VistA.multiwait(['\\?\\?', 'OK'])
                    if index == 1:
                        VistA.write('')
                        VistA.wait('new DIAGNOSIS')
                        VistA.write('Yes')
                        VistA.wait('DEFAULT DIAGNOSIS')
                        VistA.write('')
                break
        VistA.wait('Select DIAGNOSIS')
        VistA.write('')
        VistA.wait('CHK OUT:')
        VistA.write('')
        index = VistA.multiwait(['ALLOWABLE CONSECUTIVE NO-SHOWS', 'WORKLOAD VALIDATION'])
        if index == 1:
            VistA.write('')
            VistA.wait('ALLOWABLE CONSECUTIVE NO-SHOWS')
        VistA.write('10')
        VistA.wait('BOOKING')
        VistA.write('365')
        VistA.wait('BEGINS:')
        VistA.write(self.cstarttime)
        VistA.wait('REBOOK:')
        VistA.write('')
        VistA.wait('REBOOK:')
        VistA.write('365')
        VistA.wait('HOLIDAYS')
        VistA.write('Yes')
        VistA.wait('CODE:')
        VistA.write('303')
        VistA.wait('CLINIC')
        VistA.write('')
        VistA.wait('LOCATION')
        VistA.write('')
        VistA.wait('CLINIC')
        VistA.write('')
        VistA.wait('MAXIMUM')
        VistA.write('4')
        VistA.wait('INSTRUCTIONS')
        VistA.write('')
        VistA.wait('LENGTH')
        VistA.write('30')
        VistA.wait('LENGTH')
        VistA.write(self.cvarlen)
        VistA.wait('HOUR')
        VistA.write('2')
        for day in range(0, 7):
            VistA.wait('DATE:')
            VistA.write(self.cdate[day])
            VistA.wait('TIME:')
            VistA.write(self.ctime)
            VistA.wait('SLOTS:')
            VistA.write(self.cslots)
            VistA.wait('TIME:')
            VistA.write('')
            VistA.wait('INDEFINITELY')
            VistA.write('Yes')
        VistA.wait('DATE:')
        VistA.write('')
        VistA.wait('NAME:')
        VistA.write('')
