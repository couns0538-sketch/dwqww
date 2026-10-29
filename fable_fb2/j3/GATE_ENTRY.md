# Gate proposal entries — FB2-J3 search options (proposal only; nothing queued)

Engine: `F:\opus_scratch\build\fable_fb2\forge_fable_j3.exe` (branch `fable-fb2-j3`, box recipe, OFF identity ALL OK;
`fable_fb2/j3/logs/build_pc_j3.log`, `identity_off_j3.log`). Base: the same exe with every option off (= AL1 lock
pins). Format: fastchess 1.8.2, 10+0.1, Threads 1, Hash 16, 8moves_v3 book, concurrency 8, new srand each.
Bounds per `F:\opus_scratch\fable\GATE_BOUNDS.md` design 1: **SPRT normalized [0,10] nElo, a = b = 0.05, cap 6000**
(about 6 h each; the queue's 1500-game cap cannot decide effects below about +13 Elo).

| entry | candidate options | base | prior (GATE_BOUNDS section 5) | order |
|---|---|---|---|---|
| FB2-J3-1 | `CorrHistV2=true` | all off | +3 +- 5 | 1 |
| FB2-J3-2 | `LmrTableV2=true` | all off | +1 +- 6 | 2 |
| FB2-J3-3 | `TtPruneV2=true` | all off | +2 +- 5 | 3 |
| FB2-J3-4 | `SingularV2=true` | all off | +2 +- 5 | 4 |
| FB2-J3-5 | all four on | all off | sum of accepted parts; run only after 1-4, to check the combination | 5 |

Manifest sketch (same fields as `F:\opus_scratch\r3\GATE_ENTRIES.json`): candidate exe = base exe =
`forge_fable_j3.exe`, candidate `setoption name <Option> value true`, `tc 10+0.1`, `sprt elo0=0 elo1=10 alpha=0.05
beta=0.05 model=normalized`, `cap 6000`, `early_stop` = the crew rule (>= 750 games, Elo < -8, LLR < -1.5).
Pre-checks the runner can do: `uci` lists the option; `bench` with the option on differs from the lock pins
(CorrHistV2 d11 node count differs, see `logs/unit_tests.log`: every option changes the depth-10 trees), so the
"option did not apply" test fires on the ON side. No Elo is claimed for any entry; the self-play evidence
(`logs/selfplay_*`) only shows the options play without crashes or illegal moves.
