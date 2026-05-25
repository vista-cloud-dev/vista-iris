# VistA on IRIS — Containerized Instance Specification (v3)

**Status:** Canonical · **Version:** 3 · **Date:** 2026-05-24
**Supersedes:** `vista-iris-container-spec-v2.md` (v2, kept for history)
**Companion:** `vista-iris-implementation-log.md` (the failure narratives + chronology this spec distills)

---

## How to read this document

v3 is the **single, forward-looking, normative contract** for building the VistA-on-IRIS
image and for the runtime contract of the instance it produces. It reconciles three prior
sources — the v2 design spec, the implementation log, and **the working code, which is the
ground truth** — into one document a competent engineer could re-implement the whole thing
from, cleanly and in the right order, without repeating the original trial-and-error.

Conventions:

- **Normative** requirements use *must / must not / should*. Every normative statement is
  traceable to a source doc or verified against the code.
- Where v2 or the log **disagreed with the code, the code wins**; such cases are called out
  in a **⚠ Reconciliation** note and listed together in [Appendix B](#appendix-b--reconciliation-ledger-doc-vs-code).
- Named references — routines (`^%RI`, `LIST^ZGI`, `%ZSTART`), files (`#8994.1`), env vars
  (`VISTA_ENABLE_RPC`), ports, tags (`latest-cd-linux-arm64`), make targets (`make build`) —
  are used freely. This document contains **no source listings** by design; for the actual
  implementation, read the files named in [§12](#12-repository-layout--artifact-reference).
- "the log" = `vista-iris-implementation-log.md`. "v2" = `vista-iris-container-spec-v2.md`.

---

## 1. Purpose & Scope

Define how to **build** a single-container VistA instance on InterSystems **IRIS for Health
Community**, and define that instance's **runtime contract** — the ports, services, license
posture, and test users it exposes. The deliverable is an OCI image (published multi-arch to
GHCR) plus a portable `Makefile` + Compose setup, that:

1. Boots IRIS for Health Community (latest continuous-delivery release).
2. Loads the WorldVistA "FOIA" VistA M codebase (routines + globals).
3. Configures namespace, OS interface, FileMan/Kernel, institution, and the **RPC Broker
   (XWB) listener** so a CPRS / RPC client can connect.
4. Loads Tier-1 sample data (institution, users, clinics, ward, patients).
5. Starts only the services whose license-aware toggle is on, via an IRIS `%ZSTART` boot hook.
6. Is verifiable by a shared acceptance script used identically by `make verify` and CI.

### In scope

- The normative **build/provisioning contract** (the "image factory"): config resolution,
  the preflight gate, base image, license/capacity, the ordered install sequence
  ([Phases 0–11](#7-the-ordered-install-sequence--phases-011)), sample data, build hygiene,
  and the multi-arch GHCR publication flow.
- The instance's **runtime contract**: published ports, service/license toggles, test users,
  and acceptance checks.

### Out of scope (guardrails)

- **Not a redesign.** v3 reconciles existing sources + code; it introduces no new requirements
  or architecture. Genuinely missing/ambiguous points are listed as **Open Questions**
  ([§13](#13-known-limitations-deferred-items--risks)), not resolved by fiat.
- **Not a management CLI, and not runtime operations tooling.** Operating a *built* instance
  (start/stop lifecycle management, day-2 admin, a control plane) belongs to a **separate
  control-plane tool** and is out of scope. v3 covers building the image and the instance's
  runtime *contract* — not a CLI to drive it. See [§15](#15-future-directions-non-binding).
- **Not a Go-rewrite plan.** "The orchestrator could later be Go" survives only as a
  non-binding [Future Directions](#15-future-directions-non-binding) note.
- **Not production, not real PHI.** Sample/synthetic data only; the instance is bannered
  test-only.

> **⚠ Reconciliation (HL7 reachability).** v2 §1 made HL7/MLLP reachability a *first-class
> requirement*. In the working code the HL7 `#870` MLLP listener is **deferred** (see
> [§7 Phase 7](#phase-7--post-install-site-configuration) and [§13](#13-known-limitations-deferred-items--risks));
> port `5026` is published but **unbacked**. v3 keeps HL7 as an intended interface and a
> published port, but states plainly that the listener does not yet exist. RPC (CPRS) is the
> reachable external interface today.

---

## 2. Goals & Non-Goals

### Goals

- **One command up** — `make up` (build path) or `make run` / a single `podman run` (consumer
  path) yields a working, pre-loaded VistA.
- **Portable** — identical artifacts on Linux + macOS, `amd64` + `arm64` (Apple Silicon).
- **Lightweight** — single base image (IRIS for Health Community); no external services.
- **Reproducible** — image built from a pinned VistA-M submodule and a recorded `IRIS_TAG`;
  the same `scripts/smoke.sh` gates locally and in CI; `:latest` moves only after a candidate
  passes verification on every arch.
- **Externally reachable (RPC today)** — the RPC Broker (CPRS) listens on a published port;
  HL7/MLLP is published but its listener is deferred ([§13](#13-known-limitations-deferred-items--risks)).
- **License-aware** — services are individually toggled and license consumption is observable,
  so a deployment stays within the Community license budget ([§9](#9-service--license-model)).
- **Developer-tooling parity** — exposes the IRIS superserver/web ports so a developer can
  attach the VA-realistic inner loop (VS Code + InterSystems ObjectScript over `isfs`; VistA's
  own XINDEX / M-Unit / KIDS / FileMan). See `vista-dev-iris-tooling.md`.
- **Ephemeral by default** — disposable; durable persistence is an explicit opt-in.

### Non-Goals

- Not production-grade (Community is dev/eval-licensed and capacity-capped).
- No real patient data; no bundled Windows CPRS GUI; no HA/clustering, VistA Imaging, or
  multi-site federation.
- No class-grade IDE features for flat M (refactoring, SQL projection, `%UnitTest`).
- No EWD.js / web framework, no GT.M/YottaDB, no CDash dashboards, no legacy Caché installer,
  **no fakes** — all removed from the forked installer ([§4](#4-locked-decisions--rationale), [§12](#12-repository-layout--artifact-reference)).

---

## 3. Glossary

| Term | Meaning |
|---|---|
| **VistA** | Veterans Health Information Systems and Technology Architecture — the VA's EHR, written in MUMPS (M). |
| **MUMPS / M** | The language + integrated hierarchical database ("globals") VistA is built on. |
| **IRIS / IRIS for Health** | InterSystems' M data platform (successor to Caché); the Health edition bundles the HL7 v2 / FHIR interoperability engine and a FHIR server. |
| **Globals** | Persistent sparse arrays = VistA's data store (e.g. `^DPT` = PATIENT file #2). |
| **Routines** | Compiled M program units (`.m` source). |
| **FileMan** | VistA's database management layer over globals; DBS calls like `UPDATE^DIE` file data programmatically. |
| **KIDS** | Kernel Installation & Distribution System — VistA's package installer. |
| **RPC Broker (XWB)** | TCP listener GUI clients (CPRS) connect to; site parameters in file #8994.1. The listener routine is `ZISTCP^XWBTCPM1` → blocking `LISTEN^%ZISTCPS`. |
| **HL7 / HL package** | VistA's HL7 v2 subsystem; the HL7 Link Manager runs logical links (HL LOGICAL LINK, file #870), each an MLLP TCP endpoint. |
| **MLLP** | Minimal Lower Layer Protocol — framing for HL7 v2 over TCP. |
| **CPRS** | Computerized Patient Record System — the Windows clinical GUI; talks to VistA over the RPC Broker. |
| **FOIA VistA** | The public-domain VistA release, mirrored to GitHub as routines + `.zwr` globals (`WorldVistA/VistA-M`). |
| **`%ZSTART`** | IRIS startup hook; IRIS calls `SYSTEM^%ZSTART` once at every instance start (no enable flag). The image installs it to start toggled VistA services. |
| **Durable %SYS** | IRIS mechanism (`ISC_DATA_DIRECTORY`) for keeping instance data on a mounted volume outside the image layer. |
| **`^%RI` / `^%RO`** | IRIS routine import / the routine-transfer file format `^%RI` reads. |
| **`LIST^ZGI`** | WorldVistA global importer (vendored, IRIS-patched) that loads each `.zwr` listed in a manifest. |
| **`^ZTMGRSET`** | Kernel OS-manager setup; "system type 3" selects the Caché-compatible OS interface (correct for IRIS). |
| **box:volume pair** | IRIS instance/volume-set identity VistA needs for TaskMan/RPC config; here `VISTA:IRIS`. |

---

## 4. Locked Decisions & Rationale

Merged from v2's decision tables and the log's §4. Each row is a settled decision; "Source"
gives provenance and, where relevant, the code that confirms it.

| Decision | Value | Rationale | Source |
|---|---|---|---|
| Base image | `intersystems/irishealth-community` (Health edition; FHIR server retained) | FHIR is a kept feature; the Health edition bundles HL7 v2 / FHIR interop on the same M engine. | v2 §4 · `Dockerfile` |
| Version policy | **Latest, then recorded** — track the latest `-cd` Community release; record the resolved per-arch `IRIS_TAG`; legacy (e.g. Caché 2011) prohibited. | Reproducible rebuilds without freezing on EOL versions. | v2 §4 · `Makefile` |
| Per-arch tag | `latest-cd-linux-arm64` (Apple Silicon) / `latest-cd-linux-amd64`; floating `latest-cd` is a compose fallback only. | Guessed `…-arm64` would 404; the OS/arch-qualified tag is the real one. | log D2/E1 · `Dockerfile`, `Makefile`, `publish.yml` |
| Container engine | **Podman primary, Docker drop-in compatible** | Daemonless/rootless; identical `Dockerfile`/Compose under both. | v2 §3 · `Makefile` (`ENGINE ?= podman`) |
| Build strategy | **Strategy A — bake at build time** | Boots in seconds; fully reproducible; ephemeral by default. | v2 §7 · `Dockerfile` |
| VistA-M source | `WorldVistA/VistA-M`, **pinned shallow submodule @ `b7aecb9`** | Avoids ~20 GB of history in repo; reproducible pin. | log Q1/§10 · `.gitmodules`, submodule gitlink |
| Installer | **Cleaned, IRIS-only Python 3 fork** of the WorldVistA import/config path, driven over `iris session` via pexpect | The proven VistA site build is a branching, expect-driven dialog a flat stream can't drive; GT.M/Caché-2011/EWD/dashboards/fakes removed. | v2 §5 · log Q2 · `scripts/vista/` |
| Import mechanism | **`prepare.py` → `^%RI` → `LIST^ZGI` → `^ZTMGRSET` type 3** (not `$SYSTEM.OBJ.ImportDir`) | `ImportDir`/`Load` reject raw `.m`/`.zwr` (Err #5840). | log D4/E2 · `00_import.py`, `prepare.py` |
| Global importer | Vendored **IRIS-patched `ZGI.m`** (`$ZV["IRIS"`) | Upstream `ZGI.m` recognizes only Caché/GT.M. | log D5/E3 · `scripts/vista/m/ZGI.m` |
| Layering | **Cached import layer + separately iterated site-build layer** | Iterating the site build must not re-import ~GBs of routines/globals. | log §4 · `Dockerfile` |
| Patient creation | **Programmatic `UPDATE^DIE`** into #2, not the registration menu | The menu hangs on "Searching the MVI…" (`MPIFXMLP`) in a standalone instance. | log D10/E9 · `setup.py:addPatient` |
| RPC start mechanism | **IRIS `%ZSTART` hook** jobs `ZISTCP^XWBTCPM1` — **not** TaskMan | TaskMan cold-start exhausts the 8-unit Community license. | log D11/D12/E16 · `startup.script` |
| TaskMan | **Off by default** | Measured to consume all 8 license units (~37 processes). | log D13/E16 · `02_postinstall.py`, `startup.script` |
| Build hygiene | **Journal purge after each clean `iris stop`; commit a stopped instance** | Import journals (GBs) overran the build disk; a committed *running* IRIS isn't restartable. | log D14/D16/E11/E15 · `Dockerfile` |
| Distribution | **Multi-arch image published to GHCR**, verified before `:latest` moves | A new developer needs only Podman — no submodule, build, or Python. | `publish.yml`, `docker-compose.run.yml`, `Makefile` |

---

## 5. Architecture Overview

**Strategy A (bake-at-build-time factory).** All VistA code/data and configuration are
imported during the image build, so a `run` starts an already-loaded instance. The committed
image *is* the artifact; the running container holds no irreplaceable state (durable %SYS is
opt-in).

```
┌───────────────────────────────────────────────────────────────────────┐
│ Container: vista-iris   (Podman primary · Docker compatible)            │
│ FROM intersystems/irishealth-community:<IRIS_TAG>                       │
│                                                                         │
│  IRIS for Health instance (M engine + HL7/FHIR interop)                 │
│   Namespace VISTA ──► Database VISTA (iris.dat)                          │
│     • Global map:  %Z*           → VISTA                                 │
│     • Routine map: %DT* %RCR %XU* %ZIS* %ZO* %ZT* %ZV*  → VISTA         │
│   FOIA VistA codebase (Kernel/FileMan/RPC/HL/…)                          │
│   %ZSTART boot hook ─ starts only TOGGLED-ON services:                  │
│     • RPC Broker (XWB)  JOB ZISTCP^XWBTCPM1  ── TCP 9430   (default ON)  │
│     • TaskMan (^ZTMB)                          (default OFF, license)    │
│     • HL7 Link Manager                         (default OFF; #870 TODO)  │
│   IRIS FHIR server (Health edition)            ── via 52773              │
│                                                                         │
│  Durable %SYS (opt-in) ──► volume /durable  (ISC_DATA_DIRECTORY)        │
└───────────────────────────────────────────────────────────────────────┘
   │1972            │52773               │9430              │5026
   ▼                ▼                    ▼                  ▼
 IRIS terminal /  Mgmt Portal +       CPRS / RPC         HL7 v2 (MLLP)
 roll-and-scroll  FHIR REST           clients            ── published but
 + VS Code isfs   (browser)           (XWB listener)        listener DEFERRED
```

### 5.1 The image factory and its publication boundary

The heavy, Python/pexpect-driven build runs **once, in CI**, and is published multi-arch to
**GHCR** (`ghcr.io/vista-cloud-dev/vista-iris`). Consumers pull the result; they never build
locally and need only Podman/Docker — no submodule, no Python/Node. The build → publish →
verify → promote flow is normative and is specified in [§11.2](#112-multi-arch-publication-ghcr).
The local `make build` path exists for **changing** the build (it requires the submodule + an
engine), and runs the *same* `scripts/smoke.sh` acceptance checks CI runs.

---

## 6. Prerequisites & the Preflight Gate

A build/run must be **gated by an ordered preflight** (`scripts/preflight.sh`, invoked by
`make preflight`; `make fresh` runs it with `--clean`). Order matters: each check prevents a
class of failure observed in this build. The gate fails loud (non-zero) with remediation text.

| Order | Check | What it prevents | Threshold / detail |
|---|---|---|---|
| 1 | **Container engine responsive** | building against a dead engine | `ENGINE info` succeeds (default `podman`); hint: `podman machine start` |
| 2 | *(`--clean` only)* **cleanup for fresh install** | stale containers/images/cache causing port or disk failures | removes prior `vista-iris`, stops other containers, prunes dangling images + build cache |
| 3 | **No other running containers** | a competing container holding ports/resources | warns and lists them; `make fresh` stops them |
| 4 | **Host ports free** | a prior instance / other service holding a published port | `1972, 52773, 9430, 5026` each probed with `nc -z`; prevents `#5001 superserver` (1972) and `9430 address already in use` |
| 5 | **Engine free disk ≥ threshold** | `no space left` while committing the import layer | **≥ 40 GB for a from-scratch build** (image ~20 GB, commit ~35 GB transient peak); **≥ 25 GB** for running a prebuilt image (`make up`/`make run`) |
| 6 | **VistA-M sources present** | a half-populated submodule breaking the Dockerfile `COPY` | `vista-m/Packages` non-empty; else `make sources` |
| 7 | **Prior `vista-iris:dev` image** *(informational)* | accidental reuse of a stale build | warns; `make fresh` removes it |

> **⚠ Reconciliation (disk threshold).** The header comment in `scripts/preflight.sh` still
> reads "default 50"; the **effective default is 40** (the script body and the `Makefile`),
> lowered post-cleanup (log E18). v3 states **40 GB build / 25 GB run**.

> **⚠ Reconciliation (port probe method).** Preflight (and `smoke.sh`) probe ports with host
> `nc -z`. The log (D15) notes a rootless port-forwarder (and Docker's proxy) can *answer* a
> TCP connect even with nothing behind it. For a **true** listener check the log recommends
> `ss` **inside** the container; the host probe is adequate as a *free/in-use* gate but is not
> proof of a backing listener — see [§10](#10-runtime-contract--verification).

---

## 7. The Ordered Install Sequence — Phases 0–11

This is the heart of the spec. The phases are the log's §8 blueprint **promoted to normative
requirements** and reconciled to the code. They **must** run in this order; each gate prevents
a class of failure that surfaced late in the original build. For each phase: *inputs* →
*actions* → *failure it prevents* → *how it's verified*. The narrative detail of each failure
lives in the log (§5 discoveries, §6 errors); here the "why" is one line.

> **Code mapping.** Phases 0–3 are config/preflight/base-image/capacity gates (`config.py`,
> `preflight.sh`, `Makefile`, license APIs). Phase 4 = `bootstrap.script`. Phase 5 =
> `prepare.py` + `00_import.py`. Phase 6 = `01_osinit.py`. Phase 7 = `02_postinstall.py`.
> Phase 8 = `03_sampledata.py`. Phase 9 = `startup.script`. Phase 10 = the `Dockerfile` layer
> tails. Phase 11 = `smoke.sh`.

### Phase 0 — Configuration

- **Inputs:** defaults in `scripts/vista/config.py`, overridable by environment.
- **Actions:** establish the single source of truth: `INSTANCE=IRIS`, `NAMESPACE=VISTA`,
  `DOMAIN=DEMO.VISTA.ORG` (dotted, **no spaces**), `INSTITUTION="VISTA HEALTH CARE"`,
  `VOLUME_SET=VISTA`, `RPC_PORT=9430`, `HL7_PORT=5026`, `SITE_NUMBER=6161`, plus the service
  toggles ([§9](#9-service--license-model)). `IRIS_TAG` and the toggles are also resolved in
  the `Makefile`/Compose for the engine layer.
- **Prevents:** naming failures — DOMAIN with spaces is illegal in file #4.2 (log E5), and a
  wrong `VOLUME_SET` breaks the box:volume match (log E6). Making the toggle set explicit
  makes the license budget computable in Phase 3.
- **Verified by:** Phases 4–8 consume these values and fail loud if a name is wrong.

> **⚠ Reconciliation (site numbers).** Three distinct numbers exist and are intentional:
> `SITE_NUMBER=6161` (the **MPI local site / DINIT site number**, Phase 6), **institution**
> station `6100`, and **division** `6101` (Phase 7). v2 §9 mentioned only `6100`; the `6161`
> default is an [Open Question](#13-known-limitations-deferred-items--risks) to confirm but is
> documented here as-is.

### Phase 1 — Preflight (the gate)

- **Inputs:** host state.
- **Actions:** run the ordered checks of [§6](#6-prerequisites--the-preflight-gate).
- **Prevents:** disk exhaustion mid-commit (E11), superserver-port contention (E12),
  published-port conflicts (E13), and building under-provisioned (E18).
- **Verified by:** non-zero exit blocks `make build`/`make up`/`make run`.

### Phase 2 — Base image

- **Inputs:** host arch (`uname -m`), the registry.
- **Actions:** resolve the **explicit per-OS/arch tag** (`latest-cd-linux-{arm64,amd64}`) —
  the `Makefile` auto-selects it; CI passes it per matrix row — and record it for
  reproducibility. Do **not** guess a tag.
- **Prevents:** a 404 on a guessed tag (E1/D2).
- **Verified by:** the `FROM` pull succeeds; the resolved tag is recorded in the build args.

### Phase 3 — License / capacity check (do this EARLY)

- **Inputs:** the running base instance; the requested toggle set.
- **Actions:** query `$SYSTEM.License.KeyLicenseUnits()` / `LUAvailable()` /
  `LUConsumed()` / `MaxConnections()`; compute the cost of the requested services
  (RPC = 1 + 1/client; TaskMan ≈ exhausts the budget; HL7 ≈ 1/active link) and refuse or warn
  if it cannot fit ([§9](#9-service--license-model)).
- **Prevents:** discovering the **8-unit ceiling** only after a ~40-minute build dies in the
  site phase with `LICENSE LIMIT EXCEEDED` (E16). Checking here turns that into an instant
  message.
- **Verified by:** `make license` reports units + per-service processes against a running
  instance.

> **Status note.** The capacity *budget* and its observability (`make license`,
> `scripts/license.script`) are implemented; an automatic *pre-build refuse/warn* gate is not
> yet a discrete step — it is realized today by defaulting TaskMan/HL7 **off**. Treat the
> explicit pre-build gate as the normative target ([§13](#13-known-limitations-deferred-items--risks)).

### Phase 4 — Namespace bootstrap (IRIS-native, non-interactive)

- **Inputs:** a running IRIS; `scripts/bootstrap.script`.
- **Actions (pure ObjectScript, no expect):** create the `VISTA` database directory and
  database, create the `VISTA` namespace, and set the mappings that keep VistA's
  percent-routines and `%Z*` globals in the `VISTA` database instead of the shared system
  library — global map `%Z*` → VISTA; routine maps `%DT*`, `%RCR`, `%XU*`, `%ZIS*`, `%ZO*`,
  `%ZT*`, `%ZV*` → VISTA. Fail loud (`halt` on any bad status).
- **Prevents:** VistA's OS-interface routines failing to resolve, and `%Z*` data landing in
  the wrong database.
- **Verified by:** the namespace exists and the import in Phase 5 resolves against it.

> **⚠ Reconciliation (what bootstrap does).** v2 §11.4 claimed `bootstrap.script` also
> "import[s] & compile[s] the routines and load[s] the globals (§8 steps 1–4)." It does
> **not** — it does steps 1–2 only (namespace + mappings, via `Config.*` classes). Import is
> Phase 5 (`00_import.py`). Code wins.

### Phase 5 — Routine & global import (the crux; its own cached layer)

- **Inputs:** the pinned `vista-m/` tree; the IRIS-patched `ZGI.m`; `prepare.py`; `00_import.py`.
- **Actions:**
  1. `prepare.py` walks the M source tree(s) and writes `routines.ro` (the `^%RO`
     routine-transfer format, including the patched `ZGI`) and `globals.lst` (absolute
     `.zwr` paths). It is built to `/tmp` and removed in the same layer so it doesn't bloat
     the image.
  2. `D ^%RI` reads `routines.ro` (override existing = YES, **All Routines**), then compiles.
  3. `D LIST^ZGI("…/globals.lst")` loads each `.zwr`.
  4. `D ^ZTMGRSET` choosing **system type 3** ("Cache (VMS, NT, Linux), OpenM-NT" — the
     Caché-compatible interface IRIS presents), renaming the FileMan routines = YES.
- **Prevents:** `ERROR #5840: not a supported type` from feeding raw `.m`/`.zwr` to
  `$SYSTEM.OBJ.ImportDir`/`Load` (E2), and `ZGI` printing "does not support IRIS" (E3).
- **Verified by:** routines compile and FileMan is callable; this is the **cached layer** —
  iterating later phases must not re-run it.

### Phase 6 — OS-interface initialization

- **Inputs:** the imported instance; `01_osinit.py`; helpers in `setup.py`.
- **Actions:** set the device `$I` entries for the TELNET (`|TNT|`) and TRM console
  (`|TRM|:|`) devices; set the **MPI local site number**; run FileMan re-init via
  `^DINIT` (MUMPS OPERATING SYSTEM → **CACHE**) + `^ZUSET`.
- **Prevents:** a half-wired OS layer where device/locale resolution fails at runtime.
- **Verified by:** subsequent menu-driven steps (Phase 7) reach their prompts.

> **⚠ Reconciliation (`^ZTMGRSET` vs `^DINIT`).** v2 §11.4 said `^DINIT`+`^ZUSET`
> "supersedes the manual `^ZTMGRSET`." In code **both** run, in different phases:
> `^ZTMGRSET` type 3 in Phase 5, `^DINIT`/`^ZUSET` in Phase 6. They coexist; "supersedes" is
> wrong. Code wins.

### Phase 7 — Post-install (site configuration)

- **Inputs:** the initialized instance; `02_postinstall.py`; `setup.py`.
- **Actions, in upstream order:** set the primary **HFS** dir; remove resource-usage logging;
  set intro text; configure NULL/console/HFS devices; **christen the DOMAIN** (`DEMO.VISTA.ORG`,
  dotted, no spaces); set the **box:volume pair** (`VISTA:IRIS`) and write the **RPC Broker
  (XWB) listener port** (`9430`) into RPC BROKER SITE PARAMETERS (#8994.1); set the volume set;
  **schedule** the startup options (`XWB LISTENER STARTER`, `XMRONT`, `HL AUTOSTART LINK
  MANAGER`, `HL TASK RESTART` at STARTUP; `HL PURGE TRANSMISSIONS` daily) as **dormant
  config**; re-index file #19.2; remove the CAPRI login; create the **System Manager**
  (`MANAGER,SYSTEM`, access `SM1234` / verify `SM1234!!`, keys incl. `XUMGR`, `XUPROG`,
  `XUPROGMODE`, `SD SUPERVISOR`); create the **institution** (`VISTA HEALTH CARE`, station
  `6100`), **division** (`VISTA MEDICAL CENTER`, `6101`), and MAS parameters.
- **Two hard rules (each prevents a real failure):**
  - **Do NOT cold-start TaskMan here.** `D ^ZTMB` spawns a manager + submanager + every
    scheduled STARTUP job (~37 persistent processes) and exhausts the 8-unit license — which
    starved Phase 8 with `LICENSE LIMIT EXCEEDED` (E16). The scheduled options above remain as
    *dormant* config; the RPC Broker is started at boot by `%ZSTART` (Phase 9), one process.
  - **Release every menu session cleanly, one at a time.** A session that enters a menu must
    escape to the programmer prompt → `halt` → wait for EOF so IRIS deregisters its license
    slot synchronously; force-closing leaves the slot held and the next connect hits
    `LICENSE LIMIT EXCEEDED` (E8). Open one connection at a time.
- **Prevents:** license exhaustion (E16/E8) and `Select OPTION:` desync from a spaced DOMAIN
  (E5) / wrong `VOLUME_SET` (E6).
- **Verified by:** Phase 11 confirms the institution/users exist and the RPC port is configured.

> **⚠ Reconciliation (RPC start path).** v2 §8 step 7 described the RPC listener as started by
> the TaskMan-scheduled `XWB LISTENER STARTER`. That option *is* scheduled (dormant), but
> because TaskMan is off, the **live** listener is started by `%ZSTART` (Phase 9). Code wins.

> **⚠ Reconciliation (HL7 `#870` listener — DEFERRED).** v2 §8 step 8 required defining an HL
> LOGICAL LINK (#870) MLLP listener on `5026`. In code, `setup.setupHL7Listener(...)` is
> **commented out**: the link is edited through the `HL EDIT LOGICAL LINKS` full-screen List
> Manager UI, which pexpect cannot drive reliably (E7). Only the autostart **scheduling** of
> the Link Manager is done (dormant). No listener binds `5026` inside the container. Tracked
> as Deferred ([§13](#13-known-limitations-deferred-items--risks)); needs a programmatic
> `#870` (FileMan/global) approach.

### Phase 8 — Sample data (Tier-1)

- **Inputs:** the configured instance; `03_sampledata.py`; `setup.py`.
- **Actions:** create a NURS location (`FAKE NURWARD`); an orderable `STREPTOZYME` lab test +
  quick order; register vitals for CPRS; a primary clinic (`VISTA HEALTH CARE`/`VHC`) and
  seven scheduling clinics (`Clinic1`, `Clinic2`, `CLINICX`, `CLInicA`–`CLInicD`) via the
  `SDBUILD` option; an inpatient ward (`TESTWARD1`) with four beds; the three clinical users
  with access/verify codes, security keys, and e-signatures (see [§8](#8-sample-data-strategy));
  set non-expiring codes; then the fictitious **patients** via `UPDATE^DIE`.
- **Prevents:** the registration menu hanging on "Searching the MVI…" (`MPIFXMLP`, E9); user
  ScreenMan desync from a stray trailing CR (E10); and license exhaustion across the many
  short sessions (E8, via the per-session release/retry helpers).
- **Verified by:** Phase 11's FileMan inquiry returns a sample patient from `^DPT` and the
  Kernel NEW PERSON file (`^VA(200)`) is populated.

### Phase 9 — Service startup hook + toggles

- **Inputs:** the loaded instance; `scripts/startup.script` (run in `%SYS`).
- **Actions:** install a `%ZSTART` routine **via the `%Routine` class API** (not a file
  import — `.m`/`.mac` `Load` hits #5840, E14). IRIS calls `SYSTEM^%ZSTART` once at every
  start; the hook reads the environment toggles and starts **only enabled** services:
  RPC Broker = `JOB ZISTCP^XWBTCPM1(<port>)` (one process); TaskMan = `JOB ^ZTMB` (gated off);
  HL7 = best-effort `STARTALL^HLCSLM` (gated off). This is the runtime license-management
  surface.
- **Prevents:** TaskMan license exhaustion (services off unless explicitly enabled) and a
  failed routine import (E14).
- **Verified by:** on boot, the RPC port becomes reachable (Phase 11 check 5); `make license`
  attributes processes to services.

### Phase 10 — Build hygiene

- **Inputs:** a populated instance per layer.
- **Actions:** after a **clean** `iris stop`, purge the IRIS journal files
  (`/usr/irissys/mgr/journal/20*`) **in each layer** (the bulk import journals GBs); commit a
  **stopped** instance.
- **Prevents:** `no space left` during the layer commit (E11) and a committed *running* IRIS
  that won't restart cleanly (E15/D16 — `iris stop` + `podman start` is a no-op on PID 1;
  clean-stop-then-commit, verify with `podman restart`).
- **Verified by:** the image restarts cleanly; its size stays near the ~20–25 GB target.

### Phase 11 — Verify

- **Inputs:** a running instance; `scripts/smoke.sh` (shared by `make verify` and CI).
- **Actions:** see [§10](#10-runtime-contract--verification) for the exact six checks.
- **Prevents:** promoting an image whose ports/data aren't actually present.
- **Verified by:** non-zero exit on any gating failure; in CI, `:latest` moves only if this
  passes on every arch.

---

## 8. Sample Data Strategy

**v3 ships Tier-1 only; Tier-2/3 are deferred.** All identities are clearly fictitious; the
instance is bannered test-only; no real PHI.

| Tier | Source | Content | Status |
|---|---|---|---|
| **0 — Built-in** | Globals shipped in VistA-M | Base reference files (and any FOIA test patients in `^DPT`). | Loaded in Phase 5. |
| **1 — WorldVistA test setup** | `02_postinstall.py` + `03_sampledata.py` (forked from `PostImportSetupScript`/`ClinicSetup`) | Institution + division, System Manager, three clinical users, clinics, a ward, an orderable test, and three patients. | **Default in v3.** |
| **2 — Rich demo DB** | VEHU-/Astronaut-style dataset | Many longitudinal patients. | **Deferred** (license/availability). |
| **3 — Synthetic** | Synthea → HL7/FHIR → ingest | Arbitrarily large cohorts. | **Deferred** (depends on the HL7/FHIR-import path; needs the deferred `#870` listener). |

### 8.1 Required patient identifiers

Patients are filed directly into PATIENT (#2) via `UPDATE^DIE` with the file's required
identifiers — `.01` NAME, `.02` SEX, `.03` DATE OF BIRTH, `.09` SSN, `.301` SERVICE CONNECTED?,
`391` TYPE (resolved to `NSC VETERAN`), `1901` VETERAN. This is deterministic and MVI-free.
Full registration (eligibility/enrollment) is deferred.

### 8.2 Sample patients (fictitious)

| Name | Sex | DOB | SSN |
|---|---|---|---|
| `PATIENT,ALPHATEST` | M | 2/3/1955 | 666-00-0001 |
| `PATIENT,BETATEST` | F | 7/14/1968 | 666-00-0002 |
| `PATIENT,GAMMATEST` | M | 11/30/1979 | 666-00-0003 |

> The `666-xx-xxxx` SSNs and `…TEST` surnames make these unmistakably non-real. The log
> records "DFN 1–3"; because FOIA Tier-0 globals may pre-populate `^DPT`, `UPDATE^DIE` assigns
> the next free IENs, so DFNs are **not** guaranteed to be 1–3 — look patients up by name/SSN.

### 8.3 Test users (the runtime sign-on contract)

Created in Phase 8; their initial verify codes are changed during e-signature setup (VistA
forces a verify change), so the **effective** sign-on codes are below. See also
[§10](#10-runtime-contract--verification).

| User | Role | Access | Verify | Signature |
|---|---|---|---|---|
| `MANAGER,SYSTEM` | System Manager (programmer; keys `XUMGR`/`XUPROG`/`XUPROGMODE`/…) | `SM1234` | `SM1234!!` | — |
| `ALEXANDER,ROBERT` | Provider | `fakedoc1` | `1Doc!@#$` | `ROBA123` |
| `SMITH,MARY` | Nurse | `fakenurse1` | `1Nur!@#$` | `MARYS123` |
| `CLERK,JOE` | Clerk | `fakeclerk1` | `1Cle!@#$` | `CLERKJ123` |

---

## 9. Service & License Model

IRIS Community is **license-capped**, and the cap — not CPU/RAM — is the binding constraint on
running VistA's background services. Services are individually switchable and license use is
observable, so a deployment stays within budget.

### 9.1 The caps (independent dimensions)

| Cap | Community value | Limits | API / control |
|---|---|---|---|
| **License units** | **8** | concurrent license-consuming connections/processes | `$SYSTEM.License.KeyLicenseUnits()` |
| Max connections | 25 | hard ceiling on total connections | `$SYSTEM.License.MaxConnections()` |
| Core cap (CPU) | ~20 cores | CPU parallelism (separate) | `--cpus` / `cpuset` |

The **8 units** are the practical limit; they are connection/process-based, not CPU-based.
Kernel daemons are largely exempt; *application* connections (the RPC listener, TaskMan jobs,
HL7 links, each CPRS / `iris session` user) consume units.

### 9.2 Per-service footprint (measured on Community, 8 units)

| Service | Toggle (default) | Identifying routine | Units | Notes |
|---|---|---|---|---|
| IRIS core (daemons, 1972, 52773/FHIR) | always on | `%SYS*` | ~1–2 baseline | most daemons exempt |
| **RPC Broker (XWB)** listener | `VISTA_ENABLE_RPC` (**on**) | `ZISTCP^XWBTCPM1` → `LISTEN^%ZISTCPS` | 1 + **1 per CPRS client** | the default cost |
| **TaskMan** + scheduled STARTUP jobs | `VISTA_ENABLE_TASKMAN` (**off**) | `ZTM*` / `%ZTM*` | **exhausts 8/8** (~37 procs) | → `LICENSE LIMIT EXCEEDED` |
| **HL7 Link Manager** | `VISTA_ENABLE_HL7` (**off**) | `HL*` | ~1 per active link | inert until a `#870` listener exists (deferred) |
| Interactive / CPRS session | per connection | `VISTA` job | 1 per signed-in user | |

Measured datapoints (log): **default (RPC only) = 2/8 used (6 free)**; **`VISTA_ENABLE_TASKMAN=1`
= 8/8 → `LICENSE LIMIT EXCEEDED`** (even the report's own connection is then refused).

> **⚠ Reconciliation (RPC routine name).** v2 §14.2 labeled the RPC listener `XWBTCPM`. The
> code jobs `ZISTCP^XWBTCPM1`; `license.script` matches `"XWBTCP"`/`"ZISTCPS"`. v3 uses the
> code's name.

### 9.3 Budget

| Configuration | Units | CPRS headroom |
|---|---|---|
| RPC only (default) | 2 | ~6 concurrent users |
| RPC + TaskMan | 8 → over | none |
| RPC + TaskMan + HL7 | ≫8 | not viable on Community |

On Community, keep TaskMan/HL7 **off** (RPC Broker + ~6 clinical users). TaskMan-class
background services require a larger, non-Community license.

### 9.4 Toggles

Read at boot by the `%ZSTART` hook (Phase 9); only enabled services start and consume units.
Set via Compose `environment:`, the host env (e.g. `VISTA_ENABLE_TASKMAN=1 podman compose up -d`),
or `make run ENABLE_TASKMAN=1`.

| Variable | Default | Effect |
|---|---|---|
| `VISTA_ENABLE_RPC` | `1` | start the RPC Broker (XWB) listener on `VISTA_RPC_PORT` |
| `VISTA_RPC_PORT` | `9430` | RPC Broker port |
| `VISTA_ENABLE_TASKMAN` | `0` | cold-start TaskMan (`^ZTMB`) + its scheduled STARTUP jobs |
| `VISTA_ENABLE_HL7` | `0` | start the HL7 Link Manager (needs a `#870` listener — deferred) |

### 9.5 Observability — `make license`

`make license` (`scripts/license.script`) reports, against a running instance: license units
(total / consumed / available), max connections, the active toggles, and **every live process
labeled by service** (RPC Broker / TaskMan / HL7 / VistA session / IRIS system).

> Caveat: when the pool is fully consumed (e.g. TaskMan on), even `make license` cannot connect
> to report it (Error 133 / empty) — read it from a config with headroom, or use `iris list` /
> a process count. Expected behavior (E19).

---

## 10. Runtime Contract & Verification

### 10.1 Published ports

| Endpoint | Port | Notes |
|---|---|---|
| IRIS superserver — RPC / xDBC / SQL | 1972 | terminal: `<engine> exec -it vista-iris iris session IRIS -U VISTA`; also the VS Code `isfs` dev path |
| IRIS Management Portal (web) + FHIR REST | 52773 | `http://localhost:52773/csp/sys/UtilHome.csp`; FHIR served on the Health edition |
| **VistA RPC Broker (XWB)** | 9430 | CPRS / RPC clients; the reachable external interface today (default ON) |
| **VistA HL7 MLLP** | 5026 | **published but unbacked** — the `#870` listener is deferred ([§13](#13-known-limitations-deferred-items--risks)) |

Both Compose files and `make run` publish all four ports. The base image already exposes 1972
and 52773; the `Dockerfile` additionally `EXPOSE`s 9430 and 5026.

### 10.2 Acceptance checks (`make verify` == CI, via `scripts/smoke.sh`)

The same script gates `make verify` locally and the `verify` job in CI; it retries briefly to
absorb boot warm-up and exits non-zero on any **gating** failure.

| # | Check | Method | Gating? |
|---|---|---|---|
| 1 | IRIS instance `running` | `iris list` (retry ~40) | **yes** |
| 2 | VISTA sign-on reachable — Kernel NEW PERSON file `^VA(200,0)` populated | M probe in `VISTA` | **yes** |
| 3 | FileMan sample patient present in `^DPT` | M probe (`$O(^DPT(0))`) | **yes** |
| 4 | TaskMan schedule `^%ZTSCH` present | M probe in `%SYS` | **no — best-effort/warn** |
| 5 | RPC Broker reachable on `9430` | host `nc -z` (retry ~30) | **yes** |
| 6 | HL7 MLLP reachable on `5026` | host `nc -z` (retry ~30) | **yes** |

> **⚠ Reconciliation (checks 4 and 6).** v2 §7.1/§10 implied `make verify` confirms "TaskMan
> active" and a true HL7 round-trip. In code: **check 4 is non-gating** (a present `^%ZTSCH`
> only means TaskMan was *scheduled*, not running). **Check 6 passes deceptively** — nothing
> binds `5026` (the listener is deferred, [§7 Phase 7](#phase-7--post-install-site-configuration)),
> so its "pass" is an artifact of the port forwarder answering the connect (D15). v3 documents
> the checks as implemented and flags 6 as not proof of an HL7 listener. The
> [Open Questions](#13-known-limitations-deferred-items--risks) note this gap; v3 does not
> alter the code.

---

## 11. Build Hygiene & Reproducibility

### 11.1 Local build hygiene

- **Two layers, by design.** Layer 1 (expensive, cached): namespace bootstrap + routine/global
  import (Phases 4–5). Layer 2 (iterated): OS-init, post-install, sample data, and the
  `%ZSTART` install (Phases 6–9). Editing Layer-2 scripts reuses the cached import layer.
- **Journal purge per layer** after a clean `iris stop` (Phase 10): the bulk import journals
  GBs; after a clean shutdown the data is in the `.DAT` and IRIS recreates journals on next
  start.
- **Commit a stopped instance** (Phase 10): a committed *running* IRIS is non-restartable;
  `iris stop` + `podman start` is a no-op on PID 1 — clean-stop then commit; verify with
  `podman restart`.
- **One build path at a time.** `podman compose build` (docker-compose provider) and
  `podman build` (buildah) keep **separate** layer caches; don't expect reuse across them (D18).
- **Reproducibility inputs:** the pinned `vista-m` submodule (`b7aecb9`) + the recorded
  per-arch `IRIS_TAG`. Re-sync the submodule with upstream **deliberately**, recording the new
  commit.

### 11.2 Multi-arch publication (GHCR)

The image is published to `ghcr.io/vista-cloud-dev/vista-iris` by
`.github/workflows/publish.yml`. The flow verifies a candidate **before** the public `:latest`
moves and uses **no QEMU** (each arch builds on its own native runner, so the interactive site
build isn't emulated):

| Job | Action |
|---|---|
| **build** (matrix) | Build each arch on a native runner — `linux/amd64` on `ubuntu-24.04`, `linux/arm64` on `ubuntu-24.04-arm`, passing the matching `IRIS_TAG` — and **push by digest** (no human tag yet). Frees runner disk first (the loaded image is multi-GB); checks out with the `vista-m` submodule. |
| **merge** | Assemble a `sha-<commit>` **candidate** manifest from the per-arch digests (cheap). |
| **verify** (matrix) | Pull the candidate, boot it (`docker run` with the four published ports), and run `scripts/smoke.sh` — the **same** §10 checks `make verify` runs locally — fail-loud per arch. |
| **promote** | Only if verify is green on every arch, retag the candidate to `:latest` and `:<YYYYMMDD>` (plus the git tag on `v*` tag pushes). |

Triggers: manual `workflow_dispatch`, and `push` of `v*` tags. A `concurrency` group prevents
two publishes of the same ref racing on the `:latest` pointer.

### 11.3 Consumer path (no local build)

Consumers pull the published image and need only Podman/Docker:

- `make pull` + `make run` (plain `<engine> run`, **not** Compose — `podman compose` may
  delegate to `podman-compose`, a Python tool that reintroduces a host runtime dependency), or
- `docker-compose.run.yml` (references the GHCR image; durable %SYS commented out to match the
  disposable Quickstart; override the tag with `VISTA_TAG=…`), or
- a single documented `podman run` one-liner (see `readme.md`).

The build path (`make build` / `docker-compose.yml`) is for **changing** the build and does
require the submodule + an engine.

---

## 12. Repository Layout & Artifact Reference

Reconciled to the **actual** files (the phantom v1 spec in v2 §12 does not exist; this tree
also adds artifacts absent from both v2 §12 and the log's §9 component table).

```
vista-iris/
├── Dockerfile                       Strategy A; cached import layer + iterated
│                                    site-build layer; journal purge (Phases 4-10)
├── docker-compose.yml               BUILD path: builds the image; ports; durable
│                                    %SYS (opt-in); service-toggle env
├── docker-compose.run.yml           CONSUMER path: runs the prebuilt GHCR image
├── Makefile                         Entry point: preflight/fresh/sources/build/up/
│                                    down/run/pull/stop/verify/lint/test/ci/clean/
│                                    license; ENGINE + IRIS_TAG + toggle vars
├── .dockerignore                    Trims build context (esp. the .git store)
├── readme.md                        Quickstart (consumer) + Contributing (build)
├── .github/workflows/publish.yml    Multi-arch GHCR build → verify → promote (§11.2)
├── scripts/
│   ├── preflight.sh                 Phase 1 gate (engine/disk/ports/conflicts/sources);
│   │                                --clean = fresh install
│   ├── smoke.sh                     Phase 11 / §10 acceptance checks (shared local+CI)
│   ├── bootstrap.script             Phase 4: VISTA db + namespace + mappings (IRIS-native)
│   ├── startup.script               Phase 9: installs the toggle-driven %ZSTART hook
│   ├── license.script               `make license` report (units + per-service procs)
│   └── vista/                      Cleaned, IRIS-only Python 3 fork of the WorldVistA driver
│       ├── config.py                Phase 0: env-overridable settings + connect()
│       ├── helper.py                `iris session` pexpect driver (write/wait/multiwait)
│       ├── prepare.py               Packs routines.ro (^%RO) + globals.lst
│       ├── 00_import.py             Phase 5: ^%RI / LIST^ZGI / ^ZTMGRSET type 3
│       ├── 01_osinit.py             Phase 6: devices / MPI / DINIT / ZUSET
│       ├── 02_postinstall.py        Phase 7: site config (NO TaskMan cold-start)
│       ├── 03_sampledata.py         Phase 8: users/clinics/ward/patients (UPDATE^DIE)
│       ├── setup.py                 The forked install steps used by 00-03
│       └── m/ZGI.m                  IRIS-patched global importer ($ZV["IRIS")
└── vista-m/                         Pinned shallow submodule: WorldVistA/VistA-M @ b7aecb9
```

> The legacy WorldVistA artifacts that were audited and **removed** in the fork (GT.M/YottaDB
> branches, the Caché-2011 installer, EWD.js, the CDash dashboard, run-time fetches from
> personal repos, OS-spoofing/encryption-disable "fakes") are documented in v2 §5 and are
> intentionally absent here.

---

## 13. Known Limitations, Deferred Items & Risks

| Item | Status | Note / direction |
|---|---|---|
| **HL7 `#870` MLLP listener on 5026** | **Deferred** | The `HL EDIT LOGICAL LINKS` List-Manager UI can't be pexpect-driven (E7); needs a programmatic `#870` (FileMan/global) approach. Port 5026 is published but unbacked. |
| **TaskMan** | **Off by default** | Exhausts the 8-unit Community license (~37 procs); needs a larger license. |
| **`make test` (M-Unit)** | **Stub** | No automated M tests run yet (`D EN^%ut(...)` is a TODO). |
| **`make lint` XINDEX** | **Partial/stub** | `shellcheck` runs on wrappers; in-instance XINDEX over changed routines is a TODO. |
| **`make verify` depth** | **Partial** | Ports + Kernel/`^DPT` data gated; the TaskMan check is non-gating ([§10](#10-runtime-contract--verification)). |
| **Pre-build capacity gate** | **Target** | Phase 3's refuse/warn is realized today by defaulting TaskMan/HL7 off; an explicit early gate is the normative target. |
| **Image size** | ~25 GB | Whole `vista-m` is COPYed *and* loaded; a builder stage could drop the source from the final layer. |
| **Platform coverage** | arm64 validated locally; amd64 wired in CI | Both build in CI; amd64 not locally validated here. |
| **IRIS vs Caché** | Adjusted | `%Z*`/`^%ZOSF`, locale, `irissession`→`iris session` handled; further `$ZU` edge cases possible. |
| **Character set / locale** | Risk | IRIS is Unicode; FOIA VistA traditionally `enu8`. Lock the namespace locale; mismatches corrupt extended characters. |
| **Forked-installer maintenance** | Risk | `scripts/vista/` is a cleaned fork; re-sync with upstream `WorldVistA/VistA` deliberately, recording the commit. |
| **No real PHI** | By design | Sample data only; instance bannered test-only. |

### Open Questions (flagged, not resolved)

1. **5026 verification gap.** Should `smoke.sh` stop fail-gating port 5026 (or switch to `ss`
   inside the container) until the `#870` listener exists, so a green check means a real
   listener? Documented as-is for now; no code change proposed by this spec.
2. **`SITE_NUMBER` 6161 vs institution 6100 / division 6101.** Three distinct numbers exist
   ([§7 Phase 0/7](#phase-0--configuration)); the `6161` MPI/DINIT default is unexplained in
   the prior docs. Confirm intent.
3. **Compose floating-tag footgun.** `docker-compose.yml` falls back to floating `latest-cd`
   (non-arch) when `IRIS_TAG` is unset; only the `Makefile` guarantees the arch-specific tag.
   A direct `podman compose build` without the env var may pull a multi-arch floating tag.

---

## 14. Key Technical Facts (Appendix A)

Each value verified against the code unless marked *(measured)* — a runtime datapoint from the
log, recorded as historical color, not a build invariant.

| Fact | Value |
|---|---|
| Base image | `intersystems/irishealth-community:latest-cd-linux-arm64` (arm64) / `…-linux-amd64` (amd64); `latest-cd` = compose fallback |
| VistA source | `WorldVistA/VistA-M` @ `b7aecb9` (pinned shallow submodule) |
| Routines / globals loaded | 33,952 routines · 2,922 global files *(measured)* |
| Namespace / database | `VISTA` / `VISTA` (db dir `/usr/irissys/mgr/VISTA/`; durable opt-in `/durable/iris`) |
| Global / routine maps | `%Z*` global → VISTA; `%DT* %RCR %XU* %ZIS* %ZO* %ZT* %ZV*` routines → VISTA |
| OS system type | `^ZTMGRSET` → 3 = Cache (VMS, NT, Linux), OpenM-NT |
| OS init | `^DINIT` (MUMPS OPERATING SYSTEM → CACHE) + `^ZUSET` |
| Domain / institution / division | `DEMO.VISTA.ORG` / `VISTA HEALTH CARE` (station 6100) / `VISTA MEDICAL CENTER` (6101) |
| MPI / DINIT site number | `6161` (config default) |
| Box:volume | `VISTA:IRIS` (volume-set anchor `VISTA`) |
| Ports | 1972 superserver · 52773 portal/FHIR · 9430 RPC Broker · 5026 HL7 (published, listener deferred) |
| RPC Broker start | `%ZSTART` → `JOB ZISTCP^XWBTCPM1(9430)` → `LISTEN^%ZISTCPS` |
| Startup hook | `%ZSTART` (`SYSTEM^%ZSTART`), installed via the `%Routine` API as `%ZSTART.MAC` |
| Service toggles | `VISTA_ENABLE_RPC=1`, `VISTA_RPC_PORT=9430`, `VISTA_ENABLE_TASKMAN=0`, `VISTA_ENABLE_HL7=0` |
| License caps | **8 units**, 25 max connections, ~20-core cap |
| License: default (RPC only) | **2 / 8** *(measured)* |
| License: TaskMan on | **8 / 8** → `LICENSE LIMIT EXCEEDED` (~37 processes) *(measured)* |
| PATIENT (#2) identifiers | `.01` NAME · `.02` SEX · `.03` DOB · `.09` SSN · `.301` SC? · `391` TYPE · `1901` VETERAN |
| Sample patients | `PATIENT,{ALPHA,BETA,GAMMA}TEST`, SSN `666-00-000{1,2,3}` |
| Preflight disk | ≥ 40 GB (build) · ≥ 25 GB (run prebuilt) |
| Final image size | ~25.6 GB *(measured)* |
| Published image | `ghcr.io/vista-cloud-dev/vista-iris` (`:latest`, `:<YYYYMMDD>`, `:sha-<commit>`, git tag) |

---

## Appendix B — Reconciliation ledger (doc vs. code)

Every place a prior doc disagreed with the working code, resolved in favor of code. The
narrative for each lives in the log (§5 discoveries / §6 errors); the in-line **⚠ Reconciliation**
notes throughout this spec are gathered here for audit.

| # | Prior doc claim | Code ground truth | Where addressed |
|---|---|---|---|
| C1 | v2 §8 step 9 / §7.1: cold-start TaskMan during install | TaskMan **not** cold-started (E16); RPC via `%ZSTART`; TaskMan off by default | §4, §7 Phase 7/9, §9 |
| C2 | v2 §8 step 8 / §10 / §6: HL7 `#870` MLLP listener configured + verified on 5026 | `setupHL7Listener` commented out — listener **deferred** (E7); 5026 unbacked | §1, §7 Phase 7, §10, §13 |
| C3 | v2 §11.4: `bootstrap.script` imports routines/globals (steps 1–4) | It does steps 1–2 (namespace + mappings) only; import is `00_import.py` | §7 Phase 4/5 |
| C4 | v2 §11.4: `^DINIT`/`^ZUSET` *supersedes* `^ZTMGRSET` | Both run, in Phases 5 and 6 respectively | §7 Phase 6 |
| C5 | v2 §10/§7.1: verify confirms "TaskMan active" + true HL7 reachability | TaskMan check non-gating; HL7 check passes only via the port forwarder | §6, §10 |
| C6 | v2 §12: v1 spec `vista-iris-container-spec.md` retained | v1 does not exist on disk | §12 |
| C7 | v2 §12 / §11.4: stale script list (no `00_import.py`/`prepare.py`/`m/ZGI.m`; `README.md`) | Actual tree adds those + `preflight.sh`/`smoke.sh`/`startup.script`/`license.script`/`docker-compose.run.yml`/`publish.yml`; file is `readme.md` | §12 |
| S1 | `preflight.sh` comment "default 50" GB | Effective default 40 GB (25 for run) — E18 | §6 |
| S2 | v2 §14.2 RPC routine `XWBTCPM` | `ZISTCP^XWBTCPM1` → `LISTEN^%ZISTCPS` | §3, §9.2 |
| S3 | v2 §7.1/§15: `make ci` is the whole pipeline | Real distribution is GHCR `publish.yml`; `make lint`/`test` are stubs | §11, §13 |

---

## 15. Future Directions (non-binding)

These mirror the log's §8.13 and are **not requirements** — they describe options a future,
separate effort could take. None is in scope for v3.

- **A Go orchestrator (optional).** The hard, irreducible part is the interactive VistA
  dialog; a Go expect library (e.g. `Netflix/go-expect`) could replace pexpect while the IRIS
  work stays in M/ObjectScript. Keep the `write/wait/multiwait` primitives and the per-step
  "release cleanly" helper. Prefer the IRIS Native API / call-in where a programmatic path
  exists (`UPDATE^DIE`, license/process queries, `%Routine` creation); reserve expect for the
  genuinely menu-only steps (SDBUILD clinic, ScreenMan user add). See `go-cli-selection-guide.md`.
- **A separate control-plane tool.** Operating a *built* instance — lifecycle, day-2 admin,
  the toggle/license surface as a runtime API — belongs to a distinct tool, **explicitly out
  of scope** for this build spec ([§1](#1-purpose--scope)). v3 defines the runtime *contract*
  that such a tool would target.
- **Idempotent, individually-runnable phases.** Modeling each phase to run against a persistent
  instance (so iteration never re-imports) and feeding a single declarative config (Phase 0)
  into preflight, build, the runtime hook, and the license report — one schema, many consumers.
- **Completing the deferred interfaces.** A programmatic `#870` MLLP listener (closing the
  5026 gap) and the HL7/FHIR-import path enabling Tier-3 synthetic data.

---

## 16. References

- IRIS for Health Community — [Docker Hub `intersystems/irishealth-community`](https://hub.docker.com/r/intersystems/irishealth-community) · [InterSystems Container Registry](https://containers.intersystems.com/contents)
- WorldVistA VistA M components — [`WorldVistA/VistA-M`](https://github.com/WorldVistA/VistA-M) · build/install automation (forked & cleaned) — [`WorldVistA/VistA`](https://github.com/WorldVistA/VistA)
- Companion docs in this repo: `vista-iris-implementation-log.md` (history) · `vista-iris-container-spec-v2.md` (superseded design spec) · `vista-dev-iris-tooling.md` · `va-trm-m-tools.md` · `vaec-vista-hosting-general.md` · `go-cli-selection-guide.md` · `dev-guide-streamlined-onboarding.md`
