# T04P-01-failhigh-tt-deeper: a fail-high TT cutoff needs a one-ply-deeper entry (own port built, never gated)
Status: COMPLETE - evidence WEAKER than notes/CRITIC2.md line 16 says: Stockfish b280d2f (STC +3.91) measured the fail-low
side the lock already has, not this rule; PlentyChess 373 FAILED its STC (H0); the only passes of form A are at 40+0.4.

## Source
- Caissa [d39fcfb](https://github.com/Witek902/Caissa/commit/d39fcfb0d6) "Require higher depth for TT beta cutoff" (test
  furybench.com/test/1384), [9d566cc](https://github.com/Witek902/Caissa/commit/9d566ccbd5) "Tweak TT cutoff margin" (/7473):
  messages + one-line diffs. PlentyChess [PR 373](https://github.com/Yoshie2000/PlentyChess/pull/373) (merge 9c520de) text,
  tests /1382 (STC), /1373 (LTC). Stockfish [b280d2f](https://github.com/official-stockfish/Stockfish/commit/b280d2f065) =
  PR 5314 text + fishtest `api/get_run` args of 66578e2e6b0e318cefa8d447 (STC), 6657f46b6b0e318cefa8d7e9 (LTC).

## Licence
Caissa MIT at d39fcfb0d6 and 9d566ccbd5: copy with notice (the own port still needs its MIT notice before a merge, per its
CR pass note). PlentyChess GPL-3.0 at 9c520de7b7, Stockfish GPL-3.0 at b280d2f065: ideas only, no source or diff read.

## Mechanism
The lock takes a stored score as a cutoff at a non-PV node from an entry of equal depth whatever the result. The rule asks
one more ply when the stored score is >= beta (fail high), equal depth below beta. Form A (Caissa d39fcfb, PlentyChess 373;
Stockfish's state after b280d2f, whose own step went from "deeper for every cutoff" to "equal depth for fail lows"): every
fail high needs it. Form B (Caissa 9d566cc): only beta <= score < beta + M; a score clearly above beta cuts at equal depth.
The side of beta decides, not the bound (an exact entry above beta counts). Own reading (unproven): a same-depth cutoff just
above beta is the one most likely to flip with one more ply, and a false fail high drops a whole subtree.

## Forge fit
`bash tools/forge_has.sh 'tt_depth >= depth'` -> `src/search.cpp:921` (block :921-926: non-PV, no excluded move, usable
score, `tt_depth >= depth` for every bound, halfmove < 90, bound points the right way): LACKS. Own off-lock code HAS form B:
caissa_c123 (`forge_push/qa_ltopgo_al1_stage/cands/caissa_c123/...src`) `search.hpp:217`, `search.cpp:41`, `:89` (spin 0-200),
`:931-933`; CR PASS-notes 2026-10-30 ("bundle HELD; C3 LTC flag"); exe `forge_push/bin/forge_ltopgo_x_caissa_c123_al1_8924099a.exe`
(kit v2.3 -Expose, pc1 = pc2, OFF = pins); never gated (`tried_gates.py`: 0 rows). A gate item, not new code; form A is not
built. Same line as T04D-02 (node-type match): both only remove cutoffs; gate apart. qsearch, :1003, :1090 stay as they are.

## Expected gain
- Form A vs no rule: Caissa d39fcfb 40+0.4 Threads=1, [0.00, 2.50] LLR 2.95, N 48,018 W 11,008 L 10,717 D 26,293,
  +2.11 +- 1.55, no STC logged. PlentyChess 373: STC 8+0.08 [0.00, 2.50] LLR -2.25 = H0, N 29,214 W 7,116 L 7,222 D 14,876,
  -1.26 +- 2.03; LTC 40+0.4 LLR 3.02 passed, N 61,338 W 15,088 L 14,782 D 31,468, +1.73 +- 1.31. Books not in the logs.
- Form B vs form A: Caissa 9d566cc 10+0.1 Threads=1, [0.00, 2.00] LLR 2.95, N 112,192 W 26,924 L 26,487 D 58,781, +1.35 +- 1.06.
- Not this rule: Stockfish b280d2f (equal depth for fail lows; the lock has it): STC 10+0.1 1 thread UHO_Lichess_4852_v1
  [0,2] normalized LLR 2.93, 26,592 games W 6,944 L 6,645 D 13,003 (+3.91); LTC 60+0.6 [0.5,2.5] LLR 2.96, 142,572 games (+1.31).
Forge estimate: form B 0 to +2 Elo, form A -1 to +2 (TC-dependent) **UNPROVEN**; at [0,5] nElo with a 3,000-game cap a
+1 to +2 effect most likely ends capped (no decision).

## Effort
Crew 0.5 h for form B (no code: OFF pins, ON box at the start value, 2-minute smoke on the built exe, INDEX line; MIT notice
before any merge). Exact form A (no upper limit) +1.5 h (range change, kit rebuild, pins). CPU: STC to the 3,000-game cap
6-7 h at 430-502 games/h, +6-7 h if extended; LTC ~3x per game. GPU none.

## Test plan
OFF (margin 0): bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690
(lock pins; ALL_OK in `qa_v22_checks/xchk_caissa_c123_TtCutExtraMargin.json`). Box test ON at 72: fixed-depth bench
d11-d22 node counts become the ON reference (the record at 80 shows the shape: 342592/879873/2333863/12556911/39261538 =
+9.5 / +2.0 / -22.8 / +1.4 / +15.3 % vs OFF); TT cutoffs per 1M nodes split by side of beta OFF vs ON (fail-high
cutoffs from equal-depth entries with score < beta + M must reach 0); mate probe OFF/ON. Gate (crew route): Threads=1,
UHO, SPRT [0,5] normalized Elo, alpha = beta = 0.05, pentanomial, cap 3,000; capped = UNPROVEN / no decision, one
extension if its Elo is positive; STC then LTC. Form A only after B and only at LTC (its one STC test lost).

## OFF-by-default design
UCI spin `TtCutExtraMargin` (the port's name and range, so the built exe gates by setoption), default 0 = off, range 0-200
cp, own start 72 = one step of the lock's `RfpMargin` (search.cpp:23, the per-ply margin the lock already uses), not the
source's value; SPSA it after a first STC result. At 0 the added depth term is 0, so :921 is the lock's test and every
node and bench pin equals the lock. M = 200 on the same exe approximates form A (only scores >= beta + 200 cut at depth).
