# Spec v3 Consolidation — Session Prompt

**Purpose:** A self-contained prompt to paste into a fresh Claude Code session to
consolidate the three overlapping sources of truth (spec v2, the implementation
log, and the working code) into one canonical `docs/vista-iris-container-spec-v3.md`.

**How to use:** Open a new session at the repo root (`vista-cloud-dev/vista-iris`)
and paste everything in the prompt block below. The prompt instructs the session
to plan first (present a TOC + reconciliation findings) and wait for your approval
before writing the spec.

---

ROLE & GOAL
You are consolidating three overlapping sources of truth in this repo into ONE
forward-looking, canonical specification: docs/vista-iris-container-spec-v3.md.

This repo builds a containerized VistA instance running on InterSystems IRIS for
Health Community. The first working build was reached by trial-and-error; the
fixes now live in the code, but the design, the discoveries, and the "why" are
spread across three documents that partly disagree. v3 must become the single
document a competent engineer could re-implement the whole thing from — cleanly,
in the right order, without repeating the original thrash.

THE THREE INPUTS (read all of them fully before writing anything)
1. docs/vista-iris-container-spec-v2.md   — the DESIGN spec (16 sections, incl.
   §14 license model). This is the intended structure.
2. docs/vista-iris-implementation-log.md  — the DISCOVERIES + ordered rewrite
   blueprint. Especially: §5 (discoveries), §6 (errors+remedies), §7 (caveats/
   deferred), §8 (Phase 0–11 blueprint, each phase naming the failure it
   prevents), §8.13 (notes for a Go rewrite), §10 (key technical facts).
3. THE WORKING CODE = GROUND TRUTH. When the docs and the code disagree, the
   code wins. Read and reconcile against: Dockerfile, docker-compose.yml,
   docker-compose.run.yml, Makefile, scripts/preflight.sh, scripts/smoke.sh,
   scripts/bootstrap.script, scripts/startup.script, scripts/license.script,
   scripts/osehra/*.py, scripts/osehra/m/ZGI.m, readme.md,
   .github/workflows/publish.yml.

Also skim (for consistency only — do NOT merge wholesale):
docs/dev-guide-streamlined-onboarding.md, docs/vista-dev-iris-tooling.md,
docs/va-trm-m-tools.md, docs/vaec-vista-hosting-general.md,
docs/go-cli-selection-guide.md.

WHAT v3 IS
- The normative BUILD/PROVISIONING contract (the "image factory"): config,
  preflight gate, base image, license/capacity, the ordered install sequence
  (Phases 0–11 from log §8, promoted to normative requirements), sample data,
  build hygiene/reproducibility, the instance's RUNTIME CONTRACT (ports,
  services, license toggles, test users), and verification/acceptance checks.
- A distillation of the log's blueprint + discoveries into requirements, with
  the "why" preserved as short rationale. Cross-reference the log for the full
  failure narratives instead of copying them verbatim.
- Self-contained: re-implementable from v3 alone; the log is only needed for
  historical color.

WHAT v3 IS NOT (scope guardrails — do not cross these)
- NOT a redesign. You are reconciling existing sources + code, not inventing new
  requirements or new architecture. Add nothing that isn't already decided in a
  source or present in the code. If something is genuinely missing/ambiguous,
  list it as an Open Question — do not resolve it by fiat.
- NOT a management-CLI design and NOT runtime operations tooling. Operating a
  built instance belongs to a separate control-plane tool and is out of scope.
  v3 covers building the image and the instance's runtime *contract*, not a CLI.
- NOT a Go-rewrite plan. Keep "the orchestrator could later be Go" only as a
  clearly-marked, non-binding Future Directions note (mirroring log §8.13).
- NOT code. Stay prose + tables. You MAY (and must) reference commands,
  routines, file paths, env vars, ports, and config keys by name (e.g. ^%RI,
  LIST^ZGI, UPDATE^DIE, %ZSTART, make build, latest-cd-linux-arm64,
  VISTA_ENABLE_RPC). You may NOT include copy-paste source listings, Dockerfile
  bodies, or script implementations. No fenced code blocks of implementation.
- Do NOT modify, refactor, or "improve" any code or script. Do NOT delete the
  log or v2.

METHOD (work in plan mode first; do not write the full doc until approved)
1. Read all three inputs + the code above.
2. Build a reconciliation table: for each material claim in v2 and in the log,
   mark CONFIRMED-by-code / CONTRADICTED-by-code (with the code's actual value)
   / STALE / UNVERIFIABLE. Verify concretely against the code: the per-arch IRIS
   tag, the exact published ports, the namespace/domain/institution/volume-set
   values, the service toggles and their env-var names, the license numbers, the
   install phases actually implemented in scripts/osehra/, the preflight
   thresholds, and the GHCR publish flow.
3. STOP and present to me: (a) the proposed v3 table of contents, (b) the
   reconciliation findings — especially every place the docs contradict the code
   — and (c) anything you propose to mark as Open Question or Deferred. Wait for
   my approval before writing v3.

PROPOSED v3 STRUCTURE (adjust only with justification)
 1. Purpose & Scope (incl. in/out of scope; relationship to the log; statement
    that runtime control is delegated to a separate tool)
 2. Goals & Non-Goals
 3. Glossary
 4. Locked Decisions & Rationale (merge v2 decisions + log decision tables)
 5. Architecture Overview (Strategy-A bake-at-build-time factory model)
 6. Prerequisites & the Preflight Gate (ordered checks; what each prevents)
 7. The Ordered Install Sequence — Phases 0–11 (the heart; normative; each phase
    states inputs, actions, the failure it prevents, and how it's verified)
 8. Sample Data Strategy (programmatic UPDATE^DIE; required identifiers; users)
 9. Service & License Model (8-unit budget; per-service cost; toggles; report)
10. Runtime Contract & Verification (ports, test users, acceptance checks)
11. Build Hygiene & Reproducibility (journal purge, clean-stop-before-commit)
12. Repository Layout & Artifact Reference (reconciled to the ACTUAL files)
13. Known Limitations, Deferred Items, Risks (from log §7)
14. Key Technical Facts (appendix; from log §10, each value verified vs code)
15. Future Directions (non-binding: Go orchestrator option; control-plane tool)

OUTPUT / DELIVERABLES
- Create docs/vista-iris-container-spec-v3.md per the approved outline. Date it,
  mark it "Status: Canonical", and note it supersedes v2.
- Add a one-line banner to the TOP of docs/vista-iris-container-spec-v2.md:
  "Superseded by vista-iris-container-spec-v3.md (kept for history)." Do not
  otherwise change v2; do not delete it.
- Update the documentation links in readme.md to point at v3 instead of v2.
- In your final message, print the reconciliation findings (the doc-vs-code
  discrepancies you found) as a short summary so I can sanity-check them.

ACCEPTANCE CRITERIA (the spec is done when…)
- Every normative statement is traceable to a source doc or verified against the
  code; doc/code conflicts are resolved in favor of code and footnoted.
- No statement contradicts the current working code.
- The Phases 0–11 section is complete, correctly ordered, and each phase names
  the failure it prevents and its verification.
- It's code-free (prose + tables; named references allowed) and self-contained.
- v2 carries the supersession banner; readme links point to v3.

Begin by reading the inputs and the code, then present the TOC + reconciliation
findings for my approval. Do not write v3 until I approve.
