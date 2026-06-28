# Editing VistA code in VS Code

VistA's ~40k routines live **inside the IRIS database**, not as files on disk. This guide
connects VS Code straight to the running `vista-iris` container so you edit routines in
place — **save = compile on the server**. No export, no import, no checkout.

Three one-time steps, then you're editing.

## Contents

- [1. Have the container running](#1-have-the-container-running)
- [2. Install the ObjectScript extension](#2-install-the-objectscript-extension)
- [3. Open the workspace](#3-open-the-workspace)
- [Edit a routine](#edit-a-routine)
- [Run something](#run-something)
- [Close the workspace when done](#close-the-workspace-when-done)
- [Troubleshooting](#troubleshooting)

## 1. Have the container running

The web port **52773** (the REST API the extension talks to) must be published — the
`podman run` in the [readme](../../readme.md) already does this. Check:

```bash
podman ps                                                                            # the `vista` container is Up
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:52773/csp/sys/UtilHome.csp # expect 200
```

## 2. Install the ObjectScript extension

```bash
code --install-extension intersystems-community.vscode-objectscript-pack
```

(Or install **InterSystems ObjectScript Extension Pack** from the Extensions view,
`Cmd+Shift+X`.)

## 3. Open the workspace

The repo ships a ready-to-use **`vista-iris.code-workspace`** at its root. Open it:

```bash
code vista-iris.code-workspace
```

(or **File → Open Workspace from File…**). It points the extension at the container and
mounts the `VISTA` namespace, so you land directly in the routines.

If you only pulled the image and don't have the repo checked out, save this as
`vista-iris.code-workspace` anywhere and open it:

```jsonc
{
  "folders": [
    // type=rtn = M routines only;  flat=1 = one flat list, not package folders
    { "name": "VISTA routines", "uri": "isfs://vista-iris:VISTA/?type=rtn&flat=1" }
  ],
  "settings": {
    "intersystems.servers": {
      "vista-iris": {
        "webServer": { "scheme": "http", "host": "localhost", "port": 52773 },
        "username": "_SYSTEM",
        "password": "SYS"
      }
    }
  }
}
```

These are the image defaults. This is a local, fictitious-data container, so keeping the
password right in the file is fine. If you built the image with custom `VISTA_USERNAME` /
`VISTA_PASSWORD` (see [`scripts/vista/config.py`](../../scripts/vista/config.py)), use those.

---

## Edit a routine

Open one from the **VISTA routines** folder and edit it. With ~40k routines, narrow the
list by adding a filter to the workspace `uri`, e.g. `…/?type=rtn&flat=1&filter=XU*`.
**Save (`Cmd+S`)** writes the routine back to the `VISTA` database and recompiles it;
results and errors show in the **ObjectScript** output channel.

> Routines appear as `.int` (and some `.mac`). For most VistA routines the `.int` **is**
> the source — edit it directly. Add `&generated=1` to the `uri` if a routine doesn't appear.

## Run something

To test code, open an IRIS terminal in the `VISTA` namespace: `Cmd+Shift+P` →
**ObjectScript: Open WebSocket Terminal**. (No extension, or it won't connect?
`podman exec -it vista iris session IRIS -U VISTA` gives you the same prompt from any shell.)

## Close the workspace when done

Your edits already live in the container (save = compile on the server), so there's nothing
to commit or export — just close up:

1. **Go back to your own project.** A VS Code window shows one workspace at a time, so
   "close" the VistA workspace by *opening yours over it*: **File → Open Recent** (`Ctrl+R`
   / `Cmd+R`) and pick your usual folder, or **File → Open Folder…**. Don't use **Close
   Workspace** — it just empties the window (it can look like VS Code disappeared) and
   doesn't take you back to anything.

   > Want to keep both open side by side? Open the VistA workspace in its own window next
   > time (`code -n vista-iris.code-workspace`, or **File → New Window** then open it).
   > Then closing that window leaves your local one untouched.

   Either way this only disconnects the editor — it doesn't touch the container.
2. **Leave the container running** if you'll be back soon — it holds your compiled routines
   and any terminal session state.
3. **Stop the container** when you're truly done to free the ports and memory:

   ```bash
   podman stop vista
   ```

   Restart later with `podman start vista` (or the readme's `podman run` if you removed it),
   then reopen the workspace — your saved routines are still there.

> The container keeps its data between `stop`/`start`. Only `podman rm vista` (or removing
> the image) discards the namespace, so your edits survive an ordinary stop.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Won't connect / timeout | Container down or 52773 not published. Run `podman ps`; the readme's `podman run` publishes the port. |
| `401 Unauthorized` | Wrong credentials — defaults are `_SYSTEM` / `SYS`. |
| "Password change required" / login loop | IRIS Community can force a change on first login. Log in once at http://localhost:52773/csp/sys/UtilHome.csp, then put the new password in the workspace file. |
| `VISTA` namespace not listed | Not the VistA image. `podman exec -it vista iris session IRIS -U VISTA` should reach a `VISTA>` prompt. |
| Edits don't take effect | Check the **ObjectScript** output channel — a routine with a compile error is saved but not active. |
