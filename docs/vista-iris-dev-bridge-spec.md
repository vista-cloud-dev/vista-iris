# VistA-on-IRIS Dev Bridge — Core Specification (instance-seeded, environment-neutral)

**Status:** Proposed (design) · **Version:** 1 · **Date:** 2026-05-25
**Generalizes / supersedes:** `historical/iris-dev-bridge-spec.md` (the FOIA-instance-specific draft — its
round-trip *mechanics* fold into this core; its live-instance *facts* become evidence for the public profile)
**Defines (forthcoming siblings):** `vista-iris-dev-bridge-spec-public.md` · `vista-iris-dev-bridge-spec-va.md`
**Companions:** `vista-iris-container-spec-v3.md` (one *example* target instance) · `vista-dev-iris-tooling.md`

---

## How to read this document

This is the **environment-neutral core contract** for a **git-first, instance-seeded, test-driven**
development bridge for VistA M code running on InterSystems IRIS. It is written **once** and bound by **two
parallel environment profiles** — **public** (open development on public github.com with public tooling) and
**VA** (locked-down endpoints behind in-boundary GitHub — primarily **GHEC-US** at `va.ghe.com`, with a
self-hosted **GHES** alongside). The core **guarantees that a
developer's VS Code and tooling experience is identical** in both environments; the profiles differ only in
*where the services live*.

