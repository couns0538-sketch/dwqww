# STATUS — longgame (replaying long games move by move in one process)

**State: complete. All five brief items answered, plus the two follow-ups (position identity and the
halfmove clock). Two clean negatives that matter (the bail, the clock) and one large difference that
is not a defect (46% move divergence).**

Build `6b98f217`, g++ 13.3, `-DFORGE_MARCH=x86-64-v4`. Four pins matched before any recording:
bench 11 = 312,866 / bench 13 = 862,329 / bench 16 = 3,024,920 / `go perft 5` = 4,865,609.
`go depth 8` throughout. No `quit` ever piped into a live search.

## The five items the brief asked for

| # | item | answer |
|---|---|---|
| 1 | 200 real games, move by move, one process | **200 games, 27,788 plies** searched; per-ply bestmove/score/nodes/depth in `evidence/session.jsonl` |
| 2 | 40 games vs fresh process per ply | **2,486 / 5,401 = 46.0%** bestmove divergence; isolated to **histories**, not the table |
| 3 | drawn-root bail firings | **89** (1 per 312 plies, 44.5% of games); **0 disagreements** with fresh, in either direction; all play the generator head |
| 4 | RSS + wall time | **42.2 MiB at every one of 277 samples from ply 300 to the end**; 78–85 s total (mean 0.42 s/game) |
| 5 | `go depth 8`, not a clock | yes; every answer reproducible — 0/27,788 diffs on an identical re-run |
| + | **position identity** (move-list board vs fresh FEN board) | **5,401 / 5,401** at perft 4 and **1,852 / 1,852** at perft 5; 0 mismatches |
| + | **halfmove clock over a long replay** | move-list verdict == FEN verdict **5,369 / 5,369**; boundary exactly at 100; A/A control 0/120 |

## Position identity — the clean bill

For every ply of the 40-game sample the engine builds the board twice, from the move list and from
a hand-built FEN (`force_ep_fen`, not python-chess `Board.fen()`, per brief rule 5), and `go perft 4`
must return a **byte-identical move-by-move breakdown**. It does: **5,401/5,401 at perft 4**, and
**1,852/1,852** on a deeper perft-5 pass over 15 games. Perft exercises
piece placement, side to move, ep and castling; planted faults in all three of those fields change
the breakdown, so the check fires.

Perft cannot see the **halfmove clock**, so that is measured through the bail, which reads it:
sweeping one board gives the boundary exactly at 100 (99 searches, 100 bails), and the replay's
carried clock agrees with the implied clock at **5,369/5,369 plies**.

## Headline

**A single-process replay changes the move 46% of the time and never changes whether the engine
bails.** The 46% is not a strength defect: against a depth-14 oracle the in-process move is better
78 / equal 39 / worse 83 of 200 (median 0 cp), and against depth 18 the reported score is no less
accurate (median error 34 vs 37 cp). What it *is*: `ucinewgame` between plies matches a fresh
process 5,401/5,401; `Clear Hash` and the same-value `Hash` resend each remove only ~2% of the
divergence; so **the history tables, not the TT, carry the state.** `ucinewgame` between *games*
(the realistic GUI shape) still leaves 44.2% divergence.

**The bail was the finding that would have mattered and it does not reproduce.** 89 firings, every
one at the last ply of a game that ended at its threefold; re-checked fresh 89/89 same move and 89/89
still bailing; independently predicted 89/89 by python-chess with zero false positives over 27,692
positions; and a planted mid-game threefold bails 40/40 in-process and 40/40 fresh while the same
fixture sent twice bails 0/40. Its predicate reads the board from the move list and never the
table, so warm state cannot move it.

## Controls that fired (proof the instruments work)

- RSS instrument: `Hash 32 → 1024 → 32` reads **40.6 → 1,032.6 → 40.6 MiB**.
- Bail detector: a planted threefold yields 0 nodes + empty pv + generator head; a twofold does not.
- Error metric: depth 1 is worse than depth 8 (59 vs 37 cp median) — only after moving the control
  into its own process, because run warm it returned the depth-18 score.
- Determinism: repeat session 0/27,788 diffs; repeat fresh 0/200.
- FEN/illegal rejections: **zero diagnostics across 104,968 searches.**

## Withdrawn

- "0 of 89 bails predicted" — my off-by-one, not the engine. Corrected to 89/89.
- **A first clock probe reported 11 mismatches. Its A/A control read 195/200 and showed the probe
  was broken** (warm-table repeat searches return 0 nodes + hash move, trap 2d0, which my bail
  detector read as a bail). Rebuilt with fresh processes: **0/5,369.** The 11 were the instrument.
- 185 "bails" — 96 are terminal `0000` roots (`mate 0`, no legal moves). Real count is 89.

## Left untested, with reasons

Table pressure (Hash 32, peak hashfull 40/1000), `Threads > 1`, `ponder`, and any bail interaction
needing a saturated table. The literal `position startpos moves` form had to be exercised on
generated self-play (3,420 plies) because **all 5,689 repo PGN games carry `[FEN]` headers** and
none begins at startpos.

## Files

- `FINDINGS.md` — result first, then evidence, then the withdrawals and gaps.
- `scripts/` — 13 scripts; `summary.py` regenerates every number in FINDINGS.md from `evidence/` alone.
- `evidence/` — per-ply JSONL (short keys, map in `keys.json`), bail prediction, planted fixtures,
  move-quality and calibration samples, RSS control, self-play corpus, run logs.
