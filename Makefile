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

# IRIS for Health Community base tag (§4: "latest, then recorded"). Auto-selects
# the arm64 variant on Apple Silicon / aarch64; override with IRIS_TAG=...
# TODO: confirm the exact tag (and that an -arm64 variant exists) on the
# registry, then record the resolved release here for reproducibility.
ARCH := $(shell uname -m)
ifeq ($(filter arm64 aarch64,$(ARCH)),)
IRIS_TAG ?= latest-cd
else
IRIS_TAG ?= latest-cd-arm64
endif
export IRIS_TAG

# Pinned FOIA VistA-M sources (§5). TODO: pin VISTA_M_TAG to a dated FOIA tag.
VISTA_M_REPO ?= https://github.com/WorldVistA/VistA-M.git
VISTA_M_TAG  ?= master
VISTA_M_DIR  ?= vista-m

# Published ports — must match docker-compose.yml and spec §10.
RPC_PORT ?= 9430
HL7_PORT ?= 5026

.DEFAULT_GOAL := help
.PHONY: help sources build up down verify lint test ci clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n",$$1,$$2}'

sources: ## Fetch/verify the pinned VistA-M sources into $(VISTA_M_DIR)/
	@if [ -d "$(VISTA_M_DIR)/.git" ]; then \
	  echo ">> $(VISTA_M_DIR): fetching $(VISTA_M_TAG)"; \
	  git -C "$(VISTA_M_DIR)" fetch --depth 1 origin "$(VISTA_M_TAG)" && git -C "$(VISTA_M_DIR)" checkout -q FETCH_HEAD; \
	elif [ -n "$$(ls -A '$(VISTA_M_DIR)' 2>/dev/null)" ]; then \
	  echo ">> $(VISTA_M_DIR): vendored (non-git); using as-is"; \
	else \
	  echo ">> cloning $(VISTA_M_REPO) @ $(VISTA_M_TAG)"; \
	  git clone --depth 1 --branch "$(VISTA_M_TAG)" "$(VISTA_M_REPO)" "$(VISTA_M_DIR)"; \
	fi

build: sources ## Build the OCI image (Strategy A) on IRIS_TAG=$(IRIS_TAG)
	$(COMPOSE) build

up: ## Start the instance (detached)
	$(COMPOSE) up -d

down: ## Stop and remove the instance
	$(COMPOSE) down

verify: ## Run the spec §10 acceptance checks (fail-loud)
	@echo ">> [1/6] instance running"
	$(ENGINE) exec $(CONTAINER) iris list | grep -q running
	@echo ">> [2/6] VISTA login + ^XUP menu          (TODO: scripted M smoke check)"
	@echo ">> [3/6] FileMan inquiry returns a ^DPT sample patient (TODO)"
	@echo ">> [4/6] TaskMan active                    (TODO)"
	@echo ">> [5/6] RPC Broker reachable on $(RPC_PORT)"
	nc -z localhost $(RPC_PORT)
	@echo ">> [6/6] HL7 MLLP reachable on $(HL7_PORT)"
	nc -z localhost $(HL7_PORT)

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
