# Six-hour Forge soak

Start: 2026-11-14T05:32:25Z. Scheduled end: 2026-11-14T11:32:25Z.
Updated: 2026-11-14T10:01:04.288Z. Elapsed minutes: 268.65. Completed checkpoint pushes: 33.
Integration bf5574ee654a773f0ef3d06878707056b90cdad7; reference 16833ecc03b425586f91f4c8834dea8807bf4c22. Cloud-only, one agent.

| Phase | What ran | Counts | Status / faults |
| --- | --- | --- | --- |
| A | Both exact commits: Release, ASan/UBSan, TSan builds; both release bench11/13 and perft5; driver preparation | {"builds":6,"pin_checks":6,"batches":1} | Complete; faults 0 |
| B | timeout 450 /workspace/work/soak-run/play-asan --seed 4753014 --seconds 291 --threads 1 --nodes 2000 --depth 0 --trigger /workspace/work/soak-run/last-trigger.json | {"games":3281,"moves":465894,"searches":465894,"opening_moves":26248,"faults":0,"illegal":0,"missing":0,"badscore":0,"mates":2362,"stalemates":4,"repetitions":476,"fifty":200,"ply_caps":80,"insufficient":159,"sanitizer_reports":0,"batches_threads1":14,"batches":14} | Complete; faults 0 |
| C | timeout 450 /workspace/work/soak-run/play-tsan --seed 4753024 --seconds 248 --threads 4 --nodes 2000 --depth 9 --trigger /workspace/work/soak-run/last-trigger.json --trace | {"games":87,"moves":13414,"searches":13414,"opening_moves":693,"faults":0,"illegal":0,"missing":0,"badscore":0,"mates":47,"stalemates":0,"repetitions":25,"fifty":5,"ply_caps":6,"insufficient":4,"sanitizer_reports":0,"batches_threads2":5,"batches":10,"batches_threads4":5} | Complete; faults 0 |
| D | timeout 450 /workspace/work/soak-run/net-driver --seed 4753038 --seconds 398 --net /workspace/work/soak-run/converted-lock.net --corpus /workspace/work/soak-run/playout-fens.txt | {"positions":1228600000,"incremental_checks":2457200000,"loaded_checks":1228600000,"nulls":66016048,"castles":371219,"en_passant":96725,"promotions":9752254,"captures":107868310,"damaged_file_checks":49144,"chunks":12286,"faults":0,"batches":14} | Complete; faults 0 |
| E | timeout -k 5 450 /workspace/work/soak-run/search-compare --mode compare --input /workspace/work/soak-run/compare-fens.txt --offset 114706 --lock /workspace/work/soak-run/build-lock-rel/forge --integration /workspace/work/soak-run/build-int-rel/forge --fault-dir /workspace/work/soak-run/pending-faults --seed 4753048 --seconds 282 | {"positions":129793,"differences":0,"selection_attempts":0,"selected":0,"lock_runs":0,"integration_runs":0,"lock_misses":0,"integration_misses":0,"lock_lost_mates":0,"integration_lost_mates":0,"lock_failures":0,"integration_failures":0,"faults":0,"batches":10} | Complete; faults 0 |
| F | timeout -k 5 450 /workspace/work/fastchess/fastchess -engine cmd=/workspace/work/soak-run/build-int-rel/forge name=integration -engine cmd=/workspace/work/soak-run/build-lock-rel/forge name=lock -each nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false -rounds 100 -games 2 -recover -concurrency 2 -ratinginterval 0 -output format=cutechess -scoreinterval 1 -srand 4753061 -openings file=/workspace/work/soak-run/openings/UHO_Lichess_4852_v1.epd format=epd order=random -pgnout file=/workspace/work/soak-run/matches/F-61-4753061.pgn append=false nodes=true -events file=/workspace/work/soak-run/matches/F-61-4753061.events -config outname=/workspace/work/soak-run/matches/F-61-4753061.config.json -log file=/workspace/work/soak-run/matches/F-61-4753061.engine.log level=trace append=false engine=true | {"games":2600,"wins":702,"losses":758,"draws":1140,"moves":370689,"illegal":0,"crashes":0,"disconnects":0,"other_abnormal":0,"unfinished":0,"aborted":0,"pair_0":30,"pair_half":220,"pair_1":849,"pair_1half":178,"pair_2":23,"faults":0,"batches":13} | Running; faults 0 |
| G | Not yet run | {} | Pending; faults 0 |
| H | Not yet run | {} | Pending; faults 0 |

Fault files: 0.

Engine sources/headers and existing tests are unchanged. Test programs and evidence only are added under soak/. Tools, temporary controllers, generated networks, opening book and binaries stay in the VM. No Elo or speed claim.

Self-play stops at checkmate, stalemate, threefold repetition, 100 halfmoves, a dead position by insufficient material, or 300 total plies. Moves count searched moves; opening moves are recorded separately. A completed batch is counted only from its final SUMMARY. Timed-out batches must be repeated with the same seed and are not added to totals.

Notes / limits:

- Phase C uses depth 9; the driver ignores its nodes argument whenever a positive depth is specified. Ordinary batches finish the current game after their time target, within the outer 450-second limit.
- Phase C completed five batches at Threads 2 and five at Threads 4: zero ThreadSanitizer reports, therefore zero distinct race source-line pairs. Seed 4753019 included one terminal opening before eight plies; actual opening plies are recorded rather than extended past mate.
- Phase E corpus seed 4754000: 100000 sampled official-book positions and 99020 distinct sampled playout FENs before terminal-position filtering; corpus SHA256 571fd73cf5ec3ddad78d6afc1dd65c57d7f4c3f8eaa424cbfbabe94a4a8b06c1. Full corpus provenance is in preparation/E-corpus-4754000.txt.

[Detailed description of branch changes](CHANGES.md).
