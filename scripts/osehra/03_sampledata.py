#!/usr/bin/env python3
"""Step 3 -- Tier-1 sample data (spec v2 §9).

Forked from the sample-data half of PostImportSetupScript.py.in + ClinicSetup.py.in.
Creates: a NURS location, an orderable STREPTOZYME test + quick order, the
scheduling clinics, an inpatient ward with beds, the clinical users (Dr Robert
Alexander, Nurse Mary Smith, Clerk Joe Clerk) with access/verify codes and
e-signatures, the write-orders menu, and a few fictitious patients.

All identities are CLEARLY FICTITIOUS -- no real PHI.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import setup  # noqa: E402


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


# Seven scheduling clinics (from ClinicSetup.py.in).
CLINICS = [
    Clinic('Clinic1', 'C1', '0', '0000-0800', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '16',
           'Medicine', 'Regular', 'Yes', '', 'YES', [], '', '', '', 'Cardiology'),
    Clinic('Clinic2', 'C2', '8', '0800-1600', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '16',
           'Medicine', 'Regular', 'Yes', '', 'YES', [], '', '', '', 'Cardiology'),
    Clinic('CLINICX', 'CX', '16', '1600-2400', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '16',
           'Medicine', 'Regular', 'Yes', '', 'NO', [], '', '', '', 'Cardiology'),
    Clinic('CLInicA', 'CA', '0', '0000-0800', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '16',
           'Medicine', 'Regular', 'Yes', '', 'NO', [], '', '', 'Yes', '303'),
    Clinic('CLInicB', 'CB', '0', '0000-0800', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '2',
           'Surgery', 'Employee', 'Yes', '', 'YES', [], ['164.1', '391.8', '402.01'], ['C38.0', 'I01.8', 'I11.0'], 'yes', '435'),
    Clinic('CLInicC', 'CC', '0', '0000-0800', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '4',
           'None', 'Research', 'Yes', '', '', [], '', '', '', '435'),
    Clinic('CLInicD', 'CD', '0', '0000-0800', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '4',
           'Neurology', 'Service Connected', 'Yes', '', '', [], ['191.7'], ['C71.7'], '', 'NEUROLOGY'),
]

# Fictitious patients (replaces upstream's patdata0.csv). 666-xx-xxxx SSNs and
# TEST surnames make these unmistakably non-real (no PHI).
PATIENTS = [
    {'fullname': 'PATIENT,ALPHATEST', 'sex': 'M', 'dob': '2/3/1955', 'ssn': '666000001',
     'type': '1', 'veteran': 'Y', 'service': 'N', 'twin': 'N', 'cityob': 'CHICAGO', 'stateob': 'ILLINOIS'},
    {'fullname': 'PATIENT,BETATEST', 'sex': 'F', 'dob': '7/14/1968', 'ssn': '666000002',
     'type': '1', 'veteran': 'Y', 'service': 'N', 'twin': 'N', 'cityob': 'DENVER', 'stateob': 'COLORADO'},
    {'fullname': 'PATIENT,GAMMATEST', 'sex': 'M', 'dob': '11/30/1979', 'ssn': '666000003',
     'type': '1', 'veteran': 'Y', 'service': 'N', 'twin': 'N', 'cityob': 'AUSTIN', 'stateob': 'TEXAS'},
]


def main():
    V = config.connect("03_sampledata.log")
    setup.setupNursLocation(V, "FAKE NURWARD")
    setup.setupStrepTest(V)
    setup.registerVitalsCPRS(V)

    # Clinics: one via createClinic, plus the seven scheduling clinics.
    setup.createClinic(V, 'VISTA HEALTH CARE', 'VHC', 'M')
    for clinic in CLINICS:
        clinic.setup(V)

    # Inpatient ward with beds.
    setup.setupWard(V, 'VISTA MEDICAL CENTER', "VISTA HEALTH CARE", "TESTWARD1", "CLINICX", "1",
                    'Cardiac Surgery', [['1-A', 'bed1'], ['1-B', 'bed2'], ['2-A', 'bed3'], ['2-B', 'bed4']])
    setup.modifyDVBParams(V)

    # Sign on as the System Manager, then create the clinical users in-session.
    setup.signonZU(V, "SM1234", "SM1234!!")
    setup.addDoctor(V, "ALEXANDER,ROBERT", "RA", "000000029", "M", "fakedoc1", "2Doc!@#$")
    setup.addNurse(V, 'SMITH,MARY', 'MS', '000000030', 'F', 'fakenurse1', '2Nur!@#$')
    setup.addClerk(V, "CLERK,JOE", "JC", "000000112", "M", "fakeclerk1", "2Cle!@#$")
    setup.createOrderMenu(V)
    setup.addAllergiesPermission(V)
    setup.addTemplatePermission(V, "MS")

    # Turn off access/verify expiration (fresh connection, programmer access).
    V2 = config.connect("03_verifycodes.log")
    setup.setNonExpiringCodes(V2, ["ALEXANDER,ROBERT", 'SMITH,MARY', "CLERK,JOE"])

    time.sleep(10)

    # Each e-signature is set by signing in as that user (fresh connection).
    Vd = config.connect("03_sig_doc.log")
    setup.setupElectronicSignature(Vd, "fakedoc1", '2Doc!@#$', '1Doc!@#$', 'ROBA123')
    Vn = config.connect("03_sig_nurse.log")
    setup.setupElectronicSignature(Vn, "fakenurse1", "2Nur!@#$", "1Nur!@#$", "MARYS123")
    Vc = config.connect("03_sig_clerk.log")
    setup.setupElectronicSignature(Vc, "fakeclerk1", "2Cle!@#$", "1Cle!@#$", "CLERKJ123")

    # Register the sample patients (fresh connection).
    Vp = config.connect("03_patients.log")
    setup.addPatient(Vp, PATIENTS)


if __name__ == "__main__":
    main()
