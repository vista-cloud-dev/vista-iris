# =====================================================================
# VistA on IRIS — portable build + CI/CD chain
# Implements docs/vista-iris-container-spec-v2.md §7.1 and §11.3.
#
# Single, engine-agnostic entry point for: sources, build, up, down, verify,
# lint, test, ci, clean. Podman-first (§3): ENGINE defaults to podman; override
# with one variable for Docker:   make build ENGINE=docker
# The `ci` target IS the CI/CD chain, so local and CI behavior are identical.
# =====================================================================

ENGINE    ?= podman
COMPOSE    = $(ENGINE) compose
IMAGE     ?= vista-iris:dev
CONTAINER ?= vista-iris

# Prebuilt image published to GHCR by .github/workflows/publish.yml. The
# consumer path (`pull`/`run`) uses this instead of building locally, so a new
# developer needs only Podman -- no submodule, no build, no Python/Node.
PUBLISHED_IMAGE ?= ghcr.io/vista-cloud-dev/vista-iris
PUBLISHED_TAG   ?= latest

# IRIS for Health Community base tag (§4: "latest, then recorded"). Auto-selects
# the per-arch variant; override with IRIS_TAG=... InterSystems publishes
# explicit per-OS/arch tags (verified on Docker Hub 2026-05): the floating
# `latest-cd` plus `latest-cd-linux-amd64` / `latest-cd-linux-arm64`.
ARCH := $(shell uname -m)
ifeq ($(filter arm64 aarch64,$(ARCH)),)
IRIS_TAG ?= latest-cd-linux-amd64
else
IRIS_TAG ?= latest-cd-linux-arm64
endif
export IRIS_TAG

# VistA-M sources (§5) are vendored as a pinned git submodule at vista-m/ -- the
# submodule gitlink records the exact commit (the pin). VISTA_M_* below are used
# only by the non-submodule clone fallback in `sources`. TODO: bump the
# submodule deliberately when re-syncing with upstream (§13).
VISTA_M_REPO ?= https://github.com/WorldVistA/VistA-M.git
VISTA_M_TAG  ?= master
VISTA_M_DIR  ?= vista-m

# Published ports — must match docker-compose.yml and spec §10.
RPC_PORT ?= 9430
HL7_PORT ?= 5026

# Free disk (GB) the preflight requires. A from-scratch build (image ~20 GB,
# import-layer commit ~35 GB transient peak) needs ~40; running a prebuilt image
# needs far less (overridden for up/run below).
MIN_DISK_GB ?= 40
export MIN_DISK_GB

.DEFAULT_GOAL := help
.PHONY: help preflight fresh sources build up down verify lint test ci clean pull run stop

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n",$$1,$$2}'

sources: ## Init/update the pinned VistA-M submodule into $(VISTA_M_DIR)/ (shallow)
	@if git config -f .gitmodules --get submodule.$(VISTA_M_DIR).url >/dev/null 2>&1; then \
	  echo ">> updating submodule $(VISTA_M_DIR) (shallow, pinned)"; \
	  git submodule update --init --depth 1 -- "$(VISTA_M_DIR)"; \
	elif [ -n "$$(ls -A '$(VISTA_M_DIR)' 2>/dev/null)" ]; then \
	  echo ">> $(VISTA_M_DIR): present (vendored); using as-is"; \
	else \
	  echo ">> cloning $(VISTA_M_REPO) @ $(VISTA_M_TAG)"; \
	  git clone --depth 1 --branch "$(VISTA_M_TAG)" "$(VISTA_M_REPO)" "$(VISTA_M_DIR)"; \
	fi

preflight: ## Pre-install check: engine, disk, ports, conflicts, prior installs
	@bash scripts/preflight.sh

fresh: ## Preflight + CLEAN: stop other containers, remove prior vista-iris (fresh install)
	@bash scripts/preflight.sh --clean

build: preflight sources ## Build the OCI image (Strategy A) on IRIS_TAG=$(IRIS_TAG)
	$(COMPOSE) build

up: preflight ## Start the instance (detached)
	$(COMPOSE) up -d

down: ## Stop and remove the instance
	$(COMPOSE) down

# --- Consumer path: run the PREBUILT published image (no local build) --------
# `run` uses plain `$(ENGINE) run`, NOT compose: `podman compose` can delegate to
# podman-compose (a Python tool), which would reintroduce a host runtime dep.
pull: ## Pull/refresh the prebuilt published image from GHCR
	$(ENGINE) pull $(PUBLISHED_IMAGE):$(PUBLISHED_TAG)

run: preflight ## Run the prebuilt image (ephemeral; the streamlined quickstart)
	$(ENGINE) run -d --name $(CONTAINER) \
	  -p 1972:1972 -p 52773:52773 -p $(RPC_PORT):$(RPC_PORT) -p $(HL7_PORT):$(HL7_PORT) \
	  $(PUBLISHED_IMAGE):$(PUBLISHED_TAG)

# Running a prebuilt image needs far less free disk than a from-scratch build.
up run: MIN_DISK_GB := 25

stop: ## Stop & remove the `run` container
	-$(ENGINE) rm -f $(CONTAINER)

verify: ## Run the spec §10 acceptance checks (fail-loud)
	ENGINE="$(ENGINE)" CONTAINER="$(CONTAINER)" RPC_PORT="$(RPC_PORT)" HL7_PORT="$(HL7_PORT)" sh scripts/smoke.sh

lint: ## Static checks: shellcheck wrappers; XINDEX over changed routines
	@if command -v shellcheck >/dev/null 2>&1; then \
	  files=$$(git ls-files '*.sh'); \
	  if [ -n "$$files" ]; then shellcheck $$files; else echo "shellcheck: no .sh files"; fi; \
	else echo "shellcheck not installed (skipping)"; fi
	@echo ">> XINDEX (SAC / ANSI-M) over changed VistA routines (TODO: run in-instance)"

test: ## Run M-Unit (%ut) suites against the loaded instance
	@echo ">> M-Unit (%ut) suites (TODO: D EN^%ut(...) via '$(ENGINE) exec $(CONTAINER) iris session IRIS -U VISTA')"

ci: ## CI/CD chain: lint -> build -> up -> verify -> test -> down (fail-loud)
	$(MAKE) lint
	$(MAKE) build
	$(MAKE) up
	$(MAKE) verify
	$(MAKE) test
	$(MAKE) down

clean: ## Remove image, containers, and volumes for a clean ephemeral rebuild
	-$(COMPOSE) down -v
	-$(ENGINE) image rm $(IMAGE)
