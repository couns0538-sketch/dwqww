# T04C table - search gains logged by PlentyChess, Berserk and Alexandria (all GPL-3.0: titles, PR text, test logs only)

Lock = FD3A5190 source `src_al1s198_clean` (`src/search.cpp`, `src/board.cpp`); "Forge has it" = a `tools/forge_has.sh`
grep or a read of the lock file. Engines' own test conditions: PlentyChess OpenBench STC 8+0.08 16 MB / LTC 40+0.4
64 MB (furybench.com, chess.aronpetkovski.com); Berserk STC 10+0.1 8 MB / LTC 60+0.6 64 MB (chess.grantnet.us);
Alexandria STC 8+0.08 16 MB / LTC 40+0.4 64 MB; all Threads=1. Elo +- 95 % error, n = games. Forge estimates
are **UNPROVEN**. Mechanisms are described from titles only (no PR or commit gives a mechanism text; no source read).
Status PENDING rows are still being checked.

## A. Cards (candidates Forge lacks; logged >= +2 STC with an LTC result, or >= +3 STC)
| idea (card) | source + link | licence | logged numbers | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|
| QS fail-firm: return a value pulled toward beta on a qsearch fail high (T04C-01) | [PlentyChess 393](https://github.com/Yoshie2000/PlentyChess/pull/393), [329](https://github.com/Yoshie2000/PlentyChess/pull/329), [464](https://github.com/Yoshie2000/PlentyChess/pull/464); [Berserk 396920c](https://github.com/jhonnold/berserk/commit/396920cfea); [Alexandria 1ce77c8](https://github.com/PGG106/Alexandria/commit/1ce77c80ed) | GPL-3.0 x3 | PC 393 STC +6.73 +- 3.15 n=11,508 / LTC +3.88 +- 2.27 n=20,040 (both passed [0,2.5]); PC 329 stand pat STC +2.09 +- 1.62 / LTC +1.10 +- 1.07 (LLR 1.82, merged); PC 464 PV nodes +0.81 / +1.05; Berserk STC +3.57 +- 2.72 / LTC +1.00 +- 1.39 n=105,980 (LLR 1.80); Alexandria stand pat STC +3.39 +- 2.28 / LTC +0.03 +- 2.21 ("dead neutral") | LACKS: stand pat returns the raw eval `search.cpp:815-818`; capture cutoff breaks at `:860` and returns the raw best score at `:869`; 0 hits for fail.?firm / blend | card (full) |
| Lower singular beta at former-PV nodes (T04C-02) | [PlentyChess 286](https://github.com/Yoshie2000/PlentyChess/pull/286) | GPL-3.0 | STC +5.21 +- 3.51 n=9,938 LLR 2.13 [0,3]; LTC +5.34 +- 3.21 n=10,536 LLR 2.50 [0,3]; neither SPRT finished, merged | LACKS: `singular_beta = tt_score - SingularMargin * depth` at `search.cpp:1091` (no tt_pv term; tt_pv known at `:919`, used by LMR at `:1139`); SingularV2 (FB2-J3) has no such term | card (full) |
| TT replacement favouring the recent position (T04C-03) | [Berserk fe1363a](https://github.com/jhonnold/berserk/commit/fe1363af6b) | GPL-3.0 | STC +3.76 +- 2.12 n=27,964 [0,2]; LTC +5.77 +- 2.88 n=13,132 [0,2.5]; both passed | PENDING | PENDING |
| Quiet malus scaled down with the number of searched moves (T04C-04) | [Berserk 7451fd7](https://github.com/jhonnold/berserk/commit/7451fd7fde) | GPL-3.0 | STC +2.26 +- 1.55 n=52,326 [0,2]; LTC +2.04 +- 1.53 n=47,970 [0,2.5]; both passed | LACKS: every tried quiet gets the full -bonus `search.cpp:745-749`; 0 hits for malus | PENDING |

## B. Looked at, not carded (has it, tried, prepared, LTC flat, or mechanism unknown)
PENDING
