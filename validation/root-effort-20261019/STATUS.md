# Stable root effort: reproduced bug repaired; strength pending

Source/tests `7125b3379a850de34041d42529cf95993607f93c`, isolated branch `forge/root-effort-20261019`.
Parent6.4.7 source2c0c7ef, publishedca01859. Accepted integration stays9108d012.
The hosted39325939081 job tests6.4.7 versus6.4.4; its result cannot validate6.4.8.

Actual parent traces reproduced cumulative ordinal buckets mixing different root
moves. Examplec3d5 was charged1355nodes from4moves instead of its601 of3355.
The stable full-Move map now records601. All28 completed iterations across4FENs
match independently summed actual child-event totals for EVERY stored move, with
exact untouched-parent final PV/score/node signatures. Original traces, frozen
source/header/library/binaries, commands, old proposals and verifier are retained
in actual-baseline-and-proposals.zip and actual-candidate-validation.zip.

The fix preserves cumulative depths/aspiration retries, excluded aborted children,
local denominator, constants, ordering/pruning/TT/NNUE. Keys initialize from legal
restricted root candidates; lookups occur only at root; release writes are guarded.
Added fixed storage is1KB/Worker. No timer retuning or heap map.

Release8/8 and ASan/UBSan8/8 passed, including core/perft,TT8,rule50,18,947legal
queries,UCI/ponder and tooling. Six cold/warm untimed1T cases and419798bench nodes
match parent. Seven Windows Wine checks passed;351063nodes and YMM/noFMA
unchanged-input gates pass. Independent package audit52/52passed, zero findings.
[Windows ZIP](../../releases/forge-6.4.8-candidate-windows-zen5.zip) SHA256
`4b4de385808f5a383aa60de6bfc09cf48c02e5d23c191624540026cdac95b55e`.

Decision: retain the correctness-tested isolated bug repair. Actual changed timed
stop, deadline safety on native hardware, NPS and equal-clock Elo remain unmeasured.
Zero6.4.8matchgames. Offline factor differences are not observed stopping decisions.
Next: audit pending6.4.7hosted evidence; test this repair separately before promotion.
