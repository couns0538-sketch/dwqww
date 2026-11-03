# R15 status (Opus, branch opus-r15-20261103) - everything UNPROVEN until the crew gates it

Lock FD3A5190 (`forge_ltopgo_x_al1s198_v23.exe`, sha256 fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072).
Pins: bench d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354; perft startpos d5 4865609, kiwipete d5
193690690. No SPRT games are run here; no Elo claims. Scratch and exes: `D:\o15\`. Plan: `opus_r15/PLAN.md`.
Gate lines for the crew: `D:\o15\cands\INDEX.md` (copy: `opus_r15/cands/INDEX.md`).

| step | state (PC clock, 2026-11-03) | evidence |
|---|---|---|
| 0 setup (D:\o15, worktree D:\o15\wt, branch) | done 11:33 | first commit 47199b71 |
| 0 Job 0: R14-B Code Review fixes | already pushed 10:05-10:31 (f124ed3f, e29bf186, 1656e093, d3ad6881); re-verified 11:34 on fresh clones: 38 + 20 + 51 + 43 PASS, 0 FAIL | opus_r15/job0/RESULTS.md |
| 1 base re-verify (unpatched lock source, kit -Expose) | done 11:38: sha256 fd3a5190... = the lock byte for byte | opus_r15/base/ |
| 1 tools for Job 1 | done: pin_check 12 / 12, smoke2m 11 / 11 + 5, cleanroom_lint 15 / 15, cand_pack 9 / 9 | opus_r15/tools/test_logs/ |
| 2 C1 PruneLmrHist | PASS 11:59 (exe fe99a27d..., CI green) | opus_r15/cands/c1_prunelmrhist/ |
| 2 C2 QsMovePrune | PASS 12:07 (exe ff63a706..., CI green) | opus_r15/cands/c2_qsmoveprune/ |
| 2 C3 TtProbcut | PASS 12:15 (exe 4c48a25b..., CI green) | opus_r15/cands/c3_ttprobcut/ |
| 2 C4 IirShallowTt | PASS 12:22 (CI green) | opus_r15/cands/c4_iirshallowtt/ |
| 2 C5 ContHistSplit | packing (chain 1) | opus_r15/cands/c5_conthistsplit/ |
| 2 C6 LowPlyHist | patch + plain check done (OFF = pins, ON live); pack queued (chain 2) | opus_r15/cands/c6_lowplyhist/ |
| 2 extras (existing exes, never gated alone) | queued (chain 2): TtCutoffHistory on packc28 cf617e67, TtPruneV2 on B1 a0d0eca9 | INDEX "existing exes" |
| 3 Job 2 tools | done: gate_summary (62 / 62 F: gates exact) 6 / 6 + 2, index_check 8 / 8, ci_record 4 / 4, extra_check, MCP server forge-uci 18 / 18 (registered, Connected), skills forge-r15-candidates / forge-gate-summary | TOOLS.md |
| 4 30-minute bug check | todo (after chain 2) | |
| 5 FINAL_REPORT | todo | |

Crew safety: the running stB gate played 77-87 games per 10 min before and during R15 work (gate_summary --watch); own
work on CPUs 0-1 (the gate holds 4-15, the npt trainer CPU 3); D: 57-59 GB, C: 118-135 GB during the round.
