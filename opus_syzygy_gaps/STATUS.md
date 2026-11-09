# STATUS - opus-syzygy-gaps-20261107

Clock: the PC clock is wrong (about 7 h fast, measured 25156 s). Vienna times below come from HTTPS Date headers (`Get-ViennaNow` in `env.ps1`).
T0 = 2026-11-09 03:01:33 Vienna. The 20-hour floor of the first plan was dropped by Couns: finish when the work is done and a 20-30 minute bug check at the end finds nothing left.
Deadline (Couns, set 2026-11-09 13:56 Vienna): finish by 19:56 Vienna. Improvements that would take 10 hours or more are left out and listed. A bug that must be fixed still gets fixed before finishing.

## Rulings (material decisions, with cost if wrong)
- CPUs 12-15 (0xF000), Idle: Couns's override of "0-3". Disk reserve check dropped by Couns.
- One subagent at a time (Couns, for usage): one reviewer, opus-max, read-only, the same agent for R1, R2 and R3. Not Code Review. Cost if wrong: a finding a second reader would have seen; Code Review still reads the pack. After R3 Couns asked for a bug hunter next to the final work: `syz-hunter`, fable, read-only on the pack, scratch in `out/hunt_agent/`, 90 minutes at most. The reviewer stays idle meanwhile.
- Reader stays the own P6 reader, Fathom is oracle only: P6 contains no Fathom path, the prompt's "reuse Fathom path" does not match the code. Cost if wrong: none for the engine, oracle stays independent.
- AGENTS.md is absent at the P6 tip; recovered from 3e900941, md5 94169aef = the historical value. Its Astra R8 scope clauses (no engine changes, C:/astra8_data, hand-off via Engine NNUE) do not apply; its "Development review and verification" section does. Cost if wrong: a review step in the wrong order.
- Gates "221-224" = idx 221-224 of QA's dry-run manifest (USYZP, USYZPc-QA, USYZPD4, USYZPD4c-QA), today idx 230-233.
- Baseline hash: trial_w6 exe 4181A589 verified. `CURRENT_LOCK.json` now names forge_clang_combo29_trial_w6.exe (E1284F7F, same pins, set 2026-11-08). The prompt's baseline stays the reference; recorded as a fact for QA.
- Walk: the two-phase variant is rejected on the exact rows (`REVIEW_LOG.md` R2 finding 3); the single-phase walk in rounds stays.
- Move quality stays neutral on the cold 198,507 roots, so the suite does not say the switches help moves in general: they remove false claims and fix the boundary roots. Reported as it is in `BENCH.md`. QA's SPRT decides.
- No ABBA, no NPS claim: the prompt forbids quiet ABBA runs here; speed of Build B is not measured.

## State
See `GAP_LEDGER.md` for the gaps, `BENCH.md` for the numbers and hashes of the frozen head, `REVIEW_LOG.md` for reviews. Candidate source tree: `out/src/cand` (git, parent commit ded9684, the P6 tree); `patches/` holds the same change.

## Resume
```
cd /d/forge_jobs_20261107/opus1/repo && git status -sb && git log --oneline -5
# read opus_syzygy_gaps/STATUS.md, GAP_LEDGER.md, BENCH.md first; job env: D:\forge_jobs_20261107\opus1\env.ps1
# rebuild a tree from the pack: tools/repro_from_pack.sh; freeze proof: tools/final_freeze.sh; whole suite: tools/run_v6.sh <new tag>; trial_w6 line: tools/after_w6.sh <new tag>
```
Nothing here is queued. Every job exits by itself; nothing is ever killed.
Elapsed so far: see the commit times; this file is rewritten at each milestone.

## Left running by this job (0xF000, Idle, read-only on everything outside the job root)
- `oracle_exact.py` on all 4569 boundary roots (`out/exp/exact/b1.boundary.exact2.jsonl`): more rows for the same check; the judged snapshot is `b2500.exact.jsonl`. Exits by itself.
- `p6_c1tests.exe` PID 3808 on the 3-4 piece folder (heap-copy pass): very slow; its result is not required, the full-set run passed 36,825 checks with 0 failures.
- Blocked since R2, 0 CPU, no writes, left alone under the no-kill rule: `tb_root_v5.exe` PID 2488, `python.exe` PID 8512 (the reviewer's driver).
