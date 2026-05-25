# syntax=docker/dockerfile:1
#
# VistA on IRIS — container image (per docs/vista-iris-container-spec-v3.md §11.1)
# Strategy A: bake VistA into the image at build time so `up` boots a loaded
# instance (see spec §7).
#
# Base image: InterSystems IRIS *for Health* Community — bundles the HL7 v2 /
# FHIR interoperability engine (the FHIR server is retained, per spec §4). The
# Makefile selects the per-arch tag (verified on Docker Hub 2026-05):
#   amd64 -> latest-cd-linux-amd64   arm64 (Apple Silicon) -> latest-cd-linux-arm64
ARG IRIS_TAG=latest-cd-linux-arm64
FROM intersystems/irishealth-community:${IRIS_TAG}

# As root, add Python 3 + pexpect: the routine/global import and the interactive
# VistA site build run from a cleaned OSEHRA Python fork (scripts/osehra/,
# spec v3 §12) that drives `iris session` over pexpect.
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pexpect \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/vista
# The phases run as a package via `python -m osehra <phase>`; put the package
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
COPY --chown=irisowner:irisowner scripts/osehra/m/  /opt/vista/scripts/osehra/m/
COPY --chown=irisowner:irisowner \
     scripts/osehra/__init__.py scripts/osehra/__main__.py \
     scripts/osehra/config.py scripts/osehra/helper.py \
     scripts/osehra/session.py scripts/osehra/state.py scripts/osehra/prepare.py \
     scripts/osehra/phase3_license.py scripts/osehra/phase5_import.py \
     /opt/vista/scripts/osehra/
# 1) namespace + mappings (Phase 4); 2) license/capacity gate BEFORE the import
# (Phase 3 — refuses early if the requested services can't fit, vs failing ~40
# min in); 3) pack routines.ro + globals.lst; 4) ^%RI / LIST^ZGI / ^ZTMGRSET
# (Phase 5). routines.ro is built to /tmp and removed in the same layer so it
# doesn't bloat the image. Fail-loud (spec v3 §5.1).
RUN iris start IRIS quietly \
 && iris session IRIS < /opt/vista/scripts/bootstrap.script \
 && python3 -m osehra license \
 && python3 /opt/vista/scripts/osehra/prepare.py /opt/vista/vista-m /opt/vista/scripts/osehra/m -o /tmp/vista-build \
 && python3 -m osehra import \
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
     scripts/osehra/steps_fileman.py scripts/osehra/steps_osinit.py \
     scripts/osehra/steps_postinstall.py scripts/osehra/steps_sampledata.py \
     scripts/osehra/phase6_osinit.py scripts/osehra/phase7_postinstall.py \
     scripts/osehra/phase8_sampledata.py \
     /opt/vista/scripts/osehra/
RUN iris start IRIS quietly \
 && python3 -m osehra osinit \
 && python3 -m osehra postinstall \
 && python3 -m osehra sampledata \
 && iris session IRIS -U %SYS < /opt/vista/scripts/startup.script \
 && iris stop IRIS quietly \
 && rm -f /usr/irissys/mgr/journal/20*

# Note: each layer purges IRIS journal files after a clean stop. The bulk
# global import journals heavily (GBs), which otherwise bloats the image and
# overruns disk during the layer commit; after a clean shutdown the data is in
# the .DAT and the journals aren't needed (IRIS recreates them on next start).

# The base image already exposes 1972 (superserver / RPC / xDBC) and 52773
# (Management Portal + FHIR REST). Document the VistA-configured listeners:
#   9430  VistA RPC Broker (XWB)  — CPRS / RPC clients
#   5026  VistA HL7 MLLP listener — HL7 v2 / FHIR-import path (configurable)
EXPOSE 9430 5026

# The stock IRIS entrypoint (inherited from the base image) starts and serves
# the prepared instance.
