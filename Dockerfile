# syntax=docker/dockerfile:1
#
# VistA on IRIS — container image (per docs/vista-iris-container-spec-v3.md §11.1)
# Strategy A: bake VistA into the image at build time so `up` boots a loaded
# instance (see spec §7).
#
# Two-stage build (spec v3 §11.1 — build hygiene):
#   * stage `builder` does the full install — keeping the import as its own
#     CACHED layer so iterating the site build never re-imports;
#   * stage `final` copies ONLY the finished IRIS instance into a clean base as a
#     single flat layer. This avoids the single-stage bloat where (a) the ~6 GB
#     vista-m source tree lived in the image forever and (b) every RUN that
#     modified a database forced OverlayFS to copy-up the whole IRIS.DAT, storing
#     it once per layer. The final image holds the final instance state exactly
#     once, so its size stays put across rebuilds (~half the single-stage size).
#
# Base image: InterSystems IRIS *for Health* Community — bundles the HL7 v2 /
# FHIR interoperability engine (the FHIR server is retained, per spec §4). The
# Makefile selects the per-arch tag (verified on Docker Hub 2026-05):
#   amd64 -> latest-cd-linux-amd64   arm64 (Apple Silicon) -> latest-cd-linux-arm64
ARG IRIS_TAG=latest-cd-linux-arm64

# ============================================================================
# Stage 1: builder — the full VistA install (throwaway; not shipped)
# ============================================================================
FROM intersystems/irishealth-community:${IRIS_TAG} AS builder

# As root, add Python 3 + pexpect: the routine/global import and the interactive
# VistA site build run from a cleaned WorldVistA Python fork (scripts/vista/,
# spec v3 §12) that drives `iris session` over pexpect.
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pexpect \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/vista
# The phases run as a package via `python -m vista <phase>`; put the package
# parent on the path so the dispatcher resolves it from any working directory.
ENV PYTHONPATH=/opt/vista/scripts
USER irisowner

# --- Layer 1 (expensive, cached): license gate + namespace + routine/global import
# Copy the pinned VistA-M sources + only the shared/import-side modules (Phase 0
# config, connection discipline, idempotency state, the Phase 3 license check,
# and the Phase 5 import driver), so this layer — which packs ~30k routines into
# routines.ro and loads ~GBs of globals — is reused as long as the sources and
# import code are unchanged. Iterating the site build below does NOT re-import.
COPY --chown=irisowner:irisowner vista-m/  /opt/vista/vista-m/
COPY --chown=irisowner:irisowner scripts/bootstrap.script  /opt/vista/scripts/bootstrap.script
COPY --chown=irisowner:irisowner scripts/vista/m/  /opt/vista/scripts/vista/m/
COPY --chown=irisowner:irisowner \
     scripts/vista/__init__.py scripts/vista/__main__.py \
     scripts/vista/config.py scripts/vista/helper.py \
     scripts/vista/session.py scripts/vista/state.py scripts/vista/prepare.py \
     scripts/vista/phase3_license.py scripts/vista/phase5_import.py \
     /opt/vista/scripts/vista/
# 1) namespace + mappings (Phase 4); 2) license/capacity gate BEFORE the import
# (Phase 3 — refuses early if the requested services can't fit, vs failing ~40
# min in); 3) pack routines.ro + globals.lst; 4) ^%RI / LIST^ZGI / ^ZTMGRSET
# (Phase 5). routines.ro is built to /tmp and removed in the same layer so it
# doesn't bloat the image. Fail-loud (spec v3 §5.1).
RUN iris start IRIS quietly \
 && iris session IRIS < /opt/vista/scripts/bootstrap.script \
 && python3 -m vista license \
 && python3 /opt/vista/scripts/vista/prepare.py /opt/vista/vista-m /opt/vista/scripts/vista/m -o /tmp/vista-build \
 && python3 -m vista import \
 && rm -rf /tmp/vista-build \
 && iris stop IRIS quietly \
 && rm -f /usr/irissys/mgr/journal/20*

