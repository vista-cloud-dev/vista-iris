# VistA MUMPS Development on InterSystems IRIS — Toolchain & Its Constraints

**Status:** Research brief · **Date:** 2026-05-23 · **Scope:** The development toolchain used to write, debug, analyze, test, version-control, and ship VistA's code on InterSystems IRIS — **scoped to standard MUMPS / M routines, not ObjectScript classes.** VistA is ~38,000–40,000 hand-written M routines per instance plus FileMan data dictionaries and globals; it uses essentially **none** of IRIS's object-oriented (`.cls`) feature set. This brief is deliberately distinct from the general VA DevSecOps toolchain (CodePipeline / Jenkins / SonarQube / containers) covered in [vaec-vista-hosting-general.md](vaec-vista-hosting-general.md) §6 — that pipeline governs *new* cloud-native VA apps, **not** the inner-loop workflow for VistA's MUMPS code.

---

## 0. The thesis in one paragraph

InterSystems IRIS's flagship developer experience — the class compiler, Studio Assist / rich IntelliSense, SQL projection of persisted data, the `%UnitTest` framework, refactoring, the modern source-control hooks — is built around **ObjectScript classes (`.cls`)**. ObjectScript is a *superset* of standard ISO MUMPS, and VistA lives entirely in the **subset**: tens of thousands of flat M **routines** (`.mac`/`.int`) and FileMan globals, with zero classes. The practical consequence is that VistA development on IRIS cannot ride IRIS's best tooling and instead stays close to a **routine-level, terminal-and-checker workflow** that is much closer to 1990s M development than to a modern OO IDE. The VistA community closes the gaps with (a) VistA-native M tooling (XINDEX, M-Unit, FileMan, KIDS, the programmer menu), (b) third-party MUMPS-aware tools (George James Software's **Serenji** debugger and **Deltanji** source control), and (c) the official **VS Code ObjectScript extension**, which edits routines but reserves its richest language features for classes.

---

## 1. Glossary

| Term | Meaning |
|---|---|
| **M / MUMPS** | The language + integrated global database VistA is written in. ISO/ANSI-standardized. |
| **ObjectScript** | InterSystems' M *superset* — adds classes, OO, embedded SQL, macros. VistA uses only the M-compatible core. |
| **Routine** | A flat M program unit (labels + lines). VistA = ~40k of these. Compiles `.mac` → `.int` → `.obj`. |
| **Class (`.cls`)** | ObjectScript's OO unit (`%Persistent`, methods, SQL-projected). **VistA has none.** |
| **Global** | Persistent sparse array = VistA's data (e.g. `^DPT`). Exported as `.zwr`/`.GOF`. |
| **FileMan** | VistA's DBMS over globals; "schema" lives in data dictionaries (DDs), not classes. |
| **KIDS** | Kernel Installation & Distribution System — VistA's build/patch packager (the real unit of change). |
| **NPM / FORUM** | National Patch Module on FORUM — VA's central patch registry & distribution hub. |
| **SAC** | VA's *Standards and Conventions* for M code (naming, structure, prohibitions). |
| **XINDEX** | VistA's M static-analysis / cross-reference / SAC checker. |

---

## 2. The code substrate — how VistA M code is represented

Understanding the tooling requires understanding the artifacts, because the M code lives in **two** worlds: inside an IRIS namespace (as routines + globals) and, increasingly, on a filesystem / in Git (as `.m` + `.zwr`).

| Artifact | What it is | Where |
|---|---|---|
| `.mac` | Routine **source** (may contain macros / preprocessor) | IRIS namespace |
| `.int` | **Intermediate** code (macro-expanded), compiled to object | IRIS namespace |
| `.inc` | Macro/include definitions consumed by `.mac` | IRIS namespace |
| `.obj` | Executable **object** code | IRIS namespace |
| `.m` | Filesystem form of a routine (one per routine) | Git / disk |
| `.RO` | InterSystems "routine output" export bundle | Transport / disk |
| `.zwr` / `.GOF` | Global (data) export in ZWRITE format | Git / disk |

Key point for VistA: its routines are **plain standard M** — they generally do **not** use ObjectScript class macros — so they compile straight through the `.mac→.int→.obj` pipeline as ordinary routines, with none of the class machinery. The public FOIA codebase is published as `Packages/<pkg>/Routines/*.m` plus `Packages/<pkg>/Globals/*.zwr` ([WorldVistA/VistA-M](https://github.com/WorldVistA/VistA-M)). Round-trip between the IRIS namespace and files is done with InterSystems' `%RO`/`%RI` (routine out/in) and the OSEHRA `ZGO.m`/`ZGI.m` (global out/in) plus `PackRO.py`/`UnPackRO.py` (`.RO` ↔ `.m`) ([OSEHRA VistA install docs](https://github.com/WorldVistA/VistA)).

> ObjectScript is documented as a superset compatible with the M standard (["Open M Language Compatibility"](https://docs.intersystems.com/latest/csp/docbook/DocBook.UI.Page.cls?KEY=GCOS_mcompat)); legacy MUMPS and ObjectScript can even be mixed in one `.int`/`.mac` ([IDC: mixing ObjectScript with legacy MUMPS](https://community.intersystems.com/post/guidance-mixing-object-script-legacy-mumps-same-int-and-or-mac)). VistA simply doesn't use the superset features.

---

## 3. Editing surfaces — and their limits for flat M

### 3.1 Terminal / programmer "direct mode" (the floor)
The lowest-common-denominator editor, still routinely used for quick fixes, is the IRIS terminal in programmer mode. The classic routine-buffer commands operate on a single loaded routine:
- `ZLOAD` (load routine into the buffer) → `ZPRINT` (display lines) → `ZINSERT` / argumented `ZREMOVE` (edit lines) → `ZSAVE` (save + compile) → argumentless `ZREMOVE` (unload). ([ZLOAD](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=RCOS_CZLOAD), [Routine & Debugging Commands](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=RCOS_ZCOMMANDS))

This is line-at-a-time editing — no project view, no completion. It is the historical M workflow and remains a fallback on any IRIS instance, cloud or on-prem.

### 3.2 IRIS Management Portal (web)
A browser-based server-side routine/class editor is built into the Management Portal. Adequate for small edits; not a development IDE.

### 3.3 InterSystems Studio (Windows) — **deprecated**
Studio was the long-standing Windows IDE and could edit routines (`View > View Other` toggles `.mac`↔`.int`; [Working with Routines](https://docs.intersystems.com/components/csp/docbook/DocBook.UI.Page.cls?KEY=GSTUDIO_Routines)). It was **deprecated starting with IRIS 2023.2** in favor of VS Code ([InterSystems: Studio is deprecated](https://community.intersystems.com/post/intersystems-studio-deprecated-starting-20232)). Its assist features were always class-oriented. **On the VA TRM, "Caché Studio" is `Unauthorized, Conditions Required (POA&M Required)`** — so even the legacy IDE is not a freely-usable option at VA (see §11).

### 3.4 VS Code + the InterSystems ObjectScript extension (the current default)
The [InterSystems ObjectScript extension](https://marketplace.visualstudio.com/items?itemName=intersystems-community.vscode-objectscript) is the official Studio successor. For VistA M work, the salient facts:
- It classifies **`.mac` and `.int` files as language `objectscript`**, and `.cls` as `objectscript-class` ([extension repo](https://github.com/intersystems-community/vscode-objectscript)). Routines are first-class *files*, but they are not the focus of the richest language features.
- **Server-side editing** via the `isfs` / `isfs-readonly` FileSystemProviders lets you edit routines that live in the IRIS namespace directly (multi-root workspace), respecting server-side source control — important because VistA code natively lives in the DB, not on disk ([VS Code docs: GVSCO](https://docs.intersystems.com/components/csp/docbook/DocBook.UI.Page.cls?KEY=GVSCO)).
- IntelliSense / code completion is documented around **commands, system functions, and class members**; "Go to Definition" does cover **routines and routine labels** — but completion and navigation are demonstrably richest for **classes and class members**, which VistA does not have ([IntelliSense behavior](https://code.visualstudio.com/docs/editing/intellisense), extension docs). There is no meaningful refactoring for flat M.

**VA TRM status:** This is the one *modern* editor explicitly approved for VistA/IRIS work — the **InterSystems ObjectScript Extension Pack within VS Code** is **`Authorized w/ Constraints`** ([TRM tid 17070](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=17070), decision 2025-11-20; constraints include: no Unity without a POA&M, FIPS 140-2/140-3 crypto for PHI/PII, local ISSO review per VA Handbook 6500, and supervisor-approved + malware-scanned install). See §11.

**Net:** VS Code is a real upgrade for VistA developers (project view, server browse/edit, Git), but it does **not** turn flat-M development into the class-grade experience IRIS gives ObjectScript.

---

## 4. Debugging M routines

### 4.1 Native command-line debugging
IRIS provides routine-level debugging from the terminal: `BREAK`, and especially **`ZBREAK`** to set breakpoints at code locations and **watchpoints** on local variables, with single-step actions; `ZWRITE` dumps the symbol table; the error trap surfaces faults. ([Command-Line Routine Debugging](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GCOS_debug), [ZBREAK](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=RCOS_czbreak)) This works on any routine but is austere.

### 4.2 VS Code ObjectScript debugger
The extension supports launch/attach debugging of ObjectScript ([Run and Debug](https://docs.intersystems.com/components/csp/docbook/DocBook.UI.Page.cls?KEY=GVSCO_debug)). It functions for routines but, like the rest of the extension, is tuned to the class/method model.

### 4.3 Serenji (George James Software) — the MUMPS-aware debugger that fills the gap
**Serenji** is a 20-year-old, MUMPS/ObjectScript-aware editor + **step debugger** that operates **directly on routine-level code** in IRIS / Caché / Ensemble / HealthShare, now delivered as a [VS Code extension](https://marketplace.visualstudio.com/items?itemName=georgejames.vscode-serenji). It is widely used precisely because it debugs **flat M routines** (not just classes): step in/out/over a command at a time, set breakpoints and watchpoints dynamically, **view and modify variables at each stack level**, and jump straight to the source line where an error originated ([georgejames.com/serenji](https://www.georgejames.com/serenji), [IDC announcement](https://community.intersystems.com/post/serenji-debugger-and-editor-now-available-visual-studio-code)). The file explorer/editor are free; the **debugger requires a license (from £395 / $495 / €495)**. For VistA shops, Serenji is the de-facto answer to "how do I step-debug 40,000 M routines comfortably."

> **VA TRM status — important:** No Serenji entry was found on the One-VA TRM as of this check (v26.1, May 2026; see §11). Because VA policy only permits TRM-assessed technology on its systems, Serenji is **not an off-the-shelf option today** — using it would first require sponsoring a TRM new-technology assessment.

---

## 5. Static analysis & code quality — XINDEX, not an IRIS feature

VistA's "linter" is **XINDEX** (a.k.a. `%INDEX`; run via `D ^XINDEX` or the **`%Index of Routines` [XUINDEX]** programmer option). It is a VistA-aware **cross-referencer + code checker** that statically analyzes routines, builds, installs, or whole packages and flags violations against the **1995 ANSI M Standard** and the **VA SAC**, in categories **F**atal / **W**arning / **S**tandards / **I**nformational, plus `$TEXT` lines requiring manual review ([hardhats XINDEX intro](https://www.hardhats.org/tools/xindex/xindex_intro.html), [WorldVistA/XINDEX](https://github.com/WorldVistA/XINDEX)). Critically, it can index **all components of a KIDS build** (routines, options, templates, DDs), not just routines.

> IRIS provides **no modern static-analysis equivalent for pure M** comparable to XINDEX; its quality/assist tooling targets ObjectScript classes. So VistA continues to rely on its own ~30-year-old, SAC-aware checker — and the general VA SAST tools (SonarQube/Fortify in [vaec-vista-hosting-general.md](vaec-vista-hosting-general.md) §6) do not understand M either. This is one of the clearest "the cloud changed nothing here" facts in the toolchain.

---

## 6. Testing — M-Unit, not %UnitTest

VistA's unit-test framework is **M-Unit** (originally `XTMUNIT`, authored by Joel L. Ivey at the VA, 2003–2012; re-released to OSEHRA in the **`%ut`** namespace with contributions from Sam Habiel and others; Apache-2 licensed). It runs at the command line or via a GUI client, structured as `STARTUP → SETUP → test+assert → TEARDOWN → SHUTDOWN`, using transactions so each test can roll back ([joelivey/M-Unit](https://github.com/joelivey/M-Unit)). It is distributed as a KIDS build (`MASH`/MUnit) for the OSEHRA test harness ([WorldVistA/VistA Testing/Setup](https://github.com/WorldVistA/VistA)).

This is deliberately **separate** from IRIS's native **`%UnitTest`** framework, which is class-based — another instance of VistA needing an M-native tool because the IRIS-native one assumes classes.

---

## 7. Source control & change management — KIDS vs Git vs Deltanji

### 7.1 The native unit of change is the KIDS build / patch — not a commit
VistA's real version-control system is its **patch stream**:
1. A developer bundles routines **and** non-routine components (FileMan DDs, options, templates, protocols, security keys…) into a **KIDS build**.
2. KIDS produces a **transport global**, exported as a **distribution** (or **PackMan** message). (`DIFROM` is obsolete — KIDS replaced it.) ([KIDS User Guide](https://www.va.gov/vdl/documents/Infrastructure/Kernel/krn_8_0_sm_kids_ug.pdf))
3. The patch is registered in the **National Patch Module (NPM)** on **FORUM**, which assigns the patch number and stores each version; routine **checksums** move to the ROUTINE (#9.8) file as the "gold" integrity reference.
4. Sites receive it over **MailMan**, verify checksums, and install in **sequence (SEQ#) order** ([VistApedia: Patching Instructions](https://vistapedia.net/index.php/Patching_Instructions), [hardhats: Updating a VistA System](https://www.hardhats.org/projects/New/UpdatingAVistASystem.html)).

Naming/structure is governed by the **SAC**: a namespace is a **2–4 alpha-character prefix assigned by the DBA**; routine line 1 carries `name;site/programmer - description;date` and line 2 the version + applied-patch list ([M Programming SAC](https://foia-vista.worldvista.org/Policies/M_Programming_SAC_20180403.pdf), [SAC.rst](https://github.com/OSEHRA/VistA/blob/master/Documentation/Standards/SAC.rst)).

### 7.2 Git — bolted on, with an impedance mismatch
Modern VistA uses Git via OSEHRA/WorldVistA: each monthly **FOIA** release is exported as routines (`.m`) + globals (`.zwr`) to [WorldVistA/VistA-M](https://github.com/WorldVistA/VistA-M). The mismatch:
- IRIS keeps "the code" **inside a namespace** (routines + globals); Git wants **files**, so you must export/import (`%RO`/`%RI`, `ZGO`/`ZGI`, `PackRO`/`UnPackRO`) to round-trip — whereas **GT.M/YottaDB store routines as files natively**, making their Git story simpler ([hardhats: Install VistA on GT.M/YottaDB](https://www.hardhats.org/projects/New/InstallVistAOnGTM.html), [Hardhats: VISTA/M version control: GitHub vs ??](https://groups.google.com/g/Hardhats/c/JoNpq91df7g)).
- A KIDS build carries **more than routines** (DDs, options, templates as global data). A Git repo of `.m` files alone is an **incomplete** representation of a patch — the data-dictionary and config changes ride in globals.

### 7.3 InterSystems source-control hooks + Deltanji
IRIS exposes server-side source-control hooks (`%Studio.SourceControl`) that VS Code/Studio honor. The most VistA-relevant commercial option is **Deltanji** (George James Software): an IRIS-aware source-control / change-management system that "understands the internal workings of IRIS," handles routines/classes/interop productions, keeps a full audit trail with configurable workflow, and integrates with VS Code, Studio, the Management Portal, and Interop Portal ([georgejames.com/deltanji](https://georgejames.com/deltanji/)). It is positioned as a companion or alternative to Git that copes with IRIS's database-resident code model — i.e., it solves §7.2's impedance mismatch from the IRIS side rather than the file side.

> **VA TRM status — important:** Like Serenji, **no Deltanji entry was found on the One-VA TRM** as of this check (v26.1, May 2026; see §11), so it is not a currently approved VA option without a TRM assessment. VistA's TRM-sanctioned change-management story remains **KIDS / NPM-on-FORUM** (§7.1) plus VA's general enterprise GitHub standard.

---

## 8. The end-to-end VistA-native developer loop

```
                ┌─────────────────────── inner loop (per routine) ───────────────────────┐
 DBA assigns →  edit M routine            →  static check     →  unit test
 namespace      (VS Code + isfs / Serenji /   (XINDEX:            (M-Unit %ut:
 (2–4 alpha)     terminal ZLOAD/ZSAVE)         ^XINDEX / XUINDEX)   STARTUP→assert→TEARDOWN)
                + FileMan DD edits for data
                └─────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
        bundle into KIDS build  →  transport global / PackMan  →  NPM on FORUM (patch #, checksums)
                                              │
                                              ▼
                      MailMan distribution  →  site verifies checksums  →  install in SEQ# order
```

Source control overlay (optional/parallel): Git via OSEHRA export (`.m` + `.zwr`) and/or **Deltanji** for IRIS-aware change management. CI overlay (emerging): run XINDEX + M-Unit against exported routines in a pipeline — but the **authoritative artifact remains the KIDS patch**, not the Git commit.

---

## 9. What the cloud / IRIS migration changes — and what it doesn't

**Unchanged (the M inner loop):** Routines, FileMan, KIDS, NPM/FORUM, SAC, **XINDEX**, **M-Unit** — all identical whether VistA runs on-prem, on Caché, or on IRIS in AWS GovCloud. Lifting VistA to the cloud (see [vaec-vista-hosting-general.md](vaec-vista-hosting-general.md) §3) was a **rehost**; it did not modernize the development model.

**Added by IRIS / cloud:**
- **VS Code-on-IRIS** with `isfs` server-side editing replaces deprecated Studio.
- **Containerized dev instances** (cf. [vista-iris-container-spec.md](vista-iris-container-spec.md)) make a disposable, reproducible VistA-on-IRIS available to each developer.
- **Git overlays** via OSEHRA export and **Deltanji** for IRIS-aware change control.
- **Serenji** debugging against cloud IRIS instances.

**Still missing (the structural constraint):** Because VistA is flat M and not ObjectScript classes, IRIS's *best* tooling — class compiler, rich IntelliSense/refactoring, SQL projection, `%UnitTest`, class-grade quality analysis — **does not apply**. Modernizing *that* would require re-expressing VistA in classes (an EHR-rewrite-scale effort), which is exactly what the Oracle/Cerner EHRM replacement is for, not the IRIS migration.

---

## 10. Capability matrix — IRIS feature vs VistA's M routines

| IRIS / ObjectScript capability | Built for | Available to VistA's 40k M routines? |
|---|---|---|
| Class compiler, `.cls`, `%Persistent` | OO classes | **No** — VistA has no classes |
| SQL projection of stored data | `%Persistent` classes | **No** — data is FileMan globals (needs separate mapping for SQL) |
| Rich Studio Assist / IntelliSense / refactoring | class members | **Partial** — routine/label go-to only; weak completion; no refactor |
| `%UnitTest` framework | class-based tests | **Not used** — VistA uses **M-Unit** |
| Modern SAST / code-quality assist | ObjectScript classes | **No** — VistA uses **XINDEX** (SAC + ANSI M) |
| Routine editing (VS Code `isfs`, Mgmt Portal, terminal) | routines & classes | **Yes** |
| Step debugging (`ZBREAK`, VS Code, **Serenji**) | routines & classes | **Yes** (routine-level; Serenji is the comfortable option) |
| Source-control hooks / **Deltanji** | routines & classes | **Yes**, but the authoritative artifact is the **KIDS patch** |

---

## 11. VA TRM approval status — what's actually usable at VA

VA policy requires that any technology deployed on VA systems be assessed and listed in the **One-VA Technical Reference Model (TRM)**. A product **absent** from the TRM is effectively *unapproved*: it must clear a TRM "new technology" request (plus any POA&M / ISSO review) before it can be used. That governance gate — not technical merit — decides whether the tools in this brief are real options today.

| Tool (referenced in this brief) | One-VA TRM status (checked May 2026) | TRM entry |
|---|---|---|
| InterSystems **IRIS for Health** (runtime) | `Authorized w/ Constraints` (FIPS, baselines, patching) | [tid 14907](https://www.oit.va.gov/services/trm/ToolPage.aspx?tid=14907) |
| InterSystems **Caché** (legacy runtime) | `Unauthorized, Conditions Required (POA&M)` — being divested for IRIS | [tid 10](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=10) |
| **InterSystems ObjectScript Extension Pack (VS Code)** — §3.4 | **`Authorized w/ Constraints`** (decision 2025-11-20) | [tid 17070](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=17070) |
| InterSystems **Studio / "Caché Studio"** — §3.3 | `Unauthorized, Conditions Required (POA&M)` | (noted via Atelier entry) |
| **Atelier** (legacy Eclipse IDE) | Listed (vendor-deprecated) | [tid 11543](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=11543) |
| **XINDEX, M-Unit, KIDS, FileMan** (VA-authored, part of VistA itself) | Inherent to VistA — not separate TRM tool entries | — |
| **Serenji** (George James Software) — §4.3 | **No TRM entry found** → unapproved without assessment | — |
| **Deltanji** (George James Software) — §7.3 | **No TRM entry found** → unapproved without assessment | — |

**Bottom line for VistA M development at VA:**
1. The realistic, **already-approved** modern toolchain is **VS Code + the InterSystems ObjectScript Extension Pack** (`Authorized w/ Constraints`) against **IRIS for Health**, combined with VA's own M-native tooling — **XINDEX, M-Unit, KIDS, FileMan** — which is part of VistA itself and therefore inherently in scope.
2. The commercial George James Software MUMPS tools (**Serenji**'s routine-level step debugger, **Deltanji**'s IRIS-aware source control) are excellent technical fits for VistA's gaps, but **as of this check they are not on the TRM** and so cannot be deployed on VA systems without a sponsored TRM assessment — which would most likely land them as `Authorized w/ Constraints` or behind a POA&M, exactly as happened with the ObjectScript extension and IRIS.
3. Even legacy **InterSystems Studio** is not a free pass (POA&M-required), which aligns with both the vendor deprecation (§3.3) and VA steering developers to VS Code.

> **Confidence / caveat:** The One-VA TRM's public search and external indexing are imperfect. "No entry found" here reflects site-restricted (`oit.va.gov`) searches **and** the TRM's own fuzzy search returning only alphabetical neighbors (e.g., *Delinea*, *Desmond*) rather than a Serenji/Deltanji match. A direct query in the live TRM, or a note to OIT/the local ISSO, would confirm definitively — and TRM status changes over time, so re-check before relying on it.

---

## 12. References

**InterSystems IRIS — routines, editing, debugging**
- [Working with Routines and Include Files (Studio)](https://docs.intersystems.com/components/csp/docbook/DocBook.UI.Page.cls?KEY=GSTUDIO_Routines)
- [Macros and Include Files (ObjectScript)](https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=GCOS_MACROS)
- [Open M Language Compatibility (ObjectScript ⊃ ISO M)](https://docs.intersystems.com/latest/csp/docbook/DocBook.UI.Page.cls?KEY=GCOS_mcompat)
- [Mixing ObjectScript with legacy MUMPS in one .INT/.MAC](https://community.intersystems.com/post/guidance-mixing-object-script-legacy-mumps-same-int-and-or-mac)
- [Command-Line Routine Debugging](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GCOS_debug) · [ZBREAK](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=RCOS_czbreak) · [ZLOAD](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=RCOS_CZLOAD) · [Routine & Debugging Commands](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=RCOS_ZCOMMANDS)
- [InterSystems Studio is deprecated, starting with 2023.2](https://community.intersystems.com/post/intersystems-studio-deprecated-starting-20232)

**VS Code ObjectScript extension**
- [Marketplace listing](https://marketplace.visualstudio.com/items?itemName=intersystems-community.vscode-objectscript) · [GitHub repo](https://github.com/intersystems-community/vscode-objectscript) · [Docs: VS Code as IDE (GVSCO)](https://docs.intersystems.com/components/csp/docbook/DocBook.UI.Page.cls?KEY=GVSCO) · [Run & Debug](https://docs.intersystems.com/components/csp/docbook/DocBook.UI.Page.cls?KEY=GVSCO_debug)

**Third-party MUMPS-aware tools — George James Software**
- [Serenji (editor + debugger)](https://www.georgejames.com/serenji) · [Serenji on VS Marketplace](https://marketplace.visualstudio.com/items?itemName=georgejames.vscode-serenji) · [IDC: Serenji for VS Code](https://community.intersystems.com/post/serenji-debugger-and-editor-now-available-visual-studio-code)
- [Deltanji source control](https://georgejames.com/deltanji/)

**VistA-native M tooling & workflow**
- [XINDEX intro (hardhats)](https://www.hardhats.org/tools/xindex/xindex_intro.html) · [WorldVistA/XINDEX](https://github.com/WorldVistA/XINDEX)
- [M-Unit (joelivey/M-Unit)](https://github.com/joelivey/M-Unit)
- [KIDS User Guide (Kernel 8.0)](https://www.va.gov/vdl/documents/Infrastructure/Kernel/krn_8_0_sm_kids_ug.pdf) · [Patching Instructions (VistApedia)](https://vistapedia.net/index.php/Patching_Instructions) · [Updating a VistA System (hardhats)](https://www.hardhats.org/projects/New/UpdatingAVistASystem.html)
- [M Programming Standards & Conventions (SAC, 2018)](https://foia-vista.worldvista.org/Policies/M_Programming_SAC_20180403.pdf) · [SAC.rst (OSEHRA)](https://github.com/OSEHRA/VistA/blob/master/Documentation/Standards/SAC.rst)

**VistA source on Git / round-trip**
- [WorldVistA/VistA-M (FOIA routines + globals)](https://github.com/WorldVistA/VistA-M) · [WorldVistA/VistA (build/test automation)](https://github.com/WorldVistA/VistA) · [Install VistA on GT.M/YottaDB](https://www.hardhats.org/projects/New/InstallVistAOnGTM.html) · [Hardhats: VISTA/M version control thread](https://groups.google.com/g/Hardhats/c/JoNpq91df7g)
