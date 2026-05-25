# VistA on IRIS — Implementation Log & Rewrite Guide

**Status:** Living record · **Date:** 2026-05-24 · **Scope:** the complete implementation session that took this repo from an empty directory to a reproducible, license-managed, containerized VistA-on-IRIS instance — plus a phased blueprint for re-implementing it cleanly (in this stack or another, e.g. Go).

This document records **what was decided, what was discovered, what broke and how it was fixed**, and distills it into an ordered flow so a fresh implementation can avoid the trial-and-error this one went through. Read §8 first if you only want the rewrite recipe.

---

## Table of Contents

1. [Purpose of this document](#1-purpose)
2. [The original objective](#2-original-objective)
3. [Session narrative (chronological)](#3-session-narrative)
4. [Decisions log (incl. Claude questions + user responses)](#4-decisions-log)
5. [Discoveries](#5-discoveries)
6. [Errors encountered & remedies](#6-errors--remedies)
7. [Caveats, deferred items & limitations](#7-caveats--deferred)
8. [Clean re-implementation blueprint (ordered flow)](#8-rewrite-blueprint)
9. [Component / file reference](#9-component-reference)
10. [Key technical facts (appendix)](#10-key-facts)

---

<a name="1-purpose"></a>
## 1. Purpose of this document

The first working build was reached by discovery, not by design — a dozen distinct failures (import format, FileMan field rules, MVI, IRIS Community license, disk, ports, container lifecycle) each surfaced only at runtime. The fixes are now in the code, but the *reasoning* and *ordering* that would let a clean rewrite skip the thrash live only here. This log makes that explicit.

<a name="2-original-objective"></a>
## 2. The original objective

> *"Spec out how to stand up a complete functioning VistA instance including sample patient data running on the community version of IRIS using the most lightweight portable (linux, mac) container technology."*

Delivered: a Podman/Docker image of **InterSystems IRIS for Health Community** loaded with the **FOIA VistA** M codebase (~34k routines + globals), sample patients/users/clinics, the **RPC Broker (CPRS) on 9430**, an `%ZSTART` boot hook, per-service license toggles, and a license report — reproducible via `make build`, guarded by `make preflight`.

<a name="3-session-narrative"></a>
## 3. Session narrative (chronological)

| Phase | Prompt (abridged) | Outcome |
|---|---|---|
| Spec v1 | "spec out … summarize in /docs/vista-iris-container-spec" | Wrote v1 spec (IRIS Community + WorldVistA/VistA-M + Docker/Podman). |
| Code-free | "put into the spec document. do not write code" | Converted artifact sections to prose. |
| Commit | "commit; then persist" | Committed v1; PR #1 (later merged to main). |
| Scaffold build | "scaffold the Dockerfile and compose from the spec v2" | **Discovered a user-authored `…-v2.md`** (deeper spec). Scaffolded Dockerfile + compose. |
| Scaffold scripts | "a" (scaffold scripts) | MUMPS scaffolds (`install.script` + `01–06`). |
| Makefile | "commit; then scaffold the makefile" | Makefile (build/up/verify/lint/test/ci/clean). PR #2 opened. |
| Vendor sources | "vendor the vista-m sources" | **AskUserQuestion → submodule (pinned, shallow)**; +`.dockerignore`. |
| Flesh out | "flesh out … that's 20 year old routines!" | **AskUserQuestion → cleaned IRIS-only Python expect-fork** of the OSEHRA driver; replaced MUMPS scaffolds. |
| Build it | "build it on my mac" | ~10 build/iterate cycles (see §6) → first working image. |
| Diagnostics | "is the podman vista running correctly?" / "kill all other containers" | Honest status; stopped competing containers. |
| RPC auto-start | "wire up the 9430 RPC broker auto-start" | `%ZSTART` hook jobbing `ZISTCP^XWBTCPM1`. |
| Reproducibility | "run make build to confirm" | Surfaced journal/disk/port/license issues → fixed → reproducible. |
| Permissions | "provide all permissions … only ask if you need to delete" | `.claude/settings.json`: broad allow, sandbox off, ask-on-delete. |
| Configurable | "make services on/off … track license use" | `%ZSTART` toggles + `make license`. |
| Document | "document the license model … in the spec" | Spec §14. |
| PR | "open the PR against main" | Updated PR #2 to current. |

<a name="4-decisions-log"></a>
## 4. Decisions log (incl. Claude questions + user responses)

**Explicit Claude → user questions (AskUserQuestion):**

| # | Question | Options offered | User chose | Why it mattered |
|---|---|---|---|---|
| Q1 | How to bring the ~20.7 GB `WorldVistA/VistA-M` into the repo? | Git submodule (pinned) · shallow clone gitignored · full vendor | **Git submodule, pinned (shallow)** | Avoids 20 GB in history; reproducible pin (`b7aecb9`). |
| Q2 | The proven VistA install is interactive/branching — how should the installer work? | Cleaned Python expect-fork · pure-MUMPS programmatic · flat-stream MUMPS | **Cleaned Python expect-fork** | Flat stdin can't drive branching prompts; matches spec §5. |

**Decisions driven by user directive:**

| Decision | Source |
|---|---|
| Spec stays code-free (prose artifacts) | "do not write code" |
| Base image = `irishealth-community` (FHIR retained), latest tag | user's spec v2 §4 |
| Podman primary, Docker compatible | spec v2 §3 |
| Stop all non-VistA containers (free ports/resources) | "kill all other containers" |
| Run unsupervised; **ask only on delete** | "only ask if you need to delete something" |
| Per-service toggles + license tracking | "make services on/off … track license use" |

**Key engineering decisions (Claude judgment, no question needed):**

| Decision | Rationale |
|---|---|
| Strategy A — bake VistA at build time | Boots in seconds; reproducible. |
| Import via `^%RI` + `LIST^ZGI` + `^ZTMGRSET` (not `ImportDir`) | `ImportDir` rejects raw `.m`/`.zwr` (Err #5840). |
| Cached import layer + iterated site-build layer | Iterating the site build must not re-import 6 GB. |
| Patients via `UPDATE^DIE` (not the registration menu) | The menu hangs on MVI in a standalone instance. |
| RPC Broker started by an IRIS `%ZSTART` hook, not TaskMan | TaskMan exhausts the Community license. |
| TaskMan **off by default** | Measured: it consumes all 8 license units. |
| Journal purge after each clean stop | Import journals (GBs) overran the build disk. |
| Durable config in `.claude/settings.json` (not `…local.json`) | The harness auto-rewrites `settings.local.json`. |

<a name="5-discoveries"></a>
## 5. Discoveries

| # | Discovery | Impact |
|---|---|---|
| D1 | A deeper, user-authored `vista-iris-container-spec-v2.md` (+ sibling docs) existed | All scaffolding keyed to v2, not v1. |
| D2 | IRIS for Health arm64 tag is **`latest-cd-linux-arm64`** (not `…-arm64`) | Pull would 404 otherwise. |
| D3 | IRIS Community caps: **8 license units**, 25 max connections, ~20 cores | The 8 units are the binding constraint. |
| D4 | `$SYSTEM.OBJ.ImportDir`/`Load` reject raw VistA `.m`/`.zwr` (**Err #5840**) | Must package a `.ro` and use `^%RI`; load globals via `LIST^ZGI`. |
| D5 | OSEHRA `ZGI.m` recognizes only `$ZV["Cache"`/`["GT.M"`, **not IRIS** | Vendored a patched `ZGI.m` (`$ZV["IRIS"`). |
| D6 | The OSEHRA install is an **interactive, branching expect dialog** (`write`/`wait`/`multiwait`) | Drives a pexpect fork, not a flat script. |
| D7 | DOMAIN file (#4.2) forbids spaces; INSTITUTION (#4) allows them | `DOMAIN=DEMO.OSEHRA.ORG`, `INSTITUTION="VISTA HEALTH CARE"`. |
| D8 | `GETENV^%ZOSV` returns `VISTA^VISTA^<host>^VISTA:IRIS` | Volume-set anchor = `VISTA`; box:volume = `VISTA:IRIS`. |
| D9 | PATIENT (#2) requires **7 identifiers** (.02 .03 .09 .301 391 1901) | `UPDATE^DIE` must supply all of them. |
| D10 | Enterprise Search is gated by routine `MPIFXMLP`; it blocks on "Searching the MVI…" with no MVI | Bypass the registration menu entirely. |
| D11 | RPC Broker listener = `ZISTCP^XWBTCPM1(port)` → blocking `LISTEN^%ZISTCPS` | `JOB` it from `%ZSTART`; no TaskMan needed. |
| D12 | IRIS auto-calls `SYSTEM^%ZSTART` at startup (no enable flag) | Clean boot hook for service start. |
| D13 | TaskMan cold-start spawns a manager+submanager+STARTUP jobs (~37 processes) | Exhausts the 8-unit license. |
| D14 | The bulk global import journals **GBs**, bloating the image layer | Purge journals before layer commit. |
| D15 | `nc host:port` is misleading (rootlessport forwarder answers even with nothing behind it) | Verify with `ss` **inside** the container. |
| D16 | Committing a *running* IRIS yields a non-restartable image; `iris stop` + `podman start` is a no-op (PID 1 stays up) | Clean-stop then commit, or `podman restart`. |
| D17 | The build's IRIS contends with a *running* instance on port **1972** | Stop instances before `make build`. |
| D18 | `podman compose build` (docker-compose provider) and `podman build` (buildah) keep **separate layer caches** | Pick one path; don't expect cache reuse across them. |
| D19 | The harness auto-rewrites `.claude/settings.local.json` | Put durable config in `.claude/settings.json`. |

<a name="6-errors--remedies"></a>
## 6. Errors encountered & remedies

| # | Symptom | Root cause | Remedy |
|---|---|---|---|
| E1 | (pre-empted) image pull would 404 | Guessed tag `latest-cd-arm64` | Use verified `latest-cd-linux-arm64`; per-arch tag in Makefile. |
| E2 | `ERROR #5840: not a supported type` on `PRCA219P.m`; FileMan never loaded (`<NOROUTINE> *DI`) | `ImportDir` can't load raw `.m`/`.zwr` | `prepare.py` packs `routines.ro`; `^%RI` imports; `LIST^ZGI` loads globals; `^ZTMGRSET` type 3. |
| E3 | `LIST^ZGI` would print "ZGI does not support IRIS" | `ZGI.m` `$ZV` check misses IRIS | Vendored patched `ZGI.m`. |
| E4 | `02` `startFileman` `wait(PROMPT)` timed out, empty buffer | `config.connect` consumed the only prompt; next step is wait-first | `connect()` primes a fresh prompt (bare CR). |
| E5 | `setupVistADomain` got `Select OPTION:` instead of `FLAGS` | Domain "VISTA HEALTH CARE" has spaces (illegal in #4.2) | Split `DOMAIN` (`DEMO.OSEHRA.ORG`) vs `INSTITUTION`. |
| E6 | `getenv` would not match the box:volume | `VOLUME_SET=ROU` ≠ actual `VISTA` | `VOLUME_SET=VISTA`. |
| E7 | `setupHL7Listener` desynced (screen-clear codes) | `HL EDIT LOGICAL LINKS` is a full-screen List Manager UI | **Deferred**; needs programmatic `#870`. |
| E8 | `03` `<LICENSE LIMIT EXCEEDED>` after several connects | Force-closed sessions don't release the license fast enough | `_release` (escape menus → halt → wait EOF); `_connect` retry. |
| E9 | `addPatient` hung on "Searching the MVI…" | Enterprise Search (gated by `MPIFXMLP`) blocks with no MVI | Create patients via `UPDATE^DIE` (7 identifiers). |
| E10 | `addNurse` desynced at the key/mail-group prompts | A stray trailing CR on the last security key | Drop the CR → uniform `_addUser` tail. |
| E11 | Build `no space left` while committing the import layer | GBs of IRIS journals in the layer | `rm /usr/irissys/mgr/journal/20*` after clean stop, each layer. |
| E12 | Build: `ERROR #5001: Could not start superserver 1972` | A running instance held host 1972 | Stop the instance before building (now a preflight check). |
| E13 | `9430 address already in use` on `run` | `vehu` container held 9430 | Free the port / stop other containers (preflight check). |
| E14 | `%ZSTART.mac` `Load` failed (#5840) | Same `.m`/`.mac` import limitation | Create the routine via the `%Routine` class API. |
| E15 | Committed image wouldn't restart cleanly | Committed a *running* IRIS | Clean-stop before commit; verify with `podman restart`. |
| E16 | `03` `<LICENSE LIMIT EXCEEDED>`, retries never recovered (180 s) | `02` cold-started **TaskMan**, whose persistent jobs hold the 8 units | **Removed `startTaskMan` from `02`**; broker via `%ZSTART`. |
| E17 | Compact `settings.local.json` reverted | Harness owns that file | Moved durable config to `settings.json`; gitignored both. |
| E18 | Preflight failed at 45 GB free | Threshold set to 50 GB (too high post-cleanup) | Lowered to 40 GB (image ~20 GB, commit ~35 GB peak). |
| E19 | `make license` empty / `Error 133` (TaskMan on) | License fully consumed — even the report can't connect | Read the report from a config with headroom; expected behavior. |

<a name="7-caveats--deferred"></a>
## 7. Caveats, deferred items & limitations

| Item | Status | Note / workaround |
|---|---|---|
| HL7 MLLP listener on 5026 (#870) | **Deferred** | List-Manager UI can't be pexpect-driven; needs a programmatic `#870` approach. |
| TaskMan | **Off by default** | Exhausts the 8-unit Community license; needs a larger license. |
| `make test` (M-Unit) | **Stub** | No automated M tests run yet. |
| `make verify` M-level checks | **Partial** | Ports verified via `ss`/`nc`; FileMan/TaskMan checks are TODO. |
| Image size | ~25 GB | Whole `vista-m` is COPYed *and* loaded; a builder stage could drop the source. |
| Reproducible `make build` reentrancy | Requires 1972 free + ≥40 GB | Enforced by `make preflight`; `make fresh` to clean. |
| Real PHI | None | Sample data only; instance bannered test-only. |
| Platform coverage | arm64 (Apple Silicon) validated | amd64 tag wired but not built here. |
| IRIS-vs-Caché | OSEHRA path targets Caché | `%Z*`/`^%ZOSF`, locale, `irissession`→`iris session` adjusted; further `$ZU` edge cases possible. |

<a name="8-rewrite-blueprint"></a>
## 8. Clean re-implementation blueprint (ordered flow)

If re-implementing from scratch (same stack, or an orchestrator in **Go**), run the phases **in this order** — each gate prevents a class of failure this session hit late. Every phase below names the failure it prevents.

```
Phase 0  Config resolution        (defaults + env/flags)
Phase 1  Preflight                (engine → OS/arch → disk → ports → conflicts → sources)
Phase 2  Base image               (resolve & verify per-arch tag)
Phase 3  License/capacity check   (units available vs services requested)   ← new, do EARLY
Phase 4  Namespace bootstrap      (db + namespace + %Z*/%X* mappings)
Phase 5  Routine + global import  (pack .ro → ^%RI → LIST^ZGI → ^ZTMGRSET 3)
Phase 6  OS-interface init        (DINIT→CACHE, ZUSET, devices, MPI)
Phase 7  Post-install             (FileMan, DOMAIN[no spaces], box:vol, institution, users)
Phase 8  Sample data              (programmatic UPDATE^DIE patients; users; clinics)
Phase 9  Service hook + toggles   (%ZSTART starts only enabled services)
Phase 10 Build hygiene            (journal purge; clean stop; commit)
Phase 11 Verify                   (ss INSIDE; data counts; RPC/HL7 connectivity)
```

### 8.1 Phase 0 — Configuration
Single source of truth for: engine (`podman`/`docker`), per-arch `IRIS_TAG`, namespace (`VISTA`), `DOMAIN` (dotted, no spaces), `INSTITUTION`, `VOLUME_SET` (`VISTA`), ports (1972/52773/9430/5026), and **service toggles**. All overridable by env/flags. *Prevents E5/E6 (naming), and makes the license budget explicit.*

### 8.2 Phase 1 — Preflight (the gate)
Order matters: **engine responsive → OS/arch → free disk ≥ threshold → required ports free → no conflicting containers → sources present → no stale image.** Fail loud with remediation. *Prevents E11/E12/E13/E18.* (Implemented here as `scripts/preflight.sh` + `make preflight`/`make fresh`.)

### 8.3 Phase 2 — Base image
Resolve the **explicit per-OS/arch tag** from the registry (don't guess); record it for reproducibility. *Prevents E1.*

### 8.4 Phase 3 — License / capacity check (do this EARLY)
Query `$SYSTEM.License.KeyLicenseUnits()` / `LUAvailable()`. Compute the cost of the **requested** service set (RPC=1, +1/client; TaskMan≈many; HL7≈1/link) and **refuse or warn** if it can't fit. This session learned the 8-unit ceiling *after* a full build failed in the site phase (E16) — checking here turns a 40-minute failure into an instant message.

### 8.5 Phase 4 — Namespace bootstrap (IRIS-native, non-interactive)
Create the DB + namespace + the `%Z*` global and `%DT*/%RCR/%XU*/%ZIS*/%ZO*/%ZT*/%ZV*` routine mappings. Pure ObjectScript; no expect needed.

### 8.6 Phase 5 — Routine & global import (the crux)
1. Pack all `.m` (incl. an **IRIS-patched `ZGI`**) into `routines.ro` (the `^%RO` format).
2. `D ^%RI` reading `routines.ro` (override = YES, All Routines).
3. `D LIST^ZGI(globals.lst)` for the `.zwr` globals (absolute paths).
4. `D ^ZTMGRSET` system type **3** (Cache-compatible), rename FileMan routines = YES.
*Prevents E2/E3.* Make this its own cached layer (don't re-run when iterating later phases).

### 8.7 Phase 6 — OS-interface init
`D ^DINIT` (MUMPS OPERATING SYSTEM → CACHE) + `D ^ZUSET`; configure NULL/console/HFS devices; set the MPI local site number.

### 8.8 Phase 7 — Post-install (site config)
FileMan init; HFS dir; intro text; **christen the DOMAIN (dotted, no spaces)**; box:volume pair (`VISTA:IRIS`) + RPC Broker listener port into #8994.1; volume set; System Manager; institution/division/MAS. **Do NOT cold-start TaskMan here** (E16). Each connection that enters a menu must be released cleanly (escape menus → halt → wait EOF) to free its license (E8) — and open one connection at a time.

### 8.9 Phase 8 — Sample data
Create patients **programmatically** via `UPDATE^DIE` into #2 with the **7 required identifiers** — never the registration menu (E9). Create clinical users (ScreenMan) with uniform key lists (E10); set e-signatures via per-user `^ZU` (release between users — E8).

### 8.10 Phase 9 — Service startup hook + toggles
Install an `%ZSTART` (via the `%Routine` API — E14) that reads env toggles and starts only enabled services: RPC Broker = `JOB ZISTCP^XWBTCPM1(port)` (one process); TaskMan/HL7 gated off by default. *This is the runtime license-management surface.*

### 8.11 Phase 10 — Build hygiene
Purge IRIS journal files after a **clean** `iris stop` in each layer (E11); commit a stopped instance (E15).

### 8.12 Phase 11 — Verify
Check listeners with **`ss` inside the container** (not host `nc` — E15/D15); confirm data counts (patients/users); optionally round-trip an RPC/HL7 connection. Report license usage.

### 8.13 Notes for a Go (or other-language) rewrite
- **Orchestrator in Go, IRIS work stays in M/ObjectScript.** The hard, irreducible part is the interactive VistA dialog; a Go expect library (e.g. `Netflix/go-expect`/`goexpect`) replaces `pexpect`. Keep the `write/wait/multiwait` primitives and the per-step "release cleanly" helper.
- **Prefer the IRIS Native API / callin where a programmatic path exists** (FileMan DBS like `UPDATE^DIE`, license/process queries, `%Routine` creation) — it's deterministic and avoids screen-scraping. Reserve expect for the genuinely menu-only steps (SDBUILD clinic, ScreenMan user add).
- **Model services as first-class, toggle-driven units** with a declared license cost; gate startup on the capacity check (Phase 3).
- **Make every phase idempotent and individually runnable** against a persistent instance, so iteration never re-imports.
- **Treat the container lifecycle explicitly:** clean stop → journal purge → commit; never commit a running instance; `restart` ≠ `stop+start` for IRIS PID 1.
- **A single declarative config** (Phase 0) feeds preflight, build, runtime hook, and the license report — one schema, many consumers.

<a name="9-component-reference"></a>
## 9. Component / file reference (current repo)

| Path | Role |
|---|---|
| `Makefile` | Entry point: `preflight`/`fresh`/`sources`/`build`/`up`/`run`/`license`/`verify`/`ci`/`clean`; engine + toggle vars. |
| `scripts/preflight.sh` | Phase 1 gate (engine/disk/ports/conflicts/sources); `--clean` = fresh install. |
| `Dockerfile` | Strategy A; cached import layer + iterated site-build layer; journal purge. |
| `docker-compose.yml` | Service def; ports; durable %SYS (opt-in); service-toggle env. |
| `.dockerignore` | Trims build context (esp. `.git`). |
| `scripts/bootstrap.script` | Phase 4 (namespace + mappings), IRIS-native. |
| `scripts/osehra/prepare.py` | Packs `routines.ro` + `globals.lst`. |
| `scripts/osehra/m/ZGI.m` | IRIS-patched global importer. |
| `scripts/osehra/00_import.py` | Phase 5 (`^%RI` / `LIST^ZGI` / `^ZTMGRSET`). |
| `scripts/osehra/01_osinit.py` | Phase 6 (devices/MPI/DINIT/ZUSET). |
| `scripts/osehra/02_postinstall.py` | Phase 7 (site config; **no TaskMan**). |
| `scripts/osehra/03_sampledata.py` | Phase 8 (users/clinics/ward/patients via `UPDATE^DIE`); `_release`/`_connect`. |
| `scripts/osehra/{helper,setup,config}.py` | Cleaned IRIS-only fork of OSEHRA driver/steps/config. |
| `scripts/startup.script` | Installs the toggle-driven `%ZSTART` hook. |
| `scripts/license.script` | `make license` report (units + per-service processes). |
| `vista-m/` | Pinned shallow submodule: `WorldVistA/VistA-M` @ `b7aecb9`. |
| `docs/vista-iris-container-spec-v2.md` | The specification (incl. §14 license model). |

<a name="10-key-facts"></a>
## 10. Key technical facts (appendix)

| Fact | Value |
|---|---|
| Base image | `intersystems/irishealth-community:latest-cd-linux-arm64` (arm64) / `…-linux-amd64` |
| VistA source | `github.com/WorldVistA/VistA-M` @ `b7aecb9` (no release tags; ~20.7 GB history, ~6.1 GB tree) |
| Routines / globals loaded | 33,952 routines · 2,922 global files |
| IRIS Community license | **8 units**, 25 max connections, ~20-core cap |
| License consumed: default (RPC only) | **2 / 8** (6 free) |
| License consumed: TaskMan on | **8 / 8** → `LICENSE LIMIT EXCEEDED` (~37 processes) |
| Ports | 1972 superserver · 52773 portal/FHIR · 9430 RPC Broker · 5026 HL7 (deferred) |
| RPC Broker start | `JOB ZISTCP^XWBTCPM1(9430)` → `LISTEN^%ZISTCPS` |
| OS system type | `^ZTMGRSET` → 3 = Cache (VMS, NT, Linux), OpenM-NT |
| Domain / institution | `DEMO.OSEHRA.ORG` / `VISTA HEALTH CARE` |
| Box:volume | `VISTA:IRIS` (volume-set anchor `VISTA`) |
| PATIENT (#2) required identifiers | .02 SEX · .03 DOB · .09 SSN · .301 SC? · 391 TYPE · 1901 VETERAN |
| Final image size | ~25.6 GB |
| Sample patients | PATIENT,ALPHATEST / BETATEST / GAMMATEST (DFN 1–3) |
