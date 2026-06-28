# VistA-on-IRIS install driver — refactor notes (HOLISM)

Behavior-preserving decomposition of the WorldVistA-derived install driver into a
phase-aligned, idempotent, standalone-runnable Python package. **This was a
refactor, not a rewrite:** the build still produces a functionally identical
instance (same routines/globals, FileMan/Kernel install, domain/institution/
box:volume, ports, test users, sample patients, license posture).

Governing reference: `docs/archive/vista-iris-implementation-log.md` (§5 D1–D19,
§6 E1–E19, §8 Phase blueprint). Normative spec: `docs/design/vista-iris-container-spec-v3.md`.

---

## 1. BEFORE → AFTER module map

### Before (1,999 lines of driver Python)
| file | lines | role |
|------|------:|------|
| `setup.py` | 1,292 | **monolith** — every VistA dialog step (39 functions) carried from WorldVistA |
| `00_import.py` | 67 | thin orchestrator: `^%RI` / `LIST^ZGI` / `^ZTMGRSET` |
| `01_osinit.py` | 54 | thin orchestrator: device $I, MPI, DINIT/ZUSET |
| `02_postinstall.py` | 58 | thin orchestrator: site config, institution, users-prep |
| `03_sampledata.py` | 300 | orchestrator + `Clinic` class + CLINICS/PATIENTS data + per-file `_connect`/`_release` |
| `config.py` | (in 228) | values + a local `connect()` |
| `helper.py` | (in 228) | pexpect engine + unused WorldVistA methods |

### After (14-module package, 2,382 lines)
| file | lines | role |
|------|------:|------|
| `__main__.py` | 57 | **dispatcher** — `python -m vista <phase>` (lazy import per phase) |
| `config.py` | 106 | **Phase 0** — single declarative config + license-budget helpers |
| `session.py` | 108 | **centralized connection discipline** (connect / retry / clean release / context mgr) |
| `state.py` | 103 | **idempotency** — completion ledger + end-state probes |
| `helper.py` | 140 | pexpect `IRISSession` engine (dead WorldVistA methods removed) |
| `phase3_license.py` | 90 | **Phase 3 (NEW)** — license/capacity gate before the import |
| `phase5_import.py` | 78 | **Phase 5** — `^%RI` / `LIST^ZGI` / `^ZTMGRSET` (was `00_import.py`) |
| `phase6_osinit.py` | 59 | **Phase 6** — device $I, MPI, DINIT/ZUSET (was `01_osinit.py`) |
| `phase7_postinstall.py` | 66 | **Phase 7** — site config, institution, users (was `02_postinstall.py`) |
| `phase8_sampledata.py` | 104 | **Phase 8** — clinics, ward, users, patients (was `03_sampledata.py`) |
| `steps_fileman.py` | 36 | shared dialog lib: `startFileman`, `reindexFile` |
| `steps_osinit.py` | 55 | Phase 6 dialog lib: `addMPILocalNumber`, `initializeFileman` |
| `steps_postinstall.py` | 575 | Phase 7 dialog lib (18 verbatim step functions) |
| `steps_sampledata.py` | 805 | Phase 8 dialog lib (20 step fns + `Clinic` class + data) |

**Phase drivers are all 57–104 lines** — none is a new monolith. The bulk
(`steps_postinstall` + `steps_sampledata` = 1,380 lines) is the verbatim VistA
dialog **library**: a flat collection of independent, single-purpose functions,
not orchestration.

### Naming decision (refactor item B)
Renamed the execution-order files (`00–03`) to **blueprint phase numbers**
(`phase5/6/7/8`) for clarity. The dispatcher accepts both the name and the
number: `python -m vista import` ≡ `python -m vista 5`.

---

## 2. Behavior preservation — what was verified (static audit)

AST-level comparison of every function body, old vs new:

