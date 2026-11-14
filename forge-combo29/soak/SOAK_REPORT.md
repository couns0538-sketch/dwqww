# Six-hour Forge soak

Start: 2026-11-14T05:32:25Z. Scheduled end: 2026-11-14T11:32:25Z.
Updated: 2026-11-14T11:06:19.585Z. Elapsed minutes: 333.91. Completed checkpoint pushes: 41.
Integration bf5574ee654a773f0ef3d06878707056b90cdad7; reference 16833ecc03b425586f91f4c8834dea8807bf4c22. Cloud-only, one agent.

| Phase | What ran | Counts | Status / faults |
| --- | --- | --- | --- |
| A | Both exact commits: Release, ASan/UBSan, TSan builds; both release bench11/13 and perft5; driver preparation | {"builds":6,"pin_checks":6,"batches":1} | Complete; faults 0 |
| B | timeout -k 5 450 /workspace/work/soak-run/play-asan --seed 4753077 --seconds 282 --threads 1 --nodes 20000 --depth 0 --trigger /workspace/work/soak-run/last-trigger.json | {"games":4176,"moves":593782,"searches":593782,"opening_moves":33408,"faults":0,"illegal":0,"missing":0,"badscore":0,"mates":3015,"stalemates":5,"repetitions":612,"fifty":253,"ply_caps":98,"insufficient":193,"sanitizer_reports":0,"batches_threads1":20,"batches":20} | Running; faults 0 |
| C | timeout -k 5 450 /workspace/work/soak-run/play-tsan --seed 4753079 --seconds 215 --threads 4 --nodes 2000 --depth 9 --trigger /workspace/work/soak-run/last-trigger.json --trace | {"games":101,"moves":15981,"searches":15981,"opening_moves":805,"faults":0,"illegal":0,"missing":0,"badscore":0,"mates":53,"stalemates":0,"repetitions":29,"fifty":7,"ply_caps":7,"insufficient":5,"sanitizer_reports":0,"batches_threads2":6,"batches":12,"batches_threads4":6} | Running; faults 0 |
| D | timeout 450 /workspace/work/soak-run/net-driver --seed 4753038 --seconds 398 --net /workspace/work/soak-run/converted-lock.net --corpus /workspace/work/soak-run/playout-fens.txt | {"positions":1228600000,"incremental_checks":2457200000,"loaded_checks":1228600000,"nulls":66016048,"castles":371219,"en_passant":96725,"promotions":9752254,"captures":107868310,"damaged_file_checks":49144,"chunks":12286,"faults":0,"batches":14} | Complete; faults 0 |
| E | timeout -k 5 450 /workspace/work/soak-run/search-compare --mode compare --input /workspace/work/soak-run/compare-fens.txt --offset 114706 --lock /workspace/work/soak-run/build-lock-rel/forge --integration /workspace/work/soak-run/build-int-rel/forge --fault-dir /workspace/work/soak-run/pending-faults --seed 4753048 --seconds 282 | {"positions":129793,"differences":0,"selection_attempts":0,"selected":0,"lock_runs":0,"integration_runs":0,"lock_misses":0,"integration_misses":0,"lock_lost_mates":0,"integration_lost_mates":0,"lock_failures":0,"integration_failures":0,"faults":0,"batches":10} | Complete; faults 0 |
| F | timeout -k 5 450 /workspace/work/fastchess/fastchess -engine cmd=/workspace/work/soak-run/build-int-rel/forge name=integration -engine cmd=/workspace/work/soak-run/build-lock-rel/forge name=lock -each nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false -rounds 100 -games 2 -recover -concurrency 2 -ratinginterval 0 -output format=cutechess -scoreinterval 1 -srand 4753069 -openings file=/workspace/work/soak-run/openings/UHO_Lichess_4852_v1.epd format=epd order=random -pgnout file=/workspace/work/soak-run/matches/F-69-4753069.pgn append=false nodes=true -events file=/workspace/work/soak-run/matches/F-69-4753069.events -config outname=/workspace/work/soak-run/matches/F-69-4753069.config.json -log file=/workspace/work/soak-run/matches/F-69-4753069.engine.log level=trace append=false engine=true | {"games":4200,"wins":1136,"losses":1205,"draws":1859,"moves":594779,"illegal":0,"crashes":0,"disconnects":0,"other_abnormal":0,"unfinished":0,"aborted":0,"pair_0":45,"pair_half":342,"pair_1":1390,"pair_1half":283,"pair_2":40,"faults":0,"batches":21} | Complete; faults 0 |
| G | timeout -k 5 450 /workspace/work/soak-run/search-compare --mode krk --input /workspace/work/soak-run/krk-fens.txt --offset 0 --lock /workspace/work/soak-run/build-lock-rel/forge --integration /workspace/work/soak-run/build-int-rel/forge --fault-dir /workspace/work/soak-run/pending-faults --seed 4753071 --seconds 240 | {"positions":40,"differences":0,"selection_attempts":208,"selected":40,"lock_runs":400,"integration_runs":400,"lock_misses":58,"integration_misses":53,"lock_lost_mates":0,"integration_lost_mates":0,"lock_failures":58,"integration_failures":53,"faults":27,"batches":2} | Complete: 40 roots, 400 runs per build; missing-mate faults recorded; faults 27 |
| H | Additional B/C/F rotations | {"batches":8,"B_batches":6,"B_games":895,"B_moves":127888,"B_searches":127888,"B_opening_moves":7160,"B_faults":0,"B_illegal":0,"B_missing":0,"B_badscore":0,"B_mates":653,"B_stalemates":1,"B_repetitions":136,"B_fifty":53,"B_ply_caps":18,"B_insufficient":34,"B_sanitizer_reports":0,"B_batches_threads1":6,"B_batches_nodes2000":3,"B_batches_nodes20000":3,"C_batches":2,"C_games":14,"C_moves":2567,"C_searches":2567,"C_opening_moves":112,"C_faults":0,"C_illegal":0,"C_missing":0,"C_badscore":0,"C_mates":6,"C_stalemates":0,"C_repetitions":4,"C_fifty":2,"C_ply_caps":1,"C_insufficient":1,"C_sanitizer_reports":0,"C_batches_threads2":1,"C_batches_threads4":1} | Running; faults 0 |

