# T04T-01: In-check nodes skip the ply-4 continuation-history update
Status: COMPLETE

## Source
- Clockwork PR [#380](https://github.com/official-clockwork/Clockwork/pull/380) "Do not update long horizon conthists
  when in check", merged 2026-03-16, merge commit
  [b10cbf0133](https://github.com/official-clockwork/Clockwork/commit/b10cbf0133). Test logs:
  [STC ob.cwchess.org/test/1267](https://ob.cwchess.org/test/1267/), [LTC ob.cwchess.org/test/1272](https://ob.cwchess.org/test/1272/).
- The PR text says the author saw the rule in Stockfish (origin not known to him) and that it "heavily interacts" with
  the conthist sum-base update (Clockwork #234, the idea of T04S-01, merged there 2025-09-28, so it was in the base).
  No Stockfish page or source was opened for this card.

## Licence
AGPL-3.0 at b10cbf0133 (`tools/licence_at.py --row`, notes/T04T/licences.md): ideas only. Read: PR title, PR body
(test blocks), merge sha. No source file or diff opened.

## Mechanism
When a quiet move is credited or penalised in the continuation histories, the update normally walks back over the
earlier plies' move pairs. At a node whose side to move is in check, the move choice is forced by the check, so the
pairing with moves far back in the line says little; the rule keeps only the short-distance updates (1 and 2 plies
back) there and skips the long-distance ones. Which plies Clockwork counts as "long horizon" is not stated in the PR
text; it had 4-ply and 6-ply tables at the time (#181, #252).

## Forge fit
LACKS. `bash tools/forge_has.sh 'for \(const int back : \{1, 2, 4\}\)'` -> `src/search.cpp:721`: `update_continuation`
updates plies 1, 2 and 4 (ply 4 at half bonus, `:725`) with no in-check test. Four call sites use it: cutoff bonus
`:743`, malus loop `:748`, the LMR half bonus for a late quiet that beat alpha `:1156`, and the fail-low parent bonus
`:1208` (called with `ss - 1`). `SearchStack` already has `bool in_check` (`include/forge/search.hpp:275`), set at node entry (`:902`; qsearch `:784`). Change:
inside the loop, skip `back == 4` when the option is on and `ss->in_check`; one test covers all four sites, and the
`ss - 1` site then reads the parent's own check flag, which is the node that played the credited move. Forge's only
long-distance ply is 4, so its change is smaller than Clockwork's (which may also have skipped ply 6).
Caveat: the lock never reads at offset 4 (`forge_has.sh 'ss - 4'` = 1 hit, `:948`, the improving test). All offsets
share one continuation table set chosen by the earlier move (`ss->continuation`, `:1121`), and ordering reads it at
offsets 1 and 2 only (`quiet_history`, `:708-709`). So the ply-4 writes land in entries that are later read as 1- or
2-ply pairs: skipping them at in-check nodes does change the tree, but through that indirect path, not through a
4-ply ordering term as in the source. Check before any gate [last round, coordinator, unverified]: this indirect path is a lock quirk on its own - every ply-4 update leaks into the ply-1 / ply-2 reads of the same table set - so a plain "no ply-4 write" option (all nodes) is a separate, gateable screen; gate it apart from this card, never stacked untested.

## Expected gain
Clockwork #380, Threads=1, OpenBench, book not named in the PR (missing):
STC 8+0.08 Hash 16 MB +5.33 +- 3.19 Elo, n=15,584, [0,3] LLR 2.95, penta [177, 1808, 3606, 2001, 200] (own conversion
+9.1 nElo); LTC 40+0.4 Hash 64 MB +9.69 +- 4.28, n=7,068, [0,3] LLR 2.95, penta [27, 769, 1758, 940, 40] (+18.4 nElo).
Both measured on top of the sum-base update (T04S-01), which the lock lacks.
Forge estimate: +0 to +2 Elo **UNPROVEN** (one ply affected, half weight, never read at offset 4 in the lock;
interaction with T04S-01 unknown).

## Effort
Crew hours: ~1.5 (3-line option, OFF bench / perft pins, ON smoke, clean-room lint). CPU: one STC SPRT up to 3,000
games = ~6-7 h at 430-502 games/h; LTC only after an STC pass. GPU: none.

## Test plan
Pre-gate: OFF bench and perft equal to the lock pins (FD3A5190), ON bench differs and is stable over 2 runs, 2-minute
T1 smoke, no illegal moves. Gate route (crew rule): Threads=1, UHO book, SPRT [0,5] in normalized Elo, alpha = beta =
0.05, pentanomial, cap 3,000 games; capped = UNPROVEN / no decision, one extension if positive; then LTC on pass.
Gate it alone first; if T04S-01 passes later, re-test this on top of it (the source says the two interact).
Not a tried line: gates 31-33 tuned ContHist4Pct, a pack option outside the lock (`forge_has.sh 'ContHist4'` = 0
hits in the lock); this card changes no weight, it only skips ply-4 writes at in-check nodes. (verify: bundle gate 68 also carried ContHist4Pct=45 and passed H1 at [0,10]; a re-test on that bundle port is the natural follow-up.)

## OFF-by-default design
UCI spin `ContHistCheckShort`, default 0, range 0-1. At 0 the update loop runs exactly as the lock (no new branch
taken), so the tree, bench nodes and perft are the lock's. At 1 the ply-4 update is skipped at in-check nodes.
