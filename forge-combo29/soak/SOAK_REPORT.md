# Six-hour Forge soak

Start: 2026-11-14T05:32:25Z. Scheduled end: 2026-11-14T11:32:25Z.
Updated: 2026-11-14T06:42:19.536Z. Elapsed minutes: 69.91. Completed checkpoint pushes: 8.
Integration bf5574ee654a773f0ef3d06878707056b90cdad7; reference 16833ecc03b425586f91f4c8834dea8807bf4c22. Cloud-only, one agent.

| Phase | What ran | Counts | Status / faults |
| --- | --- | --- | --- |
| A | Both exact commits: Release, ASan/UBSan, TSan builds; both release bench11/13 and perft5; driver preparation | {"builds":6,"pin_checks":6,"batches":1} | Complete; faults 0 |
| B | timeout 450 /workspace/work/soak-run/play-asan --seed 4753014 --seconds 291 --threads 1 --nodes 2000 --depth 0 --trigger /workspace/work/soak-run/last-trigger.json | {"games":3281,"moves":465894,"searches":465894,"opening_moves":26248,"faults":0,"illegal":0,"missing":0,"badscore":0,"mates":2362,"stalemates":4,"repetitions":476,"fifty":200,"ply_caps":80,"insufficient":159,"sanitizer_reports":0,"batches_threads1":14,"batches":14} | Running; faults 0 |
| C | Not yet run | {} | Pending; faults 0 |
| D | Not yet run | {} | Pending; faults 0 |
| E | Not yet run | {} | Pending; faults 0 |
| F | Not yet run | {} | Pending; faults 0 |
| G | Not yet run | {} | Pending; faults 0 |
| H | Not yet run | {} | Pending; faults 0 |

Fault files: 0.

Engine sources/headers and existing tests are unchanged. Test programs and evidence only are added under soak/. Tools, temporary controllers, generated networks, opening book and binaries stay in the VM. No Elo or speed claim.

Self-play stops at checkmate, stalemate, threefold repetition, 100 halfmoves, a dead position by insufficient material, or 300 total plies. Moves count searched moves; opening moves are recorded separately. A completed batch is counted only from its final SUMMARY. Timed-out batches must be repeated with the same seed and are not added to totals.
