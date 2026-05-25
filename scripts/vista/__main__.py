"""Dispatcher -- ``python -m vista <phase>`` runs one install phase standalone.

Each phase opens its OWN ``iris session`` connection (see :mod:`session`), is
idempotent (a completed phase is a safe no-op; see :mod:`state`), and can be
re-run against a persistent instance without re-running earlier phases -- so you
can iterate Phase 7 without re-running the ~6 GB import. Phases are imported
LAZILY so the cached import layer (which ships only a subset of phase modules)
can still dispatch its phase.

Examples::

    python -m vista license       # Phase 3 (or: 3)
    python -m vista import        # Phase 5 (or: 5)
    python -m vista postinstall   # Phase 7 (or: 7) -- re-runnable, no re-import
"""
import importlib
import sys

# phase name -> module within this package
PHASES = {
    "license": "phase3_license",
    "import": "phase5_import",
    "osinit": "phase6_osinit",
    "postinstall": "phase7_postinstall",
    "sampledata": "phase8_sampledata",
}
# blueprint phase number -> name (spec v3 §7)
ALIASES = {"3": "license", "5": "import", "6": "osinit",
           "7": "postinstall", "8": "sampledata"}
ORDER = ["license", "import", "osinit", "postinstall", "sampledata"]


def usage():
    nums = {name: num for num, name in ALIASES.items()}
    sys.stderr.write("usage: python -m vista <phase>\n")
    sys.stderr.write("phases (blueprint #):\n")
    for name in ORDER:
        sys.stderr.write("  %-12s (Phase %s)  -> %s\n"
                         % (name, nums.get(name, "?"), PHASES[name]))


def main(argv):
    if len(argv) != 1:
        usage()
        return 2
    name = ALIASES.get(argv[0].lower(), argv[0].lower())
    if name not in PHASES:
        sys.stderr.write("error: unknown phase %r\n" % argv[0])
        usage()
        return 2
    module = importlib.import_module("." + PHASES[name], __package__)
    module.run()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
