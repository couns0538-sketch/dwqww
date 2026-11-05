# T04C-01: Quiescence fail-firm: pull a qsearch fail-high toward beta (stand pat and capture cutoffs)
Status: COMPLETE

## Source
- PlentyChess PR 393 "Do fail medium in qsearch" (dev branch qs-fail-medium, merged 2025-09-17),
  https://github.com/Yoshie2000/PlentyChess/pull/393 ; tests https://furybench.com/test/2921/ (STC), https://furybench.com/test/2923/ (LTC).
- PlentyChess PR 329 "Fail medium in stand pat" (merged 2025-03-03), https://github.com/Yoshie2000/PlentyChess/pull/329
  (tests https://chess.aronpetkovski.com/test/8263/ , /8266/); PR 464 "Also apply fail-firm in qsearch pv-nodes",
  https://github.com/Yoshie2000/PlentyChess/pull/464 (https://furybench.com/test/4946/ , /4947/).
- Berserk 396920c (PR 544) "Average out fail highs in QS", https://github.com/jhonnold/berserk/commit/396920cfea
  (tests http://chess.grantnet.us/test/35597/ , /35604/); Alexandria 1ce77c8 (PR 531) "Qs stand pat failfirm",
  https://github.com/PGG106/Alexandria/commit/1ce77c80ed ; MIT cross-check in notes/T04/TABLE.md B: Caissa ae2eb0c +1.19.

## Licence
PlentyChess @fdbdbccab8, Berserk @a3a6f62397, Alexandria @829daf405e: GPL-3.0 (notes/T04C/licences.md) = ideas only. Read:
PR titles + OpenBench blocks, commit messages, test page furybench 2921; no source, no diff, no formula: the blend is own.

## Mechanism
A qsearch fail high proves only "score >= beta". The overshoot comes from one static eval (stand pat) or a short capture
line and is noisy; returned as is (fail soft) it travels up as a too-optimistic lower bound. Fail-firm keeps the bound
valid but returns beta + (score - beta) x K / 64 with 0 < K < 64, at two return points: (a) stand pat >= beta, (b) a
capture (or evasion) whose score >= beta. Mate scores (score or beta) pass unchanged. Reading of the logs: stand-pat-only
tests are LTC-flat (PlentyChess 329 +1.10, Alexandria 531 +0.03); Berserk 544 (return point not stated) +1.00 at LTC;
only PlentyChess 393 passed LTC. 393 came six months after 329 had blended the stand pat and is titled "in qsearch", so
(own inference from titles and dates) 393 added (b); PlentyChess has had both since. PV nodes (PR 464, < +1.1) left out.

## Forge fit
LACKS. Lock `src/search.cpp:815-818`: stand pat >= beta stores BoundLower and returns the raw eval; `:860` breaks on a
cutoff and `:868-869` store and return the raw best score. `forge_has.sh 'fail.?firm|fail.?medium|blend'` = 0 hits.
Tried relatives sit at other return points, never qsearch: FailHighBlend (main-search non-PV fail high pulled toward
beta by depth; gates 36 / 42: -2.08 / +0.46 Elo, 1,500 games each, no decision) and RfpReturnBlend=25 (gate 86: -16.42,
H0 at 868 games); T04 dropped Caissa's stand-pat number as under +1. qsearch is a different population: depth 0, no
TT-depth gate, stand pat decides most of its fail highs, and its scores are the leaf values of every main-search line.
Change: ~6 lines (two return points; the TT store at `:868` takes the blended value, which stays >= beta).

## Expected gain
- PlentyChess 393: STC 8+0.08, 1 thread, 16 MB, book UHO_4060_v2.epd, SPRT [0, 2.5]: +6.73 +- 3.15, n=11,508
  (W 2,896 L 2,673 D 5,939), LLR 2.93 passed; LTC 40+0.4, 64 MB: +3.88 +- 2.27, n=20,040, LLR 2.89 passed.
- PlentyChess 329 (stand pat): STC +2.09 +- 1.62 n=45,534 LLR 2.96 [0, 3] passed; LTC +1.10 +- 1.07 n=93,286, LLR 1.82
  (not passed, merged). PR 464 (PV nodes): STC +0.81 +- 0.96 n=120,068, LTC +1.05 +- 0.97 n=104,068.
- Berserk 544: STC 10+0.1, 8 MB, [0, 2]: +3.57 +- 2.72 n=29,550 LLR 2.90 passed; LTC 60+0.6, 64 MB: +1.00 +- 1.39
  n=105,980, LLR 1.80 (not passed, merged).
- Alexandria 531 (stand pat): STC 8+0.08 +3.39 +- 2.28 n=22,856 LLR 2.95 [0, 3] passed; LTC 40+0.4 +0.03 +- 2.21
  n=21,922, LLR -0.78 ("dead neutral"). Books of all tests but PlentyChess 393 are not stated.
Forge estimate: 0 to +2 Elo at STC and at LTC **UNPROVEN** (one LTC pass, three LTC-flat relatives).

## Effort
Crew ~1.5 h (two return points, option, mate guards, debug check, pins). CPU: UHO SPRT [0, 5] at STC, 3,000 games = 6-7 h
at 430-502 games/h, +6-7 h one extension if positive [last round, coordinator, unverified]; LTC ~3x per game. GPU: none.

## Test plan
Pre-gate: OFF bench pins d11 312866 / d13 862329 / d16 3024920 / d20 12389307 / d22 34048354 + perft; ON bench differs
(live); debug build asserts every blended return >= beta and mate scores unchanged; 2-minute smoke. Gate: UHO SPRT [0, 5]
at STC with QsFailFirm=3, Keep=32, then LTC, which decides (the logs say the gain shrinks with TC); flat STC: one line
QsFailFirm=2 (cutoffs only) before dropping.

## OFF-by-default design
UCI `QsFailFirm` bit mask, default 0 = off (1 = stand pat, 2 = capture / evasion cutoffs); `QsFailFirmKeep` 0-64 = share
of the overshoot kept in 64ths, default 32 (midpoint of fail hard 0 and fail soft 64; own start, SPSA range 16-48).
Non-PV qsearch only. OFF leaves both return points and the TT store exactly as the lock, so the bench pins hold.