Fault files: 27.
- [001.txt](faults/001.txt): integration: missing mate score 3/10; FEN 8/3R4/8/8/8/k7/8/4K3 w - - 0 1
- [002.txt](faults/002.txt): lock: missing mate score 6/10; FEN 8/3R4/8/8/8/k7/8/4K3 w - - 0 1
- [003.txt](faults/003.txt): integration: missing mate score 4/10; FEN 8/8/8/4R3/5K2/8/8/k7 w - - 0 1
- [004.txt](faults/004.txt): lock: missing mate score 6/10; FEN 8/8/8/4R3/5K2/8/8/k7 w - - 0 1
- [005.txt](faults/005.txt): integration: missing mate score 1/10; FEN 8/8/8/k7/3R4/1K6/8/8 w - - 0 1
- [006.txt](faults/006.txt): lock: missing mate score 2/10; FEN 8/8/8/k7/3R4/1K6/8/8 w - - 0 1
- [007.txt](faults/007.txt): integration: missing mate score 2/10; FEN 8/6K1/8/8/8/8/3R4/7k w - - 0 1
- [008.txt](faults/008.txt): lock: missing mate score 2/10; FEN 8/6K1/8/8/8/8/3R4/7k w - - 0 1
- [009.txt](faults/009.txt): integration: missing mate score 2/10; FEN 2k5/4K1R1/8/8/8/8/8/8 w - - 0 1
- [010.txt](faults/010.txt): integration: missing mate score 8/10; FEN 8/8/1k6/3K2R1/8/8/8/8 w - - 0 1
- [011.txt](faults/011.txt): lock: missing mate score 5/10; FEN 8/8/1k6/3K2R1/8/8/8/8 w - - 0 1
- [012.txt](faults/012.txt): integration: missing mate score 1/10; FEN 8/8/1k6/8/1K6/2R5/8/8 w - - 0 1
- [013.txt](faults/013.txt): lock: missing mate score 1/10; FEN 8/8/1k6/8/1K6/2R5/8/8 w - - 0 1
- [014.txt](faults/014.txt): lock: missing mate score 1/10; FEN 8/8/2R5/8/8/8/8/3K1k2 w - - 0 1
- [015.txt](faults/015.txt): integration: missing mate score 2/10; FEN 5K2/8/7k/8/1R6/8/8/8 w - - 0 1
- [016.txt](faults/016.txt): lock: missing mate score 6/10; FEN 5K2/8/7k/8/1R6/8/8/8 w - - 0 1
- [017.txt](faults/017.txt): integration: missing mate score 6/10; FEN 8/7R/8/5K2/8/8/k7/8 w - - 0 1
- [018.txt](faults/018.txt): lock: missing mate score 3/10; FEN 8/7R/8/5K2/8/8/k7/8 w - - 0 1
- [019.txt](faults/019.txt): integration: missing mate score 2/10; FEN 3K4/1k6/8/8/3R4/8/8/8 w - - 0 1
- [020.txt](faults/020.txt): lock: missing mate score 1/10; FEN 3K4/1k6/8/8/3R4/8/8/8 w - - 0 1
- [021.txt](faults/021.txt): integration: missing mate score 6/10; FEN 8/8/8/8/7K/8/R7/6k1 w - - 0 1
- [022.txt](faults/022.txt): lock: missing mate score 8/10; FEN 8/8/8/8/7K/8/R7/6k1 w - - 0 1
- [023.txt](faults/023.txt): integration: missing mate score 6/10; FEN 1k6/8/8/7R/4K3/8/8/8 w - - 0 1
- [024.txt](faults/024.txt): lock: missing mate score 6/10; FEN 1k6/8/8/7R/4K3/8/8/8 w - - 0 1
- [025.txt](faults/025.txt): lock: missing mate score 1/10; FEN 8/8/8/8/1R6/5k2/3K4/8 w - - 0 1
- [026.txt](faults/026.txt): integration: missing mate score 10/10; FEN 7k/8/3K4/8/8/8/8/5R2 w - - 0 1
- [027.txt](faults/027.txt): lock: missing mate score 10/10; FEN 7k/8/3K4/8/8/8/8/5R2 w - - 0 1

