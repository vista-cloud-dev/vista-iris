# VA TRM — MUMPS / M Tools Survey

**Status:** Research brief · **Date:** 2026-05-23 · **Source:** [VA Technical Reference Model (TRM)](https://www.oit.va.gov/services/trm/), entries surveyed against TRM v26.x · **Scope:** Every MUMPS/M-related entry on the VA TRM — the M language standard itself, all M database/runtime implementations, the ObjectScript language layer, the M/ObjectScript development tooling (IDEs, editors, debuggers-by-proxy), and the connectivity/interoperability platforms built directly on the M stack. Pure VistA application artifacts (FileMan, KIDS, XINDEX) are out of scope here — they are covered in [vista-dev-iris-tooling.md](vista-dev-iris-tooling.md).

> ⚠️ **TRM statuses are quarterly and volatile.** Every status below is captured with its TRM **decision date**. The TRM re-evaluates each entry every quarter, and the dominant theme of this survey — the planned **divestment of the entire Caché family in favor of InterSystems IRIS** — means most legacy entries flipped from "Authorized w/ Constraints" to "Unauthorized, Conditions Required (Divest)" at the **Q1 2026** boundary. Always re-check the live TRM page (linked per row) before making a procurement or architecture decision.

---

## Table of Contents

1. [Executive summary](#1-executive-summary)
2. [Methodology & scope](#2-methodology--scope)
3. [Glossary](#3-glossary)
4. [Master summary table — all MUMPS tools on the TRM](#4-master-summary-table--all-mumps-tools-on-the-trm)
   - [Status key — VA TRM decision colors](#status-key--va-trm-decision-colors)
5. [Detailed entries](#5-detailed-entries)
   - 5.1 [The standard: MUMPS / M](#51-the-standard-mumps--m)
   - 5.2 [M database & runtime implementations](#52-m-database--runtime-implementations)
     - [FIS-GT.M](#fis-gtm)
     - [InterSystems Caché](#intersystems-caché)
     - [InterSystems IRIS for Health](#intersystems-iris-for-health)
   - 5.3 [The language layer: Caché ObjectScript](#53-the-language-layer-caché-objectscript)
   - 5.4 [Development tools & IDEs](#54-development-tools--ides)
     - [Cache Studio](#cache-studio)
     - [Atelier (Eclipse plug-in)](#atelier-eclipse-plug-in)
     - [InterSystems ObjectScript Extension Pack for VS Code](#intersystems-objectscript-extension-pack-for-vs-code)
   - 5.5 [Caché data-access & web components](#55-caché-data-access--web-components)
     - [Cache Server Pages (CSP)](#cache-server-pages-csp)
     - [Cache Objects](#cache-objects)
     - [Cache ODBC Driver](#cache-odbc-driver)
     - [Cache Management Portal & Cache Zen](#cache-management-portal--cache-zen)
   - 5.6 [Interoperability & integration platforms on the M stack](#56-interoperability--integration-platforms-on-the-m-stack)
     - [InterSystems Ensemble](#intersystems-ensemble)
     - [HealthShare](#healthshare)
     - [InterSystems API Manager (IAM)](#intersystems-api-manager-iam)
6. [Notable absence: YottaDB](#6-notable-absence-yottadb)
7. [Cross-cutting themes](#7-cross-cutting-themes)
8. [Vendor & authoritative documentation links](#8-vendor--authoritative-documentation-links)
9. [How to verify / re-run this survey](#9-how-to-verify--re-run-this-survey)

---

## 1. Executive summary

The VA TRM treats "MUMPS tooling" as essentially two lineages plus one open-source outlier:

1. **The InterSystems lineage** — by far the largest. It spans the legacy **Caché** platform and its constellation of sub-components (ObjectScript, Studio, CSP, Objects, ODBC driver, Management Portal, Zen), the **Ensemble** integration engine and **HealthShare** interoperability suite that sit on top of Caché, the modern successor **InterSystems IRIS for Health**, and the current-generation developer tooling (the **VS Code ObjectScript Extension Pack**, and the now-retired **Atelier** Eclipse plug-in) plus the **API Manager (IAM)**. This is the stack VistA actually runs on at the VA.
2. **The FIS lineage** — **FIS-GT.M**, an open-source M database/runtime, the historical free alternative used by the open-source VistA community (OSEHRA/WorldVistA).
3. **The bare standard** — **MUMPS / M** itself, listed as an ISO/ANSI language standard with no associated vendor.

**The single most important finding:** the TRM is actively steering the VA *off* Caché and onto IRIS. Caché and every component that depends on it (ObjectScript, Studio, CSP, Objects, ODBC, Ensemble) are on a **divestment trajectory that took effect at Q1 2026** — they moved from "Authorized w/ Constraints (POA&M)" to "Unauthorized, Conditions Required." The only entries with a clean forward runway are **IRIS for Health** (authorized through 2026+), **HealthShare**, the **VS Code ObjectScript Extension Pack**, and **IAM** (authorized through CY2027). FIS-GT.M followed the same divestment cliff at Q1 2026.

**Notable absence:** **YottaDB** — the actively maintained open-source fork/successor of GT.M — has **no dedicated TRM entry**, despite being the modern home of the GT.M codebase.

---

## 2. Methodology & scope

- **Population.** Every TRM entry whose subject is (a) the M language, (b) an M database/runtime, (c) the ObjectScript superset, (d) an M/ObjectScript development tool, or (e) a platform whose runtime *is* the M database (Ensemble, HealthShare, IAM). Entries were located by searching the public TRM site and following the InterSystems product family cross-references on the Caché entry.
- **Per-entry data captured.** Description, vendor/standards-body, current TRM decision + decision date, latest version, key constraints, and use case — read directly from each TRM `ToolPage`/`StandardPage`.
- **Out of scope.** VistA application-layer tooling (FileMan, KIDS, XINDEX, M-Unit, the programmer menu) and third-party M tools that are *not* on the TRM (e.g. George James Software's Serenji/Deltanji) — those live in [vista-dev-iris-tooling.md](vista-dev-iris-tooling.md).
- **Provenance flag.** Entries marked **✔ fetched** below were read field-by-field from the TRM page. Entries marked **◑ listed** were confirmed present on the TRM (and their status inferred from the parent Caché family decision matrix) but not separately fetched field-by-field; their TRM links are provided for direct verification.

---

## 3. Glossary

| Term | Meaning |
|---|---|
| **MUMPS / M** | *Massachusetts General Hospital Utility Multi-Programming System.* A procedural language with a built-in hierarchical key-value (global) database and ACID transactions. The substrate of VistA. |
| **ObjectScript** | InterSystems' proprietary **superset** of standard M — adds classes, OO, embedded SQL, and a macro preprocessor while remaining M-compatible. |
| **Global** | A persistent, sparse, multi-dimensional array — the native M data structure and on-disk format. |
| **POA&M** | *Plan of Action & Milestones.* A remediation/risk-acceptance document the VA requires to keep using a constrained or otherwise-unauthorized technology. |
| **TRM decision** | The authorization verdict: *Authorized*, *Authorized w/ Constraints*, *Authorized w/ Constraints (POA&M)*, or *Unauthorized, Conditions Required* (often annotated **Divest**). |
| **Divest** | TRM signal that the technology is being phased out; new use is discouraged and existing use must migrate. |
| **ESCCB** | *Enterprise Security Change Control Board* — reviews external connections. |
| **VistA** | *Veterans Health Information Systems and Technology Architecture* — the VA's M-based EHR; the reason all of this is on the TRM. |

---

## 4. Master summary table — all MUMPS tools on the TRM

| # | Tool (TRM entry) | Type | Vendor / body | Latest ver. | TRM status | Core features | Primary VA use case | TRM link |
|---|---|---|---|---|:---:|---|---|---|
| 1 | **MUMPS / M** | Language + DB **standard** | ISO / ANSI (M Dev. Committee) | ISO/IEC 11756:1999; ANSI X11.1-1995 | ⚪ ISO · 🔘→🟨 ANSI | Integrated key-value global DB; ACID transactions; data access via subscripted arrays | The language VistA is written in | [tid=6402](https://www.oit.va.gov/Services/TRM/StandardPage.aspx?tid=6402) |
| 2 | **FIS-GT.M** | M database/runtime (**open source**) | FIS (Greystone Technology M) | 7.0.x (2021-02-12) | 🔘→🟨 | ACID M engine; embedded global DB; runs on RHEL; free/OSS | Open-source VistA hosting (OSEHRA/WorldVistA); low VA-network footprint | [tid=6632](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=6632) |
| 3 | **InterSystems Caché** | M-based object+relational DBMS / RAD platform | InterSystems | 2018.1.x | 🔘→🟥 | Object + relational DBMS on M globals; rapid app dev; web/mobile | Production VistA database engine (legacy) | [tid=10](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=10) |
| 4 | **InterSystems IRIS for Health** | Modern M-based data platform (Caché successor) | InterSystems | 2024.x / 2025.1.x | 🔘 | Data mgmt + app dev + FHIR/HL7/DICOM interoperability + analytics; on-prem & cloud | The forward target for VistA modernization | [tid=14907](https://www.oit.va.gov/services/trm/ToolPage.aspx?tid=14907) |
| 5 | **Caché ObjectScript** | Programming language (M superset) | InterSystems | 2018.1.9 | 🔘→🟥 | OO + procedural; compiles to Caché VM; cross-platform; "Associated Standard: MUMPS" | Server-side logic, routines, CSP scripting in Caché | [tid=6393](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=6393) |
| 6 | **Cache Studio** | IDE for M / ObjectScript | InterSystems | 2018.1.9 (2024-02-14) | 🔘→🟥 | Syntax coloring, code checking, graphical debugger, project view; M + ObjectScript + C++/Python/web | Classic VistA/Caché development desktop (Windows) | [tid=6394](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=6394) |
| 7 | **Atelier** | Eclipse-based IDE plug-in | InterSystems | 1.3.x (2018-09-17) | 🔘→🟨 | Eclipse plug-in; source storage, client/server sync, code formatting | Superseded transitional IDE for InterSystems dev *(vendor EOL)* | [tid=11543](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=11543) |
| 8 | **InterSystems ObjectScript Extension Pack for VS Code** | Modern editor extension | InterSystems | 1.0.x (1.0.3) | 🔘 | Connects VS Code to an InterSystems server; edit/compile ObjectScript & M routines; Win/macOS/RHEL | Current-gen VistA/IRIS developer experience | [tid=17070](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=17070) |
| 9 | **Cache Server Pages (CSP)** | Server-side web framework | InterSystems | 2018.1.10 | 🔘→🟥 | Dynamic web pages from Caché data; requires Caché DB + IIS/Apache | Web front-ends over VistA/Caché data (legacy) | [tid=6386](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=6386) |
| 10 | **Cache Objects** | Object-access layer / bindings | InterSystems | (Caché-family) | 🔘→🟥 | Object projections/bindings (Java/.NET/etc.) over Caché data | Object access to VistA/Caché globals | [tid=171](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=171) |
| 11 | **Cache ODBC Driver** | ODBC connectivity driver | InterSystems | (Caché-family) | 🔘→🟥 | ODBC access to Caché relational projection of M data | SQL/reporting access to VistA data | [tid=5590](https://www.oit.va.gov/services/trm/ToolPage.aspx?tid=5590) |
| 12 | **Cache Management Portal** | Web admin console | InterSystems | (Caché-family) | 🔘→🟥 | Browser-based config/monitoring/management of a Caché instance | Operating a VistA/Caché instance | (sub-component of [tid=10](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=10)) |
| 13 | **Cache Zen** | Web UI / AJAX framework | InterSystems | (Caché-family) | 🔘→🟥 | Object-oriented, component-based web-app framework on CSP | Rich web UIs over Caché (legacy) | (sub-component of [tid=10](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=10)) |
| 14 | **InterSystems Ensemble** | ESB / SOA integration engine | InterSystems | 2018.1.x | 🔘→🟥 | ESB/SOA, BPM, business rules, data transforms, event processing; auto-logs messages | Interface engine over the VistA/Caché stack (legacy) | [tid=6450](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=6450) |
| 15 | **HealthShare** | Health interoperability & analytics suite | InterSystems | 2025.1.x (2025-03-27) | 🔘 | Aggregates clinical/demographic data into patient-centric records; HIE standards | Cross-facility health information exchange | [tid=8686](https://www.oit.va.gov/services/trm/ToolPage.aspx?tid=8686) |
| 16 | **InterSystems API Manager (IAM)** | API gateway / management | InterSystems | 3.10.0.2 (2025-05-20) | 🔘 | Centralized gateway for HTTP/API traffic to/from IRIS; monitoring & throttling (Kong-based) | API governance for IRIS-based VA apps | [tid=16536](https://oit.va.gov/Services/TRM/ToolPage.aspx?tid=16536) |
| — | **YottaDB** | M database/runtime (open source) | YottaDB LLC | — | — | GT.M-compatible OSS M engine; modern fork | (none — not assessed) | — |

### Status key — VA TRM decision colors

Each status is a **single glyph whose *shape* is the verdict and *color* is the condition**: a **circle (○) = Authorized**, a **box (□) = Unauthorized**. An arrow — e.g. 🔘→🟥 — marks an entry transitioning across the TRM timeline; the **right-hand glyph is the current/effective decision** (as of ~May 2026, past the Q1 2026 boundary), the left is the prior state detailed in §5.

- **Circles — Authorized (2):** ⚪ **Authorized** · 🔘 **Authorized w/ constraints**.
- **Boxes — Unauthorized (4):** ⬛ **flat, unconditional prohibition**, or one of **three "Conditions Required"** colors below, ordered by **severity**.
- A bare **—** = no TRM entry (not assessed).

| Severity | Box | Condition `[id]` | One word | Why it ranks here |
|:---:|:---:|---|---|---|
| most severe | 🟥 | Divest `[b]` | **Retiring** | Being phased out; new use barred, existing use must migrate off. No forward runway — terminal. |
| medium | 🟧 | Under evaluation `[c]` | **Piloting** | Controlled testing only; *not available to the general population*; outcome still pending. |
| least severe | 🟨 | POA&M review `[a]` | **Remediate** | Usable **now** via a POA&M signed by the AODR/AO — a defined, achievable path to use. |

> **Glyph note.** Shape carries the verdict (circle = authorized, box = unauthorized), so the two verdicts are distinguishable without color; color carries the condition/severity. The **Decision** column restates each status in words, so the encoding is never shape- or color-only. These are plain emoji — they render in terminals, on GitHub, and in VS Code alike (no image assets). One detail: GitHub-flavored Markdown has no true gray-circle emoji, so **constraints** uses 🔘 (the radio-button emoji) as the gray *circle* — it keeps the authorized = circle shape and avoids reusing a color.

| Glyph | Shape · color | Decision | Definition |
|:---:|---|---|---|
| ⚪ | circle · white | **Authorized** | The technology/standard has been authorized for use. |
| 🔘 | circle · gray | **Authorized w/ Constraints** | The technology/standard can be used within the specified constraints located below the decision matrix in the footnote [1] and on the General tab. |
| ⬛ | box · black | **Unauthorized** | The technology/standard is not (currently) permitted to be used under any circumstances. |
| 🟨 | box · yellow | **Unauthorized, Conditions Required `[a]` — POA&M review (Remediate)** | This technology or standard can be used only if a POA&M review is conducted and signed by the Authorizing Official Designated Representative (AODR) as designated by the Authorizing Official (AO) or designee and, based upon a recommendation from the POA&M Compliance Enforcement, has been granted to the project team or organization that wishes to use the technology. *(Least severe — a defined, achievable path to use.)* |
| 🟧 | box · orange | **Unauthorized, Conditions Required `[c]` — Under evaluation (Piloting)** | The period of time this technology is currently being evaluated, reviewed, and tested in controlled environments. Use of this technology is strictly controlled and not available for use within the general population. If a customer would like to use this technology, please work with your local or Regional OI&T office and contact the appropriate evaluation office displayed in the notes below the decision matrix. *(Medium severity.)* |
| 🟥 | box · red | **Unauthorized, Conditions Required `[b]` — Divest (Retiring)** | VA has decided to divest itself of the use of the technology/standard. As a result, all projects currently utilizing the technology/standard must plan to eliminate their use of the technology/standard. Additional information on when the entry is projected to become unauthorized may be found on the Decision tab for the specific entry. *(Most severe — terminal, no forward runway.)* |

> **Mapping note.** The glyph per row reflects this brief's mapping of each entry's captured TRM decision language to the six-status scheme: the **Caché family** (Caché, ObjectScript, Studio, CSP, Objects, ODBC Driver, Management Portal, Zen) and **Ensemble** are explicitly **Divest** 🟥; **FIS-GT.M**, **MUMPS (ANSI edition)**, and **Atelier** carry the POA&M-only **yellow `[a]`** 🟨 flavor; the authorized-with-constraints entries (IRIS for Health, the VS Code Extension Pack, HealthShare, IAM) and the **ISO** edition of MUMPS are circles (⚪ / 🔘). The flat **Unauthorized** ⬛ and **Under evaluation** 🟧 statuses are defined for completeness but are not currently assigned to any entry here; **YottaDB** has no TRM entry (shown as **—**). **Re-verify on the live TRM Decision tab before relying on any status.**

---

## 5. Detailed entries

### 5.1 The standard: MUMPS / M
**✔ fetched · TRM [tid=6402](https://www.oit.va.gov/Services/TRM/StandardPage.aspx?tid=6402)**

- **What it is.** MUMPS (a.k.a. **M**) is a programming language with a built-in **key-value/global database** and **ACID** transaction processing. Disk storage is reached transparently through subscripted symbolic variables; the database is woven into the language rather than bolted on. The TRM lists it as a *standard* (no vendor) governed by ISO.
- **TRM status (as of 01/15/2026).** Two standardized editions are tracked separately:
  - **ISO/IEC 11756:1999** — **Authorized** through the displayed quarters (2025–2027).
  - **ANSI X11.1-1995** — **Authorized w/ Constraints (POA&M)** through Q1 2026, then transitions to unauthorized/conditions-required.
- **Constraints.** Compliance with VA Handbooks 6102 & 6500; VA Directives 6004, 6513, 6517; and NIST/FIPS. Sensitive data must be protected per VA regulation.
- **Stated risks.** "No recent development activity on this industry standard," and the language "lacks object-oriented and functional programming capabilities."
- **Related tech.** No comparable/associated standards or implementing technologies are cross-linked from this entry (the implementations are listed as their own product entries — see below).
- **Use case.** It is the language VistA is written in; the TRM entry exists to govern the *standard* the VA's M code must conform to.

### 5.2 M database & runtime implementations

#### FIS-GT.M
**✔ fetched · TRM [tid=6632](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=6632)**

- **What it is.** A database engine and M application-development platform — the same ACID/global-database model as the M standard, delivered as an engine that runs on RHEL. Notable for being **open source / free**.
- **Vendor.** FIS (the product traces to **Greystone Technology M**, hence "GT.M").
- **TRM status.** **Authorized w/ Constraints (POA&M)** for all versions through CY2025; **all versions transition to "Unauthorized, Conditions Required"** beginning **Q1 2026** (requiring POA&M review + Authorizing Official approval).
- **Latest version.** **7.0.x** (released 2021-02-12).
- **Constraints.** VA Handbooks 6102/6500, Directives 6004/6513/6517, NIST/FIPS; sensitive-data protection; pre-implementation approval required.
- **Use case / notes.** ACID transaction workloads needing an integrated M database; the historical free alternative to Caché for **open-source VistA** (OSEHRA/WorldVistA). The TRM notes VA-network usage is **minimal**.

#### InterSystems Caché
**✔ fetched · TRM [tid=10](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=10)**

- **What it is.** An **object and relational DBMS** and rapid-application-development platform built on M technology — the commercial M database that runs production VistA at the VA. Lets organizations process/analyze large data sets and build web/mobile apps over M globals.
- **Vendor.** InterSystems.
- **TRM status.** **Authorized w/ Constraints (POA&M).** Critically, the TRM states *"ongoing support for Caché is being reduced as the product has been replaced by InterSystems IRIS for Health,"* and older versions (5.0 → 2017.2.x) require POA&M in **Q1 2026** then become fully unauthorized. **Migration off Caché is explicitly encouraged.**
- **Latest version.** 2018.1.x.
- **Use case.** Production VistA database engine (legacy); the parent of the entire "Cache *" component family below.

#### InterSystems IRIS for Health
**✔ fetched · TRM [tid=14907](https://www.oit.va.gov/services/trm/ToolPage.aspx?tid=14907)**

- **What it is.** InterSystems' **successor to Caché** — a healthcare data platform unifying data management, application development, **healthcare-standards interoperability (FHIR, HL7 v2, DICOM)** and analytics. Full name *Intuitive Reliable Interoperative Scalable (IRIS) for Health*; aliases "IRIS Health," "HealthShare instance." On-prem and hosted-cloud (the TRM entry covers on-prem).
- **Vendor.** InterSystems.
- **TRM status (as of 05/08/2025).** **Authorized w/ Constraints** for current versions — **2024.1.x, 2024.2.x, 2024.3.x, 2025.1.x.** Older versions (2019.x → 2023.3.x) transition to "Unauthorized, Conditions Required" across 2025–2026. **This is the strategic forward direction.**
- **Constraints (≈23 numbered conditions).** FIPS 140-2 encryption for data at rest; ESCCB review for external connections; Kubernetes limited to on-prem AWS VAEC; FTP/SSL/TELNET/OpenJDK/Opera prohibited without POA&M; VA Handbook/Directive 6500 compliance.
- **Supported DBs / runtimes.** IBM Db2, MS SQL Server, MySQL (Commercial, RHEL-constrained), Oracle; runtimes include Kubernetes, .NET, Node.js, VS Code.
- **Use case.** The platform VistA is being modernized onto; greenfield M/ObjectScript + FHIR interoperability work.

### 5.3 The language layer: Caché ObjectScript
**✔ fetched · TRM [tid=6393](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=6393)**

- **What it is.** An **object-oriented superset of MUMPS** for building business applications; compiles to object code that runs in the Caché Virtual Machine, with cross-platform portability. The TRM explicitly lists **MUMPS as an "Associated Standard"** of ObjectScript, and notes the language is *"implemented by Cache."*
- **Vendor / body.** InterSystems.
- **TRM status (decision 04/16/2024).** **Authorized w/ Constraints (POA&M)** through 2025, transitioning to **unauthorized (Divest)** by **Q1 2026** — it shares Caché's deprecation curve.
- **Versions / OS.** Through 2018.1.9; RHEL, Windows Client/Server (OpenVMS unauthorized).
- **Use case.** Server-side scripting in CSP apps, Caché routines/programs, interactive use in Caché Terminal. *(Note for VistA specifically: VistA's ~40k routines are mostly **standard M**, not ObjectScript classes — see [vista-dev-iris-tooling.md](vista-dev-iris-tooling.md).)*

### 5.4 Development tools & IDEs

#### Cache Studio
**✔ fetched · TRM [tid=6394](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=6394)**

- **What it is.** InterSystems' classic **integrated development environment** for rapid app development: **syntax coloring, code checking, a graphical debugger, and project organization.** Supports **MUMPS** programming and Caché ObjectScript, plus C++, Python, and web standards (HTML/CSS/JS/XML).
- **Vendor.** InterSystems.
- **TRM status.** **Authorized w/ Constraints (POA&M)** through **Q4 2025**, then **Unauthorized, Conditions Required** from **Q1 2026.**
- **Versions / OS.** 2010.1 → 2018.1.x (current 2018.1.9, 2024-02-14); Windows Client/Server.
- **Key risk.** Requires Caché (itself unapproved/divesting) and lacks verified FIPS 140-2 compliance.
- **Use case.** The traditional VistA/Caché development desktop.

#### Atelier (Eclipse plug-in)
**✔ fetched · TRM [tid=11543](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=11543)**

- **What it is.** A **plug-in for the Eclipse IDE** giving an open, standards-based environment to build InterSystems solutions — source-code storage, client/server synchronization, code formatting. (Implicitly an ObjectScript/M dev tool, as that is what InterSystems products use.)
- **Vendor.** InterSystems.
- **TRM status.** **Unauthorized, Conditions Required (as of Q2 2026)** — previously Authorized w/ Constraints (POA&M) through Q4 2025. The product is **deprecated** (standalone Rich Client discontinued Nov 2017; deprecated at v2021.1).
- **Versions.** 1.0.x → 1.3.x (2018-09-17).
- **Use case.** A short-lived transitional IDE between Cache Studio and the VS Code extension; effectively **end-of-life** — do not adopt.

#### InterSystems ObjectScript Extension Pack for VS Code
**✔ fetched · TRM [tid=17070](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=17070)**

- **What it is.** A **Visual Studio Code extension pack** that connects VS Code to an InterSystems server to **develop ObjectScript** (and edit/compile M routines). The current-generation, cross-platform developer experience.
- **Vendor.** InterSystems (community-published).
- **TRM status (as of 11/20/2025).** **Authorized w/ Constraints** — the *only* actively-authorized M/ObjectScript IDE-class tool with a forward runway. Constraints: Unity disallowed (separate POA&M); patch per Federal policy; FIPS 140-2/140-3 for PHI/PII; VA Handbook/Directive 6500; supervisor/ISSO approval before download.
- **Versions / OS.** 1.0.x (current 1.0.3); Windows Client/Server, macOS, RHEL.
- **Dependencies.** Node.js, MS Visual Studio, .NET Framework.
- **Use case.** The recommended modern toolchain for editing VistA/IRIS M and ObjectScript code.

### 5.5 Caché data-access & web components

These are all **sub-components of the Caché platform** ([tid=10](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=10)) and therefore all inherit Caché's **divestment trajectory** — "Authorized w/ Constraints (POA&M)" trending to **"Unauthorized, Conditions Required (Divest)"** as the VA migrates to IRIS.

#### Cache Server Pages (CSP)
**✔ fetched · TRM [tid=6386](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=6386)**

- **What it is.** A platform to build/deploy **scalable web applications** that generate dynamic pages from a Caché database (with authentication and encryption support).
- **Vendor.** InterSystems.
- **TRM status.** Versions 2008.2 → 2018.1.x **Authorized w/ Constraints (POA&M)**; transition to **Unauthorized, Conditions Required at Q1 2026.** Current 2018.1.10.
- **Dependencies / constraints.** **Requires the Caché database** (itself POA&M); IIS or Apache on VA-authorized baselines; ISSO review for sensitive data; VA Handbooks 6102/6500, Directives 6004/6513/6517.
- **Use case.** Legacy web front-ends over VistA/Caché data.

#### Cache Objects
**◑ listed · TRM [tid=171](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=171)**

- **What it is.** The Caché **object-access layer / language bindings** — projects M globals/Caché classes as objects to client languages (e.g., Java/.NET) for object-style data access.
- **TRM status.** Listed among the Caché components as **Authorized w/ Constraints (POA&M) → Divest** per the Caché decision matrix.
- **Use case.** Object access to VistA/Caché data from external applications.

#### Cache ODBC Driver
**◑ listed · TRM [tid=5590](https://www.oit.va.gov/services/trm/ToolPage.aspx?tid=5590)**

- **What it is.** An **ODBC driver** exposing Caché's relational projection of M data to SQL/ODBC clients (reporting tools, ETL, BI).
- **TRM status.** Caché-family component, **Authorized w/ Constraints (POA&M) → Divest.**
- **Use case.** SQL/ODBC reporting and integration access to VistA data.

#### Cache Management Portal & Cache Zen
**◑ listed · sub-components of [tid=10](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=10)**

- **Cache Management Portal** — the **browser-based administration console** for configuring, monitoring, and managing a Caché instance.
- **Cache Zen** — Caché's **object-oriented, component-based web-application framework** (built on CSP) for rich AJAX UIs.
- **TRM status.** Both are enumerated on the Caché entry's component list as **Authorized w/ Constraints (POA&M) → Divest.**
- **Use case.** Operating a VistA/Caché instance (Portal) and building rich legacy web UIs (Zen).

### 5.6 Interoperability & integration platforms on the M stack

#### InterSystems Ensemble
**✔ fetched · TRM [tid=6450](https://www.oit.va.gov/Services/TRM/ToolPage.aspx?tid=6450)**

- **What it is.** A **connectivity and application-development platform** — an **ESB/SOA** infrastructure for composite applications. Capabilities: business process management, business-rule authoring, data transformations, event processing, and dashboards. It **auto-stores all messages/interactions in its embedded (M) database** for audit and reporting.
- **Vendor.** InterSystems.
- **TRM status.** **Authorized w/ Constraints** through CY2025; **all versions 2008.2 → 2018.1.x become "Unauthorized, Conditions Required" at Q1 2026.**
- **Critical dependency.** **Runs on Caché** — and the entry warns users *"must not utilize Cache, as it is currently sunsetting"* — which is exactly why Ensemble is on the same divestment path. (Its capabilities are absorbed into IRIS interoperability.)
- **Use case.** Legacy interface engine over the VistA/Caché stack.

#### HealthShare
**✔ fetched · TRM [tid=8686](https://www.oit.va.gov/services/trm/ToolPage.aspx?tid=8686)**

- **What it is.** InterSystems' **interoperability and analytics suite** — aggregates clinical and demographic data from many sources into **patient-centric records** compatible with major **health-information-exchange standards**, "within a single facility, or across a hospital network."
- **Vendor.** InterSystems. *(Built on the IRIS/Caché data engine — a "HealthShare instance" is one of IRIS for Health's aliases.)*
- **TRM status (as of 08/25/2025).** **Authorized w/ Constraints.** Releases 2015.1.x → 2025.1.x (current 2025.1.x, 2025-03-27); pre-2024.2.x versions go unauthorized by **Q2 2026.**
- **Constraints.** VA security policies; FIPS 140-2; PII/PHI handling; authorized baselines for Java/DB/browsers/OS.
- **Use case.** Cross-facility health information exchange and aggregation.

#### InterSystems API Manager (IAM)
**✔ fetched · TRM [tid=16536](https://oit.va.gov/Services/TRM/ToolPage.aspx?tid=16536)**

- **What it is.** An **API gateway / management** layer for microservices and APIs with **InterSystems IRIS** applications — manages communication between IRIS servers and apps, and monitors/regulates HTTP-based API traffic through a centralized gateway (Kong-based).
- **Vendor.** InterSystems.
- **TRM status.** **Authorized w/ Constraints** for **version 3.x through CY2027** (current 3.10.0.2, 2025-05-20). Constraints: VA Handbook/Directive 6500; FIPS 140-2/140-3 for PHI/PII; patch per Federal policy; Docker Compose (Community) prohibited, PODMAN approved; runs on RHEL; **Kong Gateway dependency marked for divestment.**
- **Use case.** API governance/throttling/monitoring for IRIS-based VA applications.

---

## 6. Notable absence: YottaDB

**YottaDB** — the actively-maintained **open-source successor/fork of GT.M**, maintained by YottaDB LLC and the present-day home of the GT.M codebase used widely in the open-source VistA world — **does not have a dedicated VA TRM entry** as of this survey (multiple targeted searches of the TRM returned no `ToolPage` for it). The TRM's open-source M coverage is represented only by the **FIS-GT.M** entry (§5.2), which is itself now on a divestment path. Anyone needing YottaDB authorized for VA use would have to submit it for TRM assessment via the TRM Management Group. See vendor links in §8.

---

## 7. Cross-cutting themes

1. **The Caché → IRIS migration dominates everything.** The TRM is unambiguous: Caché *"has been replaced by"* IRIS for Health, and the entire Caché component family (ObjectScript, Studio, CSP, Objects, ODBC, Management Portal, Zen) plus Ensemble are on a **Q1 2026 divestment cliff.** Only **IRIS for Health, HealthShare, IAM,** and the **VS Code ObjectScript Extension Pack** have a clean forward runway.
2. **Open-source M is thinly covered.** Only **FIS-GT.M** appears, and it too hits the Q1 2026 cliff; **YottaDB is absent.** The TRM's M story is overwhelmingly the InterSystems commercial stack.
3. **The IDE story modernized.** The IDE lineage is **Cache Studio → Atelier (Eclipse, now EOL) → VS Code ObjectScript Extension Pack**, and only the last is authorized going forward.
4. **Uniform constraint boilerplate.** Nearly every entry carries the same compliance scaffolding: **VA Handbooks 6102/6500, Directives 6004/6513/6517, NIST/FIPS (140-2/140-3) encryption for PHI/PII, ISSO/supervisor approval, POA&M for anything constrained.**
5. **The standard itself is "stable but stagnant."** The MUMPS standard entry flags *no recent development activity* and the language's lack of OO/functional features — context for why the VA is investing in the ObjectScript/IRIS superset rather than bare M.

---

## 8. Vendor & authoritative documentation links

| Tool | Vendor / authoritative documentation |
|---|---|
| **MUMPS / M (standard)** | [ISO/IEC 11756:1999](https://www.iso.org/standard/29268.html) · [MUMPS Development Committee (MDC) standard archive](https://en.wikipedia.org/wiki/MUMPS#Standards) · [M Technology overview (Wikipedia)](https://en.wikipedia.org/wiki/MUMPS) |
| **FIS-GT.M** | [GT.M on SourceForge](https://sourceforge.net/projects/fis-gtm/) · [GT.M product page (FIS)](https://www.fisglobal.com/) · [GT.M documentation](https://docs.yottadb.com/) (shared docs lineage) |
| **InterSystems Caché** | [Caché product page](https://www.intersystems.com/products/cache/) · [Caché 2018.1 documentation](https://docs.intersystems.com/) |
| **InterSystems IRIS for Health** | [IRIS for Health product page](https://www.intersystems.com/products/intersystems-iris-for-health/) · [IRIS documentation](https://docs.intersystems.com/iris) |
| **Caché ObjectScript** | [Using Caché ObjectScript (docs)](https://docs.intersystems.com/latest/csp/docbook/DocBook.UI.Page.cls?KEY=GCOS_intro) · [Caché ObjectScript (Wikipedia)](https://en.wikipedia.org/wiki/Cach%C3%A9_ObjectScript) |
| **Cache Studio** | [Using Studio (docs)](https://docs.intersystems.com/latest/csp/docbook/DocBook.UI.Page.cls?KEY=GSTD) |
| **Atelier** *(deprecated)* | [Atelier documentation (archived)](https://docs.intersystems.com/) · [Atelier on the InterSystems Developer Community](https://community.intersystems.com/tags/atelier) |
| **ObjectScript Extension Pack (VS Code)** | [VS Code Marketplace listing](https://marketplace.visualstudio.com/items?itemName=intersystems-community.objectscript-pack) · [GitHub: vscode-objectscript](https://github.com/intersystems-community/vscode-objectscript) |
| **Cache Server Pages (CSP)** | [CSP / web apps documentation](https://docs.intersystems.com/) |
| **Cache Objects** | [Caché object access docs](https://docs.intersystems.com/) |
| **Cache ODBC Driver** | [Using Caché with ODBC (docs)](https://docs.intersystems.com/) |
| **Cache Zen** | [Using Zen (docs)](https://docs.intersystems.com/) |
| **InterSystems Ensemble** | [Ensemble product page](https://www.intersystems.com/products/ensemble/) · [Ensemble documentation](https://docs.intersystems.com/) |
| **HealthShare** | [HealthShare product page](https://www.intersystems.com/products/healthshare/) · [HealthShare documentation](https://docs.intersystems.com/) |
| **InterSystems API Manager (IAM)** | [API management product page](https://www.intersystems.com/products/intersystems-iris/api-management/) · [IAM documentation](https://docs.intersystems.com/) |
| **YottaDB** *(no TRM entry)* | [YottaDB home](https://yottadb.com/) · [YottaDB source (GitLab)](https://gitlab.com/YottaDB/DB/YDB) · [YottaDB documentation](https://docs.yottadb.com/) |

> Note: InterSystems consolidates product manuals at **[docs.intersystems.com](https://docs.intersystems.com/)**; deep-linked sub-pages move between releases, so the version-specific docs are reached from each product's documentation landing page.

---

## 9. How to verify / re-run this survey

- **Live TRM lookup.** Every row links its TRM `ToolPage`/`StandardPage`. Open the page → **Decision Matrix** tab for the authoritative, current-quarter status (these change every TRM release; this brief reflects v26.x / ~May 2026 decision dates as annotated).
- **Find new M entries.** Search the TRM at [oit.va.gov/Services/TRM](https://www.oit.va.gov/services/trm/) for `MUMPS`, `Caché`/`Cache`, `ObjectScript`, `IRIS`, `Ensemble`, `HealthShare`, `GT.M`, `YottaDB`. The InterSystems family is cross-linked from the **Caché** entry's component list.
- **Submit a technology for assessment.** Technologies absent from the TRM (e.g., **YottaDB**) can be submitted to the **TRM Management Group** for SME assessment via the TRM site.

---

*Compiled from the public VA Technical Reference Model (oit.va.gov/services/trm). Statuses are point-in-time and were captured with their TRM decision dates; re-verify against the live TRM before relying on any authorization status.*
