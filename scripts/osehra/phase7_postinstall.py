#!/usr/bin/env python3
"""Phase 7 -- post-install site configuration (spec v3 §7 Phase 7).

Was ``02_postinstall.py``. In upstream order: HFS dir, resource logging, intro
text, device fixups, domain christening, box:volume + RPC Broker (XWB) listener
on RPC_PORT, volume set, the TaskMan STARTUP scheduling (dormant config), re-index,
System Manager, institution/division/MAS.

Run via: ``python -m osehra postinstall``.
"""
from . import config, session, state, steps_postinstall as steps
from .steps_fileman import reindexFile

NAME = "postinstall"


def run():
    V = session.connect_with_retry("phase7_postinstall.log")
    if state.phase_done(V, NAME):
        print("[phase7] post-install site config already done -- skipping")
        session.release(V)
        return

    steps.setupPrimaryHFSDir(V, config.HFS_DIR)
    steps.removeResourceUsageLogging(V)
    steps.setupIntroText(V, config.VISTA_M_TAG)
    steps.configureNULLDevice(V)
    steps.configureConsoleDevice(V)
    steps.configureHFSDevice(V)
    steps.setupVistADomain(V, config.DOMAIN)

    # RPC Broker (XWB) listener on RPC_PORT (9430) -- CPRS / RPC clients.
    steps.setupBoxVolPair(V, config.VOLUME_SET, config.DOMAIN, config.RPC_PORT)
    steps.setupVolumeSet(V, config.DOMAIN, config.VOLUME_SET, config.NAMESPACE)

    # Schedule the listeners + HL7 services at every TaskMan startup.
    steps.scheduleOption(V, 'XWB LISTENER STARTER', 'STARTUP')
    steps.scheduleOption(V, 'XMRONT', 'STARTUP')
    steps.scheduleOption(V, 'HL AUTOSTART LINK MANAGER', 'STARTUP')
    steps.scheduleOption(V, 'HL TASK RESTART', 'STARTUP')
    steps.scheduleOption(V, 'HL PURGE TRANSMISSIONS', '1D', scheduleTime='0045')

    # HL7 MLLP listener on HL7_PORT (5026) -- spec v3 §7 Phase 7. DEFERRED: the
    # "HL EDIT LOGICAL LINKS" option is a full-screen List Manager UI that pexpect
    # cannot drive reliably; an HL LOGICAL LINK (#870) listener needs a programmatic
    # FileMan/global approach instead. The HL7 Link Manager itself is already
    # autostart-scheduled above (HL AUTOSTART LINK MANAGER). TODO: implement #870.
    # steps.setupHL7Listener(V, config.HL7_PORT)

    reindexFile(V, '19.2')
    # TaskMan is intentionally NOT cold-started here. `D ^ZTMB` spawns a manager +
    # submanager + every scheduled STARTUP job (XWB listener, HL7 link manager, ...)
    # as persistent processes, which exhausts IRIS Community's ~8-unit process/license
    # cap and starves the rest of the build (Phase 8 hit <LICENSE LIMIT EXCEEDED>). The
    # RPC Broker is started at container boot by the %ZSTART hook (scripts/startup.script,
    # one listener process); the scheduled options above remain as dormant config.
    steps.removeCAPRILogin(V)
    steps.addSystemManager(V)

    # Institution + Medical Center division (identities per §9 Tier-1).
    steps.addInstitution(V, config.INSTITUTION, '6100')
    steps.addDivision(V, 'VISTA MEDICAL CENTER', '6101', '6100')
    steps.addtoMASParameter(V, config.INSTITUTION, 'VISTA MEDICAL CENTER')

    state.mark_done(V, NAME)
    session.release(V)
