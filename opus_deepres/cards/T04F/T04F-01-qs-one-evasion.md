# T04F-01: qsearch in check: stop after the first evasion that is not mated
Status: COMPLETE

## Source
- Caissa a677c89 "QSearch: Aggressive check evasion pruning" (2023-08-23): https://github.com/Witek902/Caissa/commit/a677c890f9
  and c8a30a7 "QSearch tweaks" (2023-08-17, first stop at the first quiet evasion, bundled with a futility retune):
  https://github.com/Witek902/Caissa/commit/c8a30a7d11 (result blocks in the messages; diffs read). HEAD form:
  `src/backend/Search.cpp:1421` @57cae7ef71 (in check, break after the first evasion that raises the best score).
- Same family, other rule (no engine found with the cut itself): Stockfish 392b529 (PR 3221) "Qsearch pruning:
  follow-up", https://github.com/official-stockfish/Stockfish/commit/392b529c3f (message + fishtest records only):
  the normal qsearch pruning also in check once a defense better than a TB loss exists. Stormphrax PR 203
  https://github.com/Ciekce/Stormphrax/pull/203 (PR text only) is, by its title, that guard; the lock has it (T04B row 50).

## Licence
Caissa @57cae7ef71 and the 2023 commits: MIT (notes/T04F/licences.md), copy allowed with notice; nothing copied.
Stockfish and Stormphrax: GPL-3.0, ideas only; commit message, PR text and test pages read, never source.

## Mechanism
In check inside quiescence search every legal evasion is normally searched, because stand pat is not allowed. The
rule: once one evasion has returned a score that is not a "mated" score, return; the remaining evasions are pruned.
Ordering puts the TT move and captures of the checker first, so the first evasion is usually the best. Caissa's raw
rule breaks after the first evasion whatever its score, which can report a mate that a later evasion avoids; the
Forge version keeps searching while the best score is still in the mated range, so the pruning never claims a mate.

## Forge fit
`bash tools/forge_has.sh 'generate_evasions'` -> `src/search.cpp:414`, `:538`. In qsearch the lock searches all
evasions: best = -Infinite in check (`src/search.cpp:801-805`); futility and SEE run only under
`!in_check && best_score > -MateInMaxPly` (`:831-839`); mated only with no legal move (`:865`). Tried nearby:
QsEvasionSeeNonPv (P27R-AL1, SEE filter per non-PV evasion, +4.63 after 3,000 games, no decision): another rule.
R15 C2 QsMovePrune (prepared, D:/o15/cands/INDEX.md) acts only out of check (patch inside `!in_check`): no overlap.

## Expected gain
Caissa a677c89: cutechess SPRT llr 2.95 (bounds -2.94 / 2.94; Elo bounds, TC, book and thread count not in the
message; corrected by verify: "1 thread" was not stated), n=25,531 (W 5052 L 4810 D 15669), +3.3 +- 2.6; c8a30a7 bundle +5.9 +- 4.8, n=8,606; no LTC logged.
Stockfish 392b529 (other rule): STC 10+0.1, Threads 1, noob_3moves, SPRT [-0.25,1.25] logistic, LLR 2.97, N=22,632
(W 2,433 L 2,264 D 17,935, about +2.6); LTC 60+0.6 [0.25,1.25] LLR 2.94 N=105,432 (about +1.0). Stormphrax PR 203
(guard only): 8+0.08 +3.91 +- 2.57 n=20,596 [0,3]; 40+0.4 +3.36 +- 2.27 n=22,018.
Forge estimate: +1 to +3 Elo at STC **UNPROVEN** (in the lock a qsearch node in check follows a checking capture
only, so the node share may be smaller than in the sources).

## Effort
Crew 1-2 h (option, OFF pins, ON bench, mate probe, WAC count). CPU: one STC SPRT [0, 5]; 3,000-game cap = 6-7 h at 430-502
games/h (measured at Threads 2 / conc 4; no Threads=1 rate measured); 6,000 games, about 12-14 h of the gate PC, = the cap + the one extension if capped positive (review fix, FIXER3: crew cap); queue it after the P27R-AL1 QsEvasionSeeNonPv=1 extension result, not beside it (second vote 2); LTC only after an STC H1. No GPU.

## Test plan
Pre-gate: OFF bench d11/d13/d16/d20/d22 = the lock pins; perft unchanged; ON bench nodes drop (record d13 and d22:
the P14 lesson was a d22 node blow-up and a tactics loss, so also count WAC 300 solved at fixed nodes OFF vs ON);
mate probe OFF/ON (no new false mate, no lost mate). Gate: UHO SPRT [0, 5] at STC, then LTC.

## OFF-by-default design
UCI spin `QsEvasionLimit` default 0 (off), range 0-4: at k > 0, in check, stop after k searched legal evasions once
the best score is above -MateInMaxPly. Own gate value 1, second line 2 if 1 fails. No option for the Stockfish form:
a SEE test on evasions is the tried P27R QsEvasionSeeNonPv line (re-run that one if wanted). At 0 the new condition
is false before any other test, so every node and the bench pins equal the lock.
