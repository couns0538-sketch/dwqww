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

## Verdict so far
- At 2:1 node odds and 20k / 10k nodes, **UHO is not better for Forge**: about 13 % less nElo per pair.
- This is a large-gap proxy at low depth. It says nothing final about gate-size changes (0-10 nElo) at 10+0.1, where
  draws are 80 %.
- Next (T1b): the same runner at 20000 vs 15000 nodes (1.33:1), 2000 pairs per book, to see where the ratio goes as
  the gap shrinks.
- **UNPROVEN** for gates in both directions.
