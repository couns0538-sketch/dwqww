# REPORT job18 — my area-1 finds re-run on the PC build under PC20 (Threads 1)

**What was asked.** TEXT 2: re-run my own finds on the PC build under settings PC20, and say in
each finding line which build and which settings it used. Plus the swarm rule: every score at
Threads 1.

**The answer — the headline.** **21-F9 is REPAIRED on the PC build.** On the base tree it misses
a mate in 1 at halfmove 100 in both colours; on the PC build it finds it in both colours, in
both PC20 and no-setoption configurations. I isolated the cause: it is the **compile-time**
`FORGE_FIX_ROOT_DRAWN` (default 1), not the PC20 options — the PC build finds the mate with NO
setoption at all, and the base build with S14 still misses it.

Three of my finds **survive on the PC build**: 21-F8 (`fullmove 0` refused), 21-F11
(checkmated root scored `mate 0`), and 21-F2 (a refused FEN still answers `readyok` and the next
search uses the old board). 21-C2 (illegal-prefix rule) is unchanged.

**How sure.** High. Four configurations × three cases, all Threads 1, every option verified
accepted (`no unknown option / invalid value / ERROR`), every FEN acceptance asserted, every
`nodes`/`bestmove` present or the run raises.

## The isolation table (pasted from `job18/isolate/summary.md`)

| config | case | mate in 1 | bestmove | verdict |
|---|---|---|---|---|
| pc, no setoption | W hm100 | e1e8 | **e1e8** | FOUND |
| pc, no setoption | B hm100 | a8a1 | **a8a1** | FOUND |
| pc, no setoption | W hm99 (control) | e1e8 | e1e8 | FOUND |
| pc, PC20 | W hm100 | e1e8 | **e1e8** | FOUND |
| pc, PC20 | B hm100 | a8a1 | **a8a1** | FOUND |
| pc, PC20 | W hm99 (control) | e1e8 | e1e8 | FOUND |
| base, no setoption | W hm100 | e1e8 | f2f3, `cp 0 nodes 0` | **MISSED** |
| base, no setoption | B hm100 | a8a1 | f7f6, `cp 0 nodes 0` | **MISSED** |
| base, no setoption | W hm99 (control) | e1e8 | e1e8 | FOUND |
| base, S14 | W hm100 | e1e8 | f2f3, `cp 0 nodes 0` | **MISSED** |
| base, S14 | B hm100 | a8a1 | f7f6, `cp 0 nodes 0` | **MISSED** |
| base, S14 | W hm99 (control) | e1e8 | e1e8 | FOUND |

Reading: the PC build finds the mate with **no options at all**, so the repair is in the source,
not in the options. `FORGE_FIX_ROOT_DRAWN` is `#define`d to 1 by default in
`src/search.cpp:35-36`, and under it the drawn-root test shrinks to
`board.is_insufficient_material()` only (`src/search.cpp:2575`), so a halfmove-100 or
third-occurrence root is searched normally.

## The PC20 re-run of every find (`job18/out/summary.md`)

PC build, ASan+UBSan, PC20, Threads 1:

| find | case | result on the PC build | python | verdict |
|---|---|---|---|---|
| 21-F9 | W hm100 | e1e8, 105 nodes | mate e1e8 | **REPAIRED** |
| 21-F9 | B hm100 | a8a1, 105 nodes | mate a8a1 | **REPAIRED** |
| 21-F9 | W hm99 / B hm99 | e1e8 / a8a1, 105 nodes | same | unchanged (control) |
| 21-F11 | checkmated root | `0000`, `score mate 0` | checkmate | **SURVIVES** |
| 21-F8 | fullmove 0 | **refused**, perft 1 = 20 (stale) | 15 legal | **SURVIVES** |
| 21-F8 | fullmove 1 (control) | accepted, perft 1 = 15 | 15 | unchanged |
| 21-F2 | refused FEN after a game | `g8f6` then `g8f6`, `readyok` still sent | – | **SURVIVES** |
| 21-C2 | illegal move at ply 10 of a long list | perft 1 = 26 | 26 | unchanged (rule holds) |

## What this means for the owner

- The fifty-move/root-draw defect that my 21-F9, seat 30's 30-F7, seat 01's S-F5 and seat 12's
  patch all describe is **already fixed in the PC's own build**. No action needed on the PC;
  the patch seat 12 wrote remains the right fix for the base tree.
- The three survivors are worth acting on because the PC build still has them:
  `fullmove 0` refused (a FEN python-chess accepts), `mate 0` on a checkmated root, and the
  stale board after a refused FEN with `readyok` still answered.

## Threads audit (the swarm rule)

- Every run here is Threads 1.
- Of all my recorded results, the only Threads > 1 usage is `job13/churn_tsan.py`, which is a
  threading test by design and **reports no scores at all**. So no score of mine is provisional
  for threading.
- `job6/safe_engine.py` defaults to `threads=1` and `OwnBook false`; everything since the
  19-F12 notice goes through it.

## What I did NOT do

- Did not run the O/G depth-12 sums on the PC build (file 4 says they are S14 numbers; my area
  does not need them).
- Did not test the PC build at Threads > 1, deliberately (swarm rule).
- Did not investigate whether `mate 0` is a downstream problem for a GUI; I found the score.

## What I am NOT sure about

- Whether the PC build's `MateAlphaGuard` option affects the `mate 0` case. `MateAlphaGuard true`
  was on in PC20 and `mate 0` still appeared, so the option does not fix it; whether it changes
  the score in other mate situations I did not test.

## Times

see `job18/stamps.txt`.
