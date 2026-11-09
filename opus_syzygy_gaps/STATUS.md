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
- Step 1 inventory: GAP_LEDGER.md. Kit recipe proven in this job root: parent 150374FF and trial_w6 4181A589 rebuilt byte for byte (`out/builds/p6_parent_pc1`, `w6_defines_t1`).
- Candidate tree `out/src/cand` (git, parent commit ded9684, head 188f8ff): SyzygyTbBounds (G1 G2 G3), SyzygyRootExact (G5 G6), SyzygyRule50 (G7 logic, G8).
- Build A (macros off, c188f8ff): preprocess_diff ALL EQUAL (8 units), kit exe = 150374FF byte for byte (`out/builds/buildA_c188f8ff`). IDENTITY PASS.
- Build B (macros on, default 0): pc1 = pc2 = B1F3F66D..., plain build pins OFF = lock pins, tables = P6 ON pins (`out/base/cand_v1_plain`).
- Adversarial root fixtures on parent and candidate: `fixtures/`, A 0, C 0 everywhere; display errors 733 + 618 on the parent, 0 with SyzygyRootExact.

## In progress
- Review R1 (one reviewer, opus-max, read-only), report `out/review/R1.md`; the candidate tree stays frozen until it reports.
- G7 RED / GREEN: `warm_claims.py clock` on the parent running, then on the candidate.
- Per-move oracle for the 200k roots running (`out/exp/e1/roots200k.oracle.jsonl`), used for move_quality.

## Next
1. Read R1, fix confirmed findings (test first), recheck.
2. Identity: `tools/identity_runs.ps1` for parent exe and Build B, `compare_runs.py` per set; `warm_identity.py` parent vs Build B.
3. ON measurements: claim harness on more roots and depth; move_quality parent vs ON; UCI root checks; soak Threads 2-4; UBSan and MSVC ASan.
4. after_w6 line: tree `out/src/w6p6` (w6 + P6 port, both apply with -F0), gaps on top, Build A' = its parent, pins.
5. Pack: BENCH.md, manifests, review log, hand-off note.

## Open / blocked
- See GAP_LEDGER.md. G4 closed as no gap (no result lost: 86 vs 107 blunders on 59,547 roots with and without tables). Nothing blocked.

## Resume
```
cd /d/forge_jobs_20261107/opus1/repo && git status -sb && git log --oneline -5
# read opus_syzygy_gaps/STATUS.md and GAP_LEDGER.md first; job env: D:orge_jobs_20261107\opus1\env.ps1
# candidate source: D:orge_jobs_20261107\opus1\out\src\cand (git log there); rebuild from lock d4f43124 + P6 patch + patches/syzygy_gaps_after_p6.patch
```
Running jobs (all exit by themselves; nothing is ever killed): `warm_claims.py clock` on p6_plain (out/exp/warm/p6_clock_d14.*); `oracle_chess.py` on 200k roots; `p6_c1tests.exe` on the 3-4 piece folder (heap-copy pass, slow, its result is not required: the full-set run passed). Reviewer agent syz-reviewer.
Elapsed at this update: about 1 h 45 min since T0.
