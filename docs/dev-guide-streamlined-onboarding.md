# VistA-on-IRIS — Developer Onboarding & Build Streamlining

**Session guide — 2026-05-24**

A self-contained record of the design discussion and implementation that produced the
GHCR publish pipeline, the zero-build consumer path, and the shared §10 smoke checks on
branch `feat/container-build-scaffold` (PR [#2](https://github.com/vista-cloud-dev/vista-iris/pull/2)).
It captures the prompts asked, the decisions made, and **why** — so the rationale
survives even though the diffs don't explain themselves.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Q&A and Decisions (chronological)](#2-qa-and-decisions-chronological)
   - [2.1 Persistent Bash/edit permissions for a working directory](#21-persistent-bashedit-permissions-for-a-working-directory)
   - [2.2 Ideal language for a single portable binary](#22-ideal-language-for-a-single-portable-binary)
   - [2.3 What `pexpect` is and why it's used](#23-what-pexpect-is-and-why-its-used)
   - [2.4 Why VistA's install is interactive](#24-why-vistas-install-is-interactive)
   - [2.5 Easiest streamlined onboarding (no host runtime)](#25-easiest-streamlined-onboarding-no-host-runtime)
   - [2.6 Implementation of the three deliverables](#26-implementation-of-the-three-deliverables)
   - [2.7 Wiring the real §10 acceptance checks](#27-wiring-the-real-10-acceptance-checks)
   - [2.8 Commit, push, and PR update](#28-commit-push-and-pr-update)
3. [Tabular Summary — Changes Made](#3-tabular-summary--changes-made)
4. [Tabular Summary — Decisions & Rationale](#4-tabular-summary--decisions--rationale)
5. [The Resulting Developer Experience](#5-the-resulting-developer-experience)
6. [Open Items / Next Steps](#6-open-items--next-steps)
7. [Appendix — Prompts (verbatim)](#7-appendix--prompts-verbatim)

---

## 1. Overview

The session started with a Claude Code configuration question, moved through a series of
architecture questions about the VistA-on-IRIS install (which is driven by an
`pexpect`-based interactive terminal harness), and ended by implementing the
streamlining work: publish a prebuilt multi-arch image from CI so a new developer needs
**only Podman** — no local build, no submodule, no Python/Node runtime on the host.

The unifying insight discovered along the way: **the project already keeps Python off the
host** (it runs only inside the image build). The real friction was that every developer
had to *run that heavy build themselves*. The fix is to build once in CI and let everyone
else `podman pull`.

---

## 2. Q&A and Decisions (chronological)

### 2.1 Persistent Bash/edit permissions for a working directory

**Prompt:** *"how do I give my claude sessions permission to run bash and code within a specific working directory during all my sessions"*

**Investigation:** Read `~/.claude/settings.json` (empty `{}`), project `.claude/settings.json`
(absent), and `.claude/settings.local.json` (existing personal allow-list of specific
Bash commands).

**Decision:** Add tool-wide `Bash`, `Edit`, `Write` allow rules to the project's
**`.claude/settings.local.json`** (personal, gitignored), scoped to this project.

**Reasoning:**
- Project settings apply to **every session launched in that directory** — which is
  exactly "specific working directory" + "all my sessions".
- `.local.json` is gitignored → personal, not imposed on teammates.
- A tool name with no parentheses (`"Bash"`) matches **all** invocations, so nothing
  prompts. The user explicitly chose "all Bash + all edits" over the safer
  "auto-accept edits, still confirm Bash."
- **Trade-off surfaced:** unqualified `Bash` permits any command (including destructive
  ones) without a prompt, scoped to this directory only. A `deny` array can re-add
  guardrails later (deny overrides allow).

> Note: this change was **not** committed — it's a personal, gitignored file.

### 2.2 Ideal language for a single portable binary

**Prompt:** *"if I wanted to make this python setup and installation portable as a single binary (not require node or python environment) what would be an ideal language? needs to run on mac and linux"*

**Investigation:** Surveyed `scripts/osehra/` — ~2,000 lines of Python, dominated by
`setup.py` (1,378 lines) and `helper.py`. Found **~1,070 `wait`/`write`/`multiwait`
calls** driving an interactive `iris session` over `pexpect`.

**Decision / recommendation:**

| Option | Verdict | Why |
|---|---|---|
| **Go** | **Recommended** | Static, libc-free single binary → drops into a `scratch`/distroless image; trivial cross-compile to darwin/linux × amd64/arm64; mature PTY (`creack/pty`) + expect (`google/goexpect`, whose `ExpectSwitchCase` maps to `multiwait`). |
| **Rust** | Runner-up | `portable-pty` + `expectrl`; stronger typing, more cross-compile friction (musl/osxcross/`cargo-zigbuild`). |
| **PyInstaller / Nuitka** | Pragmatic alternative | Bundles the *existing* Python (no host Python needed), preserving the proven expect choreography. Not truly static, per-OS/arch build, larger. |

**Reasoning:** The real dependency is **not** "Python" — it's `pexpect` (PTY + expect).
So the choice hinges on which compile-to-binary language has the best PTY/expect story,
not on general-purpose features. Rewriting 1,070 load-bearing prompt/timeout steps is the
genuine risk, which is why bundling is a legitimate alternative to a rewrite.

### 2.3 What `pexpect` is and why it's used

**Prompt:** *"what is the purpose of pyexect"* (pexpect)

**Answer:** `pexpect` automates "a human at a terminal": it spawns a program inside a
**pseudo-terminal (PTY)**, waits for an expected prompt (literal or regex), then sends a
response — looping through a dialog. `helper.py` wraps it (`wait`→`expect_exact`,
`wait_re`→`expect(regex)`, `multiwait`→`expect([...])` returning the matched index,
`write`→`send`). It's required because the IRIS/VistA installer only speaks through an
interactive terminal and reveals each prompt only after the previous answer.

### 2.4 Why VistA's install is interactive

**Prompt:** *"why was it written as interactive originally? Were there too many options? was it a mega-script?"*

**Answer:** It wasn't a design choice between interactive and batch — **interactive was
the only interface VistA ever had.** VistA is a MUMPS/DHCP-era system where the *terminal
session is the API*. Its install subsystems are inherently Q&A dialogs:
- `^ZU` — sign-on (access/verify codes, forced changes)
- `^DINIT` / `Q^DI` — FileMan, whose interface *is* field-by-field prompting
- **KIDS** — the menu-driven distribution/install system

The dialog **branches on runtime state** (hence `multiwait`), so a fixed input stream
can't drive it. OSEHRA's automation replays the exact human keystroke sequence over a
PTY — which is why the forked scripts insist each sequence is "proven verbatim."

### 2.5 Easiest streamlined onboarding (no host runtime)

**Prompt:** *"what would be the easiest most streamlined approach to get a podman (docker) iris-based vista installed and operational for a new developer on mac or linux? ... easily done without requiring python or node installation or runtime (or any other runtime)."*

**Investigation:** Read `Dockerfile`, `Makefile`, `docker-compose.yml`, `bootstrap.script`;
confirmed **no CI workflow and no published image** existed.

**Key finding:** The "no host runtime" requirement was **already met** — Python/pexpect run
only inside the build (`RUN` steps), never on the host or in the running image's host
deps. Strategy A (bake at build) was already the right call. The only friction was that
**every developer ran the heavy build locally**.

**Decisions (the recommendation, accepted):**

| Decision | Reason |
|---|---|
| Publish a **prebuilt multi-arch image** from CI to GHCR | Collapses onboarding to "install Podman + one command"; the heavy pexpect build happens once. |
| New-dev path = plain **`podman run`**, not Compose | `podman compose` can delegate to `podman-compose` (a **Python** tool), reintroducing a host runtime; the one-liner has none. |
| Build each arch on a **native CI runner**, not QEMU | The interactive install under emulation is slow and timeout-prone. |
| Multi-arch **manifest** (amd64 + arm64) | Apple-silicon Macs and amd64 Linux auto-pull the right variant. |
| Default consumer instance to **ephemeral** | Simplest, resettable; baked image already contains loaded VistA. Durable %SYS is opt-in. |
| **Verify before promoting `:latest`** | Don't publish a broken `:latest`; gate the public tag on a passing smoke test. |

### 2.6 Implementation of the three deliverables

**Prompt:** *"do 1 2 and 3"* (the three proposed artifacts)

Implemented:
1. **`.github/workflows/publish.yml`** — 4-stage pipeline: `build` (per-arch native, push
   by digest) → `merge` (assemble `sha-<commit>` candidate) → `verify` (boot + smoke-test
   each arch) → `promote` (retag to `:latest` + date + git tag, only if green).
2. **`readme.md`** — consumer Quickstart (Podman one-liner, macOS `podman machine` note,
   ports table, fictitious test users) up top; contributor `make build` path separated.
3. **`Makefile` `pull`/`run`/`stop` + `docker-compose.run.yml`** — consumer targets using
   plain `podman run`; consumer Compose referencing the published image (no `build:`),
   ephemeral by default.

### 2.7 Wiring the real §10 acceptance checks

**Prompt:** *"yes"* (to: wire `make verify`'s §10 TODOs into CI, and commit)

**Investigation:** Read spec §10 acceptance checks (lines 343–348). `verify` already did
checks 1/5/6; checks 2/3/4 were echo stubs.

**Decision:** Factor checks into a shared **`scripts/smoke.sh`** used identically by
`make verify` and CI:

| # | §10 check | Implementation | Gating? |
|---|---|---|---|
| 1 | Instance running | `iris list \| grep running` | ✅ |
| 2 | VISTA login / `^XUP` menu | M probe: Kernel `^VA(200,0)` (NEW PERSON) populated | ✅ |
| 3 | FileMan sample patient | M probe: `^DPT` returns a patient name | ✅ |
| 4 | TaskMan active | `^%ZTSCH` present | ⚠️ reported, **not gating** |
| 5 | RPC Broker | `nc -z localhost 9430` | ✅ |
| 6 | HL7 MLLP | `nc -z localhost 5026` | ✅ |

**Reasoning:**
- Checks 2/3 use **always-present data globals** (non-interactive) instead of driving the
  `^XUP` menu (which would be pexpect territory) or relying on `$TEXT(^XUP)` (depends on
  routine source being retained). Confirming Kernel users + a FileMan patient exist is a
  robust proxy for "login works and data loaded."
- Check 4 (TaskMan) is **non-gating**: `^%ZTSCH` present only means TaskMan was scheduled,
  not that the submanager is running. Gating a release on a probe that couldn't be
  validated against a live instance would risk false CI failures — left as a `TODO`.
- The script is shared so **local `make verify` and CI run identical checks** (spec §7.1).

### 2.8 Commit, push, and PR update

**Prompts:** *"yes"* (commit on branch) → *"yes"* (push / open PR) → *"yes"* (update PR description)

- **Committed** `827a2ae` on `feat/container-build-scaffold` (only the 6 files of this
  work; the personal `.claude/settings.local.json` was excluded as gitignored).
- **Pushed** — discovered an **existing open PR #2** for the branch, so the push updated
  it rather than creating a duplicate.
- **Updated PR #2's description** to reflect the actual current branch state, correcting
  two stale claims that had drifted across earlier commits (that `vista-m` wasn't vendored
  — it's now a pinned submodule; that the scripts were MUMPS skeletons — they're the
  Python/pexpect fork + IRIS-native `bootstrap.script`), and folding in the new work.

---

## 3. Tabular Summary — Changes Made

| File | Status | Change | Committed? |
|---|---|---|---|
| `.claude/settings.local.json` | modified | Added tool-wide `Bash`, `Edit`, `Write` allow rules (this project, personal) | No (gitignored) |
| `.github/workflows/publish.yml` | **new** | Multi-arch GHCR publish: build (native, by digest) → merge → verify → promote | Yes (`827a2ae`) |
| `scripts/smoke.sh` | **new** | Shared §10 acceptance checks; fail-loud; used by `make verify` + CI | Yes |
| `Makefile` | modified | `PUBLISHED_IMAGE`/`PUBLISHED_TAG` vars; `pull`/`run`/`stop` targets; `verify` → `smoke.sh` | Yes |
| `docker-compose.run.yml` | **new** | Consumer Compose referencing the published image (no `build:`), ephemeral | Yes |
| `readme.md` | modified | Consumer Quickstart up top; contributor `make build` path below | Yes |
| PR #2 description | updated | Refreshed to current branch state; folded in new work | n/a (GitHub) |

**Git actions:** commit `827a2ae` → push `4b45e2f..827a2ae` → PR #2 (now 9 commits) description updated.

---

## 4. Tabular Summary — Decisions & Rationale

| # | Decision | Alternatives considered | Why chosen |
|---|---|---|---|
| D1 | Permissions in project `.claude/settings.local.json` | Global `~/.claude/settings.json`; committed project settings | Scopes to the directory + all sessions; personal, not imposed on team |
| D2 | Allow tool-wide `Bash`/`Edit`/`Write` | `defaultMode: acceptEdits` (edits only) | User wants both bash + edits with no prompts; trade-off (any command) accepted |
| D3 | Recommend **Go** for a single portable binary | Rust; PyInstaller/Nuitka; Zig/Nim/C | Best PTY+expect ecosystem + static binary + trivial cross-compile |
| D4 | Flag **bundling** (PyInstaller) as the low-risk alt | Full rewrite | 1,070 proven expect steps are risky to re-implement |
| D5 | **Publish a prebuilt image** from CI | Each dev builds locally | Removes the only real onboarding friction (the heavy build) |
| D6 | Consumer uses **`podman run`**, not Compose | `podman compose` / consumer Compose | Avoids the `podman-compose` Python dependency |
| D7 | **Native per-arch** CI runners | Single QEMU cross-build | Emulating the interactive install is slow/flaky |
| D8 | **Multi-arch manifest** (amd64 + arm64) | amd64-only | Apple-silicon + Linux auto-select the right image |
| D9 | **Ephemeral** consumer default | Durable %SYS by default | Simplest/resettable; baked image already loaded; durable is opt-in |
| D10 | **Verify before promote** (4-stage pipeline) | Build → push `:latest` directly | Never publish a broken `:latest` |
| D11 | Push by digest + `sha-<commit>` candidate → promote | Per-arch human tags | Clean multi-arch manifest; candidate gates promotion |
| D12 | **Shared `scripts/smoke.sh`** for §10 checks | Inline checks in both Makefile + workflow | Local == CI; single source of truth; shellcheck-able |
| D13 | Checks 2/3 via **data globals**, not menu-driving | Drive `^XUP`; `$TEXT(^XUP)` | Robust, non-interactive; avoids source-retention/PTY fragility |
| D14 | TaskMan check **non-gating** | Gate on `^%ZTSCH` | Couldn't validate "active" signal live; avoid false CI failures |
| D15 | **Update** existing PR #2 (not new PR) | Open a second PR | A PR already existed for the branch; avoid duplication |

---

## 5. The Resulting Developer Experience

**Consumer (just wants VistA running) — Podman only:**

```bash
# macOS one-time: brew install podman && podman machine init --cpus 4 --memory 6144 && podman machine start
podman run -d --name vista \
  -p 1972:1972 -p 52773:52773 -p 9430:9430 -p 5026:5026 \
  ghcr.io/vista-cloud-dev/vista-iris:latest
```

No clone, no build, no submodule, no Python/Node. Management Portal at
`http://localhost:52773/csp/sys/UtilHome.csp`; RPC Broker on 9430; HL7 MLLP on 5026.
(Or, with the repo checked out: `make run` / `make stop`.)

**Contributor (changing the build):** `make sources && make build && make up && make verify`
— unchanged, still requires git + the `vista-m` submodule.

---

## 6. Open Items / Next Steps

- [ ] **GHCR package visibility** — the first publish creates a *private* package; set it
  public once (or document `podman login ghcr.io`) for the zero-auth Quickstart pull.
- [ ] **Confirm the `vista-m` submodule** is committed/registered — CI's `submodules:
  recursive` checkout depends on it.
- [ ] **TaskMan check** — promote from non-gating to gating once a real "TaskMan active"
  signal is validated against a live instance (replace the `^%ZTSCH` proxy / `TODO` in
  `scripts/smoke.sh`).
- [ ] **First end-to-end CI publish** — trigger Actions → `publish` (or push a `v*` tag);
  this is where the §10 gates first confirm the baked image is operational.
- [ ] Confirm the `latest-cd-linux-{amd64,arm64}` base tags against the registry.

---

## 7. Appendix — Prompts (verbatim)

1. "how do I give my claude sessions permission to run bash and code within a specific working directory during all my sessions"
2. "if I wanted to make this python setup and installation portable as a single binary (not require node or python environment) what would be an ideal language? needs to run on mac and linux"
3. "what is the purpose of pyexect"
4. "why was it written as interactive originally? Were there too many options? was it a mega-script?"
5. "what would be the easiest most streamlined approach to get a podman (docker) iris-based vista installed and operational for a new developer on mac or linux? we want to make it as simple and streamlined as possible and easily done without requiring python or node installation or runtime (or any other runtime)."
6. "do 1 2 and 3"
7. "yes" — wire `make verify`'s §10 checks into CI, and commit on the branch
8. "yes" — push the commit / open a PR
9. "yes" — update PR #2's description to cover the new work
10. "write up everything that was in this session as a guide and put it in documents ..." (this document)
