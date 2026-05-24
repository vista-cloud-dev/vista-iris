# VistA on IRIS

A containerized [VistA](https://github.com/WorldVistA/VistA-M) instance running on
InterSystems **IRIS for Health** Community. The full VistA site build (routine/global
import + the interactive FileMan/Kernel install, spec §5) is **baked into the image at
build time**, so the container boots an already-loaded, operational instance.

> **You do not need Python, Node, or any other runtime on your machine.** All of that
> lives inside the image build, which runs in CI. To *use* VistA you only need Podman
> (or Docker).

---

## Quickstart (just want VistA running)

**1. Install a container engine.**

- **Linux:** [Podman](https://podman.io/docs/installation) (or Docker).
- **macOS:** install Podman, then start its Linux VM once — give it a few GB of RAM
  (IRIS Community is core-capped at ~20 cores):
  ```bash
  brew install podman
  podman machine init --cpus 4 --memory 6144
  podman machine start
  ```

**2. Run the prebuilt image** (one command — no clone, no build):

```bash
podman run -d --name vista \
  -p 1972:1972 -p 52773:52773 -p 9430:9430 -p 5026:5026 \
  ghcr.io/vista-cloud-dev/vista-iris:latest
```

> First pull is large (multi-GB — VistA ships gigabytes of globals). Subsequent runs are
> instant. Docker users: substitute `docker` for `podman`.

This instance is **ephemeral**: stop and re-run to get a clean, freshly-loaded VistA.
For data that survives restarts, see [Persistence](#persistence).

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

Open a VistA terminal directly:

```bash
podman exec -it vista iris session IRIS -U VISTA
```

Stop it: `podman rm -f vista`.

### Using `make` instead

If you have the repo checked out, the same consumer flow is wrapped in Make:

```bash
make pull    # pull/refresh the published image
make run     # run it (ephemeral) — equivalent to the podman run above
make stop    # stop & remove the container
```

`make run` uses plain `podman run`, **not** Compose — `podman compose` can delegate to
`podman-compose`, which is itself a Python tool and would reintroduce a host runtime
dependency. The one-liner has no such dependency.

---

## Persistence

The Quickstart is intentionally disposable. To keep instance data across restarts, run
with the consumer Compose file, which mounts a Durable %SYS volume:

```bash
podman compose -f docker-compose.run.yml up -d
```

(See the comments in that file. Note the `podman-compose` caveat above — `docker compose`
or Podman's Go compose provider avoid the Python dependency.)

---

## Contributing (changing the build)

Only needed if you're modifying the image build itself (the install scripts in
`scripts/osehra/`, the Dockerfile, etc.). This path builds locally and **does** require
the VistA-M submodule and `make`:

```bash
make sources   # init the pinned vista-m submodule
make build     # build the image locally (the heavy, Python/pexpect-driven site build)
make up        # start via docker-compose.yml (durable volume)
make verify    # spec §10 acceptance checks
make down
make ci        # lint -> build -> up -> verify -> test -> down
```

Run `make help` for the full target list. Publishing to GHCR is automated — see
[`.github/workflows/publish.yml`](.github/workflows/publish.yml), which builds each arch
on a native runner, smoke-tests it, and only then moves `:latest`.

---

## Documentation

- [`docs/vista-iris-container-spec-v2.md`](docs/vista-iris-container-spec-v2.md) — the build/runtime spec
- [`docs/vista-dev-iris-tooling.md`](docs/vista-dev-iris-tooling.md) — IRIS dev tooling
- [`docs/va-trm-m-tools.md`](docs/va-trm-m-tools.md) — M tooling notes
