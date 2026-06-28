# VistA on IRIS

A containerized [VistA](https://github.com/WorldVistA/VistA-M) instance on InterSystems
**IRIS for Health** Community. The entire VistA site build — routine/global import plus the
interactive FileMan/Kernel install — is **baked into the image at build time**, so the
container boots an already-loaded, operational instance.

> **No Python, Node, or other runtime needed on your machine.** That all lives in the image
> build (which runs in CI). To *use* VistA you only need Podman (or Docker).

---

## Contents

- [Quickstart](#quickstart)
  - [Using `make`](#using-make)
- [IRIS Management Portal](#iris-management-portal)
- [Edit VistA code in VS Code](#edit-vista-code-in-vs-code)
- [Persistence](#persistence)
- [Contributing (changing the build)](#contributing-changing-the-build)
- [Documentation](#documentation)

---

## Quickstart

**1. Install a container engine.**

- **Linux:** [Podman](https://podman.io/docs/installation) (or Docker).
- **macOS:** install Podman and start its Linux VM once (IRIS Community is core-capped at ~20):
  ```bash
  brew install podman
  podman machine init --cpus 4 --memory 6144
  podman machine start
  ```

**2. Run the prebuilt image** — one command, no clone, no build:

```bash
podman run -d --name vista \
  -p 1972:1972 -p 52773:52773 -p 9430:9430 -p 5026:5026 \
  ghcr.io/vista-cloud-dev/vista-iris:latest
```

> First pull is multi-GB (VistA ships gigabytes of globals); later runs are instant.
> Docker users: substitute `docker` for `podman`.

The instance is **ephemeral** — `podman rm -f vista` and re-run for a clean, freshly-loaded
VistA. For data that survives restarts, see [Persistence](#persistence).

**3. You're operational.** What's now listening:

| URL / Port | What |
|---|---|
| http://localhost:52773/csp/sys/UtilHome.csp | IRIS Management Portal (web) + FHIR REST |
| `localhost:9430` | VistA RPC Broker (XWB) — point CPRS / RPC clients here |
| `localhost:5026` | VistA HL7 MLLP listener |
| `localhost:1972` | IRIS superserver (RPC / xDBC / SQL) |

**Test users** (fictitious data — not for production or real PHI):

| User | Access | Verify | Signature |
|---|---|---|---|
| Robert Alexander (provider) | `fakedoc1` | `1Doc!@#$` | `ROBA123` |
| Mary Smith (nurse) | `fakenurse1` | `1Nur!@#$` | `MARYS123` |
| Joe Clerk | `fakeclerk1` | `1Cle!@#$` | `CLERKJ123` |

Open a VistA terminal: `podman exec -it vista iris session IRIS -U VISTA`.

### Using `make`

With the repo checked out, the same consumer flow is wrapped in Make:

```bash
make pull    # pull/refresh the published image
make run     # run it (ephemeral) — equivalent to the podman run above
make stop    # stop & remove the container
```

The engine is auto-detected — `make` uses Podman if installed, otherwise Docker, so no
`ENGINE=` flag is needed (override with `make run ENGINE=docker` if you have both).

`make run` uses plain `podman run`, **not** Compose: `podman compose` can delegate to
`podman-compose` (a Python tool), reintroducing a host runtime dependency. The one-liner
has none.

---

## IRIS Management Portal

The browser-based IRIS admin console (configuration, SQL, the class/routine editor, FHIR),
served on port **52773**. With the container running, open
http://localhost:52773/csp/sys/UtilHome.csp and log in with the image defaults
**`_SYSTEM`** / **`SYS`** (IRIS may force a password change on first login; credentials are
build-configurable via `VISTA_USERNAME` / `VISTA_PASSWORD`).

VistA lives in the **`VISTA`** namespace — switch to it with the namespace selector to
browse its globals and routines. The portal is bound to `localhost` only.

---

## Edit VistA code in VS Code

VistA's ~40k routines live **inside the IRIS database**, not as files on disk. With the
container running, connect VS Code straight to it and edit routines in place
(**save = compile on the server** — no export/import) using the InterSystems ObjectScript
extension and the repo's `vista-iris.code-workspace`.

→ **[Editing VistA code in VS Code](docs/guides/vscode-vista-iris-guide.md)** — three one-time
steps to a live VS Code ↔ IRIS editing setup, plus running code and troubleshooting.

---

## Persistence

The Quickstart is intentionally disposable. To keep instance data across restarts, use the
consumer Compose file, which mounts a Durable %SYS volume:

```bash
podman compose -f docker-compose.run.yml up -d
```

(See the comments in that file; `docker compose` or Podman's Go compose provider avoid the
`podman-compose` Python dependency.)

---

## Contributing (changing the build)

Only needed to modify the image build itself (the install driver in `scripts/vista/`, the
Dockerfile, etc.). This path builds locally and requires the VistA-M submodule and `make`:

```bash
make sources   # fetch the pinned vista-m submodule (reused if already present — no re-download)
make build     # two-stage build of the image (the Python/pexpect-driven site build)
make up        # start via docker-compose.yml (durable volume)
make verify    # spec §10 acceptance checks
make down
make ci        # lint -> build -> up -> verify -> test -> down
make trim      # reclaim disk: prune dangling images + build cache (keeps the current image)
```

Run `make help` for the full target list. Publishing to GHCR is automated by
[`.github/workflows/publish.yml`](.github/workflows/publish.yml), which builds each arch on
a native runner, smoke-tests it, and only then moves `:latest`.

---

## Documentation

- [`docs/design/vista-iris-container-spec-v3.md`](docs/design/vista-iris-container-spec-v3.md) — canonical build & runtime spec
- [`docs/guides/vscode-vista-iris-guide.md`](docs/guides/vscode-vista-iris-guide.md) — connect VS Code to the container and edit VistA code (VS Code ↔ IRIS)
- [`scripts/vista/REFACTOR-NOTES.md`](scripts/vista/REFACTOR-NOTES.md) — install-driver architecture (phase-aligned, idempotent, standalone-runnable)
