# Job 6 prediction

Step 1 has 35 invariant rows. NOT-guaranteed rows within the inspected legal-position UCI/current-build contract: 0. Scope exclusions are recorded in Step 1, not claimed safe.

C1, C2, C3, C4 and C5: each is predicted to give equal r15d/kF final search fields (depth, seldepth, score, nodes, hashfull, PV and bestmove/ponder). Performance fields are excluded from equality.

C1 uses depth10 with nodes12000 and may stop before depth10. C2–C5 use depth10. All use PC20, Threads1, Hash16, built-in evaluation; C5 MultiPV2 and its serialized pre-search option/reset sequence are defined in Step 1. These are five guaranteed controls, not v3-net tests or full path coverage.
