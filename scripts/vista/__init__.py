# Cleaned, IRIS-only fork of the WorldVistA VistA import/configuration path
# (spec docs/vista-iris-container-spec-v3.md §7). Phase-aligned package:
#   config / session / state  -- shared: Phase-0 config, connection discipline, idempotency
#   helper / prepare / m/ZGI.m -- pexpect engine + routine/global packer + patched importer
#   steps_*                    -- verbatim VistA dialog libraries, one per phase
#   phase{3,5,6,7,8}_*         -- thin phase drivers, dispatched by `python -m vista <phase>`
