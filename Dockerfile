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

# IRIS images run as the unprivileged `irisowner` user. Stage the VistA sources
# and install scripts under a workdir it owns.
USER root
WORKDIR /opt/vista

# Prerequisites in the build context (deliverables per spec §12):
#   vista-m/   pinned WorldVistA/VistA-M sources (routines *.m + globals *.zwr)
#   scripts/   cleaned, IRIS-only fork of the OSEHRA install orchestration
#              (spec §5.4: no GT.M/YottaDB, no Cache-2011 installer, no EWD,
#              no fakes, no dead guards). install.script is the entry point.
COPY --chown=irisowner:irisowner vista-m/  /opt/vista/vista-m/
COPY --chown=irisowner:irisowner scripts/  /opt/vista/scripts/

USER irisowner

# Create the VISTA database/namespace + routine/global mappings, import
# routines, load globals, run post-install (institution, users, OS tables,
# TaskMan, RPC Broker on 9430, HL7 Link Manager on 5026), and load Tier-1
# sample data — all driven by the orchestration entry point. The build fails
# loudly if any step errors, so a broken install never produces a runnable
# image (spec §11.3 / §5.4).
RUN iris start IRIS quietly \
 && iris session IRIS < /opt/vista/scripts/install.script \
 && iris stop IRIS quietly

# The base image already exposes 1972 (superserver / RPC / xDBC) and 52773
# (Management Portal + FHIR REST). Document the VistA-configured listeners:
#   9430  VistA RPC Broker (XWB)  — CPRS / RPC clients
#   5026  VistA HL7 MLLP listener — HL7 v2 / FHIR-import path (configurable)
EXPOSE 9430 5026

# The stock IRIS entrypoint (inherited from the base image) starts and serves
# the prepared instance.
