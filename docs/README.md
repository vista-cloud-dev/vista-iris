# vista-iris — documentation

Containerized VistA-on-IRIS instance. The repo [`readme.md`](../readme.md) is the
entry point for running the image; this folder holds the design, how-to, and
historical record.

## Layout

- **[`design/`](design/)** — this repo's own design notes.
  - [`design/vista-iris-container-spec-v3.md`](design/vista-iris-container-spec-v3.md)
    — **canonical, normative** build & runtime spec (the contract a fresh
    implementation builds to).
- **[`guides/`](guides/)** — how-to guides.
  - [`guides/vscode-vista-iris-guide.md`](guides/vscode-vista-iris-guide.md)
    — connect VS Code straight to the running container and edit VistA routines
    in place (VS Code ↔ IRIS).
- **[`archive/`](archive/)** — retired docs kept for history (superseded specs,
  the implementation log, onboarding/refactor session records). Not maintained.

Install-driver architecture lives beside the code:
[`scripts/vista/REFACTOR-NOTES.md`](../scripts/vista/REFACTOR-NOTES.md).
