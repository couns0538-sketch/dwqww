# T04G designs kept from demoted cards

T04G-02 was a full card (earlier worker, 00:12); the 4-card rule (top 2 full) made it a one-line card at 00:29 when
T04G-05 was added. Its full text is kept here unchanged so nothing is lost.

## T04G-02 (full text as written at 00:12): Capture history split by the SEE class of the capture
Status: COMPLETE

### Source
Altair PR 120 "Index capture history by whether a move is winning or losing"
(https://github.com/Alex2262/AltairChessEngine/pull/120, merge 99df021453, 2023-09-21, test
https://chess.swehosting.se/test/3942/; patch read). Current form at Altair@b2447b825b: table `src/search.h:96`,
class at scoring `src/move_ordering.cpp:87-100`, class-local malus in `update_histories` `src/search.cpp:388-404`.

### Licence
MIT at b2447b825b and at the PR's commit (LICENSE touched once, 7f28fb4127, before the PR): copy with notice.
Nothing copied; mechanism in own words; no constants carried over.

### Mechanism
Two capture-history tables instead of one: one for captures that pass a static exchange test (expected not to lose
material), one for captures that fail it. A capture is ordered and judged by the entry of its own class. After a node,
the best capture gets its bonus in its class; the malus goes only to tried captures of the SAME class. So a sacrifice
that works here is learned in the losing table without lifting the same capture's normal statistics, and failed
winning captures do not drag down the sacrificial slot. Altair takes the class from SEE at scoring time (eager) and,
in qsearch, from the ordering score. Differs from CaptSeeDiv (TRIED) and Patricia PR 209 (T04 A7): those shift the SEE
split threshold; this splits the learned table.

### Forge fit
LACKS. `bash tools/forge_has.sh 'capture_history_'`: one table piece x to x victim (`include/forge/search.hpp:255`,
read `src/search.cpp:714-718`, scored before any SEE `:516`); bonus / malus to every tried capture, also when the best
move is quiet (`:752-766`, called at `:1200`). The class is known lazily: GoodCaptures returns only SEE >= 0
(`:360`), failures go to the bad list (`:361`) and come back in BadCaptures (`:398`); the TT capture and qsearch /
evasion captures have no class (`:405-423`). Design A (lazy, cheap): score GoodCaptures from the good table, re-score
deferred captures from the bad table and sort the bad list by it; record one class bit per `captures_tried` entry
(stage of return; TT capture = one see_ge at update time); class-local malus; the capture `history` at `:1058` reads
the class table. Design B (Altair-like, eager): see_ge for every generated capture at generation; costs SEE calls for
captures never reached, so it needs an nps ABBA beside the SPRT. qsearch keeps the good table (no SEE there).

### Expected gain
Altair PR 120: +3.63 +- 2.92 Elo (95 %), 8+0.08, Threads=1, Hash 32 MB, SPRT [0,5] (-2.25, 2.89), LLR 2.97,
n=27,168 (W 6,934 L 6,650 D 13,584); book not stated; no LTC. Same PR moved the class threshold slightly (a
second change), so the split alone is not isolated. 2023 Altair, weaker than today.
Forge estimate: 0 to +3 Elo **UNPROVEN** (design A).

### Effort
Crew ~5 h (design A ~35 lines: second table, class bits, bad-list sort, option; pins, ON-live, mutant, smoke); design
B adds an nps ABBA (~1 h). CPU: one STC SPRT [0,5] ~6.6k games ~13-15 h; LTC if STC passes. No GPU. Memory +12 KB per
worker (one more int16 13 x 64 x 7 table).

### Test plan
Pre-gate: OFF bench / perft pins equal to the lock; ON bench live; planted bug (class bit inverted) changes ON nodes;
ASan/UBSan row for the new indices; T1 smoke. Gate: UHO SPRT [0,5] at STC (Threads=1), then LTC. Design B only with a
palindromic nps ABBA first (expect a small nps loss; record it with the SPRT).

### OFF-by-default design
UCI option `CapHistSplit` (default 0, range 0-2): 1 = design A without the bad-list sort, 2 = with it. Own start
value 2; class test SEE >= 0 (the lock's split; own range -100..0 cp only after a first pass). At 0 the second table
is allocated but never read or written, and the old table path runs unchanged, so the bench pins are the lock's.
