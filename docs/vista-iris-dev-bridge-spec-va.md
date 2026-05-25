# VistA-on-IRIS Dev Bridge — VA Environment Profile

**Status:** Proposed (design) · **Version:** 1 · **Date:** 2026-05-25
**Profile of:** `vista-iris-dev-bridge-spec.md` (the environment-neutral core) · **Sibling:** `vista-iris-dev-bridge-spec-public.md`
**Companions:** `vista-dev-iris-tooling.md` · `historical/iris-dev-bridge-spec.md` (its §12.5 in-boundary mapping is absorbed here)

---

## How to read this document

This is the **VA environment profile** of the dev-bridge core. **Thin by design:** it adds **no developer-facing
requirements** (**[Parity]** lives in the core) and instead binds the core to the VA's **locked-down, in-boundary**
services and records VA-specific constraints (air-gap, GHES, tiers, PHI). Public and VA are **never mixed**; the
public bindings live in the sibling profile.

> The developer experience is **identical** to public by contract ([core §7](vista-iris-dev-bridge-spec.md)).
> Anything here that a developer would *notice* in the editor or commands is a parity defect.

## 1. Scope

Collaborative development inside the **VA accredited boundary**: locked-down GFE endpoints (thin VS Code remote
clients), an **internal GitHub Enterprise Server (GHES)**, in-boundary mirrors, and **official VistA-on-IRIS**
instances (different namespace / FileMan DD / configuration / data than FOIA). The bridge **arrives by transition**
from the public reference ([core §10](vista-iris-dev-bridge-spec.md)), not by independent development.

## 2. Binding points [Profile]

| Binding point (core §9) | VA value |
|---|---|
| Git host / URL | internal **GitHub Enterprise Server** (`https://<ghes-host>/<org>/…`) |
| Container / OCI registry | **in-boundary OCI registry** (GHES Packages / Harbor / Artifactory / ECR) |
| CI runners | **self-hosted** (e.g. Actions Runner Controller on Kubernetes); ARM via self-hosted runners or QEMU |
| Package / dependency sources | **mirrored in-boundary** (internal PyPI; pinned `m-cli` / `tree-sitter-m`) |
| Base image source | **internal mirror** of `intersystems/irishealth-community` |
| Remote-dev platform | **self-hosted only** — Coder / Remote-SSH (**Codespaces unavailable on GHES**) |
| Runtime-seed source | **sanitized clone** of the official VistA at the relevant tier |
| Data sensitivity / PHI | escalates by tier (fictitious → real); governed by VA policy |
| Identity / auth | **VA SSO** (SAML/OIDC, PIV/CAC) |
| AI / MCP tooling | per VA network policy — treat `m-dev-tools-mcp` / Claude Code as **optional** |

## 3. In-boundary supply chain (no public egress)

Everything the build and dev loop fetch **must resolve in-boundary** (absorbed from the predecessor's §12.5):

- **Mirror** the published bridge image, the `m-cli` / `tree-sitter-m` binaries (pinned to the
  public-validated versions), and all language/tool dependencies.
- **GHES specifics:** no GitHub-hosted runners (self-host them); Codespaces unavailable (self-hosted remote
  dev only); re-point `PUBLISHED_IMAGE` to the in-boundary registry.
- **Reconcile `vista-iris-container-spec-v3.md` §11** — its publish flow targets `ghcr.io` + GitHub-hosted
  runners and pulls the base image from Docker Hub; all three need in-boundary equivalents.
- **Licensing:** `m-dev-tools` (AGPL-3.0) is invoked as a subprocess (CLI boundary); the mirrored binary keeps
  usage in-boundary without imposing AGPL on VA code.

## 4. Instances, tiers & data sensitivity

- **Official instances, not FOIA.** Each target VistA has its own namespace, FileMan DD, configuration, and
  data; the core's discovery + seeding handle the differences with no FOIA assumptions
  ([core §5–§6](vista-iris-dev-bridge-spec.md)).
- **Tiers (dev → test → pre-prod → prod)** carry **increasingly real data**; the **runtime seed** is a
  sanitized clone whose sensitivity — and the access controls around it — escalate per tier (PHI governed by VA
  policy).
- **~130 production systems:** the bridge is parameterized by **(instance, this profile, tier)**; per-instance
  dev environments with provenance manifests prevent cross-contamination ([core §11](vista-iris-dev-bridge-spec.md)).
- **Code promotes via git; data never moves through the bridge** ([core §8, §11](vista-iris-dev-bridge-spec.md)).

## 5. Transition acceptance (in-boundary gate)

The VA deployment is accepted only when it **passes the same parity + instance-agnostic + baseline suites the
public reference passes** ([core §13](vista-iris-dev-bridge-spec.md)), re-run **in-boundary** against an official
VistA dev instance ([core §10 step 4](vista-iris-dev-bridge-spec.md)).

## 6. Constraints & risks

- **PHI / ATO:** higher tiers hold real data; sanitization, access, and accreditation are VA-policy gates, not
  bridge functions.
- **Network policy:** AI/MCP tooling and any egress are subject to VA policy; treat as optional.
- **Version drift:** the mirrored `m-cli` / toolchain **must match** the public-validated versions exactly, or
  parity breaks ([core §10, §14](vista-iris-dev-bridge-spec.md)).

## 7. References

- Core: `vista-iris-dev-bridge-spec.md`. Sibling: `vista-iris-dev-bridge-spec-public.md`.
- Tooling landscape: `vista-dev-iris-tooling.md`. Provenance (§12.5): `historical/iris-dev-bridge-spec.md`.