- **36 / 39** `setup.py` functions are **byte-for-byte identical** after the move.
- **2** changed in **comments/docstrings only** (M-command sequence unchanged):
  - `initializeFileman` — comment `00_import.py` → `Phase 5`.
  - `setupHL7Listener` — docstring expanded to mark it **DEFERRED / not called**
    (the #870 listener, log E7); body unchanged, still a stub.
- **1 removed:** `startTaskMan` — **dead code**. It was defined in `setup.py` but
  **never called** by any phase (the original `02_postinstall.py` already carried
  the "TaskMan is intentionally NOT cold-started" comment). TaskMan-off posture
  (E16 / §7) preserved; the explanatory comment is carried into `phase7`.
- `03_sampledata.py`'s `Clinic` class, `CLINICS`, and `PATIENTS` data are
  **byte-identical** in `steps_sampledata.py` / `phase8`.
- Phase 6/7/8 **step-call sequences match the old phase files exactly** (verified
  call-by-call). The only orchestration change: the old per-file `_connect` /
  `_release` / bare `V.write('h')` are replaced by the centralized
  `session.open_session` / `session.release` — same VistA effect, one definition.

## 3. Dead code removed (refactor item A)

| removed | from | why safe |
|---------|------|----------|
| `startTaskMan()` | `setup.py` | defined, never called (TaskMan stays off, E16) |
| `IRISSession.writectrl/send/login/ZN/exitToPrompt` | `helper.py` | **zero callers** in old or new code (WorldVistA telnet/remote carryover); release discipline now lives in `session.release` |
| `from pexpect import TIMEOUT` | `helper.py` | only used by the removed `exitToPrompt` |
| per-file `_connect`/`_release`/`main` | `03_sampledata.py` | promoted to `session.py` (one definition) |

Multi-platform connection classes (Windows/telnet, GT.M, SSH), the `chardet`
dependency, and Python-2 shims were already absent from the working `helper.py`
(removed in an earlier pass; documented in its module docstring).

## 4. Line-count delta

- **Removed:** 1,771 lines (`setup.py` 1,292 + `00–03` = 479).
- **Added:** a 14-module package, **2,382 lines** total (replaces the 228-line
  old `config.py`+`helper.py` as well).
- **Net Python growth ≈ +380 lines**, all *new capability*: Phase 3 gate (90),
  idempotency ledger/probes (103), centralized session discipline (108), the
  dispatcher (57), plus richer docstrings that capture the §6 error rationale
  inline so it is never re-derived. The verbatim dialogs themselves did not grow.

---

## 5. New properties + how to exercise them

### Standalone dispatch (item E)
Each phase opens its **own** connection and can run against a persistent instance:
```
python -m vista license      # Phase 3 (or: python -m vista 3)
python -m vista import        # Phase 5
python -m vista osinit        # Phase 6
python -m vista postinstall   # Phase 7  — re-run WITHOUT re-importing
python -m vista sampledata    # Phase 8
```
Run from anywhere with `PYTHONPATH=/opt/vista/scripts` (set in the Dockerfile).

### Idempotency (item D) — `state.py`
`phase_done = ledger OR end-state-probe`:
- **Ledger:** `^VISTAIRIS("install",<phase>)` set on completion (`mark_done`).
  Empty on a clean build → every phase runs exactly once (no behavior change).
- **End-state probe:** a conservative `$D`/`$G` structural check (e.g. Phase 8 =
  patient `PATIENT,GAMMATEST` + user `ALEXANDER,ROBERT` exist by name, not DFN).
A second run short-circuits with `[phaseN] ... already ... -- skipping`.
> Scope: whole-phase convergence, **not** mid-dialog re-entrancy. A phase that
> *partially* ran then died is recovered by a fresh instance (the verbatim
> dialogs are preserved unchanged and are not safe to re-enter mid-stream).

### Centralized connection discipline (item F) — `session.py`
One place enforces the two hard-won rules (log E8): **release cleanly**
(escape menus → `halt` → wait EOF so the license deregisters synchronously) and
**one connection at a time**. `connect_with_retry` rides out a transient
`<LICENSE LIMIT EXCEEDED>`. Phases use the `open_session` context manager or the
explicit `connect_with_retry`/`release` pair. pexpect engine unchanged.

### Phase 3 license/capacity gate (item C) — NEW
Reads `$SYSTEM.License.{KeyLicenseUnits,LUAvailable,LUConsumed,MaxConnections}`,
computes the cost of the **requested** service set (`config.requested_services()`),
and **refuses before the ~6 GB import** if it can't fit the 8-unit Community
ceiling — turning the late E16 failure (~40 min in) into an instant message.
Default posture (RPC only) fits → prints OK and proceeds unchanged. Read-only →
inherently idempotent.

### Single declarative config (item G) — `config.py`
One source of truth; env-var override names match the Makefile/compose contract
(verified against `Makefile` and `docker-compose.yml`):

| container env var | Makefile var | compose key | default |
|---|---|---|---|
| `VISTA_ENABLE_RPC` | `ENABLE_RPC` | `VISTA_ENABLE_RPC` | 1 (on) |
| `VISTA_RPC_PORT` | `RPC_PORT` | `VISTA_RPC_PORT` | 9430 |
| `VISTA_ENABLE_TASKMAN` | `ENABLE_TASKMAN` | `VISTA_ENABLE_TASKMAN` | 0 (off) |
| `VISTA_ENABLE_HL7` | `ENABLE_HL7` | `VISTA_ENABLE_HL7` | 0 (off) |
| `VISTA_HL7_PORT` | `HL7_PORT` | (5026 published) | 5026 |

Identity values unchanged: `DOMAIN=DEMO.VISTA.ORG`, `INSTITUTION=VISTA HEALTH
CARE`, `SITE_NUMBER=6161`, `VOLUME_SET=VISTA` (→ box:volume `VISTA:IRIS`),
`INSTANCE=IRIS`, `NAMESPACE=VISTA`.

---

## 6. Dockerfile (item H) — cached import preserved, image de-bloated (two-stage)

The Dockerfile is a **two-stage build**. The `builder` stage does the full
install; the `final` stage ships only the finished instance as one flat layer.

**`builder` stage** (throwaway — never shipped):
- RUN invocations call `python -m vista <phase>`; `ENV PYTHONPATH=/opt/vista/scripts`.
- **Layer 1 (cached import)** copies only shared + import-side modules
  (`config/helper/session/state/prepare/__init__/__main__/phase3_license/
  phase5_import`) and runs `license` → `prepare.py` → `import`. The dispatcher's
  **lazy** phase import means this layer can dispatch its phases without the
  Phase 6/7/8 modules present.
- **Layer 2 (iterated site build)** copies `steps_*` + `phase6/7/8` *after* the
  import, so editing the site build reuses the cached import layer (D14/E11).
- Journal-purge after a clean `iris stop` (E11/E15) intact in **both** layers.
- The expensive import remains its own cached layer — **not** collapsed into the
  site build. (Verified: a rebuild after this restructure cache-hit the whole
  builder stage — 0 re-imports — and only re-ran the final flatten.)

**`final` stage** (shipped) — fixes the single-stage bloat:
- The single-stage image was 25.6 GB because (a) the ~6 GB `vista-m` source tree
  `COPY`'d for the import lived in the image forever, and (b) IRIS stores each
  database as one `IRIS.DAT`, so every RUN that modified it forced an OverlayFS
  copy-up — the ~7 GB DB was stored once per RUN layer (import layer + site-build
  layer ≈ 14 GB of the same growing file).
- The final stage `FROM`s a clean base, installs only python3/pexpect (so an
  operator can re-run an idempotent phase against a live instance), copies the
  small driver package, then `COPY --from=builder /usr/irissys/{iris.cpf,mgr}` —
  the finished instance as **one** layer. No source tree, no duplicated `.DAT`,
  no dead import layer. All IRIS state lives under `/usr/irissys` and is
  `irisowner`-owned, so the copy is faithful (no setuid/root files to mangle).
- **Result: 25.6 GB → 11.9 GB (−54%), constant across rebuilds**; behavior
  identical (`make verify` §10 checks pass; idempotent phase re-run works in the
  slim image). The builder stage's per-layer `.DAT` churn now lives only in the
  build *cache* (prunable via `make fresh`), never in the shipped image.

---

## 7. Doc/code discrepancies found

1. **Stale spec-v2 references — RESOLVED.** Every `…-spec-v2.md` / "spec v2"
   reference in code/scripts was re-pointed to the now-normative v3 (Dockerfile
   header → §11.1, `helper.py` → §12, `Makefile` → §11.1/§11.3, `smoke.sh` → §10,
   `bootstrap.script` → §7 Phase 4, `startup.script` → §7 Phase 9, the HL7 stub →
   §13). The old "§8 step N" install-sequence numbering (v2) was remapped to the
   v3 phase numbers in §7. Verified: no `spec v2` references remain in
   `Dockerfile`/`Makefile`/`scripts/`.
2. **Download guard added (preflight + `make sources`).** `make sources` now
   short-circuits when `vista-m/Packages` is already populated
   (`>> … already present -- reusing (no download)`) and only fetches the
   submodule/clone when absent; `scripts/preflight.sh` reports it authoritatively
   (`routines present (N packages) -- build will reuse them, no download`). This
   prevents re-pulling the ~GB VistA-M routines on a rebuild.
3. **Working-tree doc moves are out of scope for this session.** The working
   tree shows `docs/vista-iris-implementation-log.md`, `…-spec-v2.md`, and other
   docs *deleted from `docs/` and relocated to `docs/historical/`*. The refactor
   guardrails state other sessions own the spec/log; **this refactor did not
   author those moves and they are NOT part of the refactor commits.** Surfaced
   here so they are handled deliberately, not folded into the driver change.

---

## 8. Verification status — RAN, end-to-end green

**Static (this environment):**
- `python3 -m py_compile` on all 14 modules → **all compile**.
- AST behavior-preservation audit (§2 above) → **clean**.
- Symbol coverage: all 33 `steps.*` calls + the `Clinic` class resolve to a
  definition; no dangling references.
- Env-var contract cross-checked against `Makefile` + `docker-compose.yml` → **matches**.

**Full build + runtime (after `make fresh` cleared a prior pre-refactor
container/image that held the ports):**
- `make preflight` → **PASSED** (ports free, 78 GB free, routines present:
  `routines present (140 packages) -- build will reuse them, no download`).
- `make sources` → `>> vista-m/Packages already present -- reusing (no download)`
  (the download guard fired in the real build path).
- `make build` → **succeeded, exit 0**; image `vista-iris:dev` (25.6 GB),
  all 16 steps; the Phase 3 gate ran live mid-build
  (`license units 8/6/2 … OK: … fit within the 8-unit budget. Proceeding.`).
- `make verify` (`scripts/smoke.sh`) → **§10 acceptance checks PASSED**: IRIS up;
  VISTA namespace login; FileMan `^DPT` sample patient `PATIENT,ALPHATEST`
  present; RPC Broker reachable on 9430; HL7 port reachable on 5026. (TaskMan
  check WARNs — expected and non-gating; TaskMan is intentionally off.)

**New properties demonstrated against the running instance** (via
`podman exec vista-iris python3 -m vista <phase>`):
- **Standalone + no re-import:** `import` → `[phase5] routines/globals already
  imported -- skipping` (the ~6 GB import is skipped).
- **Idempotent convergence:** `postinstall` run twice → both
  `[phase7] post-install site config already done -- skipping`.
- **Phase 3 standalone:** `license` → reads the live license and prints
  `OK: … fit within the 8-unit budget.`

### Reproduce
```
make fresh && make build && make verify
podman exec vista-iris python3 -m vista import        # -> skip (no re-import)
podman exec vista-iris python3 -m vista postinstall   # -> skip (idempotent)
VISTA_ENABLE_TASKMAN=1 podman exec vista-iris python3 -m vista license  # -> REFUSED
```
