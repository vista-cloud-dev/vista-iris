# VistA-on-IRIS Dev Bridge — Public Environment Profile

**Status:** Proposed (design) · **Version:** 1 · **Date:** 2026-05-25
**Profile of:** `vista-iris-dev-bridge-spec.md` (the environment-neutral core) · **Sibling:** `vista-iris-dev-bridge-spec-va.md`
**Companions:** `vista-iris-container-spec-v3.md` (the reference target instance) · `historical/iris-dev-bridge-spec.md` (the FOIA-grounded draft this profile absorbs)

---

## How to read this document

This is the **public environment profile** of the dev-bridge core. It is **thin by design**: it adds **no
developer-facing requirements** — those are **[Parity]** and live in the core — and instead (1) fills the core's
binding-point table ([core §9](vista-iris-dev-bridge-spec.md)) for open, public development, and (2) records the
**reference target instance** and the **validated round-trip surfaces** observed in public. Public and VA are
**never mixed**; the VA bindings live in the sibling profile.

> Everything a developer sees and runs is defined by the **core** ([core §7](vista-iris-dev-bridge-spec.md)). If
> a requirement here would change the developer experience, it belongs in the core, not this profile.

## 1. Scope

Open, collaborative development on **public github.com** with **public tooling**, against a **fake-data**
VistA-on-IRIS — the FOIA build of `vista-iris-container-spec-v3.md`, treated as a given running instance
("forget that it had to be built"). This is the **reference environment** in which the bridge is built and
validated before it transitions to the VA ([core §10](vista-iris-dev-bridge-spec.md)).

## 2. Binding points [Profile]

| Binding point (core §9) | Public value |
|---|---|
| Git host / URL | public **github.com** (`https://github.com/<org>/…`) |
| Container / OCI registry | **GHCR** (`ghcr.io/…`) |
| CI runners | **GitHub-hosted** (`ubuntu-24.04`, `ubuntu-24.04-arm`) |
| Package / dependency sources | public (PyPI, `m-cli`, npm) — fetched directly |
| Base image source | **Docker Hub** (`intersystems/irishealth-community`) |
| Remote-dev platform | **GitHub Codespaces** *or* Coder / Remote-SSH (developer's choice) |
| Runtime-seed source | the **FOIA fake-data image** (`vista-iris-container-spec-v3.md`) |
| Data sensitivity / PHI | **fictitious only** — no real data; instance bannered test-only |
| Identity / auth | public OAuth / SSH keys |
| AI / MCP tooling | **allowed** — `m-dev-tools-mcp`, Claude Code |

## 3. Reference target instance (descriptor) [Instance]

What the core's discovery step ([core §5](vista-iris-dev-bridge-spec.md)) returns for the reference FOIA
instance — validated by read-only probe on 2026-05-25 (evidence migrated from the predecessor draft):

| Property | Value |
|---|---|
| Namespace | `VISTA` |
| Routine storage type / count | `.INT` · 33,941 (0 `.MAC`, 0 `.m`) |
| Package map | PACKAGE file #9.4 (144 packages); `^DIC(9.4,"C")` prefix→IEN cross-reference |
| Encoding | ISO-8859-1 |
| Filename mapping | `%` ⇄ `_` |
| Host mount on running container | none (export copies out; a dev container bind-mounts the tree) |

> This is **one** instance descriptor, not a core assumption. The VA profile's instances differ (namespace,
> inventory, FileMan DD, data); the *same* discovery + seeding handle them ([core §5–§6](vista-iris-dev-bridge-spec.md)).

## 4. Reference surfaces (validated in public)

The concrete realization of the core's [Parity] round-trip mechanics ([core §6.5](vista-iris-dev-bridge-spec.md)),
built and validated against the reference instance:

- **Seed / export:** `^DIC(9.4,"C")` map ▸ `%RoutineMgr:StudioOpenDialog("*.INT")` ▸ write
  `routines/Packages/<Pkg>/Routines/<NAME>.m` (`%`→`_`, ISO-8859-1).
- **Push back:** stage `.m` → `<NAME>.int`, then `$SYSTEM.OBJ.Load(…, "ck")` (one) /
  `$SYSTEM.OBJ.ImportDir(…, "*.int", "ck", , 1)` (batch) — staging to `.int` respects the raw-`.m` #5840 limit.
- **Surfaces:** `make export [EXPORT_SPEC=…]`, `make sync`, `make watch`;
  `scripts/roundtrip/{export,sync,watch}.py`; `m-cli` (`m fmt`/`lint`/`test`/`coverage`/`lsp`/`watch`).
- **Tooling licensing:** `m-dev-tools` is AGPL-3.0; invoked as a **subprocess** (CLI boundary), so it does not
  impose AGPL on this repo.

## 5. Verification (the public reference run)

The core's parity + instance-agnostic + baseline suites ([core §13](vista-iris-dev-bridge-spec.md)) run in
**public CI** on GitHub-hosted runners. **This run is the reference** the VA transition must reproduce in-boundary
([core §10](vista-iris-dev-bridge-spec.md); VA profile §5).

## 6. References

- Core: `vista-iris-dev-bridge-spec.md`. Sibling: `vista-iris-dev-bridge-spec-va.md`.
- Reference instance + build: `vista-iris-container-spec-v3.md`. Provenance: `historical/iris-dev-bridge-spec.md`.
- Toolchain: [`m-dev-tools`](https://github.com/m-dev-tools) (`m-cli`, `tree-sitter-m`, `m-test-engine`, the VS
  Code extensions, `m-dev-tools-mcp`).
