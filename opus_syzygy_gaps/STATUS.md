# STATUS - opus-syzygy-gaps-20261107

**State: FINISHED. The pack is ready for Code Review. Hand-off is blocked on the channel: Couns forwards it (`HANDOFF.md`).**

Clock: the PC clock is wrong (about 7 h fast, measured 25156 s). Vienna times below come from HTTPS Date headers (`Get-ViennaNow` in `env.ps1`).
T0 = 2026-11-09 03:01:33 Vienna. The 20-hour floor of the first plan was dropped by Couns: finish when the work is done and a bug check at the end finds nothing left.
Deadline (Couns, set 2026-11-09 13:56 Vienna): finish by 19:56 Vienna. Improvements that would take 10 hours or more are left out and listed. A bug that must be fixed still gets fixed before finishing.
This version: written 2026-11-09 about 18:20 Vienna, about 15 h 19 min after T0: full file map in `HANDOFF.md` ("Where everything is"), and every process of this job stopped.

## Final state
- **Candidate:** frozen head `989399b` (`out/src/cand`, parent `ded9684` = the P6 tree). Unchanged since the freeze; the final bug hunt found no engine bug.
- **Patches** (md5 / sha256 prefixes, `patches/`):

| patch | lines | md5 | sha256 |
|---|---|---|---|
| `syzygy_gaps_after_p6.patch` (the change to review) | 389 | de4da16a | 7ebe0714 |
| `syzygy_gaps_after_w6p6.patch` (same 234 changed lines, one hunk with new context) | 390 | bac6d5a5 | 84443a82 |
| `syzygy_port_and_gaps_after_w6.patch` (P6 port + this change on trial_w6, one patch) | 2224 | f954d879 | 626a509c |