B/C/F totals include their H repetitions. The H row lists the additional H work separately.

Engine sources/headers and existing tests are unchanged. Test programs and evidence only are added under soak/. Tools, temporary controllers, generated networks, opening book and binaries stay in the VM. No Elo or speed claim.

Self-play stops at checkmate, stalemate, threefold repetition, 100 halfmoves, a dead position by insufficient material, or 300 total plies. Moves count searched moves; opening moves are recorded separately. A completed batch is counted only from its final SUMMARY. Timed-out batches must be repeated with the same seed and are not added to totals.

Notes / limits:

- Phase C uses depth 9; the driver ignores its nodes argument whenever a positive depth is specified. Ordinary batches finish the current game after their time target, within the outer 450-second limit.
- Phase C completed five batches at Threads 2 and five at Threads 4: zero ThreadSanitizer reports, therefore zero distinct race source-line pairs. Seed 4753019 included one terminal opening before eight plies; actual opening plies are recorded rather than extended past mate.
- Phase E corpus seed 4754000: 100000 sampled official-book positions and 99020 distinct sampled playout FENs before terminal-position filtering; corpus SHA256 571fd73cf5ec3ddad78d6afc1dd65c57d7f4c3f8eaa424cbfbabe94a4a8b06c1. Full corpus provenance is in preparation/E-corpus-4754000.txt.
- G used 40 fixed-seed KRK roots, selected from 208 candidates. Lock missed a mate score in 58/400 two-thread searches and integration in 53/400; no mate-losing move was detected. The 27 fault files contain all ten trials per affected root/build. The historical 57/400 sample was not supplied and is not the sample measured here.
- G met its 40-root and 400-runs-per-build targets before its time allowance; remaining time is assigned to H, as required when phases finish early.
- H ASan/UBSan rotation ran from 10:28:32 to 10:58:26 UTC: six batches, three at nodes 2000 and three at nodes 20000; 895 complete games and 127888 searches; zero validation faults and zero sanitizer reports.

[Detailed description of branch changes](CHANGES.md).
