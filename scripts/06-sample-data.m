VISTADATA ; VistA Tier-1 sample data ; spec-v2 §9
 ;; Imported and invoked by install.script (do DATA^VISTADATA). Forked OSEHRA
 ;; PostImportSetupScript + ClinicSetup, IRIS-only (§5.4). Internal name
 ;; VISTADATA regardless of the 06-sample-data.m filename.
 QUIT
DATA ; main entry
 ; Tier-1 baseline (deterministic, lightweight) -- enough to register, schedule,
 ; and order (§9). All identities are CLEARLY FICTITIOUS -- no real PHI.
 ;
 ; --- Clinical users (Access/Verify codes + e-signatures) ---
 ; TODO: Dr Robert Alexander (provider), Nurse Mary Smith, Clerk Joe Clerk.
 ;
 ; --- Facility structure ---
 ; TODO: division VISTA MEDICAL CENTER; a ward with beds; a clinic wired for
 ;       appointment scheduling; one orderable test.
 ;
 ; --- Test patients ---
 ; TODO: load fictitious patients into ^DPT (FOIA built-ins + a few seeded here).
 QUIT
