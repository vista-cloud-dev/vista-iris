#!/usr/bin/env python3
"""Step 2 -- post-install site configuration (spec v2 §8 steps 6-9).

Forked from PostImportSetupScript.py.in (config half), in upstream order:
HFS dir, resource logging, intro text, device fixups, domain christening,
box:volume + RPC Broker (XWB) listener on RPC_PORT, volume set, TaskMan startup
options (XWB listener, HL7 link manager), the HL7 MLLP listener on HL7_PORT,
re-index, TaskMan cold-boot, System Manager, institution/division/MAS.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import setup  # noqa: E402

V = config.connect("02_postinstall.log")

setup.setupPrimaryHFSDir(V, config.HFS_DIR)
setup.removeResourceUsageLogging(V)
setup.setupIntroText(V, config.VISTA_M_TAG)
setup.configureNULLDevice(V)
setup.configureConsoleDevice(V)
setup.configureHFSDevice(V)
setup.setupVistADomain(V, config.SITE_NAME)

# RPC Broker (XWB) listener on RPC_PORT (9430) -- CPRS / RPC clients.
setup.setupBoxVolPair(V, config.VOLUME_SET, config.SITE_NAME, config.RPC_PORT)
setup.setupVolumeSet(V, config.SITE_NAME, config.VOLUME_SET, config.NAMESPACE)

# Schedule the listeners + HL7 services at every TaskMan startup.
setup.scheduleOption(V, 'XWB LISTENER STARTER', 'STARTUP')
setup.scheduleOption(V, 'XMRONT', 'STARTUP')
setup.scheduleOption(V, 'HL AUTOSTART LINK MANAGER', 'STARTUP')
setup.scheduleOption(V, 'HL TASK RESTART', 'STARTUP')
setup.scheduleOption(V, 'HL PURGE TRANSMISSIONS', '1D', scheduleTime='0045')

# HL7 MLLP listener on HL7_PORT (5026) -- spec §8 step 8 (UNVERIFIED; see setup.py).
setup.setupHL7Listener(V, config.HL7_PORT)

setup.reindexFile(V, '19.2')
setup.startTaskMan(V)
setup.removeCAPRILogin(V)
setup.addSystemManager(V)

# Institution + Medical Center division (identities per §9 Tier-1).
setup.addInstitution(V, config.SITE_NAME, '6100')
setup.addDivision(V, 'VISTA MEDICAL CENTER', '6101', '6100')
setup.addtoMASParameter(V, config.SITE_NAME, 'VISTA MEDICAL CENTER')
