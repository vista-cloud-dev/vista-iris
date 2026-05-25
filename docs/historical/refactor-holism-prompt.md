# Install-Driver Holism Refactor — Session Prompt

**Purpose:** A self-contained prompt to paste into a fresh Claude Code session to
refactor the VistA-on-IRIS install driver (`scripts/osehra/`) for holism —
decomposing the 1,292-line `setup.py` monolith into phase-aligned modules, making
each phase idempotent and standalone-runnable, and encoding the fixes recorded in
the implementation log — **without changing what the build produces**.

**How to use:** Open a new session at the repo root (`vista-cloud-dev/vista-iris`)
and paste everything in the prompt block below. The prompt instructs the session
to plan first (BEFORE→AFTER module map + idempotency/standalone mechanisms +
dead-code list) and wait for your approval before refactoring. It treats a green
`make build`/`make verify` as the definition of done.

---

ROLE & GOAL
You are refactoring the VistA-on-IRIS install driver in this repo for HOLISM,
WITHOUT changing what it produces. Today the driver works but its logic is
concentrated in a 1,292-line monolith (scripts/osehra/setup.py) carried over
from the original OSEHRA installer. The goal is a clean, phase-aligned driver
where each phase is small, idempotent, and runnable on its own — encoding the
hard-won fixes already discovered, so a future build (or a future Go port)
never repeats the original trial-and-error.

THIS IS A REFACTOR, NOT A REWRITE. The build must still produce a functionally
identical working instance: same routines/globals, same FileMan/Kernel install,
same domain/institution/box:volume, same ports, same test users and sample
patients, same license posture. You are changing HOW the driver is organized and
made re-runnable — not WHAT it does.

INPUTS (read all of these fully before touching code)
1. docs/vista-iris-implementation-log.md — THE governing reference. Internalize:
   §5 (discoveries D1–D19), §6 (errors E1–E19 + remedies), §7 (deferred/caveats),
   §8 (Phase 0–11 blueprint — each phase names the failure it prevents),
   §8.13 (rewrite/refactor principles), §10 (key technical facts). Every fix in
   §6 must be PRESERVED as behavior and captured as rationale — not re-derived.
2. The spec: if docs/vista-iris-container-spec-v3.md exists, treat it as
   normative; otherwise use docs/vista-iris-container-spec-v2.md. Do NOT edit
   either; this session does not touch spec docs.
3. The current driver and its callers (read and map all of them):
   scripts/osehra/setup.py (the monolith), scripts/osehra/00_import.py,
   01_osinit.py, 02_postinstall.py, 03_sampledata.py, config.py, helper.py,
   prepare.py, __init__.py, m/ZGI.m; plus the callers/lifecycle:
   Dockerfile, Makefile, docker-compose.yml, scripts/bootstrap.script,
   scripts/startup.script, scripts/license.script, scripts/preflight.sh,
   scripts/smoke.sh.

WHAT THIS REFACTOR MUST DO
A. Decompose setup.py. Distribute its logic into the phase modules already
   present and a shared helper layer; delete OSEHRA branches the IRIS path never
   takes (dead generality). End state: setup.py is gone, or reduced to a thin
   compatibility shim. No phase module should be a new monolith.

B. Align modules to the blueprint phases (log §8). The Python driver owns:
   - Phase 3  license/capacity check  (NEW — see C)
   - Phase 5  routine + global import   (^%RI / LIST^ZGI / ^ZTMGRSET 3; ZGI patch)
   - Phase 6  OS-interface init         (DINIT→CACHE, ZUSET, devices, MPI)
   - Phase 7  post-install / site cfg   (FileMan, DOMAIN[no spaces], box:vol, inst)
   - Phase 8  sample data               (UPDATE^DIE patients w/ 7 identifiers; users)
   Propose in your plan whether to rename the 00–03 files to the blueprint phase
   numbers (recommended for clarity) or keep execution-order names with a
   documented mapping. (Phases 0/1/2/4/9/10/11 live in config/preflight.sh/
   Dockerfile/bootstrap.script/startup.script/smoke.sh — leave their HOME, but
   align naming and config with the Python phases.)

C. Add the early Phase 3 license/capacity check (it does not exist today).
   Query IRIS license units/availability and compute the cost of the REQUESTED
   service set (RPC≈1+1/client, TaskMan≈many, HL7≈1/link); refuse or warn BEFORE
   the expensive import if it won't fit the 8-unit Community ceiling. This turns
   the late E16 failure (a 40-minute build dying in the site phase) into an
   instant message.

D. Make every Python phase IDEMPOTENT. Re-running a completed phase must
   converge safely (detect prior completion via instance state — e.g. routine/
   global counts, DOMAIN christened, box:volume set, patient DFNs 1–3, users
   exist — and/or a phase-completion ledger global). Decide the mechanism in
   your plan and apply it uniformly.

E. Make every Python phase STANDALONE-RUNNABLE against a persistent instance,
   via one dispatcher (e.g. `python -m osehra <phase>`), so you can re-run Phase
   7 without re-running the 6 GB import. Each phase opens its OWN connection.

