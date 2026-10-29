# N3 gate spec (R5C M2): Syzygy 3-4-5 + IntendedThreefold + HardDeadline=10 vs OFF

One option set, one gate; the candidate and the opponent are the same exe; only the candidate gets the three options.
Machine-readable copy: `n3_gate_spec.json`. Status: UNPROVEN, no Elo claim; gate-ready once the runner change below is
in place (owner installs the exe, adds srand and the openings start).

| item | value |
|---|---|
| exe (both sides) | `F:\opus_scratch\r5\r5c\exe\forge_r5c_m3b.exe`, sha256 `bf9f6f1619e1f47857c2a64005fe0bd22986c23b830a63b3d0fba929924ebae2`, install name `forge_r5c_n3.exe` |
| build | `opus_r5/r5c/tools/build_r5c.sh` RECIPE=v3 (g++ 15.2 -O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256, static), engine sources of commit d3e4d48a; 0 warnings, FMA 0 |
| candidate-only options, in this order | `option.SyzygyPath=D:/grok-pc-data/dwqww/.claude/worktrees/syzygy345`, `option.IntendedThreefold=true`, `option.HardDeadline=10` |
| left at their defaults | SyzygyProbeDepth, Syzygy50MoveRule, CuckooRep (off), every other option |
| both sides | `option.Threads=1`, `option.Hash=16`, `option.OwnBook=false` |
| TC | 10+0.1 |
| SPRT | elo0 0, elo1 10, alpha 0.05, beta 0.05, normalized |
| cap_games | 3000 (integer) |
| srand / openings start | blank (owner) |
| book | `C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn`, random order (the standard gate book) |
| tables | 145 WDL + 145 DTZ (3-4-5 pieces, 939 MB) at the path above; 290/290 sha256 OK against `opus_r3/R3-1L/syzygy345.sha256` (`logs/m2_syzygy345_sha256_check.log`) |
| OFF identity (exe defaults) | bench d11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609, kiwipete 193690690: ALL OK (`logs/identity_m3b.log`) |
| candidate prebench (same session, options above) | 313631 / 866959 / 2460490 / 11465604 / 31972996, perft5 4865609 (`logs/m2_n3_prebench.log`; only SyzygyPath changes the bench) |
| expected UCI lines (candidate) | `info string Syzygy: 145 WDL and 145 DTZ tables, up to 5 pieces`; info lines carry `tbhits N` |
| smoke | see REPORT.md M2 (200 games N3 vs OFF, Threads 1, 5+0.05, endgame book) |

## Runner change needed (candidate-only string option)

None of the 63 past gates (`D:\grok-pc-data\forge_push\gate*\RUN_INFO.json`, read-only survey 2026-10-29) passed an
option whose value is not a number or true/false; the runner (`forge_queue.ps1 v3-6day r7`) builds the candidate's
fastchess arguments from the `candidate.options` strings. Needed:
1. Pass `option.SyzygyPath=D:/grok-pc-data/dwqww/.claude/worktrees/syzygy345` to the candidate's `-engine` block only
   (never in `-each`), unchanged: no case change, no split at `:` or `/`, no quoting added (the path has no
   spaces). fastchess splits `option.NAME=VALUE` at the first `=`, so the value arrives whole.
2. Give the same option to the runner's pre-gate bench of the candidate ("cand ON" pins above): without the tables the
   ON bench would be the OFF bench and the pins would not match.
3. Keep the tables where they are for the whole gate (or copy them and change the path in both places); the
   candidate prints `info string SyzygyPath: no tablebase found in "<path>", tablebases off` if the folder is
   missing, so the RUN log shows a broken path at once.

## Why this gate

The three options are the endgame/draw bundle the job names (N3). Each was hardened in M1 (tests/r5c_n3_tests.cpp:
probes at the root and in the search with tables present / missing / wrong path, 50-move rule both ways, DTZ root
filter never returns an illegal or 50-move-losing move, path change while idle, IntendedThreefold x CuckooRep, and
HardDeadline=10 timing under movetime 50, wtime 100 and go infinite + stop). Tablebases help only in positions with at
most 5 pieces, so most games are unaffected: a [0,10] SPRT may run long and end at the cap; that is an expected
outcome, not a failure of the bundle.
