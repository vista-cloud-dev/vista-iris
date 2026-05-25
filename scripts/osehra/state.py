"""Idempotency for the install phases: a completion ledger + end-state probes.

Each Python phase (5/6/7/8) is guarded so a second run against a persistent
instance converges to a safe no-op (spec "Future Directions" §15 / refactor goal
D). Two complementary signals:

  * **Completion ledger** -- ``^VISTAIRIS("install",<phase>)`` is set when a
    phase finishes. Deterministic and written by us, so it is the reliable
    in-build/standalone signal: on a clean build the ledger is empty, so every
    phase runs exactly once (no behavior change); on a re-run it short-circuits.
  * **End-state probe** -- a cheap structural query confirming the phase's effect
    actually exists in the instance (authoritative cross-check, and what catches
    a populated instance whose ledger was never written). Probes are deliberately
    CONSERVATIVE: on a fresh instance every probe is false, so guards never skip
    a phase that hasn't run.

``phase_done`` = ledger OR probe. A phase that *partially* ran then failed is the
messy middle: re-running the verbatim dialog from the top is not guaranteed safe
(an "Are you adding ... NO//" prompt would be mis-answered), so the supported
recovery there is a fresh instance -- this module gives whole-phase convergence,
not mid-dialog re-entrancy (the verbatim sequences are preserved unchanged).

This module imports no pexpect: it drives the session via ``write``/``wait_re``
and reads the matched text, so its M-command construction is unit-testable with a
stub session.

Each query writes a unique sentinel and waits for it with ``wait_re`` (a regex
scan that skips past any prompt already in the buffer), so a guard never matches
a stray prompt and desyncs the proven dialog choreography. The sentinel is built
from split string literals (``"VS","TATE="``) so the joined token only appears in
IRIS's *output*, never in the echoed command.
"""
import re

_MARK = re.compile(r"VSTATE=([01])#")
_MARKED = re.compile(r"MARKED#")

# Conservative end-state probes: an M expression that is true once the phase's
# effect exists. Built from $D/$G reads only (no DUZ, no <UNDEFINED>). Refine
# against a live instance if any proves too strict/loose; the ledger is primary.
_PROBE = {
    # Phase 5: FileMan data dictionary + dictionary-of-files loaded (globals) and
    # the FileMan routine DIC present (routines) -- i.e. the import happened.
    "import": '($D(^DD))&($D(^DIC))&($T(+0^DIC)\'="")',
    # Phase 6: ^DINIT set the MUMPS OPERATING SYSTEM to CACHE (FileMan ^DD("OS")).
    "osinit": '($G(^DD("OS"))["CACHE")',
    # Phase 7: the System Manager (created only by addSystemManager) exists, and
    # the RPC Broker Site Parameters (#8994.1) domain pointer was written.
    "postinstall": '($D(^VA(200,"B","MANAGER,SYSTEM")))&(+$P($G(^XWB(8994.1,1,0)),"^",1)>0)',
    # Phase 8: the last sample patient + a clinical user exist (look up by name,
    # not DFN -- DFNs are not guaranteed 1-3 once FOIA Tier-0 pre-populates ^DPT).
    "sampledata": '($D(^DPT("B","PATIENT,GAMMATEST")))&($D(^VA(200,"B","ALEXANDER,ROBERT")))',
}

LEDGER = '^VISTAIRIS("install",%s)'


def _ledger_ref(phase):
    return LEDGER % ('"' + phase + '"')


def _query_bool(v, mexpr):
    """Evaluate an M boolean expression in the session; return True/False.

    Writes ``VSTATE=<0|1>#`` and scans forward (``wait_re``) to that sentinel,
    skipping any prompt already in the buffer. The sentinel is emitted as split
    literals so the regex matches only IRIS's output, never the echoed command.
    """
    v.write('W "VS","TATE=",$S(' + mexpr + ':1,1:0),"#"')
    v.wait_re(r"VSTATE=[01]#", 60)
    m = _MARK.search(v.connection.after or "")
    return bool(m) and m.group(1) == "1"


def is_marked(v, phase):
    """True if the completion ledger records ``phase`` as done."""
    return _query_bool(v, "$D(" + _ledger_ref(phase) + ")")


def probe(v, phase):
    """True if ``phase``'s end-state structurally exists in the instance."""
    mexpr = _PROBE.get(phase)
    if not mexpr:
        return False
    return _query_bool(v, mexpr)


def phase_done(v, phase):
    """True if ``phase`` is already complete (ledger marked OR end-state present).

    Authoritative on a fresh build (both false -> run); short-circuits a re-run.
    """
    return is_marked(v, phase) or probe(v, phase)


def mark_done(v, phase):
    """Record ``phase`` complete in the ledger ($H date.time) and confirm the SET.

    Writes the ledger node, then ``MARKED#`` (split literals) and scans to it, so
    we know the SET line executed regardless of any prompt left in the buffer.
    """
    v.write("S " + _ledger_ref(phase) + '=$ZDT($H,3) W "MARK","ED#"')
    v.wait_re(r"MARKED#", 60)
