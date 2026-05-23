# VistA on IRIS — Containerized Instance Specification (v2)

**Status:** Draft spec · **Version:** 2 · **Date:** 2026-05-23 · **Supersedes:** `vista-iris-container-spec.md` (v1) · **Scope:** A reproducible, lightweight, cross-platform (Linux + macOS, x86-64 + Apple Silicon) container that stands up a *functioning* VistA EHR instance — reachable by a CPRS client over **RPC** and by external systems over **HL7** — with sample patients, on InterSystems **IRIS for Health Community** (latest release), plus the inner-loop developer tooling a VA VistA developer would actually use.

> **What changed in v2** (driven by review of v1 and a source-level audit of the OSEHRA/WorldVistA build automation):
> 1. **§1 Purpose & Scope** — explicitly requires reachability of VistA's **RPC** (CPRS) **and HL7** interfaces (HL7 needed for test-system integration, e.g. FHIR data import and InterSystems HealthShare/Health Connect interfacing).
> 2. **§2 Goals** — adds a goal to **mock the developer tooling/UX** a VA VistA developer has (VS Code as IDE + VistA-native M tooling), cross-referencing [`vista-dev-iris-tooling.md`](vista-dev-iris-tooling.md).
> 3. **§3 Container Technology** — **Podman is now the primary** runtime (lightweight, daemonless, rootless, simple); Docker remains compatible.
> 4. **§4 Base Image** — base is **`irishealth-community`** (the **FHIR server is retained**) tracking the **latest IRIS Community release** InterSystems publishes; **legacy/ancient versions are prohibited** (explicitly *not* Caché 2011, etc.).
> 5. **§5 VistA Source** — adds a **source-level quality audit** of the OSEHRA scripts, a **catalog of the installer's options**, a **bare-bones streamlining** decision, and a binding mandate (**§5.4**) to ship a **cleaned, IRIS-only fork** of the installer: all non-IRIS code/options removed (GT.M/YottaDB, Caché-2011 installer, EWD.js, dashboards), **no fakes** (no `/etc/redhat-release` spoof, no encryption-disable hacks), **no dead/broken guards**, modernized for 2026.
> 6. **§7 Build Pipeline** — keeps Strategy A; makes the build **ephemeral and fully portable in a `Makefile` + `Dockerfile`**, and adds a **CI/CD chain expressed as a `Makefile`** for reproducibility.
> 7. **§10 Access & Verification** — adds the **HL7 (MLLP) port** and a developer-tooling (VS Code/`isfs`) access path.

---

## 1. Purpose & Scope

Define how to build and run a single-container VistA instance suitable for development, demos, training, and integration testing — **not production, not real PHI**. The deliverable is an OCI image plus a `compose` setup (Podman-first, Docker-compatible) driven by a portable `Makefile`, that:

1. Boots InterSystems IRIS for Health Community Edition (latest release).
2. Loads the OSEHRA/WorldVistA "FOIA" VistA M codebase (routines + globals).
3. Configures the namespace, TaskMan, and the **RPC Broker (XWB) listener** so VistA actually runs and **a CPRS client can connect**.
4. Configures and auto-starts VistA's **HL7 interface (HL package / HL7 Link Manager)** so external/test systems can exchange HL7 v2 messages — the path used for **FHIR data import** and for interfacing with InterSystems tools (HealthShare / Health Connect / a health-information exchange).
5. Loads sample/test patients and supporting reference data (institutions, users, clinics).
6. Exposes documented endpoints for verification (terminal/roll-and-scroll, Management Portal, RPC Broker, HL7 MLLP, FHIR REST).
7. Lets a developer attach the **VA-realistic VistA toolchain** (VS Code + InterSystems ObjectScript extension over server-side `isfs`, plus VistA-native XINDEX / M-Unit / KIDS / FileMan) — see §2 and §10.

**Interface reachability is a first-class requirement, not an afterthought:** the two interfaces that make VistA *useful from outside the container* are the **RPC Broker** (clinical GUI clients such as CPRS) and **HL7** (system-to-system messaging). Both must be reachable from the host, on documented, configurable ports.

### Glossary

