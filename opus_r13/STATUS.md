# Forge R13 (Opus) - status, one line per phase (continued by R14)

Updated: 2026-11-02 ~10:20 PC clock (= ~01:20 PT; PC clock = PT + 9 h), R14 block 1 in progress. All UNPROVEN.
R14 plan: opus_r14/PLAN.md (this branch). Remote heads below are the pushed state.

| phase | state (R14 view) | branch | last commit |
|---|---|---|---|
| P1 near-miss ports | DONE: 6 gate lines READY (b1, packa_w50, packa_w60, bnd68, packc28, eos49); crew CR PASS notes found for bnd68 / packc28 / eos49 (2026-10-31 20:03) | opus-r13-p1-nearmiss-ports | 759acc6d |
| P2 speed stack / align / sparse L1 | DONE for now (stack ff6628ce / align 302ad8fb neutral; sparse L1 exact but slower, stopped); step 5a -> R14 Main item 2 | opus-r13-p2-sparse-l1 | c93fe333 |
| P3 Sf26 split | DONE, CR PASS (3 singles, exe 029d58e8); gates uhoSF26S_* + HELD 8moves confirms queued by the crew; combined line -> R14 A5 | opus-r13-p3-sf26split | fe841cb4 |
| P4 v2-feature nets | CR final delta d884c23b applied; full cargo build 70cbae12; H256 parity PASS in fresh dirs (R14); H768+ parity next; training needs a GPU window (R14 Main item 1) | opus-r13-p4-v2nets | fa500c53 |
| P5 relabel | tools pushed (0be1d80a); job1 stopped 2026-11-01 12:25 PC clock after 440,000 rows on RECONSTRUCTED FENs (no castling / ep / clocks); fix + 1,000-position proof -> R14 A1 | opus-r13-p5-nnue-data | 0be1d80a |
| P6 Syzygy | CR PASS both lines, QA precheck done, gates uhoP6syz_path_1503 / uhoP6syz_pd4_1503 queued by the crew (exe 150374ff, pc1 = pc2); RESULTS completion -> R14 A2 | opus-r13-p6-syzygy | 73c2d139 |
| P7 E3 fit | fit done (Rule50Damp 60, Optimism 150 weak, MatScale 0); CR patch 129d440e + wide-bounds refit -> R14 A3 | opus-r13-p7-e3fit | cd9cb992 |
| P8 report | R13 FINAL_REPORT checkpoint 3; R14 report -> opus_r14/FINAL_REPORT.md | opus-r13-status | this commit |

Stray untracked copies (left in place, never deleted; not part of any branch):
- `D:\grok-pc-data\dwqww\.claude\worktrees\o13-p3\opus_r13\p4\forge_v2_bullet\src\main.rs` (2026-11-01 09:23, md5 0ca9f757):
  an early draft of the P4 trainer written into the P3 worktree; no commit has it (P4 has 8f058a22, now 9ede6e56).
- `D:\grok-pc-data\dwqww\.claude\worktrees\o13-p4\opus_r13\p5\relabel_job.py`: byte-identical copy of the P5 file.

## R13 final state (2026-11-01 ~11:20 PC clock, usage ending) - kept for the record
- P1 DONE: 6 gate lines (b1 e950c77e, packa w50/w60 07cc2393, bnd68 8dc93b38, packc28 cf617e67, eos49 a4e7f24c).
- P2 DONE for now: stack ff6628ce / align 302ad8fb (neutral); sparse L1 6fdf46dc exact but slower (stopped).
- P3 DONE (CR PASS): exe 029d58e8, singles queued; SPSA noise-level.
- P4: CR fixes pushed; parity PASS at H256 (a/b/c x AVX2/SSE 10000/10000); needs a GPU window; H768+ open.
- P5: relabel job ran until 12:25 (job C:\o13\p5\job1).
- P6: OFF pins, ON bench = original prober pins, WDL/DTZ 220/220, 50-move 20/20; LTO+PGO pc1/pc2 + CI sanitizer were running.
- P7 DONE: EvalRule50Damp 60 (fitted) beats OFF and hand; Optimism 150 weak; MatScale fits 0.
- F: had 45.0 GB free at start (< 50 GB floor), so R13 scratch/builds/handoff exes are on C:\o13\.