- **Gaps:** 7 CLOSED (G1, G2, G3, G5, G6, G7, G8), 0 open. G4, G9, G10 and G11 were checked and REJECTED. Limits: `GAP_LEDGER.md`.
- **Off means off:** Build A (macros off) is byte-identical to the parent exe 150374ff. Build B (macros on, options 0, db91700e, pc1 = pc2): pins, 10 identity sets and 3 warm runs are identical to the parent. trial_w6 line: A' is byte-identical to the w6 + port parent (5ada022c), and B' (5fee7ff8) passes every check (`BENCH.md`).
- **Reviews:** R1-R3 by one opus-max subagent and H1 by one Fable bug hunter, both this job's own and not Code Review. Every finding is fixed, tested or listed for Code Review (`REVIEW_LOG.md`, `HANDOFF.md`).
- **Strength:** no games, no Elo claim, no NPS claim. Every ON path is a SEARCH/EVAL CHANGE, UNPROVEN; QA's SPRT decides.
- **Exact pack:** this folder on branch `opus-syzygy-gaps-20261107`, at the last commit that changed this file: `git log -1 --format=%H -- opus_syzygy_gaps/STATUS.md` (a file cannot hold its own commit's hash). Check it with `MANIFEST.md5` and `MANIFEST.sha256`.
- **Blocker:** this session reaches no Code Review or QA session or queue (ListAgents lists only this job's own reviewer and hunter, both idle), and the prompt forbids queueing here. Nothing was queued, published or locked.
- **Left out by the deadline / Couns stop:** the pack's mate read-side evidence is the first **100 of 1500** rows of `fixtures/read.mate.tsv` (`tools/read_subset.sh`). A full 1500-row mate run takes about 3 h at depth 14; the full `mutants_read_side.sh r1` was later **stopped unfinished at Couns's request** (see Processes at the end). The clang recipe of the live exe is QA's. ASan was not run on the trial_w6 line.

## Rulings (material decisions, with cost if wrong)
- CPUs 12-15 (0xF000), Idle: Couns's override of "0-3". Disk reserve check dropped by Couns.
- One subagent at a time (Couns, for usage): one reviewer, opus-max, read-only, the same agent for R1, R2 and R3. Not Code Review. Cost if wrong: a finding a second reader would have seen; Code Review still reads the pack. After R3 Couns asked for a bug hunter next to the final work: `syz-hunter`, fable, read-only on the pack, scratch in `out/hunt_agent/`. The reviewer stayed idle meanwhile.
- Reader stays the own P6 reader, Fathom is oracle only: P6 contains no Fathom path, the prompt's "reuse Fathom path" does not match the code. Cost if wrong: none for the engine, oracle stays independent.
- AGENTS.md is absent at the P6 tip; recovered from 3e900941, md5 94169aef = the historical value. Its Astra R8 scope clauses (no engine changes, C:/astra8_data, hand-off via Engine NNUE) do not apply; its "Development review and verification" section does. Cost if wrong: a review step in the wrong order.
- Gates "221-224" = idx 221-224 of QA's dry-run manifest (USYZP, USYZPc-QA, USYZPD4, USYZPD4c-QA), today idx 230-233.
- Baseline hash: trial_w6 exe 4181A589 verified. `CURRENT_LOCK.json` now names forge_clang_combo29_trial_w6.exe (E1284F7F, same pins, set 2026-11-08). The prompt's baseline stays the reference; recorded as a fact for QA.
- Walk: the two-phase variant is rejected on the exact rows (`REVIEW_LOG.md` R2 finding 3); the single-phase walk in rounds stays.
- Move quality stays neutral on the cold 198,507 roots, so the suite does not say the switches help moves in general: they remove false claims and fix the boundary roots. Reported as it is in `BENCH.md`. QA's SPRT decides.
- No ABBA, no NPS claim: the prompt forbids quiet ABBA runs here; speed of Build B is not measured.
- H1 finding 1 was a test gap, not an engine bug, so the head stayed frozen: new fixture rows first, the mutants RED, the head GREEN. Cost if wrong: none for the engine; a weaker test would only miss a future regression.
- CPUs 0-11 were nearly idle at the end, but a gate (fastchess with 8 engines and its queue runner) was loaded there and could resume at any time. The job stayed on 12-15. Cost: the 1500-row mate runs did not finish in time.
- At the end Couns asked to stop this job's leftover processes (2026-11-09 about 18:15 Vienna). That lifted the plan's no-kill rule for this job's own processes only; nothing outside the job was touched.

## Resume
```
cd /d/forge_jobs_20261107/opus1/repo && git status -sb && git log --oneline -5
# read opus_syzygy_gaps/STATUS.md, GAP_LEDGER.md, BENCH.md first; job env: D:\forge_jobs_20261107\opus1\env.ps1
# rebuild a tree from the pack: tools/repro_from_pack.sh; freeze proof: tools/final_freeze.sh; whole suite: tools/run_v6.sh <new tag>; trial_w6 line: tools/after_w6.sh <new tag>
# read-side rows: tools/mutants_read_side.sh <new tag> (all rows, hours) or tools/read_subset.sh with the exes it built
```
Nothing here is queued, and no process of this job is running.

## Processes at the end
None is running: checked 2026-11-09 18:19 Vienna, 0 processes with the job root in their command line, CPUs 12-15 at 0-2 %. Stopped at Couns's request, about 18:15 Vienna (three background tasks by the session's task stop, the rest by Couns's command):
- `tools/mutants_read_side.sh r1` with `tbr_r1_head.exe` (PID 11704): full 1500-row mate read-side attempt, **stopped unfinished by Couns**. Partial summary `logs/read_side_r1_partial.txt`. Pack evidence of record remains the **100-row** mate subset in `BENCH.md` Stress (head 0 wrong; mutants RED).
- `p6_c1tests.exe` (PID 3808): a slow extra pass of P6's own table tests on the 3-4 piece folder, not required: the full-set run passed 36,825 checks with 0 failures.
- A driver from the R2 recheck, blocked since then at 0 CPU: `tb_root_v5.exe` PID 2488, `python.exe` PIDs 8512 and 6036, `powershell.exe` PID 9400.
- Four idle `tail` log watchers from the bug hunt.

Leftover files of the bug hunter in the job root: `tmp/hunt/junk_trees_m` (an empty tree copy) and `out/hunt_agent/runs/failed1`.
