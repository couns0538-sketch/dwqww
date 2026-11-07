# T1 book resolution - RESULT

Tool: Stockfish books (CC0-1.0), UHO_Lichess_4852_v1.epd vs the gates' 8moves_v3.pgn; runner fastchess 1.8.2-alpha
(MIT, own copy). Commands: CMDS.md. Analysis: `tools/t1_analyze.py` -> `t1_result.json`, `logs/t1_analyze.txt`.

## T1a: 2:1 node odds (lock trial_w6 at 20000 nodes vs the same exe at 10000 nodes), 600 pairs per book

| Book | Pairs | W / D / L (n20k) | Draw ratio | Pentanomial [LL, LD, DD+WL, WD, WW] | Score | Elo | nElo (95 %) | Mean plies |
|---|---|---|---|---|---|---|---|---|
| 8moves_v3 | 600 | 728 / 410 / 62 | 0.342 | [0, 18, 109, 262, 211] | 0.7775 | +217.3 | **+340.5** [+320.9, +360.2] | 147.0 |
| UHO_Lichess_4852_v1 | 600 | 729 / 364 / 107 | 0.303 | [1, 25, 130, 239, 205] | 0.7592 | +199.4 | **+296.3** [+276.7, +316.0] | 134.2 |

- The pentanomial counts equal fastchess's own final `Ptnml(0-2)` line for both books (MATCH); 0 broken pairs.
- **Resolution ratio nElo(UHO) / nElo(8moves) = 0.870, 95 % ~[0.794, 0.947].** At this large strength gap UHO resolves
  the difference *worse* than 8moves.
  - UHO has fewer draws (30 % vs 34 %), but the weaker engine wins more often from the favoured side (107 losses for
    n20k vs 62).
  - So the variance per pair is higher (0.0462 vs 0.0401) and the mean score lower.
- Wald drift arithmetic for a change that measures +10 / +15 nElo on 8moves, if the same ratio held for small changes:
  about 1.35x / 1.24x more pairs on UHO (from `t1_analyze.py`). **It is not known that the ratio holds for small
  changes.**
- Wall time: UHO 19:28:14-19:42:00, 8moves 19:42:00-19:55:24 (PC clock). That is about 85 games/min at concurrency 2 on
  CPUs 2-3 at Idle, next to the trainer (CPUs 0-3 were 66-100 % busy, `logs/scout_gate.jsonl`). Fixed nodes: the load
  changes only the wall time, not the games.
- The UHO games are shorter (134 vs 147 plies). At a time control that gives ~9 % more games per hour at the same
  per-move time; this run used node limits.

## Context: the gates' own regime (8moves, 10+0.1, Threads 2)
`logs/gate_context_8moves.txt` (gate_tm_scoreloss1_vs_AL1, 2128 games): draw ratio 0.797, pentanomial
[8, 176, 727, 145, 8] (68 % of pairs DD/WL). That is far more drawish than T1a (34 %). UHO books exist for that regime,
which T1a does not test.

## T1b: 1.33:1 node odds (20000 vs 15000 nodes), 1500 pairs per book (`logs/t1b_analyze.txt`, `t1b_result.json`)

| Book | Pairs | W / D / L (n20k) | Draw ratio | Pentanomial [LL, LD, DD+WL, WD, WW] | Score | Elo | nElo (95 %) | Mean plies |
|---|---|---|---|---|---|---|---|---|
| 8moves_v3 | 1500 | 1123 / 1450 / 427 | 0.483 | [23, 201, 540, 529, 207] | 0.6160 | +82.1 | **+121.2** [+108.8, +133.6] | 152.2 |
| UHO_Lichess_4852_v1 | 1500 | 1275 / 1222 / 503 | 0.407 | [23, 188, 511, 550, 228] | 0.6287 | +91.5 | **+133.5** [+121.1, +146.0] | 138.3 |

- Pentanomials equal fastchess's final lines (MATCH), 0 broken pairs.
- **Resolution ratio nElo(UHO) / nElo(8moves) = 1.102, 95 % ~[0.949, 1.255].** UHO is now slightly ahead, but the
  interval includes 1.
- Wall time: UHO 20:13:49-20:54:35, 8moves 20:54:35-21:36:01 (PC clock), conc 2 on CPUs 2-3 at Idle.
  - Around 21:0x the PC ran critically low on memory, and the session harness stopped the outer chain shell.
  - fastchess and the inner runner kept going and wrote their end line (rc 0).
  - Fixed nodes: neither event changes any game.

## Verdict
- Trend with the size of the gap:
  - 2:1 node odds: ratio 0.870 [0.794, 0.947] (UHO worse).
  - 1.33:1: ratio 1.102 [0.949, 1.255] (UHO slightly better, not significant).
  - The ratio rises as the gap shrinks. That is the direction expected for gate-size changes, which are smaller still
    and are played at 10+0.1 with ~80 % draws (8moves).
- UHO games are ~9 % shorter (138 vs 152 plies here), so there are more games per hour at the same time per move.
- If the T1b ratio held for gate-size changes, Wald arithmetic gives ~17 % fewer pairs for a +10 nElo change
  (2953 vs 3554). That is an extrapolation, **not a measurement**.
- **UNPROVEN for gates.** The next step that would decide it: near-zero changes at gate TC on both books (TUNING.md 1-2).
  Until then there is no case for switching the gate book; there is also no case against it.