F. Centralize the connection discipline. Promote the "release cleanly" helper
   (escape menus → halt → wait EOF, per E8) and the one-connection-at-a-time rule
   into the shared helper; every phase uses it. Keep the pexpect engine — do NOT
   swap expect libraries and do NOT port to Go in this session.

G. One declarative config (Phase 0). Make config the single source of truth for
   the Python driver, with env-var overrides whose names MATCH the Makefile/
   compose contract (VISTA_ENABLE_RPC, VISTA_RPC_PORT, VISTA_ENABLE_TASKMAN,
   VISTA_ENABLE_HL7; DOMAIN=DEMO.OSEHRA.ORG, INSTITUTION="VISTA HEALTH CARE",
   VOLUME_SET=VISTA, box:volume VISTA:IRIS, ports 1972/52773/9430/5026).
   Document the mapping. Do not build a cross-language config system — just stop
   the drift.

H. Update the Dockerfile's RUN invocations to call the new module structure,
   PRESERVING the layer boundaries: the import (Phase 5) MUST remain its own
   cached layer so iterating later phases never re-imports (D14/E11); the
   journal-purge + clean-stop-before-commit hygiene (E11/E15) stays intact.

WHAT THIS REFACTOR MUST NOT DO (guardrails)
- Do NOT change behavior or outputs: same M routines/FileMan calls, same naming,
  same data, same listeners. If you find a genuine bug, note it in the report —
  do not silently "fix" it here.
- Do NOT implement the deferred HL7 MLLP #870 listener (E7) — keep it a clearly
  marked stub. Do NOT enable TaskMan by default (E16/§7) or change the license
  posture (RPC-only default).
- Do NOT modify the M logic or m/ZGI.m beyond what is already patched, and do NOT
  change ports, IRIS image tags, domain/institution/volume-set values.
- Do NOT collapse the Dockerfile import layer into the site-build layer.
- Do NOT edit the spec docs or the implementation log (other sessions own those).
  If the refactor surfaces a doc/code discrepancy, record it in the report.
- Do NOT port to Go or change the expect engine.

METHOD (plan mode first — do not refactor until approved)
1. Read all inputs. Produce a BEFORE→AFTER module map: what setup.py contains,
   what each current phase file does, what calls what, and what is dead code.
2. Present for my approval: (a) the target module/dispatcher layout and naming
   decision (B), (b) the idempotency mechanism (D) and standalone-run mechanism
   (E), (c) the list of dead OSEHRA branches you will delete, (d) the Phase 3
   design (C), (e) how the Dockerfile invocations change while preserving layers
   (H). WAIT for approval.
3. Execute in reviewable commits: keep behavior-preserving MOVES (decompose,
   delete dead code) in separate commits from NEW capability (idempotency,
   standalone dispatch, Phase 3). One concern per commit where practical.

OUTPUT / DELIVERABLES
- A refactored scripts/osehra/: setup.py decomposed/removed; phases aligned to
  the blueprint; idempotent + standalone-runnable; centralized connect/release;
  single declarative config; early Phase 3 check.
- Updated Dockerfile RUN steps matching the new structure, layers preserved.
- A refactor report (print it in your final message; optionally also save it as
  scripts/osehra/REFACTOR-NOTES.md): before/after module map, dead code removed,
  line-count delta, the idempotency + standalone-run mechanisms with example
  commands, any doc/code discrepancies found, and exactly what was and was NOT
  verified.

VERIFICATION (definition of done — be honest about what you actually ran)
- `make preflight` passes.
- `make build` succeeds and `make verify` (scripts/smoke.sh) passes — i.e. the
  refactored driver still yields a working instance (listeners up; expected
  patient/user counts). This is heavy (~25 GB image, long build, needs the
  preflight gate). If you cannot run it in this environment, STOP short of
  claiming success: state clearly that the build was not run and provide a
  precise manual verification checklist.
- Demonstrate the new properties: run at least one phase TWICE to show
  idempotent convergence, and run one phase STANDALONE against an
  already-built-up instance to show it does not re-import.

ACCEPTANCE CRITERIA
- setup.py is decomposed/removed; no phase module is a new monolith; dead OSEHRA
  branches deleted.
- Each Python phase is idempotent (second run is a safe no-op/converges) and
  individually runnable against a persistent instance.
- Phase 3 license/capacity check exists and runs before the import.
- Connection discipline centralized (one connection at a time; clean release).
- One declarative config; override names aligned with the Makefile/compose.
- Dockerfile import stays a separate cached layer; journal-purge/clean-stop
  hygiene intact.
- Behavior unchanged: ports, tags, naming, data, M logic, license posture all
  identical; HL7 #870 still deferred; TaskMan still off by default.
- Build + verify green, OR an explicit statement of what wasn't run plus a
  manual checklist.

Begin by reading the inputs and mapping the current driver, then present the
BEFORE→AFTER plan for my approval. Do not refactor until I approve.
