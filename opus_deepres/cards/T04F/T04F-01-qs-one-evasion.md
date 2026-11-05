# T04F-01: qsearch in check: stop after the first evasion that is not mated
Status: COMPLETE

## Source
- Caissa a677c89 "QSearch: Aggressive check evasion pruning" (2023-08-23):
  https://github.com/Witek902/Caissa/commit/a677c890f9 (cutechess result block in the message; diff read).
- Caissa c8a30a7 "QSearch tweaks" (2023-08-17), which first stopped at the first quiet evasion (bundled with a
  futility retune): https://github.com/Witek902/Caissa/commit/c8a30a7d11
- Current form at HEAD: `src/backend/Search.cpp:1421` @57cae7ef71 (in check, break after the first evasion that raises
  the best score).
- Second engine: none found for the cut itself. Stormphrax PR 203 "Always try to find one non-mated move in qsearch"
  (PR text only, GPL-3.0): https://github.com/Ciekce/Stormphrax/pull/203 is the mated-range guard, which the lock
  already has (notes/T04B/TABLE.md row 50); it supports the guard kept in the design below, not the cut.

## Licence
Caissa @57cae7ef71 and at the 2022-2023 commits read: MIT (notes/T04F/licences.md). Copy allowed with notice; nothing
is copied here, the mechanism is described in own words. Stormphrax: GPL-3.0, ideas only; PR 203 text read, never
source.

## Mechanism
When the side to move is in check inside quiescence search, every legal evasion is normally searched, because the
stand pat is not allowed. The rule: once one evasion has returned a score that is not a "mated" score, stop and
return that best score; the remaining evasions are pruned. Ordering puts the TT move and the captures of the checker
first, so the first evasion is usually the best one. Caissa's raw rule breaks after the first evasion whatever its
score, which can report a mate that a later evasion avoids; the Forge version keeps searching while the best score
is still in the mated range, so a forced mate is never claimed by the pruning.

## Forge fit
`bash tools/forge_has.sh 'generate_evasions'` -> `src/search.cpp:414`, `:538`: in qsearch the lock generates and
searches all pseudo-legal evasions (`src/search.cpp:801-805` sets best = -Infinite in check; the loop
`:828-864` prunes only when not in check, `:831`); mated only when no legal move, `:865`. Tried nearby:
QsEvasionSeeNonPv (P27R-AL1, SEE filter on non-PV evasions, +4.63 Elo after 3,000 games, no decision) - a different
rule (SEE test per evasion, not a count cap). Change: one `break` after the move loop's score update, behind an option.

## Expected gain
Source: Caissa a677c89, cutechess SPRT llr 2.95 (bounds -2.94 / 2.94, Elo bounds not in the message), 1 thread,
n=25,531 (W 5052 L 4810 D 15669), Elo +3.3 +- 2.6 (LOS 99.3 %); TC and book not stated in the commit. c8a30a7 bundle:
+5.9 +- 4.8, n=8,606. No LTC logged by Caissa. Guard only (not the cut): Stormphrax PR 203, 8+0.08 +3.91 +- 2.57
n=20,596 [0,3], LTC 40+0.4 +3.36 +- 2.27 n=22,018 [0,3], 1 thread.
Forge estimate: +1 to +3 Elo at STC **UNPROVEN** (the lock already reaches in-check qsearch only after a checking
capture, so the node share may be smaller than the source's).

## Effort
Crew 1-2 h (option, OFF pins, ON bench, mate probe, WAC count). CPU: one STC SPRT [0, 5]; at the measured 430-502
games/h a 6,000-game run is about 12-14 h of the gate PC; LTC only after an STC H1. No GPU.

## Test plan
Pre-gate: OFF bench d11/d13/d16/d20/d22 = the lock pins; perft unchanged; ON bench nodes drop (record d13 and d22:
the P14 lesson was a d22 node blow-up and a tactics loss, so also count WAC 300 solved at fixed nodes OFF vs ON);
mate probe OFF/ON (no new false mate, no lost mate). Gate: UHO SPRT [0, 5] at STC, then LTC.

## OFF-by-default design
UCI spin `QsEvasionLimit` default 0 (off), range 0-4: at k > 0, in check, stop after k searched legal evasions once
the best score is above -MateInMaxPly. Own gate value 1 (the mechanism itself), second line 2 if 1 fails. At 0 the
new condition is false before any other test, so every node and the bench pins equal the lock.
