# Lazy MovePicker: correctness passed; speed/Elo pending

Source/tests `2c0c7efa49023d8e3f49de3f5596f333a3f01202`, branch `forge/lazy-movepicker-20261019`.
Parent6.4.6 source4e15dea (publication2ce76ad); accepted integration9108d012 unchanged.
All prior candidates, residual NNUE weights and floating operation order preserved.

The same direct-check masks are calculated only at quiet/evasion generation,
mutually exclusive stages each reached at most once. Ordinary qsearch and early
cutoffs avoid unused calculations. No added state, scores, move order or pruning.

Release8/8 and ASan/UBSan8/8 passed, including perft,UCI,ponder,TT8,rule50 and
18,947 legal-witness comparisons. Six cold/warm1T cases match parent exactly;
Linux419798bench nodes. Actual frozen parent/candidate MovePicker source TUs
produced60,138 identical ordered rows (9,590,268 bytes each), across10,023 cases
and6 variants, with nonzero histories/TT/killers/countermoves/dynamic quiet skip
and make/unmake restoration between calls. Original streams,exports,archives,
binaries,commands/logs and method limits are in differential-attempt1.zip.

Seven Windows Wine checks passed, benchmark351063nodes, with YMM/noFMA and
unchanged-input checks. Independent static artifact audit passed with zero findings.
[Windows ZIP](../../releases/forge-6.4.7-candidate-windows-zen5.zip), SHA256
`493511ad75bf340e1e0d1c4e0c842277f1987d2db0c80a26d3dfd29376e0aabb`. Native Windows/Ryzen validation remains pending.

Decision: retain the isolated correctness-tested speed candidate. No reliable NPS
or Elo difference is established on this host; zero new match games. Old full-engine
and fresh pinned-kernel AA failures remain saved. A separately calibrated bounded
native-Linux hosted pilot is prepared; launch/result unverified until recorded.
