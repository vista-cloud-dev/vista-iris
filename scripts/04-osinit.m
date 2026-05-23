VISTAOSI ; VistA OS-interface initialization ; spec-v2 §8 step 5
 ;; Imported and invoked by install.script (do OSINIT^VISTAOSI) after routines
 ;; and globals are loaded and BEFORE post-install. Wires VistA's OS layer to
 ;; the IRIS host. Internal name VISTAOSI regardless of the 04-osinit.m filename
 ;; (IRIS takes the routine name from this header line).
 QUIT
OSINIT ; main entry
 ; --- ^ZTMGRSET: choose system type "3 = Cache (VMS, NT, Linux), OpenM-NT" ---
 ; This is the correct answer for IRIS too -- it presents the Cache-compatible
 ; OS interface. ZTMGRSET renames the FileMan / %Z* routines and sets ^%ZOSF,
 ; ^%ZIS("C"), and the %Z editor for the host.
 ; TODO: D ^ZTMGRSET answering "3" (the orchestration feeds the interactive
 ;       prompt responses; the OSEHRA path scripts this interaction).
 ;
 ; --- Device / Initialize config (forked OSEHRA Initialize.py) ---
 ; TODO: define NULL / console / HFS devices; set the MPI local number, etc.
 QUIT
