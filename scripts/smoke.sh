#!/usr/bin/env sh
# =====================================================================
# §10 acceptance smoke checks (spec docs/vista-iris-container-spec-v2.md §10).
# Shared by `make verify` and CI (.github/workflows/publish.yml) so local and CI
# behavior are identical (§7.1/§11.3). Fail-loud: any failed check exits non-zero.
#
# Config via environment (defaults match the Makefile / compose):
#   ENGINE     container engine     (podman)
#   CONTAINER  running container    (vista-iris)
#   RPC_PORT   VistA RPC Broker     (9430)
#   HL7_PORT   VistA HL7 MLLP       (5026)
#
# Assumes the instance is already started (Makefile runs this after `up`; CI
# after `docker run`). Each check retries briefly to absorb boot warm-up.
# =====================================================================
set -eu

ENGINE="${ENGINE:-podman}"
CONTAINER="${CONTAINER:-vista-iris}"
RPC_PORT="${RPC_PORT:-9430}"
HL7_PORT="${HL7_PORT:-5026}"

fail() { echo "FAIL: $*" >&2; exit 1; }

# retry <tries> <cmd...> : run until it succeeds or tries are exhausted (3s gap).
retry() {
	tries=$1
	shift
	while [ "$tries" -gt 0 ]; do
		if "$@"; then return 0; fi
		tries=$((tries - 1))
		sleep 3
	done
	return 1
}

iris_running() { "$ENGINE" exec "$CONTAINER" iris list 2>/dev/null | grep -q running; }
port_open() { nc -z localhost "$1" 2>/dev/null; }

# Non-interactive M probe in the VISTA namespace (same session path the build's
# bootstrap.script uses). Reports the namespace, whether the Kernel NEW PERSON
# file is populated (so sign-on / ^XUP menu is reachable), and a sample patient
# from the FileMan PATIENT file (^DPT). Uses literal "^" (U may be unset at a
# raw programmer prompt) and $GET to avoid <UNDEFINED>.
vista_probe() {
	"$ENGINE" exec -i "$CONTAINER" iris session IRIS -U VISTA 2>/dev/null <<'M'
W "CHK:NS:",$NAMESPACE,!
W "CHK:KERNEL:",$S(+$P($G(^VA(200,0)),"^",4)>0:"OK",1:"FAIL"),!
S DPTIEN=$O(^DPT(0)) W "CHK:DPT:",$S(DPTIEN'="":"OK:"_$P($G(^DPT(DPTIEN,0)),"^",1),1:"FAIL"),!
H
M
}

# Best-effort TaskMan probe (NOT gating — see TODO below).
taskman_probe() {
	"$ENGINE" exec -i "$CONTAINER" iris session IRIS -U %SYS 2>/dev/null <<'M'
W "CHK:ZTM:",$S($D(^%ZTSCH):"PRESENT",1:"ABSENT"),!
H
M
}

echo ">> [1/6] IRIS instance running"
retry 40 iris_running || fail "IRIS instance not 'running'"

echo ">> [2,3/6] VISTA login (Kernel users) + FileMan ^DPT sample patient"
probe=""
i=0
while [ "$i" -lt 10 ]; do
	probe=$(vista_probe || true)
	if printf '%s\n' "$probe" | grep -q "CHK:DPT:OK"; then break; fi
	i=$((i + 1))
	sleep 3
done
printf '%s\n' "$probe" | grep -q "CHK:KERNEL:OK" || fail "Kernel NEW PERSON file (^VA(200)) empty — VISTA sign-on/menu not ready"
printf '%s\n' "$probe" | grep -q "CHK:DPT:OK" || fail "no sample patient in FileMan PATIENT file (^DPT)"
printf '%s\n' "$probe" | grep -E "CHK:(NS|DPT):" | sed 's/^/   /'

echo ">> [4/6] TaskMan status (best-effort; not gating)"
# TODO(verify): gate on a confirmed "TaskMan active" signal once validated on a
# live instance. ^%ZTSCH PRESENT only means TaskMan has been scheduled, not that
# the submanager is currently running — too weak to fail a release on.
tm=$(taskman_probe || true)
if printf '%s\n' "$tm" | grep -q "CHK:ZTM:PRESENT"; then
	echo "   TaskMan schedule (^%ZTSCH) present"
else
	echo "   WARN: TaskMan schedule (^%ZTSCH) not found — confirm TaskMan on a live instance"
fi

echo ">> [5/6] RPC Broker (XWB) reachable on $RPC_PORT"
retry 30 port_open "$RPC_PORT" || fail "RPC Broker not listening on $RPC_PORT"

echo ">> [6/6] HL7 MLLP reachable on $HL7_PORT"
retry 30 port_open "$HL7_PORT" || fail "HL7 MLLP not listening on $HL7_PORT"

echo ">> §10 acceptance checks passed"
