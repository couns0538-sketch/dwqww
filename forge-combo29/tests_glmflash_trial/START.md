glmflash trial, started 2026-11-15 09:05 UTC from commit 6b98f217 (tip of for-fable-and-opus/astra-0017-v3-path).
Understood: run a ThreadSanitizer check of the FORGE_NNUE_V3=1 code path (bench, perft, then 2- and 4-thread UCI searches over 500 seeded random legal positions), change no engine source, report honestly in forge-combo29/REPORT_glmflash_trial.md on my own branch.
First action: create branch for-fable-and-opus/glmflash-trial and start the CMake build with -DFORGE_NNUE_V3=1 (Step 1); START.md placed under tests_glmflash_trial/ because new files are only allowed there.
