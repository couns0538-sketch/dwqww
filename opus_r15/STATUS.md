# R15 status (Opus, branch opus-r15-20261103) - DONE; everything UNPROVEN until the crew gates it

Lock FD3A5190 (`forge_ltopgo_x_al1s198_v23.exe`, sha256 fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072).
Pins: bench d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354; perft startpos d5 4865609, kiwipete d5
193690690. No SPRT games are run here; no Elo claims. Scratch and exes: `D:\o15\`. Final report: `opus_r15/FINAL_REPORT.md`
(= `D:\o15\FINAL_REPORT.md`). Gate lines for the crew: `D:\o15\cands\INDEX.md` (copy `opus_r15/cands/INDEX.md`).

| step | state (PC clock, 2026-11-03) | evidence |
|---|---|---|
| 0 setup (D:\o15, worktree D:\o15\wt, branch) | done 11:33 | first commit 47199b71 |
| 0 Job 0: R14-B Code Review fixes | already pushed 10:05-10:31 (f124ed3f, e29bf186, 1656e093, d3ad6881); re-verified 11:34 on fresh clones: 38 + 20 + 51 + 43 PASS | opus_r15/job0/RESULTS.md |
| 1 base re-verify | done 11:38 (kit pc1) and 12:48 (cand_pack -NoPatch, pc1 = pc2): sha256 fd3a5190... = the lock | opus_r15/base/, D:\o15\cands\base_nopatch |
| 2 C1 PruneLmrHist | DONE exe fe99a27d... | opus_r15/cands/c1_prunelmrhist/ |
| 2 C2 QsMovePrune | DONE exe ff63a706... | opus_r15/cands/c2_qsmoveprune/ |
| 2 C3 TtProbcut | DONE exe 4c48a25b... | opus_r15/cands/c3_ttprobcut/ |
| 2 C4 IirShallowTt | DONE exe 34055169... | opus_r15/cands/c4_iirshallowtt/ |
| 2 C5 ContHistSplit | DONE exe 3b9f56da... | opus_r15/cands/c5_conthistsplit/ |
| 2 C6 LowPlyHist | DONE exe 7a932e79... (attempt 3; attempts 1-2 failed on tool mistakes, same exe bytes) | opus_r15/cands/c6_lowplyhist/ |
| 2 extras (existing exes) | x1 TtCutoffHistory PASS; x2 TtPruneV2 on QA B1 a0d0eca9 NOT gateable; x2b TtPruneV2 on R13 b1k PASS (needs CR) | INDEX "existing exes" |
| 2 R13 checks + mate re-probe | T1/T4 legal everywhere; every 3M flip a horizon flip at 30M | cands/*/logs/cand_checks_r13.json, mate_reprobe.json |
| 2 CI | opus-r15-san runs 41624580607, 41628366851 green; tied to every built patch | cands/ci_san_*.txt, D:\o15\cands\*\ci.json |
| 3 Job 2 tools / skills / MCP | done (TOOLS.md) | opus_r15/tools/test_logs/ |
| 4 30-minute bug check | done: 11 own mistakes fixed; final_checks_r15.sh 13:25-13:36 0 failures | FINAL_REPORT.md |
| 5 FINAL_REPORT | done | opus_r15/FINAL_REPORT.md |