# --- Layer 2 (iterated): interactive VistA site build -------------------------
# OS-init (Phase 6), post-install (Phase 7: institution, users, RPC Broker 9430),
# Tier-1 sample data (Phase 8), then install the %ZSTART hook (Phase 9) that
# auto-starts the RPC Broker listener on every boot. The verbatim dialog step
# libraries (steps_*) + thin phase drivers are copied after the import so edits
# here reuse the cached import layer. Each phase is idempotent + fail-loud.
COPY --chown=irisowner:irisowner scripts/startup.script  /opt/vista/scripts/startup.script
COPY --chown=irisowner:irisowner \
     scripts/vista/steps_fileman.py scripts/vista/steps_osinit.py \
     scripts/vista/steps_postinstall.py scripts/vista/steps_sampledata.py \
     scripts/vista/waitready.py \
     scripts/vista/phase6_osinit.py scripts/vista/phase7_postinstall.py \
     scripts/vista/phase8_sampledata.py \
     /opt/vista/scripts/vista/
# `waitready` outlasts the cold-mount race: `iris start` can return before the
# database is writable, and osinit's first FileMan write would then hit <PROTECT>
# and time out the install (observed in CI). Gate on a write probe first.
RUN iris start IRIS quietly \
 && python3 -m vista waitready \
 && python3 -m vista osinit \
 && python3 -m vista postinstall \
 && python3 -m vista sampledata \
 && iris session IRIS -U %SYS < /opt/vista/scripts/startup.script \
 && iris stop IRIS quietly \
 && rm -f /usr/irissys/mgr/journal/20*

# Note: each layer purges IRIS journal files after a clean stop. The bulk
# global import journals heavily (GBs), which otherwise bloats the image and
# overruns disk during the layer commit; after a clean shutdown the data is in
# the .DAT and the journals aren't needed (IRIS recreates them on next start).
# The builder stage is NOT shipped, so its per-layer .DAT copy-up is discarded.

# ============================================================================
# Stage 2: final — clean base + the finished instance as ONE flat layer
# ============================================================================
FROM intersystems/irishealth-community:${IRIS_TAG} AS final

# Runtime needs Python + pexpect ONLY so operators can re-run an idempotent phase
# against a live instance (e.g. `iris exec ... python3 -m vista postinstall`).
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pexpect \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/vista
ENV PYTHONPATH=/opt/vista/scripts

# The install driver package (small) — NOT the build-time source tree (the ~6 GB
# vista-m), the packer, or the .script files, so none of that lands in the image.
COPY --chown=irisowner:irisowner scripts/vista/*.py  /opt/vista/scripts/vista/

# The finished IRIS instance, copied as a single layer. All instance state lives
# under /usr/irissys (datadir); the delta from the stock base is the databases
# (mgr/, incl. the imported VISTA DB + the compiled %ZSTART routine + security)
# and the namespace/DB config (iris.cpf). Copying only these — not the unchanged
# /usr/irissys/bin binaries (already in the base) — keeps the layer minimal.
# COPY --from preserves the builder's ownership (all irisowner) and file modes.
COPY --from=builder /usr/irissys/iris.cpf  /usr/irissys/iris.cpf
COPY --from=builder /usr/irissys/mgr       /usr/irissys/mgr

# WORKDIR /opt/vista was created root-owned (USER root above), but the inherited
# IRIS entrypoint runs as irisowner and writes iris-main.log to its CWD -- so the
# runtime working dir must be writable by irisowner, else the instance aborts on
# boot ("Unable to find/open file iris-main.log in current directory /opt/vista").
RUN chown irisowner:irisowner /opt/vista

USER irisowner

# The base image already exposes 1972 (superserver / RPC / xDBC) and 52773
# (Management Portal + FHIR REST). Document the VistA-configured listeners:
#   9430  VistA RPC Broker (XWB)  — CPRS / RPC clients
#   5026  VistA HL7 MLLP listener — HL7 v2 / FHIR-import path (configurable)
EXPOSE 9430 5026

# The stock IRIS entrypoint (inherited from the base image) starts and serves
# the prepared instance.
