# STATUS - opus-syzygy-gaps-20261107

Clock: the PC clock is wrong (about 7 h fast, measured 25156 s). Vienna times below come from HTTPS Date headers.
T0 = 2026-11-09 03:01:33 Vienna. Floor = T0 + 20 h = 2026-11-09 23:01:33 Vienna.

## Rulings (material decisions, with cost if wrong)
- CPUs 12-15 (0xF000), Idle: Couns's override of "0-3". Disk reserve check dropped by Couns.
- Reader stays the own P6 reader, Fathom is oracle only: P6 contains no Fathom path, the prompt's "reuse Fathom path" does not match the code. Cost if wrong: none for the engine, oracle stays independent.
- AGENTS.md is absent at the P6 tip; recovered from 3e900941, md5 94169aef = the historical value. Its Astra R8 scope clauses (no engine changes, C:/astra8_data, hand-off via Engine NNUE) do not apply; its "Development review and verification" section does. Cost if wrong: a review step in the wrong order.
- Gates "221-224" = idx 221-224 of QA's dry-run manifest (USYZP, USYZPc-QA, USYZPD4, USYZPD4c-QA), today idx 230-233.
- Baseline hash: trial_w6 exe 4181A589 verified. `CURRENT_LOCK.json` now names forge_clang_combo29_trial_w6.exe (E1284F7F, same pins, set 2026-11-08). The prompt's baseline stays the reference; recorded as a fact for QA.

## Done
- Step 0 bootstrap: job root, env.ps1, independent blobless sparse clone, branch cut from origin/opus-r13-p6-syzygy 4bf626eb, baseline hash match.
- Inventory first pass: GAP_LEDGER.md.

## In progress
- Step 1: re-run C1 tests on the P6 tree, build oracles, RED fixtures.

## Open / blocked
- See GAP_LEDGER.md. Nothing blocked.

## Resume
```
cd /d/forge_jobs_20261107/opus1/repo && git status -sb && git log --oneline -5
# read opus_syzygy_gaps/STATUS.md and GAP_LEDGER.md first; job env: D:\forge_jobs_20261107\opus1\env.ps1
```
Running jobs: none.
