# SPEC_SEARCH: implementation specs for the lock-direct search cards T04-01, T04-03, T04-05, T04-06, T04-04

Started 00:51 PC clock (`date`), stop 01:36. Status: PARTIAL (every unfinished section says PENDING).
Lock FD3A5190 = AL1 s198 source, read-only:
`C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean` (below: `search.cpp` = `src/search.cpp`,
`search.hpp` = `include/forge/search.hpp`). Nothing here edits the engine; every Forge-side number is UNPROVEN.

## Facts read so far (00:55)
- search.cpp (1,531 lines) and search.hpp (408 lines) read in full; uci.cpp option code :160-225, bench :377-410.
- Option mechanism: an `int` in `namespace tune` (search.cpp:13-64), a row in `tune::parameters()` (:66-100), an
  `extern` in search.hpp:194-245; uci.cpp accepts any listed name via setoption (:204-215), advertises them only
  under FORGE_EXPOSE_TUNABLES (:174-181, kit -Expose). uci.cpp untouched (skill forge-r15-candidates).
- Pins (lock FD3A5190): bench d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354; perft 5 4865609,
  kiwipete 193690690. Bench = 8 FENs (uci.cpp:383-392), Hash 16, clear per FEN, Threads 1, TTAccess Exclusive.
- T04-01: :1095 verification passes cut_node; uses inside the verification frame: :1031 IIR, :1141 LMR +2,
  :1151 / :1160 child flags; :952 block skipped (excluded).
- T04-03: cutoff_count field search.hpp:273; clear (ss+1) :905; LMR read :1145; increment :1180; (ss+2)->killers
  :907 (slot exists); NMP :965-999; null_tries_ / null_cutoffs_ search.hpp:345-346, reset :1241-1242.
- T04-05: corr update gate :1216-1223 (capture skip :1219); see_ge board.cpp:932 (promotion handled :951-953).
- T04-06: singular block :1089-1111; double :1102; budget :1116. Own port source: git fable-fb2-j3
  (1efc0b2c) src/search.cpp:1218 (triple: non-PV, < singular_beta - 80, inherited doubles <= 4, !tt_capture) and
  :1236 (`extension >= 2`).
- T04-04: corrected_eval :638-645, update_correction :647-656, tables search.hpp:322-323, alloc :568-569,
  clear :581-582. Own minor key: F:/opus_scratch/r5/r5b/flake/base_src/include/forge/correction_plus.hpp:51-56
  (avalanche of piece bitboards x own odd multipliers, Board unchanged); CorrMinorWeight default 100 on git
  opus-r5a-singles src/search/tune.inc:39.

## Common parts
PENDING

## T04-01 SingularNonCut
PENDING

## T04-03 NmpFewCutoffs
PENDING

## T04-05 CorrUpdateBadCapture
PENDING

## T04-06 TripleExt
PENDING

## T04-04 MinorCorr / MajorCorr
PENDING
