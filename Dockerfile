# syntax=docker/dockerfile:1
#
# VistA on IRIS — container image (per docs/vista-iris-container-spec-v2.md §11.1)
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
# spec §5.4) that drives `iris session` over pexpect.
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pexpect \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/vista
USER irisowner

# --- Layer 1 (expensive, cached): namespace + routine/global import -----------
# Copy the pinned VistA-M sources + only the import-side scripts, so this layer
# (which packs ~30k routines into routines.ro and loads ~GBs of globals) is
# reused as long as the sources and import code are unchanged — iterating on the
# site build below does NOT re-import.
COPY --chown=irisowner:irisowner vista-m/  /opt/vista/vista-m/
COPY --chown=irisowner:irisowner scripts/bootstrap.script  /opt/vista/scripts/bootstrap.script
COPY --chown=irisowner:irisowner scripts/osehra/m/  /opt/vista/scripts/osehra/m/
COPY --chown=irisowner:irisowner scripts/osehra/__init__.py scripts/osehra/helper.py scripts/osehra/config.py scripts/osehra/prepare.py scripts/osehra/00_import.py  /opt/vista/scripts/osehra/
# 1) namespace + mappings (§8 1-2); 2) pack routines.ro + globals.lst; 3) ^%RI /
# LIST^ZGI / ^ZTMGRSET (§8 3-5). routines.ro is built to /tmp and removed in the
# same layer so it doesn't bloat the image. Fail-loud (§5.4).
RUN iris start IRIS quietly \
 && iris session IRIS < /opt/vista/scripts/bootstrap.script \
 && python3 /opt/vista/scripts/osehra/prepare.py /opt/vista/vista-m /opt/vista/scripts/osehra/m -o /tmp/vista-build \
 && python3 /opt/vista/scripts/osehra/00_import.py \
 && rm -rf /tmp/vista-build \
 && iris stop IRIS quietly

# --- Layer 2 (iterated): interactive VistA site build -------------------------
# OS-init, post-install (institution, users, TaskMan, RPC Broker 9430, HL7 Link
# Manager 5026), and Tier-1 sample data. Copied after the import so edits here
# reuse the cached import layer. Each step is fail-loud (§5.4).
COPY --chown=irisowner:irisowner scripts/osehra/setup.py scripts/osehra/01_osinit.py scripts/osehra/02_postinstall.py scripts/osehra/03_sampledata.py  /opt/vista/scripts/osehra/
RUN iris start IRIS quietly \
 && python3 /opt/vista/scripts/osehra/01_osinit.py \
 && python3 /opt/vista/scripts/osehra/02_postinstall.py \
 && python3 /opt/vista/scripts/osehra/03_sampledata.py \
 && iris stop IRIS quietly

# The base image already exposes 1972 (superserver / RPC / xDBC) and 52773
# (Management Portal + FHIR REST). Document the VistA-configured listeners:
#   9430  VistA RPC Broker (XWB)  — CPRS / RPC clients
#   5026  VistA HL7 MLLP listener — HL7 v2 / FHIR-import path (configurable)
EXPOSE 9430 5026

# The stock IRIS entrypoint (inherited from the base image) starts and serves
# the prepared instance.
