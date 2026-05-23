# VistA on IRIS — Containerized Instance Specification

**Status:** Draft spec · **Date:** 2026-05-23 · **Scope:** A reproducible, lightweight, cross-platform (Linux + macOS, x86-64 + Apple Silicon) container that stands up a *functioning* VistA EHR instance with sample patients on InterSystems IRIS **Community Edition**.

---

## 1. Purpose & Scope

Define how to build and run a single-container VistA instance suitable for development, demos, training, and integration testing — **not production, not real PHI**. The deliverable is a Docker/OCI image plus a `docker compose` (or `podman compose`) setup that:

1. Boots InterSystems IRIS Community Edition.
2. Loads the OSEHRA/WorldVistA "FOIA" VistA M codebase (routines + globals).
3. Configures the namespace, TaskMan, and the RPC Broker listener so VistA actually runs.
4. Loads sample/test patients and supporting reference data (institutions, users, clinics).
5. Exposes documented endpoints for verification (terminal/roll-and-scroll, Management Portal, RPC Broker).

### Glossary

| Term | Meaning |
|---|---|
| **VistA** | Veterans Health Information Systems and Technology Architecture — the VA's EHR, written in MUMPS (M). |
| **MUMPS / M** | The language + integrated hierarchical database ("globals") VistA is built on. |
| **IRIS** | InterSystems IRIS data platform — the supported successor to Caché; runs M natively. The VA's production VistA runs on InterSystems' M engine, so IRIS is the most "native" host. |
| **Globals** | Persistent sparse arrays = VistA's data store (e.g. `^DPT` = patient file). |
| **Routines** | Compiled M program units (`.m` source). |
| **FileMan** | VistA's database management layer over globals. |
| **KIDS** | Kernel Installation & Distribution System — VistA's package installer. |
| **RPC Broker** | TCP listener (XWB) that GUI clients such as CPRS connect to. |
| **CPRS** | Computerized Patient Record System — the Windows clinical GUI. |
| **FOIA VistA** | The public-domain VistA release; mirrored monthly to GitHub as routines + `.zwr` globals. |

---

## 2. Goals & Non-Goals

### Goals
- **One command up:** `docker compose up` (or `podman compose up`) yields a working, pre-populated VistA.
- **Portable:** runs identically on Linux and macOS, on both `amd64` and `arm64` (Apple Silicon).
- **Lightweight:** single base image (IRIS Community), no external services required.
- **Reproducible:** image build is deterministic from pinned source tags.
- **Persistent (optional):** data survives container restarts via durable storage.
- **Verifiable:** documented "is it working?" checks.

### Non-Goals
- Not production-grade (IRIS Community is dev/eval-licensed and capacity-capped).
- No real patient data — sample/synthetic only.
- No bundled Windows CPRS GUI (Windows-only; addressed as an optional access path).
- No HA/clustering, no VistA Imaging, no multi-site federation.

---

## 3. Container Technology Decision

**Recommendation: Docker image (OCI), orchestrated with Docker Compose, Podman-compatible.**

