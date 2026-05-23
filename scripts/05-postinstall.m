VISTAPOST ; VistA post-install configuration ; spec-v2 §8 steps 6-9
 ;; Imported and invoked by install.script (do POST^VISTAPOST) after OS-init.
 ;; Forked OSEHRA PostImportSetupScript, IRIS-only (§5.4). Internal name
 ;; VISTAPOST regardless of the 05-postinstall.m filename.
 QUIT
POST ; main entry
 ; --- FileMan + environment (§8 step 6) ---
 ; TODO: initialize FileMan (DINIT); set primary HFS dir, intro text, time zone.
 ;
 ; --- Institution / domain (§8 step 6; identities per §9 Tier-1) ---
 ; TODO: christen Institution "VISTA HEALTH CARE" (station 6100) + DOMAIN;
 ;       set the Box:Volume pair.
 ;
 ; --- System Manager account (§8 step 6) ---
 ; TODO: create the System Manager account (programmer access, DUZ access/verify).
 ;       Clinical users + patients are loaded in 06-sample-data.m (§9).
 ;
 ; --- RPC Broker / XWB listener on 9430 (§8 step 7) ---
 ; TODO: write port 9430 into RPC BROKER SITE PARAMETERS (#8994.1); schedule
 ;       option XWB LISTENER STARTER to run at TaskMan startup so CPRS / RPC
 ;       clients can connect on every boot.
 ;
 ; --- HL7 interface / Link Manager on 5026 (§8 step 8) ---
 ; TODO: schedule HL AUTOSTART LINK MANAGER (STARTUP) and HL TASK RESTART
 ;       (STARTUP); schedule HL PURGE TRANSMISSIONS (daily); define/enable an
 ;       HL LOGICAL LINK (#870) as a TCP MLLP listener on port 5026 so external
 ;       / test systems can exchange HL7 v2 (the FHIR-import path).
 ;
 ; --- TaskMan (§8 step 9) ---
 ; TODO: ensure TaskMan auto-starts with the instance (D ^ZTMB via ^XUP), which
 ;       launches the scheduled XWB and HL7 STARTUP options on each boot.
 QUIT
