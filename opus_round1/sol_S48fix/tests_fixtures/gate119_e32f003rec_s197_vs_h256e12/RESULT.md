# gate119_e32f003rec_s197_vs_h256e12 RESULT: cand_h256_e32f003rec_s197 vs base_h256_e12 (h256_e12 LOCK)
- Written by forge_queue.ps1 v3-6day. Started 2026-10-25 10:20:58 PC (Vienna wall clock); fastchess exit code 0; attempt 1. Settings: fastchess 1.8.2, 10+0.1 timemargin=1000, Threads=1 Hash=16 OwnBook=false, 8moves_v3.pgn order=random start=315001, srand 624700778, 1500-game cap, concurrency 5, SPRT normalized [0,10] a=b=0.05, BelowNormal, CPUs 4-15, -recover (see RUN_INFO.json).
- Games: 1500  W/L/D (candidate view): 226 / 185 / 1089  Points 770.5 (51.37 %)
- Pentanomial Ptnml(0-2): [9, 130, 435, 163, 13]  complete pairs = 750
- Elo: 9.50 +/- 8.84   nElo: 18.90 +/- 17.58   LOS 98.24 %
- LLR: 1.72  bounds (-2.94, 2.94)  [elo0=0, elo1=10, normalized]
- Time losses: 0   Crashes/disconnects/stalls/illegal: 0   fastchess 'Warning;' lines: 0   (clean requires 0 and 0): CLEAN
- Orphan games (Games - 2*complete pairs): 0 
- Avg search depth (PGN comments, non-book moves): base_h256_e12: avg depth 21.50 over 98769 moves; cand_h256_e32f003rec_s197: avg depth 21.52 over 98763 moves
- PC nps (pre-gate paired bench d20, CPU 6): not measured for this gate
- Candidate options (candidate side only): none. Base side: none (enforced: static arg check + engine_io.log setoption check, see ENGINE_OPTIONS_CHECK.txt).
- Engine option check (engine_io.log, final): 2026-10-25 12:49:05 Vienna(PC clock) | gate119_e32f003rec_s197_vs_h256e12 engine option check PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 9000 setoption lines. seen: base_h256_e12|Hash=16 x1500; base_h256_e12|OwnBook=false x1500; base_h256_e12|Threads=1 x1500; cand_h256_e32f003rec_s197|Hash=16 x1500; cand_h256_e32f003rec_s197|OwnBook=false x1500; cand_h256_e32f003rec_s197|Threads=1 x1500 PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 9000 setoption lines. seen: base_h256_e12|Hash=16 x1500; base_h256_e12|OwnBook=false x1500; base_h256_e12|Threads=1 x1500; cand_h256_e32f003rec_s197|Hash=16 x1500; cand_h256_e32f003rec_s197|OwnBook=false x1500; cand_h256_e32f003rec_s197|Threads=1 x1500
- **Verdict: Cap with no decision (LLR 1.72 inside (-2.94, 2.94)); nothing claimed**

Source: last 'Results of' block in D:\grok-pc-data\forge_push\gate119_e32f003rec_s197_vs_h256e12\gate119_e32f003rec_s197_vs_h256e12.log. Never read this as stronger unless the verdict says H1 accepted and the run is CLEAN. UNPROVEN until then; any H1 needs a confirm gate on new openings + new seed before lock.
