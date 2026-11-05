# T04U sources (one line per source read: url or repo@sha | licence tier | what it gave | card id or "no card")
Reading rule: Clockwork (AGPL-3.0), Tarnished (GPL-3.0), motor (no licence): PR titles, PR bodies, test logs only;
never a source file, diff or compare link.

- local, no fetch: notes/T04T/TABLE.md, notes/T04T/sources.md, cards/T04T/*, notes/T04T/VERIFY.md, F:/odr/work/T04T/tests_Clockwork.txt (#281 rows) | own crew notes | brief inputs, penta of #281 | T04U-01
- github.com/official-clockwork/Clockwork/pull/281 (gh api pulls/281; merge 305e45878f, 2025-10-09; 0 comments, 0 review comments) | AGPL-3.0, PR text only | title "Move check extensions into LMR", two OpenBench blocks, bench line; no mechanism text | T04U-01
- clockworkopenbench.pythonanywhere.com/test/702/ (dead: hosting placeholder page) then ob.cwchess.org/test/702/ (same test id) | test log | STC settings: UHO_Lichess_4852_v1.epd, Threads=1, Hash 16, win adj movecount=5 score=600, draw adj movenumber=40 movecount=8 score=5; dev bench 11,595,447 vs base bench 17,351,435 (-33 % nodes) | T04U-01
- own lock reads (src_al1s198_clean, read-only): src/search.cpp:1086-1170 (extensions + LMR), forge_has.sh 'gives_check' / 'CheckExtensionDepth' / 'CheckExtDepthCap' / 'last_move_see_nonnegative'; tools/tried_gates.py --grep 'Check|LmrCheck|Ext' | own code | Forge-has cell, neighbour gate 59 | T04U-01