| Term | Meaning |
|---|---|
| **VistA** | Veterans Health Information Systems and Technology Architecture — the VA's EHR, written in MUMPS (M). |
| **MUMPS / M** | The language + integrated hierarchical database ("globals") VistA is built on. |
| **IRIS** | InterSystems IRIS data platform — the supported successor to Caché; runs M natively. The VA's production VistA runs on InterSystems' M engine, so IRIS is the most "native" host. |
| **IRIS for Health** | The healthcare edition of IRIS; bundles an **HL7 v2 / FHIR interoperability** engine (productions, MLLP, FHIR server). |
| **Globals** | Persistent sparse arrays = VistA's data store (e.g. `^DPT` = patient file). |
| **Routines** | Compiled M program units (`.m` source). |
| **FileMan** | VistA's database management layer over globals. |
| **KIDS** | Kernel Installation & Distribution System — VistA's package installer. |
| **RPC Broker (XWB)** | TCP listener that GUI clients such as CPRS connect to; configured in RPC BROKER SITE PARAMETERS (file #8994.1). |
| **HL7 / HL package** | VistA's HL7 v2 messaging subsystem; the **HL7 Link Manager** runs logical links (HL LOGICAL LINK, file #870), each an MLLP TCP endpoint. |
| **MLLP** | Minimal Lower Layer Protocol — the framing used to carry HL7 v2 over TCP. |
| **CPRS** | Computerized Patient Record System — the Windows clinical GUI; talks to VistA over the RPC Broker. |
| **FOIA VistA** | The public-domain VistA release; mirrored monthly to GitHub as routines + `.zwr` globals. |

---

## 2. Goals & Non-Goals

### Goals
- **One command up:** a single `make up` (wrapping Podman/Docker Compose) yields a working, pre-populated VistA.
- **Portable:** runs identically on Linux and macOS, on both `amd64` and `arm64` (Apple Silicon); everything needed lives in a `Makefile` + `Dockerfile`.
- **Lightweight:** single base image (IRIS for Health Community), no external services required.
- **Reproducible:** image build is deterministic from pinned source tags and a recorded IRIS release; the build and the CI/CD chain are both expressed as `make` targets.
- **Externally reachable:** the **RPC Broker** (for CPRS) and the **HL7 MLLP** interface (for test-system integration / FHIR import) are published and documented.
- **Developer-tooling parity:** the instance mocks the **toolchain and developer experience a VA VistA developer actually has** — primarily **VS Code + the InterSystems ObjectScript Extension Pack** editing routines server-side via `isfs`, complemented by VistA's own M-native tools (**XINDEX, M-Unit, KIDS, FileMan**, the programmer menu). The container must expose the IRIS superserver/web ports those tools need and ship a documented connection profile. This deliberately mirrors the *real, TRM-approved* VA inner loop documented in [`vista-dev-iris-tooling.md`](vista-dev-iris-tooling.md) — **not** IRIS's class-oriented IDE features (which VistA's flat-M codebase cannot use).
- **Ephemeral by default:** the instance is disposable and rebuilt from scratch reproducibly; durable persistence is an explicit opt-in (see §4, §11).
- **Verifiable:** documented "is it working?" checks, including an RPC and an HL7 connectivity check.

### Non-Goals
- Not production-grade (IRIS Community is dev/eval-licensed and capacity-capped).
- No real patient data — sample/synthetic only.
- No bundled Windows CPRS GUI (Windows-only; addressed as an optional access path).
- No HA/clustering, no VistA Imaging, no multi-site federation.
- **No class-grade IDE features** for VistA's M code (refactoring, SQL projection, `%UnitTest`) — structurally unavailable to flat M; out of scope by design.
- **No EWD.js / web-framework layer, no GT.M/YottaDB, no CDash dashboards, no legacy Caché installer, no fakes** — removed from the forked installer (see §5).

---

## 3. Container Technology Decision

**Recommendation: Podman as the primary runtime; Docker remains drop-in compatible.**

Rationale: Podman is **daemonless and rootless** by default, which makes it lighter, simpler, and a better fit for a single-developer, ephemeral instance — no background daemon, no privileged socket, fewer moving parts. The same `Dockerfile` and the same Compose file work under both engines, so choosing Podman costs nothing in portability.

| Option | Verdict | Rationale |
|---|---|---|
| **Podman + `podman compose`** | ✅ **Primary** | Daemonless, rootless, lightweight, simple; runs the identical `Dockerfile`/Compose file; no daemon or privileged socket to manage. Preferred default. |
| **Docker + Docker Compose** | ✅ Supported | Universally available; identical artifacts. Use where a team already standardizes on Docker. |
| **Vagrant VM** (OSEHRA's existing path) | ❌ | Heavier (full VM), not "lightweight," slower to boot. Kept only as a fallback reference. |
| **Bare metal / GT.M / YottaDB** | ❌ | Out of scope — this spec targets IRIS specifically. |

> Portability notes: (1) The `Dockerfile`, Compose file, and `Makefile` are written once. Apple Silicon users pull the `arm64` image variant; everything else is identical. (2) Rootless Podman maps published ports for an unprivileged user; the documented ports (§10) are all > 1024, so no privileged binding is required.

---

## 4. Base Image Decision

**Decision: `intersystems/irishealth-community`, tracking the latest Community release InterSystems publishes. The FHIR server is retained. Legacy/ancient versions are prohibited.**

The FHIR server is a kept feature (a hard requirement), so the base is the **healthcare edition**, which bundles the HL7 v2 / FHIR interoperability engine (interoperability productions, MLLP business services/operations, and a FHIR server) on top of the same M engine. The plain `intersystems/iris-community` edition is **not used** — it lacks the FHIR server.

**Version policy (latest, not legacy):**
- Build against the **latest IRIS for Health Community release** InterSystems currently provides (a 2025/2026-era continuous-delivery tag) — **never** a legacy/end-of-life version. The audited OSEHRA scripts that hardwired **Caché 2011** are explicitly out of scope (see §5).
- For reproducibility, the build **records the version it resolved** via the `IRIS_TAG` build argument: default to the latest tag, and when you adopt it, note the concrete release so a rebuild is deterministic. Bump it **deliberately and regularly**. The rule is "latest, then recorded" — not "frozen on an old release."

- **Registry:** Docker Hub `intersystems/irishealth-community`, mirrored at `containers.intersystems.com/intersystems/irishealth-community`. Publicly pullable; no login required for Community Edition.
- **Architectures:** `amd64` and `arm64` (append the arm64 variant to the tag) → covers Linux + Apple Silicon Macs. Confirm exact tag names against the registry before building.
- **Default ports:** `1972` (superserver / RPC + xDBC), `52773` (web / Management Portal / **FHIR REST**). VistA's RPC Broker and HL7 MLLP listeners are *additional*, configured inside VistA (§8) and published explicitly (§10).
- **Default credentials:** `_SYSTEM` / `SYS` (forced change on first login).
- **Persistence:** "Durable %SYS" — mount a host volume and set `ISC_DATA_DIRECTORY` so instance data lives outside the container layer. **Off by default** (ephemeral instance); opt-in.
- **Known limits (Community Edition):** development/evaluation license only; capped at ~20 cores (`--cpus`/`--cpuset-cpus` may be required on big hosts); limited concurrent connections. Adequate for a single-developer VistA.

> `IRIS_TAG` is a `Makefile`/build argument so the latest release and the arch-specific variant are selectable without editing the `Dockerfile`.

---

## 5. VistA Source Decision

**Agreed sources:**

| Artifact | Source | Use |
|---|---|---|
| **VistA M code** (routines + globals) | `github.com/WorldVistA/VistA-M` | The FOIA codebase: `Packages/<pkg>/Routines/*.m` and `Packages/<pkg>/Globals/*.zwr`. Actively maintained (e.g. April-2026 patch refresh). |
| **Build/install automation** | `github.com/WorldVistA/VistA` | Cross-platform import + test scripts; **IRIS-aware** (`Python/vista/OSEHRAHelper.py` connects via `irissession`, defaulting `instance='IRIS', namespace='VISTA'`). |

**We reuse the OSEHRA *CMake + Python* import/configuration path** — `Testing/Setup/ImportRG.cmake` driving `Initialize.py` / `RoutineImport.py` / `GlobalImport.py` / `PostImportSetupScript.py` / `ClinicSetup.py` through `OSEHRASetup.py` — **as a cleaned, IRIS-only fork** (§5.4). This is the part that is current, idempotent-friendly, and IRIS-capable. We **do not** reuse the legacy provisioning shell scripts (see §5.2).

> Compatibility caveat to validate during implementation: OSEHRA's documented path historically targets **Caché**. IRIS is highly compatible but differs in a few `$ZU`/legacy APIs, locale/character-set defaults (IRIS is Unicode; FOIA VistA traditionally an 8-bit `enu8` locale), and the invocation (`iris session IRIS` vs the legacy `irissession`). Expect minor adjustments to the OS-interface layer (`%Z*` / `^%ZOSF`) and namespace locale.

### 5.1 Installer option catalog (audit result)

The OSEHRA "installation script" with command-line options is `Scripts/Install/<Ubuntu|RHEL>/autoInstaller.sh` (the Ubuntu and RHEL variants share an identical option set). It is **GT.M/YottaDB-centric**; its Caché branch is a stub. Full option list, with the keep/remove decision for a bare-bones VA-developer IRIS instance. **In the forked installer (§5.4), every ❌ row is removed outright — the fork carries no GT.M/YottaDB/Caché-2011/EWD code at all:**

| Option | Meaning | Keep for VA bare-bones IRIS? | Why |
|---|---|---|---|
| `-h` | Show usage | ✅ keep (in our wrapper) | Trivial. |
| `-a <repo>` | Alternate VistA-M repo (zip or git) | ✅ keep → as a **pinned** build arg | We pin the FOIA tag for reproducibility (§4). |
| `-r <branch>` | Alternate VistA-M branch (git) | ✅ keep → pinned tag/branch | Same. |
| `-b` | Skip OS bootstrapping ("used for docker") | ✅ effectively always-on | In a container we never bootstrap/`apt-get` the OS; the base image *is* IRIS. |
| `-c <path>` | Path to **Caché** installer | ❌ remove | We use the official **IRIS** community **image**, not a Caché installer. (And this branch is a stub anyway — §5.2.) |
| `-d` | Create GT.M/YottaDB **development directories** (`s` & `p`) | ❌ remove | GT.M/YottaDB-only concept (filesystem routine/object dirs). On IRIS, routines live in the namespace. |
| `-e` | Install **EWD.js** (Node.js web framework) | ❌ **remove** | Not part of core VistA; not a VA-used tool. See §5.2/§5.3. |
| `-g` | Use **GT.M** | ❌ remove | We target IRIS. |
| `-y` | Use **YottaDB** | ❌ remove | We target IRIS. |
| `-i <name>` | Instance name | ◑ simplify | Fixed to IRIS instance `IRIS`, namespace `VISTA`. |
| `-p <script>` | Post-install hook | ✅ keep (optional) | Useful seam for loading extra site config. |
| `-s` | Skip testing (the CDash **dashboard** build) | ✅ keep as default → drop dashboard | We replace the heavy CDash/CTest dashboard submit with a lightweight smoke check (§10). |

Two additional installers were audited for completeness:
- `Scripts/Install/GTM/install.sh` — options `-h`, `-s` (skip), `-v <ver>`, `-y` (YottaDB). **Removed** (GT.M/YottaDB only).
- `Scripts/Install/GTM/createVistaInstance.sh` — options `-h`, `-f` (skip firewall), `-i <name>`, `-y`. **Removed** (GT.M/YottaDB only).
- `Scripts/Install/EWD/ewdjs.sh` — options `-h`, `-v <node-ver>`. **Removed** (see below).

### 5.2 Source-level quality findings

Comprehensive review of the candidate scripts surfaced the following. These justify *forking the Python/CMake import path and not the legacy shell provisioners*:

**Reuse (good quality, IRIS-capable):**
- `Python/vista/OSEHRASetup.py` + `OSEHRAHelper.py` + the `Testing/Setup/*.py.in` step scripts driven by `ImportRG.cmake.in`. IRIS-aware (`irissession`, defaults to instance `IRIS`/namespace `VISTA`), well-factored into discrete steps (FileMan init, devices, domain, box:volume pair, RPC Broker listener, TaskMan, institution/users/clinic), fails loudly via CMake `CheckResult`, and is actively maintained.
- The import M-commands themselves are stable across Caché→IRIS: `D ^%CD` (namespace), `D ^%RI` / `$SYSTEM.OBJ.ImportDir` (routines), `$$LIST^ZGI(...)` / `$SYSTEM.OBJ.Load` (globals), `D ^ZTMGRSET` choosing system type **"3 = Cache (VMS, NT, Linux), OpenM-NT"** (the correct answer for IRIS too — it presents the Caché-compatible OS interface).

**Do not reuse (obsolete / out-of-scope / risky) — removed in the fork (§5.4):**
1. **`Scripts/Install/Cache/install.sh` is obsolete.** It is hardcoded to **Caché 2011.1.2** from a fixed tarball path, *fakes* `/etc/redhat-release` to "release 6", and drives the long-removed `ccontrol`/`chkconfig` init model. Unusable for IRIS; the official IRIS container image replaces it entirely.
2. **`autoInstaller.sh` has a dead/broken guard ("the GT.M dead safety guard").** The "no M environment viable" check (`if [[ ! $installgtm || ! $cacheinstallerpath || ! $installYottaDB ]]`) negates non-empty strings (`"false"`), so it never triggers — and the logic should be conjunctive, not disjunctive. The intended safety check does nothing.
3. **Non-reproducible install-time downloads.** `autoInstaller.sh` curls a GT.M-optimized Kernel zip from a personal GitHub release and `KBANTCLN.m` from a personal `random-vista-utilities` repo at run time; `ewdjs.sh` curls the NVM installer from `creationix/nvm` (a since-moved org → dead URL). Run-time fetches from unpinned, personal sources are a supply-chain and reproducibility risk; everything we need must be vendored/pinned into the image.
4. **`ewdjs.sh` is unsuitable on multiple axes.** It pins **Node 0.12** (EOL since 2016), wires GT.M-specific C call-in (`GTMCI`/`gtmroutines`), **disables Access/Verify code encryption** ("Development use only!"), and opens ports 8080/8000/8081 — all for a web framework VistA does not require.
5. **OS-mutating, root-required, init.d/firewall logic** (`apt-get`, `usermod`, `chkconfig`/`update-rc.d`, `firewall-cmd`, `service ... start`) is correct for a VM/bare-metal provision but is the **wrong model for an immutable container**, where the base image owns the OS and the IRIS entrypoint owns the service lifecycle.
6. **A minor quoting bug** in `autoInstaller.sh` (`find /vagrant -name \"*.sh\"` — the escaped quotes are literal) would prevent that `find` from matching as intended.
7. **Documentation drift:** `Documentation/InstallCache.rst` walks a Caché 2011/2013 *GUI* install with screenshots. The **M-side import commands remain valid**, but the GUI/OS install steps do not apply to the IRIS container image and must not be transcribed literally.

### 5.3 Bare-bones streamlining decision

The installed instance is reduced to **exactly what a VA VistA developer would have**, and nothing more:

**Include (bare bones):**
- IRIS for Health Community (latest) + the **FOIA VistA routines & globals** (pinned).
- Core runtime: **FileMan, Kernel, TaskMan**, the **RPC Broker (XWB) listener** (CPRS), and the **HL7 package / HL7 Link Manager** (MLLP) — all configured and auto-started (§8).
- **Tier-1 sample data** (institution, users, clinic, patients — §9).
- The **VA inner-loop tooling surface**: VS Code + InterSystems ObjectScript extension over `isfs`, and the VistA-native **XINDEX, M-Unit, KIDS, FileMan**, programmer menu (these are part of VistA itself; see [`vista-dev-iris-tooling.md`](vista-dev-iris-tooling.md)).

**Exclude (removed from the fork — see §5.4):**
- **EWD.js** and any Node.js/web-framework layer (`-e` / `ewdjs.sh`).
- **GT.M / YottaDB** paths (`-g` / `-y` / `install.sh` / `createVistaInstance.sh`) and GT.M "development directories" (`-d`).
- The **legacy Caché shell installer** (`Cache/install.sh`) and any Caché-installer flag (`-c`).
- The **CDash/CTest dashboard** build & upload (`-s` default) — replaced by the lightweight §10 smoke check.
- Run-time fetches of optimized routines / auto-configurers from personal repos (vendor/pin instead).

### 5.4 Forked & cleaned installer (binding requirement)

The install orchestration shipped in this repo (`scripts/`, §12) is a **fork of the OSEHRA import/configuration code, cleaned and streamlined to IRIS-only and to what a 2026 developer actually needs.** This is a requirement, not a suggestion.

**Removed entirely (not merely defaulted off):**
- All **GT.M / YottaDB** code paths, options, and scripts (`autoInstaller.sh` GT.M/YottaDB branches, `GTM/install.sh`, `GTM/createVistaInstance.sh`, the `-g`/`-y`/`-d` options, `gtmroutines`/`mupip`/`dse` logic).
- The **legacy Caché shell installer** (`Scripts/Install/Cache/install.sh`) and the `-c` "Caché installer path" option — superseded by the official IRIS container image.
- **EWD.js** and the entire Node.js/web-framework layer (`Scripts/Install/EWD/ewdjs.sh`, the `-e` option).
- The **CDash/CTest dashboard** build & upload.
- All **run-time fetches from personal/unpinned sources** (e.g. Kernel-GTM release zips, `KBANTCLN.m` from a personal repo, NVM from a moved org). Sources are vendored/pinned into the image.

**No fakes (hard rule):**
- No spoofing the OS — the `Cache/install.sh` trick of overwriting `/etc/redhat-release` to "release 6" is removed; the container runs on the IRIS base image's real OS.
- No security-disabling hacks — the EWD step that **disabled Access/Verify code encryption** is gone.
- No faked/dummy success — every step reports real status (see "fails loudly" below).

**No dead/broken guards:**
- The broken "no M environment viable" check in `autoInstaller.sh` (the "GT.M dead safety guard": it negates non-empty strings, and uses OR where it meant AND, so it never fires) is removed, not carried forward. Guards in the fork must actually guard.

**Modernized for 2026:**
- Targets the **latest IRIS for Health Community** (§4); uses `iris session IRIS` (not the legacy `irissession`) and current `$SYSTEM.OBJ.*` import APIs.
- **Container-native:** no `apt-get`/`usermod`/`chkconfig`/`update-rc.d`/`firewall-cmd`/`service` OS mutation; the base image owns the OS and the IRIS entrypoint owns the service lifecycle.
- **Fails loudly:** non-zero exit on any import/compile/post-install error (mirrors the OSEHRA CMake `CheckResult`), so a broken build never yields a runnable image.

**Kept (the parts worth forking):** the IRIS-aware, currently-maintained import/config logic — FileMan init, device config, domain/institution, box:volume pair, **RPC Broker (XWB) listener**, **HL7 Link Manager**, TaskMan, and Tier-1 sample data — rewritten IRIS-only and parameterized (instance `IRIS`, namespace `VISTA`, RPC port `9430`, HL7 MLLP port `5026`).

**Provenance & maintenance:** the fork records its upstream source and the commit it was taken from; because the FOIA codebase is refreshed monthly, the fork is re-synced with upstream `WorldVistA/VistA` **deliberately** (see §13).

---

## 6. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│  Container:  vista-iris   (Podman primary · Docker compatible)         │
│  FROM intersystems/irishealth-community:<latest>                       │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐ │
│   │ IRIS for Health instance — M engine + HL7/FHIR interop           │ │
│   │                                                                  │ │
│   │  Namespace: VISTA  ──► Database: VISTA (iris.dat)                │ │
│   │   • Routine maps: %DT* %RCR %XU* %ZIS* %ZO* %ZT* %ZV*            │ │
│   │   • Global  maps: %Z*                                            │ │
│   │                                                                  │ │
│   │  VistA codebase (KIDS/FileMan/Kernel/CPRS RPCs/HL package/…)     │ │
│   │  TaskMan (background job scheduler)                              │ │
│   │  RPC Broker listener (XWB)        ── TCP 9430                    │ │
│   │  HL7 Link Manager (HL, MLLP)      ── TCP 5026 (configurable)     │ │
│   │  IRIS FHIR server (irishealth)    ── via 52773                   │ │
│   └────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Durable %SYS (opt-in) ──► volume: /durable  (ISC_DATA_DIRECTORY)      │
└────────────────────────────────────────────────────────────────────────┘
   │ 1972            │ 52773              │ 9430            │ 5026
   ▼                 ▼                    ▼                 ▼
 IRIS terminal /   Mgmt Portal +       CPRS / RPC        HL7 v2 (MLLP):
 roll-and-scroll;  FHIR REST;          clients           lab/ADT feeds,
 VS Code via       global/SQL viewer   (CPRS, test       FHIR-import path,
 isfs (dev IDE)    (browser)           harnesses)        HealthShare/HIE
```

---

## 7. Build Pipeline

**Strategy A is recommended** and is made **ephemeral and fully portable**: everything required to build, run, verify, and tear down the instance lives in a **`Dockerfile` + `Makefile`** committed to the repo — no host-specific setup, no manual steps.

### Strategy A — Bake at build time (recommended)
Import all code/data during the image build, so a `run` starts an already-loaded instance.

1. `FROM intersystems/irishealth-community:<latest>` (recorded via `IRIS_TAG`, §4).
2. `COPY` the pinned VistA-M sources + the **cleaned IRIS-only fork** (§5.4) of the install orchestration into the image.
3. Start IRIS quietly → run the install orchestration as an IRIS session (`iris session IRIS`) to: create DB/namespace, set mappings, import routines, load globals, initialize the OS interface, configure TaskMan, the **RPC Broker listener**, and the **HL7 Link Manager**, then load Tier-1 sample data.
4. `iris stop`, then the stock IRIS entrypoint serves the prepared instance.

**Pros:** boots in seconds, fully reproducible, no first-run wait. **Cons:** larger image, longer build. **Ephemeral:** the running container holds no irreplaceable state; `make down && make up` rebuilds an identical instance. Durable `%SYS` is opt-in only.

### Strategy B — Initialize on first boot (alternative)
Ship code/data into the image (or a mounted volume) and run the install via the IRIS container init hook on first start, persisting to durable `%SYS`. **Pros:** smaller image. **Cons:** slow first boot; init must be idempotent. Use only if image size dominates.

### 7.1 Makefile-driven build and CI/CD chain

A top-level **`Makefile`** is the single, portable entry point — it makes the build self-contained and engine-agnostic, and doubles as the **CI/CD chain** so the same targets run locally and in CI (more reproducible and higher-quality than a bespoke YAML pipeline that drifts from local behavior). Required targets (illustrative names):

| Target | Does |
|---|---|
| `make sources` | Fetch/verify the **pinned** VistA-M sources (vendored dir or submodule at the pinned tag). |
| `make build` | Build the OCI image (Strategy A) via `$(ENGINE)` (defaults to `podman`, override `ENGINE=docker`), passing `IRIS_TAG` (latest Community release, §4) + the arch variant as build args. |
| `make up` / `make down` | Start / stop the instance via `$(ENGINE) compose`. |
| `make verify` | Run the §10 acceptance checks (instance running; RPC connect on 9430; HL7 MLLP connect on 5026; FileMan inquiry returns a sample patient; TaskMan active). Non-zero exit on any failure. |
| `make lint` | Static checks: shell (`shellcheck`) on any wrapper scripts; **XINDEX** over the changed VistA routines (SAC/ANSI-M). |
| `make test` | Run **M-Unit** (`%ut`) suites against the loaded instance. |
| `make ci` | Ordered chain: `lint → build → up → verify → test → down`. Fails loudly on any step. This *is* the CI/CD pipeline; a CI runner simply calls `make ci`. |
| `make clean` | Remove image/containers/volumes for a clean ephemeral rebuild. |

`ENGINE ?= podman` keeps Podman primary while letting Docker users override with one variable.

---

## 8. Detailed Install Sequence (what the orchestration must do)

Executed as ObjectScript/M (and the forked Python step scripts), in the order the audited `ImportRG.cmake` + `PostImportSetupScript` enforce, adapted to IRIS:

1. **Database + namespace**
   - Create database `VISTA` backed by `/durable/VISTA/` (opt-in) or an in-image dir (Strategy A default).
   - Create namespace `VISTA` mapped to that database; set **locale/collation** (validate Unicode vs 8-bit `enu8` for FOIA data).

2. **Mappings** (so VistA's OS-interface code resolves)
   - Global mapping: `^%Z*` → VISTA database.
   - Routine mappings: `%DT*`, `%RCR`, `%XU*`, `%ZIS*`, `%ZO*`, `%ZT*`, `%ZV*` → VISTA database.

3. **Import routines** — load `Packages/**/Routines/*.m` (via `$SYSTEM.OBJ.ImportDir(...,"ck")` or `^%RI`, choosing the **Caché** routine write type — valid for IRIS), then compile. Apply the small set of FOIA fixes the OSEHRA setup carries.

4. **Load globals** — import `Packages/**/Globals/*.zwr` via `$$LIST^ZGI(...)` / `$SYSTEM.OBJ.Load`. Includes FileMan dictionaries, Kernel files, and the seed data VistA needs to run.

5. **OS-interface initialization** — run `D ^ZTMGRSET` choosing system type **"3 = Cache (VMS, NT, Linux), OpenM-NT"**, renaming the FileMan/`%Z*` routines and setting `^%ZOSF`, `^%ZIS('C')`, and the `%Z` editor — i.e. wire VistA's OS layer to the IRIS host. (In the automated path, the equivalent device/`Initialize` configuration runs here: NULL/console/HFS devices, MPI local number, etc.)

6. **Post-install configuration** (forked OSEHRA `PostImportSetupScript`)
   - Initialize **FileMan**; set the primary **HFS** dir, intro text, time zone; christen the **Institution / domain**.
   - Set the **Box:Volume pair**, then write the **RPC Broker (XWB) listener** TCP port into RPC BROKER SITE PARAMETERS (#8994.1) — see step 7.
   - Create the **System Manager** account and the clinical test users (step in §9).

7. **RPC Broker (XWB)** — configure the listener on TCP **9430** and schedule **`XWB LISTENER STARTER`** to run at TaskMan startup, so CPRS / RPC clients / test harnesses can connect on every boot.

8. **HL7 interface (HL package)** — schedule the HL7 services at TaskMan startup, exactly as the OSEHRA setup already does:
   - `HL AUTOSTART LINK MANAGER` (STARTUP) — brings up the **HL7 Link Manager**.
   - `HL TASK RESTART` (STARTUP) and `HL PURGE TRANSMISSIONS` (daily).
   - Define/enable an **HL LOGICAL LINK (#870)** as a TCP **MLLP listener** on the published HL7 port (default **5026**, configurable) so external/test systems can send HL7 v2 (and a FHIR-import path can land mapped HL7 v2 messages). On `irishealth-community`, the IRIS FHIR server (web port) provides the FHIR front door that an interop production translates to HL7 v2 for VistA.

9. **TaskMan** — start the background job scheduler (`^ZTMB`) via the programmer (`^XUP`) menu, which in turn launches the scheduled XWB and HL7 startup options.

10. **Verification hook** — smoke check (e.g. `D ^XUP` login, FileMan inquiry on `^DPT`, RPC connect on 9430, MLLP connect on 5026). The orchestration **fails loudly** (non-zero exit) on any import/compile/post-install error so a broken build never yields a "green" image.

---

## 9. Sample Patient Data Strategy

**v2 ships Tier 1 only; Tier 2/3 are deferred (optional, later).**

| Tier | Source | Content | Status in v2 |
|---|---|---|---|
| **0 — Built-in** | Globals shipped in VistA-M | A handful of FOIA test patients + base reference files. | Included (loaded in §8). |
| **1 — OSEHRA test setup (default)** | `PostImportSetupScript.py` + `ClinicSetup.py` (the `TEST_VISTA_SETUP` path) | Institution **VISTA HEALTH CARE** (station 6100) + division **VISTA MEDICAL CENTER**; a System Manager; clinical users (e.g. Dr. *Robert Alexander*, Nurse *Mary Smith*, Clerk *Joe Clerk*) with Access/Verify codes & e-signatures; a ward with beds; a clinic wired for scheduling; an orderable test — enough to register, schedule, and order. | **Default in v2.** Deterministic, lightweight, scriptable. |
| **2 — Rich demo database** | VEHU-/Astronaut-style demo dataset | Many longitudinal patients (meds, labs, notes, appointments). | **Deferred** (license/availability-dependent). |
| **3 — Synthetic generation** | Synthea → HL7/FHIR → ingest | Arbitrarily large synthetic cohorts. | **Deferred** (uses the §8 HL7/FHIR-import path; advanced). |

All sample identities are **clearly fictitious**; the instance is bannered test-only; no real PHI. (Tier 3 is a natural future use of the now-in-scope HL7/FHIR import path — §8 step 8.)

---

## 10. Access & Verification

| Endpoint | Port | How | Portability |
|---|---|---|---|
| **IRIS terminal / VistA roll-and-scroll** | 1972 / `exec` | `podman exec -it vista-iris iris session IRIS -U VISTA` then `D ^XUP` / FileMan menus. | ✅ Linux + macOS. Primary functional check. |
| **VS Code dev IDE (server-side `isfs`)** | 1972 / 52773 | VS Code + InterSystems ObjectScript Extension Pack; connect a server profile to the instance and edit routines in the `VISTA` namespace via `isfs` (server-side source). Mocks the VA inner loop. | ✅ |
| **Management Portal + FHIR REST** | 52773 | Browser → `http://localhost:52773/csp/sys/UtilHome.csp` (globals/SQL viewer); on `irishealth-community`, FHIR REST is served here for the FHIR-import path. | ✅ |
| **RPC Broker (XWB)** | 9430 | CPRS / RPC clients / test harnesses connect to the XWB listener. | ✅ for the listener; clients vary. |
| **HL7 (MLLP)** | 5026 (configurable) | External/test systems exchange **HL7 v2 over MLLP** with VistA's HL7 Link Manager (HL LOGICAL LINK #870). The path for **FHIR data import** and for interfacing with InterSystems HealthShare / Health Connect / a health-information exchange. | ✅ for the listener; partner systems vary. |
| **CPRS GUI** | via 9430 | Windows-only Delphi app. On Linux/macOS run under Wine or a Windows VM. | ⚠️ Not portable — documented as optional. |

**"It works" acceptance checks (run by `make verify`):**
1. `iris list` shows the instance `running`.
2. Terminal login to `VISTA` namespace succeeds; `D ^XUP` reaches a VistA menu.
3. FileMan inquiry returns a known sample patient from `^DPT`.
4. TaskMan reports active.
5. **RPC Broker** accepts a TCP connection on **9430** (CPRS reachability).
6. **HL7 MLLP** listener accepts a TCP connection on **5026** (and, optionally, a test HL7 v2 message round-trips into the HL7 message log) — i.e. the HL7/FHIR-import interface is reachable.

---

## 11. Required Artifacts (specification)

This section specifies *what* each build and runtime artifact must contain and do. It is intentionally code-free — implementation is produced separately during the build phase and documented in the repository README.

### 11.1 Container image definition (`Dockerfile`)
Must:
- Base on the **latest** `intersystems/irishealth-community` release (§4), recorded via an `IRIS_TAG` build argument so the architecture-specific variant (the arm64 tag on Apple Silicon) is selectable without editing the file.
- Copy the pinned VistA-M sources and the **cleaned IRIS-only fork** (§5.4) of the install orchestration into a working directory owned by the `irisowner` account — **no EWD.js, no GT.M/YottaDB, no legacy Caché installer, no dashboard tooling, no fakes, no run-time fetches from personal repos**.
- Under **Strategy A** (§7): during the build, start IRIS quietly, run the install orchestration (import → globals → OS-interface init → TaskMan → RPC Broker listener → HL7 Link Manager → Tier-1 data), then stop the instance cleanly — so the committed image already contains a fully loaded, RPC- and HL7-reachable VistA.
- Leave the stock IRIS container entrypoint in place to serve the prepared instance.

### 11.2 Orchestration definition (`compose` file)
Must define a single service that:
- Builds from the image definition above and assigns a stable container name.
- Publishes the documented ports, each labeled by purpose: **1972** (superserver / RPC + xDBC), **52773** (Management Portal / FHIR REST), **9430** (VistA RPC Broker / XWB), **5026** (VistA HL7 MLLP, configurable).
- Mounts a named volume for durable storage and sets `ISC_DATA_DIRECTORY` **only when persistence is opted in** (ephemeral by default).
- Optionally caps CPU to remain within the Community Edition core limit on large hosts.
- Is valid under **`podman compose`** (primary) and **`docker compose`** without modification.

### 11.3 Build & CI/CD definition (`Makefile`)
A top-level `Makefile` (§7.1) that is the portable single entry point for `sources`, `build`, `up`, `down`, `verify`, `lint`, `test`, `ci`, `clean`; defaults `ENGINE=podman` with a one-variable Docker override; and whose `ci` target *is* the CI/CD chain (so local and CI behavior are identical and reproducible).

### 11.4 Install orchestration (`scripts/`) — the cleaned fork
The cleaned IRIS-only fork (§5.4) splits the install into an IRIS-native bootstrap and an interactive site build, because the proven VistA site build is a branching, expect-driven dialog that a flat input stream cannot drive reliably:
- **`scripts/bootstrap.script`** (fed to `iris session IRIS`): establish the VISTA database, namespace, and routine/global mappings (via the configuration utilities or a CPF merge), then import & compile the routines and load the globals (§8 steps 1–4). Fail-loud.
- **`scripts/osehra/`** — a cleaned, IRIS-only **Python 3 fork** of the OSEHRA expect driver (`OSEHRAHelper`/`OSEHRASetup`, run over `iris session` via pexpect). It performs OS-interface init (`^DINIT` → MUMPS OPERATING SYSTEM = CACHE, + `^ZUSET` — the proven path, which supersedes the manual `^ZTMGRSET`), then post-install (institution, users, TaskMan, **RPC Broker on 9430**, **HL7 Link Manager on 5026**), then Tier-1 sample data (§8 steps 5–9, §9).
- **No fakes, no dead guards, no non-IRIS code** (§5.4): the GT.M / Windows-telnet / SSH connection classes, the Caché-2011 installer, EWD.js, and the dashboard/coverage machinery are removed; modernized to Python 3 + `iris session` (not the legacy `irissession`).
- Each step **fails loudly** (non-zero exit). The build runs **once** against a clean image (Strategy A); re-running the site build against an already-built instance is **not** idempotent (it would hit "already exists" prompts) — rebuild from clean instead.

---

## 12. Repository Layout (deliverables)

```
vista-iris/
├── docs/
│   ├── vista-iris-container-spec.md       ← v1 (retained)
│   └── vista-iris-container-spec-v2.md    ← this document
├── Makefile                               ← portable build + CI/CD chain (§7.1)
├── Dockerfile
├── docker-compose.yml                     ← podman compose / docker compose
├── .dockerignore                          ← trims build context (esp. the .git store)
├── scripts/                               ← cleaned, IRIS-only fork of the OSEHRA
│   │                                        import/config code (§5.4)
│   ├── bootstrap.script                   ← IRIS-native: namespace + mappings,
│   │                                        import routines, load globals (§8 1–4)
│   └── osehra/                            ← cleaned Python 3 expect-fork (§5)
│       ├── helper.py                      ← `iris session` expect driver
│       ├── setup.py                       ← VistA site-build steps
│       ├── config.py                      ← env-overridable settings + connect()
│       ├── 01_osinit.py                   ← DINIT/ZUSET + devices + MPI (§8 5)
│       ├── 02_postinstall.py              ← institution/users/TaskMan/RPC 9430/HL7 5026 (§8 6–9)
│       └── 03_sampledata.py               ← Tier-1 users/clinics/ward/patients (§9)
├── vista-m/                               ← submodule: WorldVistA/VistA-M (pinned, shallow)
└── README.md                              ← quickstart (make up / make verify)
```

---

## 13. Constraints, Risks & Open Questions

| Item | Notes / Mitigation |
|---|---|
| **IRIS Community license** | Dev/eval only, capacity-capped (~20 cores, limited connections). Fine for this use; document the non-production limit. |
| **Latest vs reproducibility (version policy)** | Track the **latest** IRIS for Health Community release (§4); **record the resolved `IRIS_TAG`** so a rebuild is deterministic; bump deliberately and regularly. **Legacy/ancient versions (e.g. Caché 2011) are prohibited.** |
| **IRIS vs Caché compatibility** | OSEHRA path targets Caché; expect tweaks to `%Z*`/`^%ZOSF` OS layer, locale/charset, a few `$ZU` calls, and `irissession` → `iris session`. **Highest-risk item — validate early with a minimal import.** |
| **Character set / locale** | IRIS is Unicode; FOIA VistA traditionally `enu8` (8-bit). Decide and lock namespace locale; mismatches corrupt extended characters. |
| **HL7 / FHIR engine** | `irishealth-community` carries the interop/FHIR engine (chosen in §4); the **FHIR server is retained**. VistA's *own* HL7 (HL package over MLLP) works regardless. Confirm Community-edition interop limits are adequate for dev. |
| **HL7 logical-link ports** | There is no single fixed HL7 port; each HL LOGICAL LINK (#870) carries its own TCP port. The published **5026** is a chosen default for one MLLP listener — adjust per the links you configure. |
| **Forked installer maintenance** | `scripts/` is a cleaned fork (§5.4). Risks: (a) drift from upstream `WorldVistA/VistA` — **re-sync deliberately**, recording the upstream commit; (b) someone reaching for the removed legacy shell scripts — mitigated by removing them outright, not just disabling. |
| **No fakes** | The fork forbids OS spoofing (`/etc/redhat-release`), encryption-disable hacks, and faked success (§5.4). Real status only. |
| **Image size vs boot time** | Strategy A (baked) trades a bigger image for instant boot — preferred for demos/ephemeral use. |
| **No real PHI** | All patients fictitious; banner the instance as test-only. |
| **CPRS access on Linux/macOS** | Not native; document Wine/VM, or rely on roll-and-scroll + RPC + HL7 for verification. |
| **Apple Silicon** | Use the arm64 IRIS tag; confirm the VistA import runs identically on arm64 (it should — M code is arch-independent). |
| **Developer-tooling fidelity** | VS Code + ObjectScript extension over `isfs` mirrors the *approved* VA inner loop, but flat-M means no class-grade IDE features (by design — §2 non-goals; see [`vista-dev-iris-tooling.md`](vista-dev-iris-tooling.md)). |
| **Legal/licensing** | FOIA VistA is public domain; the IRIS image is InterSystems Community-licensed. Keep them as separate, attributable layers. |

---

## 14. Operational Flow (target end-state)

Once implemented, standing up the instance is `make`-driven and ephemeral (exact commands in the repository README):

1. **Obtain sources** — `make sources` brings in the pinned VistA-M sources (vendored dir or submodule at the pinned tag).
2. **Build and start** — `make build && make up` (Podman by default; `ENGINE=docker make ...` to use Docker) produces and runs the loaded instance on the latest IRIS for Health Community release.
3. **Verify** — `make verify` runs the §10 checks: instance *running*; terminal login to `VISTA` reaches a VistA menu; FileMan inquiry returns a known sample patient; TaskMan active; **RPC Broker** accepts a connection on **9430**; **HL7 MLLP** accepts a connection on **5026**.
4. **Develop** — attach VS Code (ObjectScript extension, `isfs`) to edit routines server-side; use XINDEX / M-Unit / KIDS / FileMan as in the VA inner loop.
5. **Inspect (optional)** — open the Management Portal (and, on `irishealth-community`, the FHIR REST endpoint) in a browser.
6. **Dispose / rebuild** — `make down && make up` (or `make clean` first) reproduces an identical instance; durable storage only if opted in.

---

## 15. References

- InterSystems IRIS for Health Community Edition — [Docker Hub `intersystems/irishealth-community`](https://hub.docker.com/r/intersystems/irishealth-community) (track the latest `-cd` tag) · IRIS Community (non-health, no FHIR) — [`intersystems/iris-community`](https://hub.docker.com/r/intersystems/iris-community)
- Deploy & Explore IRIS Community Edition — [InterSystems Docs (ACLOUD)](https://docs.intersystems.com/irislatest/csp/docbook/Doc.View.cls?KEY=ACLOUD)
- Running InterSystems Products in Containers — [InterSystems Docs (ADOCK)](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=ADOCK)
- IRIS for Health HL7 v2 / FHIR interoperability — [InterSystems Docs (HL7/Interoperability)](https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=PAGE_interoperability)
- InterSystems Container Registry — [containers.intersystems.com](https://containers.intersystems.com/contents)
- OSEHRA VistA M components — [github.com/WorldVistA/VistA-M](https://github.com/WorldVistA/VistA-M)
- OSEHRA VistA build/install automation (forked & cleaned per §5.4) — [github.com/WorldVistA/VistA](https://github.com/WorldVistA/VistA): IRIS-aware import/config path (`Testing/Setup/ImportRG.cmake`, `Testing/Setup/{Initialize,RoutineImport,GlobalImport,PostImportSetupScript,ClinicSetup}.py.in`, `Python/vista/{OSEHRAHelper,OSEHRASetup}.py`); option-bearing installers audited & removed (`Scripts/Install/{Ubuntu,RHEL}/autoInstaller.sh`, `Scripts/Install/Cache/install.sh`, `Scripts/Install/EWD/ewdjs.sh`); import docs (`Documentation/{InstallCache,ImportCache,ConfigureCache,AutomatedVistAConfiguration}.rst`).
- VistA M development toolchain & VA TRM status (VS Code, XINDEX, M-Unit, KIDS) — [`vista-dev-iris-tooling.md`](vista-dev-iris-tooling.md)
- VA TRM MUMPS/M tools survey — [`va-trm-m-tools.md`](va-trm-m-tools.md)
- How the VA hosts/manages VistA in AWS GovCloud — [`vaec-vista-hosting-general.md`](vaec-vista-hosting-general.md)
- VistA on Caché/IRIS discussion — [InterSystems Developer Community](https://community.intersystems.com/post/mumps-cache-vista)
- Install VistA on GT.M/YottaDB (manual reference) — [hardhats.org](https://www.hardhats.org/projects/New/InstallVistAOnGTM.html)
- Podman — [podman.io](https://podman.io/) · `podman compose`
```
