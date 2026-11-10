# IDEA_SOURCE: where each idea comes from, and what was copied

Job: bit-exact speed lane on combo29 (fable2), 2026-11-10. Times are Europe/Vienna.

**Copied code: none.** Every added line was written for this job against the combo29 lock source. No source file, constant or table of any other engine or library was opened, pasted or transcribed during this job. No GPL or AGPL source was read. The MIT library named below was not opened either; it is listed because a crew note that I did read traces an idea to it.

## Per candidate

| Candidate | Idea | Where I met it | Licence of that source | What I took |
|---|---|---|---|---|
| `FORGE_SPD_KING_PAWN_CACHE` (**not new**, see DUPCHECK.md) | Keep the king-shelter and king-pawn-distance terms in the pawn-cache entry, keyed by the king square | This job's own profile (`PROFILE.md`: the shelter loop is the largest CPU-bound block of `evaluate_king`) and the crew's card `opus_deepres/cards/T05B/T05B-01-pawn-king-entry.md`, whose design (64-byte entry, per-colour king square, summed score and shelter sum) this patch follows. The card names its precedents: Stockfish commit `f83b899f` "Cache king shelter info in pawns structure" (GPL-3.0, ideas only), Arasan's per-colour king-pawn hash (MIT), Ethereal's Pawn-King table and Weiss PR 374 (GPL-3.0, ideas only). **The project's own commit `928f1ff7` (2026-10-13, Cursor branch) already implemented the shelter part**; I found it only after writing this patch (10:19, re-run of the duplicate search) and had not read its code before | card and commit: project-internal; named precedents: GPL-3.0 and MIT, none opened by me | The idea, as the card states it. My code was written against combo29 before I saw `928f1ff7`; it differs in caching the king-pawn distance too and in trusting a record only when both stored pawn bitboards and the king square equal the position's |
| `FORGE_SPD_WITNESS_NOPIN` | `has_legal_move`: a pawn on no line through its own king cannot be pinned, so its quiet push needs no legality test | `opus_speed/PLAN_HUNT.md` queue item 2 (`HASLEGAL_FAST`, 2026-11-05), never built; the exact call counts come from QA's PGO profile of combo29 | project-internal | The idea. Code is mine and uses the engine's existing `attacks::line` |
| `FORGE_SPD_EVADE_LEGAL` | `is_legal` in check: a non-king move is legal iff it captures the single checker or lands between checker and king, and respects the pin | Deep-research card T05C-01 and `notes/T05C/TABLE.md`, `BOARD_COST.md` rows 4-5. That card names its own source: the check mask and pin mask of `Disservin/chess-library` `movegen.hpp` at `430266434a` (MIT, checked by the crew in `notes/T05C` verification table) | card: project-internal; library: MIT | The rule as the card states it, which is textbook check evasion. I did not open the library. Code is mine, built on the lock's existing king lines (`king_lines_.pinned`, `attacks::between`) |
| `FORGE_SPD_PAWN_CAPMASK` | Visit only the pawns that attack an enemy piece | Own reading of QA's PGO counters (9.73M loop iterations for 0.68M captures). No listing found in the corpus or on the PC. Set-wise pawn attacks are standard bitboard practice | none | Uses the engine's existing `pawn_attacks_bb` |
| `FORGE_SPD_CHECKERS_KL` | `make_move`: read the new checkers from the mover's king lines instead of a full `attackers_to` | Card T05C-01 row 7 proposes a caller-supplied hint for the same recompute. The geometric argument is the one already written in the lock's own `gives_check` comment (KING_LINES, in the lock) | project-internal | The goal. My version needs no interface change: it reads `check_squares` and `discoverers` that `refresh_king_lines` already builds. Code is mine |

## Tools and method

| Item | Source | Licence | Use |
|---|---|---|---|
| Build recipe | the lock's own `build.log` in QA's pack `pack_combo29_20261108` | project-internal | command lines reproduced token for token apart from paths (`tools/spd_build.ps1`) |
| Identity checks (cold rows, warm session, soak, ABBA shape) | QA's adapters `overnight_timing_20261108\adapter\` and `quiet_abba_e4_c2_20261109\adapter\abba_combo29.ps1`, read for their method | project-internal | row format and settings followed; scripts written new (`tools/spd_uci.py`), no QA file edited or copied |
| `tree_index.py`, `fetch_corpus.py` | own tools of the earlier job on branch `fable52-search-gap-20261109` | own | reused for the duplicate check |
| Perft reference counts | the published standard perft positions (startpos, "kiwipete", positions 3-6), as already used in crew notes | public facts | expected node counts in `tools/spd_uci.py` |
| Compiler and runtime | llvm-mingw 20261104, clang 23.1.5 (sha256 `d05fee2c...`) with the `C:/msys64/ucrt64` sysroot: exactly the lock receipt's toolchain | as for the lock itself; this job adds no library and changes no link input | read and execute only |
| Timing with a new copy of the exe per arm (`spd_uci.py abba --recopy`, `timing2.ps1`, `file_effect.py`) | Own, from this job's own measurements (BENCH.md section 3.1). That the layout of a program in memory can bias a timing by more than the effect under test is known from the literature: Mytkowicz, Diwan, Hauswirth and Sweeney, "Producing wrong data without doing anything obviously wrong!" (ASPLOS 2009), and Curtsinger and Berger, "Stabilizer" (ASPLOS 2013). Both are named from memory as background; neither was opened during this job and no code or method text comes from them | own code; papers: ideas only | the second timing step and the copy test |
| `BUNDLE3` | no new idea: `EVADE_LEGAL`, `PAWN_CAPMASK` and `CHECKERS_KL` applied together, chosen after `WITNESS_NOPIN` timed slower under load | own | the three-switch bundle |

## What is not here

No Stockfish, Leela or other GPL/AGPL code or data. No net, dataset or book was created or changed. The harness links the engine's own units and adds no third-party code.