| Option | Verdict | Rationale |
|---|---|---|
| **Docker + Compose** | ✅ Primary | Universally available on Linux/macOS; Compose makes the volume/port/init wiring declarative. |
| **Podman + podman-compose** | ✅ Supported | Daemonless, rootless, drop-in compatible with the same `Dockerfile`/compose file; preferred where no Docker daemon is wanted. |
| **Vagrant VM** (OSEHRA's existing path) | ❌ | Heavier (full VM), not "lightweight," slower to boot. Kept only as a fallback reference. |
| **Bare metal / GT.M / YottaDB** | ❌ | Out of scope — this spec targets IRIS specifically. |

> Portability note: the `Dockerfile` and compose file are written once. Apple Silicon users pull the `arm64` image variant; everything else is identical.

---

## 4. Base Image Decision

**Use `intersystems/iris-community`** (standard) as the base. Consider `intersystems/irishealth-community` only if you also want IRIS's built-in HL7/FHIR interoperability for ingesting external data.

- **Registry:** Docker Hub `intersystems/iris-community`, mirrored at `containers.intersystems.com/intersystems/iris-community`. Publicly pullable; no login required for Community Edition.
- **Architectures:** `amd64` and `arm64` (append `-arm64` to the tag, e.g. `latest-cd-arm64`) → covers Linux + Apple Silicon Macs.
- **Default ports:** `1972` (superserver / RPC + xDBC), `52773` (web / Management Portal).
- **Default credentials:** `_SYSTEM` / `SYS` (forced change on first login).
- **Persistence:** "Durable %SYS" — mount a host volume and set `ISC_DATA_DIRECTORY` so instance data lives outside the container layer.
- **Known limits (Community Edition):** development/evaluation license only; capped at ~20 cores (`--cpuset-cpus`/`--cpus` may be required on big hosts); limited concurrent connections. Adequate for a single-developer VistA.

> **Pin the tag** (e.g. a specific `iris-community:2025.x`) in the spec'd build for reproducibility; `latest-cd` is convenient but drifts.

---

## 5. VistA Source Decision

| Artifact | Source | Use |
|---|---|---|
| **VistA M code** (routines + globals) | `github.com/WorldVistA/VistA-M` | The FOIA codebase: `Packages/<pkg>/Routines/*.m` and `Packages/<pkg>/Globals/*.zwr`. |
| **Build/install automation** | `github.com/WorldVistA/VistA` | Cross-platform install + test scripts; **already supports Caché/IRIS** (`Documentation/InstallCache.rst`, `ImportCache.rst`, `ConfigureCache.rst`, `AutomatedVistAConfiguration.rst`). |

The OSEHRA `VistA` repo's `Scripts/` + CMake harness (`Testing/Setup/ImportRG.cmake`) drives the import process that "mirrors the Caché and GT.M manual processes," and its optional `TEST_VISTA_SETUP` path runs the sample-data scripts (see §8). **We reuse this automation rather than reinventing it**, parameterized for IRIS.

> Compatibility caveat to validate during implementation: OSEHRA's documented path historically targets **Caché**. IRIS is highly compatible but differs in a few `$ZU`/legacy APIs, locale/character-set defaults (IRIS is Unicode; FOIA VistA traditionally an 8-bit `enu8` locale), and class internals. Expect minor adjustments to the OS-interface layer (`%Z*` routines) and namespace locale.

---

## 6. Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│  Container:  vista-iris                                        │
│  FROM intersystems/iris-community:<pinned>                     │
│                                                                │
│   ┌────────────────────────────────────────────────────────┐ │
│   │ IRIS instance (M engine)                                 │ │
│   │                                                          │ │
│   │  Namespace: VISTA  ──► Database: VISTA (cache/iris.dat)  │ │
│   │   • Routine maps: %DT* %RCR %XU* %ZIS* %ZO* %ZT* %ZV*    │ │
│   │   • Global  maps: %Z*                                    │ │
│   │                                                          │ │
│   │  VistA codebase (KIDS/FileMan/Kernel/CPRS RPCs/…)        │ │
│   │  TaskMan (background job scheduler)                      │ │
│   │  RPC Broker listener (XWB)  ── TCP 9430                  │ │
│   └────────────────────────────────────────────────────────┘ │
│                                                                │
│  Durable %SYS  ──►  volume: /durable  (ISC_DATA_DIRECTORY)     │
└──────────────────────────────────────────────────────────────┘
        │ 1972 (superserver)   │ 52773 (portal)   │ 9430 (broker)
        ▼                      ▼                   ▼
   IRIS terminal /        Management Portal    CPRS / RPC clients
   roll-and-scroll        (browser)            (optional, see §9)
```

---

## 7. Build Pipeline

Two viable strategies; **Strategy A is recommended** for a self-contained, fast-booting image.

### Strategy A — Bake at build time (recommended)
Import all code/data during `docker build`, so `docker run` starts an already-loaded instance.

1. `FROM intersystems/iris-community:<pinned>`
2. `COPY` the pinned VistA-M sources + ObjectScript/`iris.script` install scripts into the image.
3. Run `iris start` → `iris session IRIS < install.script` to: create DB/namespace, set mappings, import routines, load globals, run post-install, configure TaskMan + Broker, load sample data.
4. `iris stop`, then the default IRIS entrypoint serves the prepared instance.

**Pros:** boots in seconds, fully reproducible, no first-run wait. **Cons:** larger image, longer build.

### Strategy B — Initialize on first boot
Ship code/data into the image (or a mounted volume) and run the install via the IRIS container init hook (`iris-main --after` / a configured `ISC_CPF_MERGE_FILE` + init script) on first start, persisting to durable `%SYS`.

**Pros:** smaller image, install state lives on the durable volume. **Cons:** slow first boot; init must be idempotent.

---

## 8. Detailed Install Sequence (what the scripts must do)

Executed as ObjectScript/M, mirroring OSEHRA's Caché path adapted to IRIS:

1. **Database + namespace**
   - Create database `VISTA` backed by `/durable/VISTA/` (or in-image dir for Strategy A).
   - Create namespace `VISTA` mapped to that database.
   - Set namespace **locale/collation** appropriately (validate Unicode vs 8-bit `enu8` for FOIA data).

2. **Mappings** (so VistA's OS-interface code resolves correctly)
   - Global mapping: `^%Z*` → VISTA database.
   - Routine mappings: `%DT*`, `%RCR`, `%XU*`, `%ZIS*`, `%ZO*`, `%ZT*`, `%ZV*` → VISTA database.

3. **Import routines** — load `Packages/**/Routines/*.m` (bulk import via `$SYSTEM.OBJ.ImportDir(...,"ck")` or `^%RI`), then compile.

4. **Load globals** — import `Packages/**/Globals/*.zwr` (zwrite format) via `$SYSTEM.OBJ.Load(...)` / `^%GI`. This includes FileMan dictionaries, Kernel files, and the seed data needed for VistA to run.

5. **Post-install configuration** (equivalent of OSEHRA `PostImportSetupScript.py`)
   - Set up the **Institution** / domain, primary **HFS** dir, time zone.
   - Create the manager/programmer **user account** (e.g. `,` access) and a clinical test user.
   - Initialize **Kernel** parameters and **`^%ZOSF`** OS-specific tables for IRIS.

6. **TaskMan** — configure and start the background job scheduler (`^ZTMB`), so scheduled/queued jobs run.

7. **RPC Broker (XWB)** — create a listener on TCP **9430** so RPC clients (CPRS, web bridges, test harnesses) can connect; ensure it auto-starts with the instance.

8. **Verification hook** — run a smoke check (e.g. `D ^XUP` login, FileMan inquiry on the patient file).

---

## 9. Sample Patient Data Strategy

Tiered, so the spec works even if richer datasets are unavailable:

| Tier | Source | Content | Effort |
|---|---|---|---|
| **0 — Built-in** | Globals shipped in VistA-M | A handful of FOIA test patients + base reference files. | Free (loaded in §8). |
| **1 — OSEHRA test setup (recommended baseline)** | `ImportUsers.py` + `ClinicSetup.py` + `PostImportSetupScript.py` (run via `TEST_VISTA_SETUP`) | Test patients, users, institutions, and clinics wired for scheduling — enough to register, schedule, and order. | Low; reuse existing scripts. |
| **2 — Rich demo database** | A VEHU-style / Astronaut-style demo dataset (richer longitudinal patients) | Many patients with meds, labs, notes, appointments. | Medium; depends on license/availability of the dataset. |
| **3 — Synthetic generation** | Synthea → HL7/FHIR → ingest | Arbitrarily large synthetic cohorts. | High; requires an HL7/FHIR ingestion path (favoring `irishealth-community`) and FileMan mapping. Optional/advanced. |

**Recommendation:** ship **Tier 1** by default (deterministic, lightweight, scriptable), document **Tier 2/3** as opt-in. All sample patients must be clearly fictitious; no real PHI.

---

## 10. Access & Verification

| Endpoint | Port | How | Portability |
|---|---|---|---|
| **IRIS terminal / VistA roll-and-scroll** | 1972 / `docker exec` | `docker exec -it vista-iris iris session IRIS -U VISTA` then `D ^XUP` / FileMan menus. | ✅ Linux + macOS. Primary functional check. |
| **Management Portal** | 52773 | Browser → `http://localhost:52773/csp/sys/UtilHome.csp`; inspect `^DPT` etc. via SQL/global viewer. | ✅ |
| **RPC Broker (XWB)** | 9430 | RPC clients / test harness / web bridges. | ✅ for the listener; clients vary. |
| **CPRS GUI** | via 9430 | Windows-only Delphi app. On Linux/macOS run under Wine or a Windows VM. | ⚠️ Not portable — documented as optional. |

**"It works" acceptance checks:**
1. `iris list` shows the instance `running`.
2. Terminal login to `VISTA` namespace succeeds; `D ^XUP` reaches a VistA menu.
3. FileMan inquiry returns a known sample patient from the patient file (`^DPT`).
4. TaskMan reports active.
5. RPC Broker accepts a TCP connection on 9430.

---

## 11. Required Artifacts (specification)

This section specifies *what* each build and runtime artifact must contain and do. It is intentionally code-free — the implementation is produced separately during the build phase and is documented in the repository README.

### 11.1 Container image definition (`Dockerfile`)
Must:
- Base on a **pinned** `intersystems/iris-community` tag, exposed as a build argument so the architecture-specific variant (append `-arm64` on Apple Silicon) can be selected without editing the file.
- Copy the pinned VistA-M sources and the install scripts into a working directory owned by the `irisowner` account.
- Under **Strategy A** (§7): during the build, start the IRIS instance quietly, run the install orchestration as an IRIS session that reads the install script, then stop the instance cleanly — so the committed image already contains a fully loaded VistA.
- Leave the stock IRIS container entrypoint in place to serve the prepared instance at runtime.

### 11.2 Orchestration definition (`docker-compose.yml`)
Must define a single service that:
- Builds from the image definition above and assigns a stable container name.
- Publishes three ports, each documented by purpose: **1972** (superserver / RPC + xDBC), **52773** (Management Portal), **9430** (VistA RPC Broker / XWB).
- Mounts a named volume for durable storage and sets `ISC_DATA_DIRECTORY` to a path under that volume (durable `%SYS`).
- Optionally caps CPU to remain within the Community Edition core limit on large hosts.
- Remains valid under `podman compose` without modification.

### 11.3 Install orchestration (`scripts/`)
A top-level orchestration entry point, invoked once at build (Strategy A) or on first boot (Strategy B), that performs the operations in §8 in order by delegating to the per-step scripts listed in §12. Requirements:
- The namespace, database, and routine/global mappings are established first (via the configuration utilities or a CPF merge file).
- Routines are imported and compiled, then globals (`.zwr`) are loaded, then post-install configuration runs (institution, users, OS tables, TaskMan, RPC Broker on 9430), then Tier-1 sample data is loaded.
- Every step is **idempotent** so re-runs are safe, and the orchestration **fails loudly** (non-zero exit) on any import, compile, or post-install error, so a broken build never yields a "green" image.

---

## 12. Repository Layout (deliverables)

```
vista-iris/
├── docs/
│   └── vista-iris-container-spec.md   ← this document
├── Dockerfile
├── docker-compose.yml
├── scripts/
│   ├── install.script                 ← orchestration entrypoint
│   ├── 01-namespace.script            ← DB/NS + mappings (or CPF merge)
│   ├── 02-import-routines.script
│   ├── 03-load-globals.script
│   ├── 04-postinstall.m               ← institution/users/TaskMan/Broker
│   └── 05-sample-data.m               ← Tier-1 patients/clinics
├── vista-m/                           ← vendored or submodule: WorldVistA/VistA-M (pinned)
└── README.md                          ← quickstart
```

---

## 13. Constraints, Risks & Open Questions

| Item | Notes / Mitigation |
|---|---|
| **IRIS Community license** | Dev/eval only, capacity-capped (~20 cores, limited connections). Fine for this use; document the non-production limit. |
| **IRIS vs Caché compatibility** | OSEHRA path targets Caché; expect tweaks to `%Z*`/`^%ZOSF` OS layer, locale/charset, and a few `$ZU` calls. **Highest-risk item — validate early with a minimal import.** |
| **Character set / locale** | IRIS is Unicode; FOIA VistA traditionally `enu8` (8-bit). Decide and lock namespace locale; mismatches corrupt extended characters. |
| **Image size vs boot time** | Strategy A (baked) trades a bigger image for instant boot — preferred for demos. |
| **No real PHI** | All patients fictitious; banner the instance as test-only. |
| **CPRS access on Linux/macOS** | Not native; document Wine/VM, or rely on roll-and-scroll + RPC for verification. |
| **Apple Silicon** | Use `-arm64` IRIS tags; confirm the VistA import runs identically on arm64 (it should — M code is arch-independent). |
| **Legal/licensing of VistA** | FOIA VistA is public domain; the IRIS image is InterSystems Community-licensed. Keep them as separate, attributable layers. |

---

## 14. Operational Flow (target end-state)

Once implemented, standing up the instance is a four-step flow (exact commands belong in the repository README, not this spec):

1. **Obtain sources** — clone the repository and bring in the pinned VistA-M sources (vendored directory or initialized submodule).
2. **Build and start** — a single Docker Compose (or Podman Compose) "build and start in background" invocation produces and runs the loaded instance.
3. **Verify** — run the §10 acceptance checks: instance reports *running*; terminal login to the `VISTA` namespace reaches a VistA menu; a FileMan inquiry returns a known sample patient; TaskMan is active; the RPC Broker accepts a connection on 9430.
4. **Inspect (optional)** — open the Management Portal in a browser to view globals and configuration.

---

## 15. References

- InterSystems IRIS Community Edition — [Docker Hub `intersystems/iris-community`](https://hub.docker.com/r/intersystems/iris-community)
- Deploy & Explore IRIS Community Edition — [InterSystems Docs (ACLOUD)](https://docs.intersystems.com/irislatest/csp/docbook/Doc.View.cls?KEY=ACLOUD)
- Running InterSystems Products in Containers — [InterSystems Docs (ADOCK)](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=ADOCK)
- InterSystems Container Registry — [containers.intersystems.com](https://containers.intersystems.com/contents)
- OSEHRA VistA M components — [github.com/WorldVistA/VistA-M](https://github.com/WorldVistA/VistA-M)
- OSEHRA VistA build/install automation — [github.com/WorldVistA/VistA](https://github.com/WorldVistA/VistA) (`Documentation/InstallCache.rst`, `ImportCache.rst`, `ConfigureCache.rst`, `AutomatedVistAConfiguration.rst`, `Testing/Setup/ImportRG.cmake`)
- VistA on Caché/IRIS discussion — [InterSystems Developer Community](https://community.intersystems.com/post/mumps-cache-vista)
- Install VistA on GT.M/YottaDB (manual reference) — [hardhats.org](https://www.hardhats.org/projects/New/InstallVistAOnGTM.html)
