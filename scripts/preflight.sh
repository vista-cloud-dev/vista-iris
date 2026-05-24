#!/usr/bin/env bash
#
# vista-iris pre-installation check.
#
# Verifies the container host is ready for a clean build/run, and (with --clean)
# makes it a *fresh install*. This codifies the failure modes we actually hit:
#   * a running instance holding the IRIS superserver port (1972) makes the
#     build's own IRIS fail to start ("ERROR #5001: Could not start superserver");
#   * leftover images / build cache exhaust the engine disk
#     ("no space left on device" while committing the import layer);
#   * a port conflict on the published ports (e.g. another VistA on 9430);
#   * a half-populated vista-m submodule breaks the Dockerfile COPY.
#
# Usage:
#   scripts/preflight.sh            # check only; non-zero exit if NOT ready
#   scripts/preflight.sh --clean    # also: stop other containers, remove any
#                                    # prior vista-iris instance + dangling
#                                    # images/build cache (-> fresh install)
#
# Env overrides: ENGINE (podman|docker, default podman), MIN_DISK_GB (default 50,
#   the headroom a from-scratch build needs), IMAGE (default vista-iris),
#   CONTAINER (default vista-iris).
set -u

ENGINE="${ENGINE:-podman}"
IMAGE="${IMAGE:-vista-iris}"
CONTAINER="${CONTAINER:-vista-iris}"
MIN_DISK_GB="${MIN_DISK_GB:-40}"
PORTS=(1972 52773 9430 5026)
CLEAN=0
[ "${1:-}" = "--clean" ] && CLEAN=1

FAIL=0
grn() { printf '\033[32m%s\033[0m' "$*"; }
red() { printf '\033[31m%s\033[0m' "$*"; }
ylw() { printf '\033[33m%s\033[0m' "$*"; }
ok()   { printf '  [%s] %s\n' "$(grn OK)"   "$*"; }
bad()  { printf '  [%s] %s\n' "$(red FAIL)" "$*"; FAIL=1; }
warn() { printf '  [%s] %s\n' "$(ylw WARN)" "$*"; }
hdr()  { printf '\n== %s ==\n' "$*"; }

echo "vista-iris preflight  (engine=$ENGINE, clean=$CLEAN)"

# --- 1. container engine ----------------------------------------------------
hdr "container engine"
if ! command -v "$ENGINE" >/dev/null 2>&1; then
  bad "$ENGINE not installed"
elif ! "$ENGINE" info >/dev/null 2>&1; then
  bad "$ENGINE not responding -- is the machine/daemon running?  (podman machine start)"
else
  ok "$ENGINE is responsive"
fi

# --- 2. cleanup for a fresh install (--clean) -------------------------------
if [ "$CLEAN" = 1 ]; then
  hdr "cleanup for fresh install"
  if "$ENGINE" ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
    "$ENGINE" rm -f "$CONTAINER" >/dev/null 2>&1 && echo "  removed prior container $CONTAINER"
  fi
  for c in $("$ENGINE" ps --format '{{.Names}}' 2>/dev/null); do
    [ "$c" = "$CONTAINER" ] && continue
    "$ENGINE" stop -t 15 "$c" >/dev/null 2>&1 && echo "  stopped other container $c"
  done
  for tag in dev working verify import post02; do
    "$ENGINE" rmi -f "$IMAGE:$tag" >/dev/null 2>&1 && echo "  removed prior image $IMAGE:$tag"
  done
  "$ENGINE" image prune -f >/dev/null 2>&1
  "$ENGINE" builder prune -f >/dev/null 2>&1
  echo "  pruned dangling images + build cache"
fi

# --- 3. no other running containers -----------------------------------------
hdr "running containers"
others=$("$ENGINE" ps --format '{{.Names}}' 2>/dev/null | grep -vx "$CONTAINER" || true)
if [ -n "$others" ]; then
  warn "other containers running: $(echo "$others" | tr '\n' ' ')"
  warn "  they can hold ports/resources -- run 'make fresh' to stop them"
else
  ok "no other containers running"
fi

# --- 4. required host ports free --------------------------------------------
hdr "host ports (${PORTS[*]})"
for p in "${PORTS[@]}"; do
  if nc -z -w1 localhost "$p" >/dev/null 2>&1; then
    bad "port $p in use -- a prior instance or another service holds it"
  else
    ok "port $p free"
  fi
done

# --- 5. engine disk space ---------------------------------------------------
hdr "disk space (need >= ${MIN_DISK_GB} GB for a from-scratch build)"
avail=""
if [ "$ENGINE" = podman ]; then
  avail=$(podman machine ssh 'df -BG --output=avail /var 2>/dev/null | tail -1' 2>/dev/null | tr -dc '0-9')
fi
if [ -z "$avail" ]; then
  warn "could not auto-detect engine free disk; ensure >= ${MIN_DISK_GB} GB (running a prebuilt image needs less)"
elif [ "$avail" -lt "$MIN_DISK_GB" ]; then
  bad "only ${avail} GB free (need >= ${MIN_DISK_GB} GB) -- 'make fresh' / 'make clean' or grow the machine disk"
else
  ok "${avail} GB free"
fi

# --- 6. build prerequisite: vista-m sources ---------------------------------
hdr "VistA-M sources (build prerequisite)"
root="$(cd "$(dirname "$0")/.." && pwd)"
if [ -d "$root/vista-m/Packages" ] && [ -n "$(ls -A "$root/vista-m/Packages" 2>/dev/null)" ]; then
  ok "vista-m/Packages present"
else
  warn "vista-m not populated -- run 'make sources' before building"
fi

# --- 7. prior vista-iris image (informational) ------------------------------
hdr "prior vista-iris install"
if "$ENGINE" images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -qx "localhost/$IMAGE:dev\|$IMAGE:dev"; then
  warn "$IMAGE:dev already exists -- 'make fresh' removes it for a clean rebuild"
else
  ok "no prior $IMAGE:dev image"
fi

# --- summary ----------------------------------------------------------------
echo
if [ "$FAIL" = 0 ]; then
  echo "$(grn 'PREFLIGHT PASSED') -- host is ready for build/run."
else
  echo "$(red 'PREFLIGHT FAILED') -- resolve the FAIL items above (try 'make fresh')."
fi
exit "$FAIL"
