#!/usr/bin/env python3
"""Phase 8 -- Tier-1 sample data (spec v3 §7 Phase 8 / §8).

Was ``03_sampledata.py``. Creates: a NURS location, an orderable STREPTOZYME test
+ quick order, the scheduling clinics, an inpatient ward with beds, the clinical
users (Dr Robert Alexander, Nurse Mary Smith, Clerk Joe Clerk) with access/verify
codes and e-signatures, the write-orders menu, and the fictitious patients.

Each connection opens one at a time and is released cleanly (Community license
discipline, log E8) -- handled by :mod:`session`. All identities are CLEARLY
FICTITIOUS -- no real PHI. Run via: ``python -m osehra sampledata``.
"""
import time

from . import session, state, steps_sampledata as steps

NAME = "sampledata"

# Seven scheduling clinics (from ClinicSetup.py.in).
CLINICS = [
    steps.Clinic('Clinic1', 'C1', '0', '0000-0800', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '16',
                 'Medicine', 'Regular', 'Yes', '', 'YES', [], '', '', '', 'Cardiology'),
    steps.Clinic('Clinic2', 'C2', '8', '0800-1600', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '16',
                 'Medicine', 'Regular', 'Yes', '', 'YES', [], '', '', '', 'Cardiology'),
    steps.Clinic('CLINICX', 'CX', '16', '1600-2400', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '16',
                 'Medicine', 'Regular', 'Yes', '', 'NO', [], '', '', '', 'Cardiology'),
    steps.Clinic('CLInicA', 'CA', '0', '0000-0800', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '16',
                 'Medicine', 'Regular', 'Yes', '', 'NO', [], '', '', 'Yes', '303'),
    steps.Clinic('CLInicB', 'CB', '0', '0000-0800', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '2',
                 'Surgery', 'Employee', 'Yes', '', 'YES', [], ['164.1', '391.8', '402.01'], ['C38.0', 'I01.8', 'I11.0'], 'yes', '435'),
    steps.Clinic('CLInicC', 'CC', '0', '0000-0800', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '4',
                 'None', 'Research', 'Yes', '', '', [], '', '', '', '435'),
    steps.Clinic('CLInicD', 'CD', '0', '0000-0800', ['t', 't+1', 't+2', 't+3', 't+4', 't+5', 't+6', 't+7'], '4',
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


def run():
    V = session.connect_with_retry("phase8_sampledata.log")
    if state.phase_done(V, NAME):
        print("[phase8] sample data already present -- skipping")
        session.release(V)
        return

    steps.setupNursLocation(V, "FAKE NURWARD")
    steps.setupStrepTest(V)
    steps.registerVitalsCPRS(V)

    # Clinics: one via createClinic, plus the seven scheduling clinics.
    steps.createClinic(V, 'VISTA HEALTH CARE', 'VHC', 'M')
    for clinic in CLINICS:
        clinic.setup(V)

    # Inpatient ward with beds.
    steps.setupWard(V, 'VISTA MEDICAL CENTER', "VISTA HEALTH CARE", "TESTWARD1", "CLINICX", "1",
                    'Cardiac Surgery', [['1-A', 'bed1'], ['1-B', 'bed2'], ['2-A', 'bed3'], ['2-B', 'bed4']])
    steps.modifyDVBParams(V)

    # Sign on as the System Manager, then create the clinical users in-session.
    steps.signonZU(V, "SM1234", "SM1234!!")
    steps.addDoctor(V, "ALEXANDER,ROBERT", "RA", "000000029", "M", "fakedoc1", "2Doc!@#$")
    steps.addNurse(V, 'SMITH,MARY', 'MS', '000000030', 'F', 'fakenurse1', '2Nur!@#$')
    steps.addClerk(V, "CLERK,JOE", "JC", "000000112", "M", "fakeclerk1", "2Cle!@#$")
    steps.createOrderMenu(V)
    steps.addAllergiesPermission(V)
    steps.addTemplatePermission(V, "MS")
    session.release(V)

    # Turn off access/verify expiration (fresh connection, programmer access).
    V2 = session.connect_with_retry("phase8_verifycodes.log")
    steps.setNonExpiringCodes(V2, ["ALEXANDER,ROBERT", 'SMITH,MARY', "CLERK,JOE"])
    session.release(V2)

    time.sleep(10)

    # Each e-signature is set by signing in as that user. Open one session at a
    # time and release it -- IRIS Community caps concurrent processes.
    Vd = session.connect_with_retry("phase8_sig_doc.log")
    steps.setupElectronicSignature(Vd, "fakedoc1", '2Doc!@#$', '1Doc!@#$', 'ROBA123')
    session.release(Vd)
    Vn = session.connect_with_retry("phase8_sig_nurse.log")
    steps.setupElectronicSignature(Vn, "fakenurse1", "2Nur!@#$", "1Nur!@#$", "MARYS123")
    session.release(Vn)
    Vc = session.connect_with_retry("phase8_sig_clerk.log")
    steps.setupElectronicSignature(Vc, "fakeclerk1", "2Cle!@#$", "1Cle!@#$", "CLERKJ123")
    session.release(Vc)

    # Register the sample patients (fresh connection); mark the phase complete on
    # this last connection before releasing it.
    Vp = session.connect_with_retry("phase8_patients.log")
    steps.addPatient(Vp, PATIENTS)
    state.mark_done(Vp, NAME)
    session.release(Vp)
