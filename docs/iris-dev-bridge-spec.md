# IRIS Dev Bridge — Filesystem / Git Round-Trip Specification

**Status:** Proposed (design) · **Version:** 1 · **Date:** 2026-05-25
**Companion:** `vista-iris-container-spec-v3.md` (the image this bridges into) · `vista-dev-iris-tooling.md` (the VA inner-loop landscape this modernizes)
**Depends on:** a built, running VistA-on-IRIS instance ([v3 §1](vista-iris-container-spec-v3.md))

---

## How to read this document

This is the **normative design contract** for a *dev-time* capability that does **not yet exist
in the code**: a bidirectional bridge that exposes IRIS-resident VistA routines as a
git-tracked **filesystem** tree, lets a developer edit and manage them with **file-based
tooling** (linting, LSP, SAST, code review, CI), and pushes edits **back into IRIS** for runtime
testing. It modernizes the VA inner loop described in `vista-dev-iris-tooling.md` — where routines
live *inside* the database and are edited server-side — into a files-first, git-first workflow.

Conventions (aligned with v3):

- **Normative** requirements use *must / must not / should*. This document contains **no source
  listings** by design; mechanisms are named (`$SYSTEM.OBJ.Load`, `^DIC(9.4,"C")`, `make export`),
  and the implementation lives in the files named in [§10](#10-repository-layout--artifacts-proposed)
  once built.
- Statements are tagged **[Validated]** when verified against the live `vista-iris:dev` instance on
  2026-05-25 (the probes in [§5](#5-validated-ground-truth-this-instance)), or **[Proposed]** when
  they are the design target not yet implemented. Where a claim would contradict an established v3
  decision, a **⚠ Reconciliation** note explains the interaction.
- "v3" = `vista-iris-container-spec-v3.md`. "the bridge" = the tooling specified here. "the dev
  tree" = the canonical git-tracked `.m` routines this bridge produces ([§7](#7-canonical-on-disk-format--layout-locked-decisions)).

---

## 1. Purpose & Scope

### The problem this solves

A VA VistA developer on IRIS edits routines **inside the database**: the routine is the unit of
work, it is stored and compiled in the `VISTA` namespace, and the modern tooling reaches it
server-side (VS Code over `isfs`, the terminal, the Management Portal). This is the inner loop v3
exposes ([v3 §2 "Developer-tooling parity"](vista-iris-container-spec-v3.md)). It is faithful to
the VA experience — and it is **pre-modern**: there are no files, so there is no git history, no
branches, no pull requests, no code review, no file-based linters/formatters/SAST, and no CI gate.
"The code" is a database state, not a reviewable artifact.

The FOIA distribution (`WorldVistA/VistA-M`) shows the other half of the picture: the *same*
routines as **`.m` files** in `Packages/<pkg>/Routines/`, the form the entire filesystem M
ecosystem (YottaDB tooling, LSP, linters, SAST, git) consumes. v3 already uses that tree as a
*build-time input* (`prepare.py` → `^%RI`), but only **inward** (files → DB) and only at image
build; there is no path **outward** (DB → files) and no dev-time round-trip.

### What the bridge does

Provide a **bidirectional, dev-time round-trip** that makes the **filesystem the source of truth**
for routine development while IRIS remains the **runtime test target**:

1. **Export (DB → files):** turn the running namespace's routines into a git-tracked `.m` tree in
   the recognizable FOIA layout, derived from the **running instance** (not from FOIA).
2. **Develop (files):** edit `.m` files locally; manage them with git (branches, PRs, code review)
   and file-based M tooling (lint / LSP / SAST / format) and CI.
3. **Push back (files → DB):** import the edited routine(s) into the `VISTA` namespace and compile
   them, on save (incremental) or on demand / in CI (batch), for runtime testing.

### In scope

- The **source-of-truth model** ([§4](#4-the-source-of-truth-model-the-central-decision)) and the
  **canonical on-disk format & layout** ([§7](#7-canonical-on-disk-format--layout-locked-decisions)).
- The **export** mechanism (Stage 1), the **filesystem tooling / git / CI** seam (Stage 2), and the
  **push-back bridge** — incremental *and* batch (Stage 3) — in [§8](#8-the-ordered-stages).
- The **round-trip mechanics** that make `.m` ⇄ IRIS lossless ([§9](#9-round-trip-mechanics)).
- The **dev contract & verification** of round-trip fidelity ([§11](#11-dev-contract--verification)).
- The **team distribution & scaling** model for locked-down VA endpoints — remote-dev baseline, one
  IRIS per developer, and per-workspace footprint ([§12](#12-team-distribution--scaling)).

### Out of scope (guardrails)

- **Not the image build.** Building the loaded instance is v3's job; the bridge assumes one exists
  and runs against it. This spec adds **no** build-time requirement.
- **Not a replacement for KIDS.** The bridge moves *routines* for development and runtime testing.
  Packaging a change for *distribution* (KIDS build, the authoritative VA artifact;
  `vista-dev-iris-tooling.md` §7) is a separate, downstream concern.
- **Not globals/data.** Routines only. Globals (`.zwr`) round-trip is a possible later extension,
  not specified here.
- **Not (initially) a server-side source-control hook.** Mirroring *in-IRIS* edits back to disk
  via `%Studio.SourceControl` (Deltanji / git-source-control) is **deferred** to Stage 4
  ([§8](#8-the-ordered-stages)); the v1 contract funnels all edits through the filesystem.
- **Not production, not real PHI.** Same posture as v3.

---

## 2. Goals & Non-Goals

### Goals

- **Files-first inner loop** — a routine's authoritative form for development is a `.m` file under
  git, not a database object.
- **Recognizable layout** — the dev tree is the FOIA `Packages/<pkg>/Routines/*.m` shape, so the
  existing M ecosystem and any VistA developer reads it without translation.
- **Authentic to the instance** — the tree is derived from the **running** `VISTA` namespace (which
  may carry patches beyond FOIA), not copied from an external FOIA checkout.
- **Lossless round-trip** — a routine exported and re-imported with no edits must compile to the
  byte-identical source the namespace started with ([§11](#11-dev-contract--verification)).
- **Incremental by default, batch on demand** — editing one routine pushes only that routine (a
  fast save→compile loop); CI / bulk operations push the changed set in one pass.
- **CI-gateable** — the `.m` tree is lint-/test-able in a pipeline on every PR, a capability the
  IRIS-internal workflow cannot offer.
- **Engine-agnostic, no new host deps** — driven through `make` over Podman/Docker, reusing the
  existing `osehra.session` connection discipline; no new runtime stack on the host.

### Non-Goals

- Not a class-IDE workflow. VistA is flat M; the bridge does **not** convert routines to `.cls` or
  adopt ObjectScript class tooling ([v3 §2](vista-iris-container-spec-v3.md)).
- Not a two-way live mirror in v1 (DB→FS hooks are Stage 4, deferred).
- Not a merge-conflict resolver for concurrent in-IRIS + on-disk edits (the v1 model forbids the
  former; see [§14](#14-known-limitations-deferred-items--risks)).
- Not a globals/data sync, a KIDS builder, or a distribution mechanism.

---

## 3. Glossary

| Term | Meaning |
|---|---|
| **Routine** | A compiled M program unit. In IRIS a routine has a *type*: `MAC` (macro source) → `INT` (intermediate source) → `OBJ` (object). For flat-M VistA (no class macros) the **`.INT` is the source**. |
| **`.m`** | The filesystem extension for a standard-MUMPS routine (YottaDB/GT.M and FOIA convention). One routine per file. The dev tree's format. |
| **`.int` / `.mac`** | IRIS-internal routine source extensions. **[Validated]** this instance stores VistA routines as **`.INT`** ([§5](#5-validated-ground-truth-this-instance)). |
| **UDL** | Unit Definition Language — IRIS's plain-text (diffable) form of a routine/class, as opposed to the XML export form. The bridge uses plain text only. |
| **`isfs`** | InterSystems virtual FileSystem — VS Code editing of routines that live *in the server*. Server-side; produces **no** local files. The thing the bridge complements / supersedes for git work. |
| **`%RoutineMgr:StudioOpenDialog`** | The class query that enumerates routines in a namespace (backs the Management Portal Routines page). The bridge's enumeration primitive. **[Validated]**. |
| **`$SYSTEM.OBJ.Load` / `.ImportDir`** | IRIS import APIs. Accept `.mac`/`.int`/`.inc`/`.cls`/`.xml`; **reject raw `.m`** (Err #5840 — [v3 §4](vista-iris-container-spec-v3.md)). The qualifier `ck` = compile + keep source. |
| **`^DIC(9.4,"C")`** | The PACKAGE file (#9.4) **prefix cross-reference**: routine-namespace prefix → package IEN. The authentic, in-instance source of the FOIA folder map. **[Validated]**. |
| **`^%RO` / `^%RI`** | Legacy VistA routine-out / routine-in utilities + their transfer-file format. v3's build imports via `^%RI`; the bridge uses the programmatic APIs instead ([§9](#9-round-trip-mechanics)). |
| **XINDEX** | VistA's native M static-analysis ("lint") tool; runs in-instance. The incumbent VA lint path; the `Makefile lint` seam already references it. |
| **m-dev-tools** | The [`m-dev-tools`](https://github.com/m-dev-tools) org's filesystem M toolchain — chiefly **`m-cli`** (`m fmt`, `m lint` [36 rules / 8 profiles], `m test`, `m coverage`, `m lsp`, `m watch`) over a real M parser (**`tree-sitter-m`**, calibrated on the 39,330-routine VistA corpus), with VS Code extensions and an MCP server (`m-dev-tools-mcp`, for AI agents incl. Claude Code). Operates on **`.m`** source. Test/coverage execute on **YottaDB** (`m-test-engine`); IRIS is "cooperative scope." |
| **`%`-routine** | A VistA percent-routine (e.g. `%ZIS`). On disk the leading `%` maps to `_` in the filename (`_ZIS.m`), per the existing `prepare.py` convention. |

---

## 4. The Source-of-Truth Model (the central decision)

A routine can be authoritative in **the database** or **on the filesystem**. The two models are
coherent but mutually exclusive for a given workflow; choosing one is the spec's foundational
decision.

| Model | Authoritative form | Round-trip | Fits |
|---|---|---|---|
| **DB-as-truth** | routine inside IRIS; files are a mirror | `isfs` server-side editing; a `%Studio.SourceControl` hook exports each save to disk for git | emulating the VA inner loop verbatim (KIDS is the artifact) — **what v3 exposes today** |
| **Files-as-truth** | `.m` file under git; IRIS is a disposable runtime target | the bridge: bulk export once, then edit-on-disk → import-to-IRIS | **modernization** — git/PR/CI/file-tooling as the primary workflow |

> **Decision.** The bridge adopts **files-as-truth**. After the Stage-1 export, the git `.m` tree is
> canonical; IRIS is the place you *run* code, not the place you *own* it. This is the single change
> that unlocks branches, pull requests, code review, file-based linters/SAST, and CI — none of which
> the DB-resident model affords.

> **⚠ Reconciliation (vs v3's `isfs` parity goal).** v3 §2 lists "developer-tooling parity" via VS
> Code + `isfs` (server-side). That remains valid as a *live view of what is running*. The bridge
> does **not** remove it; it adds a files-first layer **beside** it and shifts authorship to the
> files. The `isfs` folder is retained as a read-mostly "what's in the DB right now" lens.

---

## 5. Validated Ground Truth (this instance)

Probed against the running `vista-iris:dev` container on 2026-05-25 (read-only). These facts shape
the design and are the basis for the [Open Questions](#open-questions-flagged-not-resolved).

| Fact | Value | How probed |
|---|---|---|
| Routine storage type | **`.INT`** (not `.MAC`) | `%RoutineMgr:StudioOpenDialog("*.INT")` = **33,941**; `"*.MAC"` = 0; `"*.m"` = 0 |
| Source readability | `%Routine.%OpenId("DIC.INT")` opens (5,857 lines) | `%OpenId` + `.Size` |
| Package map present | **PACKAGE file #9.4 with 144 packages**; `^DIC(9.4,"C")` is a live prefix→IEN cross-reference (`ABSV`, `ACKQ`, `AFJX`, …) | `$O(^DIC(9.4,"C",…))`, `$P(^DIC(9.4,0),"^",4)` |
| Host mount | **none** — the running container has no bind mount | `podman inspect … .Mounts` (empty) |
| Encoding | **ISO-8859-1** (Latin-1) | existing `helper.py` / `prepare.py` codecs |
| Percent-routine naming | `%` ⇄ `_` in filenames | existing `prepare.py` (`name.replace("_","%")`) |

> **⚠ Reconciliation (`.mac` assumption).** The motivating request assumed VA developers see `.mac`;
> on *this* instance the FOIA `.m` import via `^%RI` lands routines as **`.INT`**. The bridge round-trips
> `.INT` (IRIS) ⇄ `.m` (disk). Whether to *promote* routines to `.MAC` is an explicit
> [Open Question](#open-questions-flagged-not-resolved), not a default.

> **⚠ Reconciliation (count vs v3 §14).** v3 records "33,952 routines loaded"; the namespace
> enumerates **33,941** `.INT`. The small delta is expected (mapped `%`-routines / system routines
> counted differently); the bridge enumerates what `StudioOpenDialog` returns for the `VISTA`
> namespace and reports the exported total.

---

## 6. Architecture Overview

```
        EDIT · LINT · REVIEW   (filesystem, git)            RUNTIME TEST   (IRIS)
 ┌───────────────────────────────────────────────┐   ┌────────────────────────────────┐
 │ routines/Packages/<Pkg>/Routines/<NAME>.m      │   │ VISTA namespace                 │
 │   • git: branches · PRs · code review · blame  │   │   33,941 .INT routines          │
 │   • m-dev-tools: LSP · lint · SAST · format    │   │   ^DIC(9.4,"C") prefix map      │
 │   • CI gate on every PR (the modernization win)│   │   $SYSTEM.OBJ.{Load,ImportDir}  │
 └───────────────────────────────────────────────┘   └────────────────────────────────┘
        ▲                                                          │
        │  Stage 1 — EXPORT (DB → files, batch, one-time/refresh)  │
        │     StudioOpenDialog ▸ prefix-map ▸ %→_ ▸ ISO-8859-1     │
        └──────────────────────────────────────────────────────────┘
        │
        │  Stage 3 — PUSH BACK (files → DB)            stage .m → .int, then:
        ├─ sync-one     (watcher, per save) ───────▶  $SYSTEM.OBJ.Load(<NAME>.int,"ck")
        └─ sync-changed (make / CI, batch)  ───────▶  $SYSTEM.OBJ.ImportDir(*.int,"ck",,1)

        Stage 4 (DEFERRED) — DB → FS mirror via %Studio.SourceControl hook (Deltanji / git-source-control)
```

The bridge runs **inside the container** (it needs the `iris` binary) and reuses the v3
`osehra.session` discipline (license-clean release, ISO-8859-1, retry). Because the running
container has no bind mount **[Validated §5]**, Stage 1 writes inside the container and a `make`
target copies the tree onto the host repo (or a bind mount is added for the dev container); Stage 3
reads a staged copy mounted/copied into the container. See [§8](#8-the-ordered-stages).

---

## 7. Canonical On-Disk Format & Layout (locked decisions)

| Decision | Value | Rationale |
|---|---|---|
| On-disk format | **`.m`** (one routine per file), **not** `.int`/`.mac`/XML | The entire filesystem M ecosystem (m-dev-tools, LSP, SAST, YottaDB, FOIA) consumes `.m`; it is portable and diff-friendly. IRIS-internal types stay internal. |
| Layout | **FOIA package folders:** `routines/Packages/<Package>/Routines/<NAME>.m` | The recognizable VistA layout; browsable, supports per-package ownership/CODEOWNERS. |
| Package assignment | **longest-prefix match against the live `^DIC(9.4,"C")`** → package IEN → name from `^DIC(9.4,IEN,0)` | Authentic to the running instance; no external FOIA artifact required. |
| Unmapped routines | `routines/Uncategorized/Routines/<NAME>.m` (with a reported count) | Deterministic placement for routines no #9.4 prefix claims (typically `%`-utilities / orphans), rather than guessing. |
| Filename ↔ routine name | `%` ⇄ `_` (e.g. `%ZIS` ⇄ `_ZIS.m`); extension `.m` | Matches the existing `prepare.py` convention; bidirectional and lossless. |
| Encoding & line endings | **ISO-8859-1** content; **LF** line endings; no trailing-whitespace rewrite; `.gitattributes` pins both | M is whitespace-sensitive at line start; CRLF or a reformat corrupts routines. |
| Tree root | `routines/` at repo root (distinct from the `vista-m/` build submodule) | Keeps the *dev* source-of-truth separate from the *immutable build pin* ([§13](#13-relationship-to-the-image-build-v3--vista-m)). *Root name is an [Open Question](#open-questions-flagged-not-resolved).* |

> The dev tree mirrors FOIA's *shape* but is **not** the `vista-m/` submodule and **not** sourced
> from FOIA — it is generated from the running namespace ([§13](#13-relationship-to-the-image-build-v3--vista-m)).

---

## 8. The Ordered Stages

Each stage follows the v3 phase idiom: *inputs → actions → what it prevents/why → verified by*.

### Stage 1 — Bulk export (DB → `.m`)

- **Inputs:** a running `VISTA` namespace; the `osehra.session` connection.
- **Actions:** (1) build the prefix→package map from `^DIC(9.4,"C")` + `^DIC(9.4,IEN,0)`;
  (2) enumerate routines via `%RoutineMgr:StudioOpenDialog("*.INT")`; (3) for each routine, read its
  source text via the `%Routine` API, choose its package folder by longest matching prefix
  (else `Uncategorized`), and write `routines/Packages/<Pkg>/Routines/<NAME>.m` (`%`→`_`, ISO-8859-1,
  LF); (4) emit a manifest (count, per-package totals, unmapped list). The exporter accepts a
  **routine filter** (default `*` = all) so a developer can export one package for a narrow first run.
- **Prevents:** the impedance mismatch that blocks git entirely today (no files → no version control);
  and an inauthentic tree (deriving from FOIA instead of the live, possibly-patched instance).
- **Verified by:** the manifest total equals the namespace count; a [round-trip fidelity check
  (§11)](#11-dev-contract--verification) on a sample passes; `git status` shows the new tree.
- **Surface:** `make export` (filter via `EXPORT_SPEC=…`); writes inside the container, copies to the
  host repo.

> **[Proposed] Programmatic, not `^%RO`.** v3's *build* uses the `^%RO`/`^%RI` transfer format because
> it imports raw FOIA `.m` (which `ImportDir` rejects, #5840). The bridge's *export* instead reads
> routines through the `%Routine`/`%RoutineMgr` API and writes per-file `.m` directly — deterministic,
> no interactive dialog to screen-scrape (consistent with the log's "prefer the programmatic path"
> principle, [v3 §15](vista-iris-container-spec-v3.md)).

### Stage 2 — Filesystem tooling, git & CI

- **Inputs:** the `routines/` tree.
- **Actions:** commit the tree; adopt **m-dev-tools** over `.m` — `m lsp` (editor intelligence, via
  the `tree-sitter-m-vscode` extension), `m fmt` (format), `m lint` (analysis); add the `.gitattributes`
  pins ([§7](#7-canonical-on-disk-format--layout-locked-decisions)); wire `m lint` (and `m test` once
  M-Unit suites exist) into the existing `make lint`/`make test` targets — which today reserve slots
  for "XINDEX over changed routines" and an M-Unit stub ([v3 §13](vista-iris-container-spec-v3.md)) —
  and into CI on PR.
- **Prevents:** the absence of review/CI in the DB-resident workflow; CRLF/whitespace corruption
  (via `.gitattributes`); ad-hoc/hand-rolled linting (m-cli's parser is calibrated on the VistA corpus).
- **Verified by:** `make lint` runs `m lint` over the `.m` tree and CI gates a PR; a deliberately
  broken routine fails the gate.

> **[Resolved] Tooling is `m-dev-tools`.** The Stage-2 linter/formatter/LSP is the
> [`m-dev-tools`](https://github.com/m-dev-tools) `m-cli`, not a hand-rolled step. The
> `m-dev-tools-mcp` server additionally exposes the toolchain to AI agents (incl. Claude Code).
> **XINDEX** (in-instance) remains available as a complementary, VistA-native check *post-import*.

> **⚠ Reconciliation (two-tier testing: YottaDB vs IRIS).** m-dev-tools runs `m test`/`m coverage` on a
> lightweight **YottaDB** container (`m-test-engine`), while the bridge's runtime target is **IRIS**.
> These are **complementary layers, not a conflict**: file-based **unit/lint/format** (fast, local,
> parser- and YottaDB-based) gate a PR; **IRIS runtime/integration** testing happens after Stage-3
> push-back, against the real VistA-on-IRIS instance. Pure-M logic is portable across both; engine
> specifics (`$ZF`, IRIS `%`-APIs) are exercised only on the IRIS side.

### Stage 3 — Push back (`.m` → DB), incremental + batch

- **Inputs:** edited `.m` files; a running `VISTA` namespace.
- **Actions:** one bridge with two entry points sharing one import primitive ([§9](#9-round-trip-mechanics)):
  - **`sync-one <file.m>`** — stage the file as `<NAME>.int` (reverse `_`→`%`) and
    `$SYSTEM.OBJ.Load(<staged>.int,"ck")`; surface the compile result. Driven by a **file-watcher**
    on `routines/**/*.m` (the "run on IRIS when saved" loop) or a VS Code Run-on-Save task.
  - **`sync-changed`** — stage all `git diff` changed `.m` and `$SYSTEM.OBJ.ImportDir(<stage>,"*.int","ck",,1)`;
    report the per-item error log. Driven by `make sync` and CI.
- **Prevents:** the #5840 raw-`.m` import failure (by **staging to `.int`**, a type `ImportDir`/`Load`
  accept — see [§9](#9-round-trip-mechanics)); and a slow loop (per-save touches only the one routine,
  never the ~34k set).
- **Verified by:** after a push, the namespace's routine source equals the edited file
  ([§11](#11-dev-contract--verification)); a syntactically broken routine reports a compile error and
  is **not** silently activated.
- **Surface:** `make sync` (batch), `make watch` (live), plus the watcher invoking `sync-one`.

> **Note (vs `m watch`).** m-cli already ships **`m watch`**, which re-runs file-side `lint`/`test` on
> save. The bridge's watcher is the **other half** — it pushes the saved routine into IRIS for runtime
> testing. Preferred composition: `m watch` for the file-side gate, the bridge's `sync-one` for the
> IRIS push; `watch.py` may simply invoke `sync-one` from an `m watch` hook rather than re-implement
> file watching.

### Stage 4 — DB → FS mirror (DEFERRED)

- **Intent:** if edits ever originate *inside* IRIS (terminal, Management Portal, a KIDS install),
  mirror them back to the `.m` tree so git stays canonical, via an IRIS `%Studio.SourceControl` hook
  (open-source **git-source-control**, or commercial **Deltanji**; `vista-dev-iris-tooling.md` §7.3).
- **Status:** **Deferred.** The v1 contract funnels *all* authorship through the filesystem, so the
  mirror is unnecessary until multi-surface editing is required. Tracked in
  [§14](#14-known-limitations-deferred-items--risks).

---

## 9. Round-Trip Mechanics

The round-trip is **lossless** because flat-M VistA carries no ObjectScript class macros, so a
routine's `.INT` source text and its `.m` text are identical M — the only differences are the
*extension*, the *filename ↔ routine-name* mapping, and *encoding normalization*.

| Concern | Export (DB → `.m`) | Push back (`.m` → DB) |
|---|---|---|
| Type / extension | read `.INT` source → write `.m` | stage `.m` → `<NAME>.int`, import as `.int` |
| Name ↔ filename | routine `NAME` → `<NAME with % → _>.m` | filename → routine name (`_` → `%`) |
| Encoding | read as ISO-8859-1 → write ISO-8859-1 (LF) | read `.m` → write staged `.int` as ISO-8859-1 |
| Compile | n/a (read-only) | `Load`/`ImportDir` with **`ck`** = compile + keep source |
| Errors | manifest of unmapped routines | per-item compile status surfaced to editor/CI |

> **Why stage to `.int`, not feed `.m`.** [v3 §4](vista-iris-container-spec-v3.md) established that
> `$SYSTEM.OBJ.Load`/`ImportDir` **reject raw `.m`** (Err #5840) — which is why v3's *build* uses
> `^%RI`. The bridge respects that constraint by staging the `.m` content under a `.int` filename
> before import; `.int` is a type the API accepts. No change to v3's build path.

> **⚠ Reconciliation (import as `.int` vs `.mac`).** Routines are stored as `.INT` **[Validated §5]**,
> so the faithful, no-side-effect round-trip imports them back as **`.int`**. Importing as `.mac`
> would make IRIS treat the file as macro source and *generate* a fresh `.int`, changing the routine
> type for the whole codebase — a mass change with no benefit for macro-free M. v1 imports as `.int`;
> any `.mac` promotion is an [Open Question](#open-questions-flagged-not-resolved).

---

## 10. Repository Layout & Artifacts (proposed)

Dev-time tooling is kept **separate from the v3 install phases** (`scripts/osehra/`, which build the
*image*); it reuses `osehra.session`/`config` for connection discipline.

```
routines/                              the canonical .m dev tree (git-tracked)
  Packages/<Package>/Routines/*.m      FOIA layout, generated by Stage 1
  Uncategorized/Routines/*.m           routines no #9.4 prefix claims

scripts/roundtrip/
  export.py      Stage 1: ^DIC(9.4,"C") map ▸ StudioOpenDialog ▸ write .m (%→_, ISO-8859-1)
  sync.py        Stage 3: sync-one <file.m> | sync-changed   (stage→.int ▸ Load/ImportDir "ck")
  watch.py       Stage 3: invoke sync-one on save (preferably from an `m watch` hook — §8 Stage 3 note)

Makefile  (new targets, engine-agnostic, mirroring the existing style)
  make export [EXPORT_SPEC=XU*]   bulk export + copy to host repo
  make sync                       push git-changed routines to IRIS (batch)
  make watch                      live loop: m watch (file lint/test) + sync-one (IRIS push)
  make lint / make test           extend existing targets with `m lint` / `m test` (Stage 2)

m-cli config  (e.g. m.toml / per m-dev-tools convention)   lint profile, fmt, paths = routines/
vista-iris.code-workspace  (amended)
  add a client-side "routines/" folder + the tree-sitter-m-vscode extension, beside the isfs view (§4 ⚠)

.gitattributes  (new, at routines/)   *.m  text eol=lf   per §7
```

> The exporter and bridge **must not** be added to `scripts/osehra/` (the build/install driver) —
> conflating dev-time round-trip with build-time image construction is explicitly avoided.

---

## 11. Dev Contract & Verification

| # | Check | Method | Gating? |
|---|---|---|---|
| 1 | **Export completeness** | manifest total == `StudioOpenDialog` namespace count; unmapped count reported | **yes** |
| 2 | **Round-trip fidelity** | export a routine → re-import unchanged → re-export → byte-identical to the first export (ISO-8859-1) | **yes** |
| 3 | **Incremental push** | edit one `.m`, `sync-one` → the namespace's routine source equals the file | **yes** |
| 4 | **Compile-error safety** | push a syntactically broken routine → non-zero/compile error surfaced; routine **not** silently activated | **yes** |
| 5 | **Batch push** | `make sync` over N changed files imports exactly N routines; error log lists any failure | **yes** |
| 6 | **Lint gate** | `make lint` runs the `.m` linter; a known-bad routine fails | **yes (CI)** |

Check **2** is the keystone: it proves files-as-truth is safe — that nothing is lost crossing the
`.INT` ⇄ `.m` boundary.

---

## 12. Team Distribution & Scaling

The dev tree is **~139 MB across ~33,941 `.m` files** ([§5](#5-validated-ground-truth-this-instance)).
At that size **bandwidth is a non-issue**; the cost of "every developer has the whole tree" is **file
count** (LSP/parser indexing, git index churn) and **scoping** — and, for the VA, the endpoint itself.

> **Environmental assumption (normative).** VA developers work on locked-down, government-furnished
> endpoints (GFE) that **cannot** host the toolchain, a ~34k-file tree, or a local IRIS. Therefore **all
> development is remote**: the laptop runs *only* the VS Code client and a remote extension; the dev tree,
> the `m-dev-tools` toolchain, git, and a per-developer IRIS instance run on a **remote dev host inside the
> VA's accredited boundary**. The "download everything locally" problem is therefore **moot** — nothing of
> substance is local. The scaling concerns *move to the remote host*: per-workspace file count, one IRIS
> per developer, and the license budget.

### 12.1 The remote-dev baseline (mandatory)

- The endpoint is a **thin client**: VS Code + **Remote-SSH / Remote-Tunnels** (or a dev container). The
  **VS Code Server** and all extensions (InterSystems ObjectScript, `tree-sitter-m-vscode`) run on the
  remote host *next to* the files and IRIS — so editing, LSP, lint, and compile are **local-speed**, not
  the WAN-latency-bound experience `isfs`-over-WAN would give.
- **No code on the endpoint.** Files, git history, and build artifacts stay on the remote host; git
  operations run remotely. This satisfies the locked-down posture and keeps code inside the boundary.
- **Boundary placement.** Prefer **self-hosted** remote dev — Remote-SSH to a VA dev host, or a self-hosted
  workspace platform (e.g. Coder, or `devcontainer`-based provisioning) **within the ATO boundary** — over
  public **GitHub Codespaces** when real systems/data must not leave the boundary. For *this*
  fictitious-data container, hosted Codespaces is acceptable; the VA-realistic target is self-hosted.

### 12.2 One environment per developer — not a shared instance

- Each developer gets their **own** environment = their branch's `routines/` tree **+ their own IRIS +**
  the bridge. This is required, not a preference: Stage-3 `sync` **mutates the namespace**, so a shared
  IRIS would let developers clobber one another's routines mid-test, and IRIS Community's **8-unit license**
  (~6 concurrent sessions; [v3 §9](vista-iris-container-spec-v3.md)) cannot host a team *plus* their
  listeners. Per-developer IRIS instances are independent (each its own 8-unit budget) and cheap from the
  **published GHCR image** (`make run`).
- One sufficiently large remote host can run **N such containers** (image layers are shared, so the
  marginal cost per developer is the writable layer + journals, not another ~25 GB), or a platform
  (Coder / Kubernetes) provisions one workspace-with-IRIS per developer on demand.

### 12.3 Keeping the per-workspace footprint small

Even remote, each workspace's LSP/git still index its files. Two levers shrink that:

- **Partial + sparse checkout (Lever A).** Clone with `--filter=blob:none` (blobs fetched on demand) and
  **sparse-checkout** the packages a developer owns (cone mode); the rest exist in the repo but are not
  materialized. Wrap in **Scalar** for background maintenance + a filesystem monitor when the file *count*
  (not size) is the bottleneck. Git LFS does **not** apply — these are diffable text, not large binaries.
- **Separate routines repo (Lever C).** Keep `routines/` in its **own repository** (or submodule),
  mirroring the existing `vista-m/` pattern, so container/build-only work never pulls the 34k-file tree.

### 12.4 Topology

```
 Locked-down GFE laptop                VA dev host / workspace platform (inside the boundary)
 ┌────────────────────┐    remote      ┌──────────────────────────────────────────────────────┐
 │ VS Code (client)   │    channel     │ Per-developer workspace                                │
 │  + Remote extension│◀─────────────▶ │  • routines/  (sparse: only my packages) ──┐  git     │
 │  (thin; no files)  │   (SSH/tunnel) │  • m-dev-tools m-cli + tree-sitter-m        │          │
 └────────────────────┘                │  • bridge: export / sync / m watch          ▼          │
                                        │  • own IRIS (own 8-unit license)     ┌─────────────────┐
                                        │        ▲  Stage-3 sync (.m → .int ck) │  routines repo  │
                                        │        └──────────────────────────── │   (Lever C)     │
                                        └───────────────────────────────────────┴─────────────────┘
```

> **⚠ Reconciliation (no host mount — §5/§6).** [§5](#5-validated-ground-truth-this-instance) found the
> *as-built* running container has no bind mount, so [§6](#6-architecture-overview) routes Stage-1 export
> through a copy-out. In the **dev** topology the workspace tree is **bind-mounted into the dev container**,
> so export writes straight into `routines/` and `sync` reads it in place — the copy step is a property of
> the published *runtime* image, not the developer environment.

| Concern | Lever | Effect |
|---|---|---|
| Endpoint can't host tooling/files/IRIS | **§12.1** remote-dev baseline | laptop is a thin VS Code client; everything runs remotely, in-boundary |
| Concurrent edits / license cap | **§12.2** per-dev environment | each developer owns an isolated IRIS + tree; no cross-clobber |
| 34k-file LSP/git cost per workspace | **§12.3** partial + sparse (+ Scalar) | materialize only the packages a developer owns |
| Infra-only devs shouldn't pull routines | **§12.3 / Lever C** separate repo | `routines/` is its own repo/submodule |

---

## 13. Relationship to the Image Build (v3) & `vista-m`

There are now **two `.m` trees**, with distinct roles — this must not be conflated:

| Tree | Role | Source | Lifecycle |
|---|---|---|---|
| `vista-m/` (submodule) | **Build-time input** to the image | pinned FOIA `WorldVistA/VistA-M @ b7aecb9` | immutable pin; bumped deliberately ([v3 §11.1](vista-iris-container-spec-v3.md)) |
| `routines/` (dev tree) | **Dev-time source of truth** | exported from the **running** namespace | edited continuously under git |

> **Open strategic question — how dev-tree changes reach the *image*.** The bridge pushes edits into a
> *running* instance for testing; it does **not** by itself bake them into a rebuilt image. Three
> candidate paths (to be decided, [Open Questions](#open-questions-flagged-not-resolved)): (a) make
> `routines/` the build input, replacing the `^%RI`-from-`vista-m/` path with an `ImportDir`-from-`.int`
> path; (b) promote a change set to a **KIDS build** (the VA-authoritative artifact) and install it at
> build; (c) keep `vista-m/` as the baseline and overlay the dev tree at build. v1 of the bridge does
> not require choosing — it targets the *running* instance — but the strategy must converge here.

---

## 14. Known Limitations, Deferred Items & Risks

| Item | Status | Note / direction |
|---|---|---|
| **`m-dev-tools` toolchain** | **Identified** | [`m-dev-tools`](https://github.com/m-dev-tools) `m-cli` (`m fmt`/`lint`/`test`/`coverage`/`lsp`/`watch`) on `tree-sitter-m`. Pin a version; choose lint profile(s). |
| **m-dev-tools licensing (AGPL-3.0)** | **Risk / check** | Most `m-dev-tools` repos are **AGPL-3.0** (VS Code extensions MIT). Invoking `m` as a **subprocess** in CI/`make` does not impose AGPL on this repo; **linking/embedding** would. Keep usage at the CLI boundary. |
| **Two test runtimes (YottaDB vs IRIS)** | **By design** | `m test`/`coverage` run on YottaDB (`m-test-engine`); runtime/integration on IRIS via Stage 3. Complementary, not a conflict ([§8 Stage 2 ⚠](#stage-2--filesystem-tooling-git--ci)). |
| **DB → FS mirror (Stage 4)** | **Deferred** | Needs a `%Studio.SourceControl` hook (git-source-control / Deltanji). Unnecessary while all authorship is file-first. |
| **In-IRIS edits diverge from git** | **Risk** | Without Stage 4, a routine edited inside IRIS (terminal/KIDS) is invisible to git. v1 mitigates by **convention** (edit on disk only) + periodic re-export reconciliation. |
| **Whitespace / encoding corruption** | **Risk** | M is column-sensitive; a reformatter or CRLF will break routines. Mitigated by `.gitattributes` + a no-reformat lint policy. |
| **No host bind mount** | **[Validated] constraint** | The running container mounts nothing; export copies out / push copies in. A dedicated *dev* container should bind-mount `routines/` to remove the copy step. |
| **Import as `.int` vs `.mac`** | **Open** | v1 imports `.int` (fidelity); `.mac` promotion would change routine type codebase-wide. |
| **`.mac` vs `.INT` premise** | **[Validated] correction** | Instance stores `.INT`, not `.mac` ([§5](#5-validated-ground-truth-this-instance)). |
| **Globals/data** | **Out of scope** | Routines only; `.zwr` round-trip is a possible later extension. |
| **Path to the image (§13)** | **Open strategic** | How dev-tree changes get baked into a rebuilt image is undecided. |
| **Remote dev platform + per-dev IRIS** | **Ops dependency** | The team model ([§12](#12-team-distribution--scaling)) needs an in-boundary remote dev host/platform that provisions one IRIS per developer; sizing, lifecycle, and cost are an ops concern outside this spec. |

### Open Questions (flagged, not resolved)

1. **m-cli version & lint profile.** Pin which `m-dev-tools`/`m-cli` release, and which of `m lint`'s
   8 profiles applies to legacy VistA M (modernization rules can be noisy against 1990s idioms) —
   gating vs. advisory. The tool is identified ([§3](#3-glossary)); the config is the open part.
2. **Dev-tree root name.** `routines/` (this spec's default), `r/`, or `Packages/` at repo root
   (exact FOIA mirror)? Affects tooling globs and `.gitattributes` placement.
3. **Package assignment ambiguity.** Some routine prefixes map to multiple/overlapping packages in
   `^DIC(9.4,"C")`; the longest-prefix rule must define tie-breaking, and the `Uncategorized/` bucket
   needs a review policy.
4. **Path to the image ([§13](#13-relationship-to-the-image-build-v3--vista-m)).** (a) dev tree as
   build input, (b) KIDS promotion, or (c) overlay-on-`vista-m/`?
5. **Import type ([§9](#9-round-trip-mechanics)).** Keep `.int`, or promote the codebase to `.mac`?

---

## 15. Key Technical Facts (Appendix A)

Each value verified against the live instance unless marked *(proposed)*.

| Fact | Value |
|---|---|
| Routine storage type | `.INT` (33,941 in `VISTA`); 0 `.MAC`; 0 `.m` |
| Enumeration primitive | `%RoutineMgr:StudioOpenDialog("*.INT")` |
| Source read | `%Routine.%OpenId("<NAME>.INT")` (e.g. `DIC.INT` = 5,857 lines) |
| Package map | PACKAGE file #9.4 (144 packages); `^DIC(9.4,"C")` prefix→IEN cross-reference; name = `$P(^DIC(9.4,IEN,0),"^",1)` |
| On-disk format / layout | `.m`, `routines/Packages/<Pkg>/Routines/<NAME>.m`; unmapped → `Uncategorized/` *(proposed)* |
| Filename mapping | `%` ⇄ `_`; extension `.m` |
| Encoding / EOL | ISO-8859-1 content; LF endings |
| Import primitive | stage `.m` → `<NAME>.int`; `$SYSTEM.OBJ.Load(…, "ck")` (one) / `$SYSTEM.OBJ.ImportDir(…, "*.int", "ck", , 1)` (batch) |
| Raw-`.m` import | rejected by `ImportDir`/`Load` (Err #5840) — staged to `.int` ([v3 §4](vista-iris-container-spec-v3.md)) |
| Host mount on running container | none |
| Surfaces *(proposed)* | `make export [EXPORT_SPEC=…]`, `make sync`, `make watch`; `scripts/roundtrip/{export,sync,watch}.py` |
| File-side toolchain | [`m-dev-tools`](https://github.com/m-dev-tools) `m-cli`: `m fmt` / `m lint` (36 rules, 8 profiles) / `m test` / `m coverage` / `m lsp` / `m watch`; parser `tree-sitter-m`; AGPL-3.0 (extensions MIT) |
| Test runtimes | file-side unit/coverage on **YottaDB** (`m-test-engine`); runtime/integration on **IRIS** (Stage 3) |
| Connection discipline | reused from `scripts/osehra/session.py` (license-clean release, retry, ISO-8859-1) |

---

## 16. References

- Companion specs in this repo: `vista-iris-container-spec-v3.md` (the image + runtime contract this
  bridges into) · `vista-dev-iris-tooling.md` (VA inner-loop tooling: `isfs`, XINDEX, KIDS, Deltanji) ·
  `vscode-iris-editing.md` (the existing server-side `isfs` editing guide).
- IRIS import/export: `$SYSTEM.OBJ.Load` / `ImportDir`; `%RoutineMgr` Routines query — InterSystems
  IRIS documentation.
- **File-side toolchain — [`m-dev-tools`](https://github.com/m-dev-tools)** (AGPL-3.0; extensions MIT):
  `m-cli` (`m fmt`/`lint`/`test`/`coverage`/`lsp`/`watch`), `tree-sitter-m` (M parser, 99.06% on the
  39,330-routine VistA corpus), `m-standard` (machine-readable M reference), `m-stdlib` (pure-M
  stdlib), `m-test-engine` (YottaDB test container), `tree-sitter-m-vscode` / `m-stdlib-vscode`
  (editor support), `m-dev-tools-mcp` (MCP server for AI agents incl. Claude Code).
- Filesystem M tooling precedents: server-side source-control hooks
  ([git-source-control](https://community.intersystems.com/post/git-source-control-iris)); a
  compile-on-save analog for the file-first loop
  ([YottaDB-VSCode](https://github.com/RamSailopal/YottaDB-VSCode), runs `ydbcompil` on save).
- FOIA layout reference: [`WorldVistA/VistA-M`](https://github.com/WorldVistA/VistA-M)
  (`Packages/<pkg>/Routines/*.m`).
