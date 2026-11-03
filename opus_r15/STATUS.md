# R15 status (Opus, branch opus-r15-20261103) - everything UNPROVEN until the crew gates it

Lock FD3A5190 (`forge_ltopgo_x_al1s198_v23.exe`, sha256 fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072).
Pins: bench d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354; perft startpos d5 4865609, kiwipete d5
193690690. No SPRT games are run here; no Elo claims. Scratch and exes: `D:\o15\`. Plan: `opus_r15/PLAN.md`.

| step | state | evidence |
|---|---|---|
| 0 setup (D:\o15, worktree D:\o15\wt, branch) | done 11:33 | this commit |
| 0 Job 0: R14-B Code Review fixes | already pushed 10:05-10:31 (f124ed3f, e29bf186, 1656e093, d3ad6881); re-verify running | opus_r15/job0/RESULTS.md |
| 1 tools for Job 1 (pin_check, kit_build_r15, cand_pack, smoke2m, cleanroom_lint) | todo | opus_r15/tools/ |
| 1 base re-verify (unpatched lock source, kit -Expose = FD3A5190) | todo | |
| 2 candidates C1-C5 (+C6) | todo | D:\o15\cands\INDEX.md |
| 3 gate_summary, index_check, skills, MCP server, TOOLS.md | todo | |
| 4 30-minute bug check | todo | |
| 5 FINAL_REPORT | todo | |
