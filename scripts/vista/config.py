"""Phase 0 -- the single declarative configuration for the Python install driver.

All values default here and are overridable by environment variables, so the
Dockerfile / Makefile / Compose can parameterize the build without editing code
(spec v3 §7 Phase 0). This module is the one source of truth the phases read;
the connection logic lives in :mod:`session` and the idempotency ledger in
:mod:`state`.

Env-var contract (names match the Makefile / docker-compose.yml so nothing
drifts; see spec v3 §9.4):

    container env var        Makefile var      compose key                default
    ----------------------   ---------------   ------------------------   -------
    VISTA_ENABLE_RPC         ENABLE_RPC        VISTA_ENABLE_RPC           1  (on)
    VISTA_RPC_PORT           RPC_PORT          VISTA_RPC_PORT             9430
    VISTA_ENABLE_TASKMAN     ENABLE_TASKMAN    VISTA_ENABLE_TASKMAN       0  (off)
    VISTA_ENABLE_HL7         ENABLE_HL7        VISTA_ENABLE_HL7           0  (off)
    VISTA_HL7_PORT           HL7_PORT          (5026 published only)      5026

The ENABLE_* toggles are read at runtime by the %ZSTART hook (Phase 9); the
driver reads the *same* names so Phase 3 (license/capacity) can budget the
requested service set before the expensive import. This module intentionally
imports nothing heavy (no pexpect) so the pure helpers below are unit-testable.
"""
import os


def _flag(name, default):
    """Parse a boolean-ish env toggle the same way the %ZSTART hook does
    (blank -> default; 0/false/off/no -> off; anything else -> on)."""
    v = os.environ.get(name, "")
    if v == "":
        return bool(default)
    return v.strip().lower() not in ("0", "false", "off", "no")


# -- identity / naming (spec v3 §7 Phase 0; do not change without the spec) ----
INSTANCE = os.environ.get("VISTA_INSTANCE", "IRIS")
NAMESPACE = os.environ.get("VISTA_NAMESPACE", "VISTA")
USERNAME = os.environ.get("VISTA_USERNAME", "_SYSTEM")
PASSWORD = os.environ.get("VISTA_PASSWORD", "SYS")
# DOMAIN is the messaging domain / DINIT site name (file #4.2) -- it must be
# punctuation-restricted (dots/dashes, NO spaces; log E5/D7). INSTITUTION is the
# facility name (file #4), where spaces are fine. These are distinct in VistA.
DOMAIN = os.environ.get("VISTA_DOMAIN", "DEMO.VISTA.ORG")
INSTITUTION = os.environ.get("VISTA_INSTITUTION", "VISTA HEALTH CARE")
SITE_NUMBER = os.environ.get("VISTA_SITE_NUMBER", "6161")
# Volume-set name; on IRIS GETENV^%ZOSV reports "...^VISTA:IRIS", so "VISTA" is
# the anchor that yields box:volume pair "VISTA:IRIS" (log D8/E6).
VOLUME_SET = os.environ.get("VISTA_VOLUME_SET", "VISTA")

# -- ports (spec v3 §10.1) -----------------------------------------------------
RPC_PORT = os.environ.get("VISTA_RPC_PORT", "9430")
HL7_PORT = os.environ.get("VISTA_HL7_PORT", "5026")

# -- service toggles (spec v3 §9.4 -- the license budget surface) --------------
# Defaults preserve the RPC-only posture: TaskMan/HL7 OFF (log E16 / §7).
ENABLE_RPC = _flag("VISTA_ENABLE_RPC", 1)
ENABLE_TASKMAN = _flag("VISTA_ENABLE_TASKMAN", 0)
ENABLE_HL7 = _flag("VISTA_ENABLE_HL7", 0)

# -- misc / build-time ---------------------------------------------------------
HFS_DIR = os.environ.get("VISTA_HFS_DIR", "/tmp")
VISTA_M_TAG = os.environ.get("VISTA_M_TAG", "FOIA")
LOG_DIR = os.environ.get("VISTA_LOG_DIR", "/tmp")

# IRIS Community license ceiling (spec v3 §9.1; log D3). Used by Phase 3.
LICENSE_UNITS_COMMUNITY = 8


# -- license budget helpers (pure; used by Phase 3, unit-testable) -------------
# Per-service unit cost of the *requested* service set, measured on Community
# (spec v3 §9.2 / log D3/D13/E16). RPC = 1 listener (+1 per CPRS client, counted
# at connect time, not here); TaskMan cold-start spawns a manager+submanager+all
# scheduled STARTUP jobs (~37 procs) -- it exhausts the whole budget; HL7 ~ 1 per
# active link (inert until the deferred #870 listener exists).
SERVICE_COST = {
    "rpc": 1,
    "taskman": LICENSE_UNITS_COMMUNITY,  # effectively the whole budget (E16)
    "hl7": 1,
}
# IRIS core baseline (daemons, superserver, portal/FHIR); most are license-exempt
# but reserve a small headroom so the budget isn't optimistic (spec v3 §9.2).
BASELINE_UNITS = 2


def requested_services():
    """Return the set of services the current config asks the hook to start."""
    svc = set()
    if ENABLE_RPC:
        svc.add("rpc")
    if ENABLE_TASKMAN:
        svc.add("taskman")
    if ENABLE_HL7:
        svc.add("hl7")
    return svc


def license_cost(services):
    """Baseline + the summed per-service cost of ``services`` (in license units)."""
    return BASELINE_UNITS + sum(SERVICE_COST.get(s, 0) for s in services)


def fits(services, units):
    """True if the requested service set fits within ``units`` license units."""
    return license_cost(services) <= units