Per the governing directive, **the two environments are never mixed in one document**: this core plus each
profile are **separate specs**. The core holds everything developer-facing; each profile fills only a
binding-point table ([§9](#9-environment-profiles--the-binding-points)).

Conventions (aligned with the house specs; see `vista-iris-container-spec-v3.md`):

- **Normative** requirements use *must / must not / should*. **No source listings**; mechanisms are named
  and live in the tooling repo ([§12](#12-repository--artifact-layout)).
- Three inline tags express the layering:
  - **[Parity]** — must be **identical** across the public and VA environments (lives in this core).
  - **[Profile]** — a value **supplied by an environment profile** (public or VA).
  - **[Instance]** — a value **discovered from the specific target VistA** the developer points at.
- "the bridge" = the tooling specified here. "target instance" = the running VistA-on-IRIS being developed
  against. "the profiles" = the two sibling specs.

---

## 1. Purpose & Scope

Define a **collaborative, team-based, test-driven, version-controlled, git-first** workflow for VistA M
routines on IRIS that:

1. **Works against any VistA-on-IRIS instance** — the FOIA/fake-data demo, an official VA developer VistA,
   and any of the VA's ~130 production systems across their dev / test / pre-prod / prod tiers.
2. **Is seeded by the specific target instance** — the dev environment (code tree *and* runtime) is a
   **function of the instance** it targets; nothing is hardcoded to FOIA or to any one site, namespace, data
   set, or FileMan data dictionary.
3. **Presents an identical developer experience** whether run in the open public environment or inside the
   VA's locked-down / GHES boundary, with a **smooth transition** from one to the other.

### In scope

- The **core contract**: the instance contract ([§5](#5-the-instance-contract-works-against-any-vista-on-iris)),
  instance seeding & baseline ([§6](#6-instance-seeding--baseline)), the identical developer experience
  ([§7](#7-the-developer-experience-identical-across-environments)), the git/TDD/team model
  ([§8](#8-git-first-team-tdd-model)), the profile binding points ([§9](#9-environment-profiles--the-binding-points)),
  the transition strategy ([§10](#10-the-transition-strategy-develop-public--deploy-va)), multi-instance /
  multi-tier operation ([§11](#11-multi-instance--multi-tier-operation-the-130-systems)), and the parity
  verification ([§13](#13-verification--parity-contract)).

### Out of scope (guardrails)

- **Building or provisioning the target instance.** How a VistA-on-IRIS comes to exist is the container spec's
  job (`vista-iris-container-spec-v3.md`) or VA provisioning. The bridge assumes a running instance and seeds
  from it.
- **The two concrete profiles.** Their service bindings live in `…-public.md` / `…-va.md`, not here.
- **Globals / data / FileMan DD sync or migration.** The bridge moves **routines (code)**; it does **not**
  reconcile data dictionaries or data across instances ([§6.4](#64-why-two-seeds-code-is-meaningless-without-its-dd)).
- **KIDS distribution** (the VA-authoritative packaging artifact) and **PHI handling policy** (governed by the
  VA profile + VA policy).

---

## 2. Goals & Non-Goals

### Goals

- **Instance-agnostic** — one bridge runs against *any* VistA-on-IRIS; no assumptions about namespace name,
  routine inventory, package layout, data, or DD ([§5](#5-the-instance-contract-works-against-any-vista-on-iris)).
- **Instance-seeded** — the dev environment is defined and seeded by the specific target VistA
  ([§6](#6-instance-seeding--baseline)).
- **Identical experience [Parity]** — public and VA developers use the same VS Code, extensions, `m-cli`,
  configuration, `make` targets, and commands ([§7](#7-the-developer-experience-identical-across-environments)).
- **Develop-in-public, deploy-to-VA** — all tooling is built and validated on open public tooling outside the
  VA, and reaches the VA environment by a **profile swap + artifact mirroring**, never a rewrite
  ([§10](#10-the-transition-strategy-develop-public--deploy-va)).
- **Git-first & test-driven** — branches, pull requests, review, and CI; fast file-side unit tests plus IRIS
  integration tests against the target ([§8](#8-git-first-team-tdd-model)).
- **Provenance** — every code tree is traceable to a specific instance baseline ([§6.3](#63-the-instance-baseline-manifest)).

### Non-Goals

- **Not one document for both environments** — mixing is prohibited; the core + two profiles stay separate.
- **Not data/DD sync** — routine behavior depends on the target's DD + data; the bridge validates code *against*
  the target instance rather than trying to make instances equal.
- **Not a build spec, not KIDS, not a data-migration tool.**
- **No class-grade IDE features for flat M** (carried from `vista-dev-iris-tooling.md`).

---

## 3. Glossary

| Term | Meaning |
|---|---|
| **Target instance** | The running VistA-on-IRIS a developer develops against (and tests on). Parameter to everything downstream. |
| **Source / seed instance** | The target instance at the moment it seeds a dev environment ([§6](#6-instance-seeding--baseline)). |
| **Instance descriptor** | The discovered facts about a target instance (namespace, routine inventory, package map, encoding, DD/site identity) — output of the discovery step ([§5](#5-the-instance-contract-works-against-any-vista-on-iris)). **[Instance]**. |
| **Code seed** | The `.m` git tree exported from a source instance's routines. |
| **Runtime seed** | A runnable copy of the source VistA (DD + data + config) that per-developer IRIS instances test against. |
| **Instance baseline (manifest)** | The provenance record pinning a code tree to a specific source instance + timestamp + content hashes ([§6.3](#63-the-instance-baseline-manifest)). |
| **Environment profile** | A binding of the bridge's abstract dependencies (git host, registry, runners, package sources, remote-dev platform, runtime-seed source, data posture, auth) to concrete services. Two exist: **public**, **VA**. **[Profile]**. |
| **Core contract** | This document — the environment-neutral, developer-facing contract. **[Parity]**. |
| **Tier** | A stage of a VistA's lifecycle — **dev → test → pre-prod → prod** — with increasingly accurate / real data. |
| **Parity** | The property that the developer-facing surface is identical across environments ([§7](#7-the-developer-experience-identical-across-environments), [§13](#13-verification--parity-contract)). |
| **Binding point** | An abstract dependency the core defers to a profile ([§9](#9-environment-profiles--the-binding-points)). |
| **`m-dev-tools` / `m-cli`** | The filesystem M toolchain (`m fmt`/`lint`/`test`/`coverage`/`lsp`/`watch`) on `tree-sitter-m`; see `historical/iris-dev-bridge-spec.md` §3. |

---

## 4. Three-Layer Architecture (the proposal)

The directive — *parallel public and VA specs, identical experience, smooth transition, no mixing* — is met by
**factoring the design into three layers** and writing **one core + two thin profiles**.

```
        Developer  ─────────────────────────────────────────────────────────────────
           │  VS Code + remote-dev + m-cli + make targets   ← IDENTICAL  [Parity]
           ▼
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │  LAYER 1 — CORE CONTRACT   (this spec; environment-neutral)        [Parity]   │
   │  developer experience · instance contract · seeding · git/TDD · parity tests  │
   └───────────────┬───────────────────────────────────────┬───────────────────────┘
                   │ binds                                   │ seeds-from
                   ▼                                          ▼
   ┌───────────────────────────────┐        ┌────────────────────────────────────────┐
   │ LAYER 3 — ENVIRONMENT PROFILE │        │ LAYER 2 — INSTANCE ADAPTER     [Instance]│
   │  public  |  VA      [Profile] │        │  discovers + seeds from a target VistA   │
   │  git host · registry · runners│        │  (any namespace / inventory / DD / data) │
   │  pkg sources · remote-dev     │        └────────────────────────┬─────────────────┘
   │  runtime-seed · auth · data   │                                 │ runs against
   └───────────────────────────────┘                                 ▼
                                                          any VistA-on-IRIS instance
```

- **Layer 1 — Core contract (this spec).** Everything a developer touches. All **[Parity]** requirements live
  here. Written once.
- **Layer 2 — Instance adapter.** Discovers a target VistA and seeds the dev environment from it; the *same*
  adapter works against any instance. All **[Instance]** values flow from here.
- **Layer 3 — Environment profile.** Binds the abstract dependencies to concrete services; two profiles, each
  its own spec. All **[Profile]** values live here.

**How the documents relate (the proposal, concretely):**

| Concern | Owner doc | Tag |
|---|---|---|
| Developer experience, commands, tooling versions | **core** (this) | [Parity] |
| Instance contract + discovery + seeding | **core** (this) | [Instance] |
| Git/TDD/team workflow, tier promotion | **core** (this) | [Parity] |
| Parity & instance-agnostic verification | **core** (this) | [Parity] |
| Git host, registry, CI runners, package/base-image sources | **profile** (`-public` / `-va`) | [Profile] |
| Remote-dev platform, runtime-seed source, data sensitivity, auth | **profile** (`-public` / `-va`) | [Profile] |

> **Why this guarantees identical experience and a smooth transition.** Everything developer-facing is in the
> core and tagged **[Parity]**; divergence is **quarantined** to the profile's binding-point table. Identical
> experience falls out by construction. The VA transition is then *swap the profile + mirror artifacts +
> re-seed from a VA instance* — never a rewrite ([§10](#10-the-transition-strategy-develop-public--deploy-va)).

---

## 5. The Instance Contract (works against any VistA-on-IRIS)

The bridge must run against **any** VistA-on-IRIS — FOIA fake-data, official VA dev, or any of ~130 production
systems at any tier — so it **requires a minimum** of the target and **discovers the rest** rather than
assuming it.

### 5.1 What the bridge requires of a target instance (minimum)

| Requirement | Why |
|---|---|
| Reachable IRIS (session / superserver) | to enumerate, read, write, and compile routines |
| A namespace containing the VistA routines | the unit of work (name **discovered**, not assumed `VISTA`) |
| Programmer-level access in that namespace | enumerate / read / `Load` / compile |
| *(Recommended)* PACKAGE file `#9.4` | for the package-folder layout; degrades gracefully if absent |

### 5.2 What the bridge discovers (the instance descriptor) [Instance]

A **discovery step** probes the target and emits an **instance descriptor** that parameterizes seeding,
layout, and round-trip:

- **Namespace** name (not assumed).
- **Routine inventory + type** — count, names, and storage type (`.INT` vs `.MAC`); the round-trip extension
  mapping follows the discovered type.
- **Package map** — from `^DIC(9.4,"C")` (prefix → package) where present.
- **Encoding / locale** — to read/write routine text without corruption.
- **Instance identity** — site number, DD/version fingerprint, and a content hash, for the baseline
  ([§6.3](#63-the-instance-baseline-manifest)).

> **⚠ Generalization (vs `historical/iris-dev-bridge-spec.md`).** The predecessor spec grounded everything in one
> observed instance (FOIA: namespace `VISTA`, `.INT`, 33,941 routines, 144 packages). Those facts are now just
> **one instance descriptor** — evidence for the *public profile*, not a core assumption. The core assumes
> **none** of them and discovers each.

### 5.3 Degradation rules (no FOIA assumptions)

- **No `#9.4` / partial map** → fall back to a **namespace-prefix** layout, else a **flat** layout; report the
  fallback.
- **`.MAC` storage** (instead of `.INT`) → adapt the extension mapping per the descriptor.
- **Non-`VISTA` namespace** → use the discovered name throughout.
- Any assumption the descriptor cannot confirm **must not** be hardcoded.

---

## 6. Instance Seeding & Baseline

**The dev environment is a function of the target instance.** Seeding produces **two artifacts**, both derived
from the *same* source instance and tied together by one baseline manifest.

### 6.1 Code seed [Instance]

Export the source instance's routines → a `.m` git tree, using the **discovered** package layout and encoding
(the instance-agnostic generalization of `historical/iris-dev-bridge-spec.md` Stage 1). This tree is the
**version-controlled baseline** the team develops on.

### 6.2 Runtime seed [Instance / Profile]

A **runnable copy of the source VistA** (DD + data + config) that per-developer IRIS instances test against:

- **Public** [Profile]: the FOIA fake-data image (`vista-iris-container-spec-v3.md`).
- **VA** [Profile]: a **sanitized clone** of the official VistA at the relevant tier (data sensitivity escalates
  with tier — [§11](#11-multi-instance--multi-tier-operation-the-130-systems); sanitization is VA policy).

### 6.3 The instance baseline (manifest)

Seeding **must** record provenance pinning the code tree to a specific instance state:

- source instance identity (site, namespace, DD/version fingerprint),
- routine inventory + per-routine content hashes,
- export timestamp, encoding, and the layout rule used,
- the runtime-seed reference (image/clone) it pairs with.

This makes the git tree **traceable**, enables **drift detection** (routines changed in the instance outside
git), and supports **reproducible re-seed**.

### 6.4 Why two seeds: code is meaningless without its DD

VistA routines are tightly coupled at runtime to the FileMan **data dictionary** and **globals**. The *same*
routine can behave differently against a different DD/data state. Therefore correctness is validated **against
the specific instance** — which is exactly why the dev environment must be **seeded by the particular instance**
(both its code *and* a runnable copy of its DD+data). The bridge does **not** try to make instances equal; it
makes the dev environment *match* its target.

### 6.5 Round-trip mechanics

**[Parity].** The export ↔ push-back round-trip is **identical in every environment** (only the endpoints
differ). Because flat-M VistA carries no class macros, a routine's IRIS source text and its `.m` text are the
same M — the round-trip is a lossless rename + encoding normalization:

- **Export:** read the namespace's routines (the discovered type, e.g. `.INT`) → write one `.m` per routine in
  the discovered package layout (`%` → `_`, the instance's encoding).
- **Push back:** stage `.m` → `<NAME>.int` (reverse `_` → `%`), then `$SYSTEM.OBJ.Load(…, "ck")` (one) or
  `$SYSTEM.OBJ.ImportDir(…, "*.int", "ck", , 1)` (batch) — compile **and** keep source.
- **Why stage to `.int`:** IRIS rejects raw `.m` on import (Err #5840; cf. `vista-iris-container-spec-v3.md` §4),
  so `.m` content is staged under an IRIS-native extension first. No data / DD is touched.
- **Fidelity:** export → re-import unchanged → re-export must be byte-identical
  ([§13](#13-verification--parity-contract) suite 2).

The concrete, validated realization (commands, scripts, the reference instance) is recorded in the **public
profile**; the **VA profile** re-validates the same mechanics in-boundary.

---

## 7. The Developer Experience (identical across environments)

**[Parity].** This is the **parity surface**: everything below **must be identical** for a public developer and a VA
developer. Only the endpoints *behind* these differ ([Profile]).

| Surface | Requirement [Parity] |
|---|---|
| **Editor** | VS Code, **remote-dev** (thin client; Remote-SSH / dev container), same extension set (InterSystems ObjectScript, `tree-sitter-m-vscode`), same settings + keybindings |
| **Toolchain** | the **same `m-cli` version** + config (lint profile, `fmt`), same `m lint` / `fmt` / `test` / `coverage` / `lsp` / `watch` |
| **Commands** | the **same `make` targets** — `seed` (discover+seed), edit→save→`sync`, `lint`, `test`, `watch` |
| **Loop** | edit `.m` → file-side lint/test → `sync` to a per-dev IRIS → integration test — **identical** |
| **Layout** | the FOIA-style `.m` package tree (or the discovered fallback), identical conventions |

A developer **must not** be able to tell, from the editor and commands, which environment they are in. Any
observable difference is a parity defect ([§13](#13-verification--parity-contract)).

---

## 8. Git-first, Team, TDD model

- **Git-first collaboration** — branches, pull requests, code review, and CI on whichever git host the profile
  binds ([§9](#9-environment-profiles--the-binding-points)); the **workflow is identical**. Per-developer
  environments (own code tree + own runtime IRIS), shared via git — **no shared mutable IRIS** (a routine `sync`
  mutates the namespace; see `historical/iris-dev-bridge-spec.md` §12.2).
- **Two test tiers (test-driven):**
  1. **File-side unit tests** — `m test` / `coverage` on the `.m` tree (parser + YottaDB engine), fast, no IRIS;
     **gate the PR**.
  2. **IRIS integration tests** — `sync` the routine(s) into a per-dev runtime seed and run M-Unit / behavioral
     tests against the **actual DD + data**; validates code where it will run.
- **Tier promotion (dev → test → pre-prod → prod)** maps onto git (branch / release flow) plus deployment to
  each tier's instance; **data realism increases per tier**, and the **same bridge** operates against each.
  Code moves via git (reviewed, tested); **data never moves through the bridge**.

---

## 9. Environment Profiles — the binding points

Each profile spec (`-public`, `-va`) **must** fill exactly this table and **add nothing developer-facing** (that
belongs to the core, [§7](#7-the-developer-experience-identical-across-environments)). This table *is* the
contract for writing the two parallel specs.

| Binding point | Public profile | VA profile |
|---|---|---|
| Git host / URL | public **github.com** | in-boundary VA GitHub — **GHEC-US** (`va.ghe.com`) and/or self-hosted **GHES** (`github.ec.va.gov`) |
| Container / OCI registry | GHCR / public | in-boundary registry (GHES Packages / Harbor / Artifactory / ECR) |
| CI runners | GitHub-hosted | **self-hosted** (e.g. Actions Runner Controller) |
| Package / dependency sources | public (PyPI, `m-cli`, npm) | **mirrored** in-boundary |
| Base image source | Docker Hub (`intersystems/irishealth-community`) | **internal mirror** of the InterSystems image |
| Remote-dev platform | Codespaces **or** Coder / Remote-SSH | **self-hosted** (Coder / Remote-SSH); Codespaces exists on GHEC-US but is policy-gated, and is absent on GHES |
| Runtime-seed source | FOIA fake-data image | **sanitized clone** of the official VistA (per tier) |
| Data sensitivity / PHI | fictitious only | escalates by tier; PHI governed by VA policy |
| Identity / auth | public OAuth / SSH keys | **VA SSO** (SAML/OIDC, PIV/CAC) |
| AI / MCP tooling | allowed (`m-dev-tools-mcp`, Claude Code) | per VA network policy (treat as optional) |

> Each profile is a **separate spec**, so the two environments are never mixed. The **public profile** carries the
> concrete, validated reference-instance facts and surfaces; the **VA profile** carries the in-boundary
> supply-chain mapping. This core makes both *thin*.

---

## 10. The Transition Strategy (develop-public → deploy-VA)

The bridge is **built and validated entirely in the public environment** (open tooling, fake-data instance),
then reaches the VA environment **without a rewrite**:

1. **Mirror artifacts** in-boundary — the published image, `m-cli` + `tree-sitter-m` binaries, and language/tool
   dependencies (the air-gap step; VA profile).
2. **Swap the profile** — repoint git host, registry, runners, base-image source, remote-dev platform, and auth
   to the in-boundary services (the [Profile] table, [§9](#9-environment-profiles--the-binding-points)).
3. **Re-seed from a VA instance** — run the *same* discovery + seeding ([§5](#5-the-instance-contract-works-against-any-vista-on-iris)–[§6](#6-instance-seeding--baseline)) against the official VistA dev tier; its
   different namespace / DD / data flow in as **[Instance]** values.
4. **Validate parity** — run the parity + instance-agnostic suites ([§13](#13-verification--parity-contract))
   in-boundary; a green run is the transition's acceptance gate.
5. **Roll up the tiers** — repeat against test → pre-prod → prod instances, with access/data controls
   tightening per tier.

> **What makes it smooth.** The **[Parity]** guarantee (the developer surface is unchanged), the **[Profile]**
> quarantine (only bindings change), and **instance-agnosticism** (re-seed, don't re-engineer). The transition
> touches the profile and the artifact mirror — **not** the bridge core or the developer's workflow.

### Inbound contribution from the outside community

§10 sends VA's *own* code outward (public → VA). The reverse flow — folding in work from the **outside
developer community** (OSEHRA, WorldVistA, the FOIA releases, the M/MUMPS world) — needs its own discipline,
because the boundary that protects operational code also **severs that community**: under the VA profile's
**EMU** identity model, public-github.com accounts cannot be added as collaborators at all
([VA profile §2](vista-iris-dev-bridge-spec-va.md)). Two mechanisms keep the channel open without breaching
the boundary:

- **Outbound mirror (publish).** A one-way mirror of FOIA-releasable repos from the in-boundary host to a
  public presence (the public profile's github.com org). Push-only — the boundary is never reachable
  inbound; the community gets read / fork / issue access.
- **Inbound airlock (ingest).** Community PRs land on the **public mirror**; a maintainer reviews, scans
  (license — cf. `m-dev-tools` AGPL-3.0, [§14](#14-known-limitations-deferred-items--risks); security;
  PII/PHI), then **cherry-picks** accepted commits in-boundary. Humans + scanners gate every inbound commit;
  nothing crosses automatically.
- **Credential sustained partners.** Ongoing collaborators take the **`@va.gov` + PIV** path (VA profile §2)
  — heavyweight per person, so reserve it for *relationships*, not crowd contribution.

> **Policy basis.** Publishing-by-default has federal backing: **OMB M-16-21** (Federal Source Code Policy,
> 2016 — release ≥20% of new custom code as OSS + inventory via code.gov) and the **SHARE IT Act** (Pub. L.
> 118-187, 2024-12-23 — agencies *shall* share custom-developed code, with national-security / privacy
> exemptions). Both frame the outbound mirror and its inventory as a compliance obligation. The **per-repo
> clearance policy** (FOIA-releasable vs. internal-only, and who signs off) is VA-governed — an
> [Open Question](#open-questions-flagged-not-resolved).

---

## 11. Multi-instance & Multi-tier operation (the ~130 systems)

The bridge is parameterized by **(target instance, environment profile, tier)**. Operating across the VA's
~130 sites and their dev / test / pre-prod / prod tiers is **many such tuples, one tooling**:

- **Per-instance dev environments** — each seeded from its own target ([§6](#6-instance-seeding--baseline));
  baseline manifests keep them distinct and prevent cross-contamination.
- **Per-tier data sensitivity** — fictitious at dev, escalating to real PHI at prod; access controls and
  sanitization tighten accordingly (VA profile + policy).
- **Code promotion across tiers via git** — a change validated at one tier is promoted by review + deploy to the
  next tier's instance; **data is never moved down or up through the bridge**.
- **Site/tier provenance** — every tree records which site + tier + instance baseline it derived from.

---

## 12. Repository & Artifact Layout

| Repo / artifact | Contents | Public ↔ VA |
|---|---|---|
| **bridge tooling** | env-neutral core: instance adapter (discover/seed), export / `sync` / `watch`, `m-cli` config, parity suite | same code; built in public, **mirrored** to GHES |
| **routines tree(s)** | the `.m` code seed, per instance / site / tier (branches or repos) | many trees; same layout conventions |
| **profile specs/config** | the two profiles + their concrete bindings | one repo each side, or shared with overrides |
| **runtime-seed images** | the runnable VistA per target/tier | FOIA image (public) ↔ sanitized clones (VA) |

The structure is **identical** across environments; only the **host** (github.com ↔ GHES) and **registry**
differ ([§9](#9-environment-profiles--the-binding-points)).

---

## 13. Verification & Parity Contract

| # | Suite | What it proves | Gating? |
|---|---|---|---|
| 1 | **Parity suite** | the developer surface ([§7](#7-the-developer-experience-identical-across-environments)) is identical across profiles — same extension/version set, same `m-cli` version + config, same `make` targets, same command behavior on a fixed fixture | **yes** |
| 2 | **Instance-agnostic suite** | the bridge discovers, seeds, and round-trips correctly against **≥2 structurally different** instances (e.g. FOIA `VISTA`/`.INT`/#9.4 **and** a synthetic alt-namespace / no-#9.4 / `.MAC` instance) — proving no FOIA assumptions | **yes** |
| 3 | **Transition conformance** | the **VA deployment passes the same suites** the public reference passes ([§10](#10-the-transition-strategy-develop-public--deploy-va) step 4) | **yes (VA gate)** |
| 4 | **Baseline/provenance** | a seeded tree carries a valid baseline manifest traceable to its source instance ([§6.3](#63-the-instance-baseline-manifest)) | **yes** |

Suites 1–2 run **in public CI**; suite 3 re-runs them **in-boundary** as the transition's acceptance gate.

---

## 14. Known Limitations, Deferred Items & Risks

| Item | Status | Note |
|---|---|---|
| **DD / data divergence across instances** | **By design** | Routine behavior depends on the target's DD + data; validated only at runtime against the target ([§6.4](#64-why-two-seeds-code-is-meaningless-without-its-dd)). |
| **DB → FS drift mirror** | **Deferred** | In-IRIS edits diverging from git (carried from `historical/iris-dev-bridge-spec.md` Stage 4); baseline manifests enable *detection* ([§6.3](#63-the-instance-baseline-manifest)). |
| **Profile specs** | **Written** | `vista-iris-dev-bridge-spec-public.md` and `…-va.md` fill the binding table ([§9](#9-environment-profiles--the-binding-points)). |
| **Predecessor migration** | **Done** | Retired to `historical/iris-dev-bridge-spec.md`; mechanics → [§6.5](#65-round-trip-mechanics), FOIA reference facts → the public profile. |
| **Runtime-seed sanitization** | **VA policy** | Cloning an official VistA for a dev runtime requires PHI sanitization governed by VA policy, not this core. |
| **Discovery robustness** | **Risk** | Discovery must tolerate IRIS/VistA variants (locale, mapped %-routines, non-standard #9.4); covered by the instance-agnostic suite ([§13](#13-verification--parity-contract)). |
| **Air-gapped tool pinning** | **Risk** | `m-cli` / `tree-sitter-m` versions must be pinned and mirrored so public and VA run the *same* toolchain ([§10](#10-the-transition-strategy-develop-public--deploy-va)). |

### Open Questions (flagged, not resolved)

1. **Profiles: separate repos or branches/overlays?** Affects how the [Profile] table is maintained and how
   parity drift is caught.
2. **Canonical VistA instance fingerprint.** How to identify a VistA + DD version reproducibly for the baseline
   manifest ([§6.3](#63-the-instance-baseline-manifest)) across 130 sites/tiers.
3. **Tier-promotion git model.** Branch-per-tier, environment branches, or release tags + deploy targets?
4. **Baseline scope.** Beyond routines, how much config/DD metadata should the baseline capture to make a
   re-seed faithful?
5. **Shared vs per-dev runtime seed at higher tiers.** Per-dev IRIS is clear at dev; pre-prod/prod testing model
   (and PHI access) needs definition in the VA profile.
6. **Community-contribution clearance.** Which repos are FOIA-releasable (eligible for the outbound mirror /
   inbound airlock, [§10](#10-the-transition-strategy-develop-public--deploy-va)) vs. internal-only, and who
   signs off — VA-governed.

---

## 15. Key Facts Appendix (A)

| Fact | Value |
|---|---|
| Layer model | Core (this) **[Parity]** · Instance adapter **[Instance]** · Environment profile **[Profile]** ([§4](#4-three-layer-architecture-the-proposal)) |
| Documents | this core + `…-public.md` + `…-va.md` (never mixed) |
| Instance minimums | reachable IRIS · routine namespace · programmer access · (recommended) `#9.4` ([§5.1](#51-what-the-bridge-requires-of-a-target-instance-minimum)) |
| Discovered (per instance) | namespace · routine inventory + type · package map · encoding · site/DD identity |
| Seeds | **code seed** (`.m` tree) + **runtime seed** (runnable VistA), one baseline manifest ([§6](#6-instance-seeding--baseline)) |
| Parity surface | VS Code + extensions · `m-cli` version + config · `make` targets · the edit→lint→test→sync loop ([§7](#7-the-developer-experience-identical-across-environments)) |
| Binding points | git host · registry · runners · pkg/base-image sources · remote-dev · runtime-seed · data posture · auth · AI tooling ([§9](#9-environment-profiles--the-binding-points)) |
| Transition | mirror artifacts → swap profile → re-seed from VA instance → validate parity → roll tiers ([§10](#10-the-transition-strategy-develop-public--deploy-va)) |
| Tiers | dev → test → pre-prod → prod (increasing data realism) |

---

## 16. References

- **Core / siblings:** this document; `vista-iris-dev-bridge-spec-public.md` and
  `vista-iris-dev-bridge-spec-va.md` (the two environment profiles); `historical/iris-dev-bridge-spec.md`
  (predecessor — FOIA-instance-specific draft this generalizes).
- **Companions in this repo:** `vista-iris-container-spec-v3.md` (one example target instance + its build) ·
  `vista-dev-iris-tooling.md` (VA inner-loop tooling landscape) · `vscode-iris-editing.md`.
- **Toolchain:** [`m-dev-tools`](https://github.com/m-dev-tools) — `m-cli`, `tree-sitter-m`, `m-test-engine`,
  the VS Code extensions, and `m-dev-tools-mcp`.
