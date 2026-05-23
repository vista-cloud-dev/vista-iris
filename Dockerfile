# syntax=docker/dockerfile:1
#
# VistA on IRIS — container image (per docs/vista-iris-container-spec-v2.md §11.1)
# Strategy A: bake VistA into the image at build time so `up` boots a loaded
# instance (see spec §7).
#
# Base image: InterSystems IRIS *for Health* Community — it bundles the HL7 v2
# / FHIR interoperability engine (the FHIR server is retained, per spec §4).
# Track the LATEST Community release; never a legacy version. The resolved tag
# is exposed as a build arg and recorded for reproducibility (spec §4 version
# policy: "latest, then recorded"). On Apple Silicon / arm64, pass the arm64
# variant, e.g.:
#   docker build --build-arg IRIS_TAG=latest-cd-arm64 .
# Confirm the exact available tag against the registry before building:
#   https://hub.docker.com/r/intersystems/irishealth-community/tags
ARG IRIS_TAG=latest-cd
FROM intersystems/irishealth-community:${IRIS_TAG}

# IRIS images run as the unprivileged `irisowner` user. As root, add Python 3 +
# pexpect: the interactive VistA site build runs from a cleaned OSEHRA Python
# fork (scripts/osehra/, spec §5.4) that drives `iris session` over pexpect.
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pexpect \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/vista

# Prerequisites in the build context (deliverables per spec §12):
#   vista-m/   pinned WorldVistA/VistA-M sources (routines *.m + globals *.zwr)
#   scripts/   bootstrap.script (IRIS-native ns/import) + the cleaned, IRIS-only
#              Python fork of the OSEHRA site build (osehra/, spec §5.4: no
#              GT.M/YottaDB, no Cache-2011 installer, no EWD, no fakes).
COPY --chown=irisowner:irisowner vista-m/  /opt/vista/vista-m/
COPY --chown=irisowner:irisowner scripts/  /opt/vista/scripts/

USER irisowner

# Build the instance (Strategy A): bootstrap the VISTA namespace + import the
# FOIA routines/globals (bootstrap.script), then run the interactive site build
# from the OSEHRA Python fork — OS-init, post-install (institution, users,
# TaskMan, RPC Broker on 9430, HL7 Link Manager on 5026), and Tier-1 sample
# data. Each `&&` step is fail-loud, so a broken install never produces a
# runnable image (spec §11.3 / §5.4).
RUN iris start IRIS quietly \
 && iris session IRIS < /opt/vista/scripts/bootstrap.script \
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
