#!/usr/bin/env python3
"""Phase 3 -- license / capacity check, run BEFORE the expensive import.

NEW in the refactor (spec v3 §7 Phase 3). IRIS Community caps license units at 8
(spec v3 §9.1); TaskMan cold-start alone exhausts the budget (~37 processes, log
E16). The original build discovered that only ~40 minutes in, when Phase 8 died
with ``<LICENSE LIMIT EXCEEDED>``. This phase queries the live license and the
requested service toggles up front and turns that late failure into an instant
message:

  * read ``$SYSTEM.License.{KeyLicenseUnits,LUAvailable,LUConsumed,MaxConnections}()``;
  * compute the cost of the REQUESTED service set (config.requested_services());
  * if it provably cannot fit (e.g. TaskMan on Community) -> REFUSE (exit 1)
    before the import; otherwise print the budget and proceed.

The default posture (RPC only, TaskMan/HL7 off) fits comfortably, so the default
build prints OK and continues unchanged. Read-only -> inherently idempotent.
Run via: ``python -m osehra license``.
"""
import re
import sys

from . import config, session

_LIC = re.compile(r"LIC:(\d+):(\d+):(\d+):(\d+)#")


def query_license(V):
    """Return (units, available, consumed, max_connections) from the instance.

    The marker is split (``"LI","C:"``) so the regex matches only IRIS's output.
    Returns None if the values can't be read (so the caller can warn, not break).
    """
    V.write('W "LI","C:",$SYSTEM.License.KeyLicenseUnits(),":",'
            '$SYSTEM.License.LUAvailable(),":",$SYSTEM.License.LUConsumed(),":",'
            '$SYSTEM.License.MaxConnections(),"#"')
    try:
        V.wait_re(r"LIC:\d+:\d+:\d+:\d+#", 60)
    except Exception:  # noqa: BLE001 -- a query failure must not break the build
        return None
    m = _LIC.search(V.connection.after or "")
    if not m:
        return None
    return tuple(int(x) for x in m.groups())


def run():
    V = session.connect("phase3_license.log")
    try:
        lic = query_license(V)
    finally:
        session.release(V)

    services = sorted(config.requested_services())
    cost = config.license_cost(services)

    print("==== Phase 3: IRIS license / capacity check ====")
    if lic is None:
        print("  WARN: could not read $SYSTEM.License.* -- skipping the capacity "
              "gate (assuming Community %d units)." % config.LICENSE_UNITS_COMMUNITY)
        units = config.LICENSE_UNITS_COMMUNITY
    else:
        units, available, consumed, maxconn = lic
        print("  license units (total/available/consumed): %d / %d / %d"
              % (units, available, consumed))
        print("  max connections                         : %d" % maxconn)
    if units <= 0:
        units = config.LICENSE_UNITS_COMMUNITY

    print("  requested services: %s" % (", ".join(services) or "(none)"))
    print("  estimated cost     : %d unit(s)  [baseline %d + services]"
          % (cost, config.BASELINE_UNITS))
    if "hl7" in services:
        print("  NOTE: HL7 is requested but the #870 MLLP listener is deferred -- "
              "it will not bind a port (spec v3 §13).")

    if not config.fits(services, units):
        print("  REFUSED: the requested service set needs ~%d unit(s) but the "
              "license has %d. " % (cost, units), end="")
        if "taskman" in services:
            print("TaskMan cold-start exhausts the 8-unit Community budget "
                  "(~37 processes, log E16); it needs a larger license.")
        else:
            print("Reduce the requested services or use a larger license.")
        print("  (Refusing now, before the ~6 GB import, instead of failing in "
              "the site phase.)")
        sys.exit(1)

    print("  OK: requested services fit within the %d-unit budget. Proceeding."
          % units)
