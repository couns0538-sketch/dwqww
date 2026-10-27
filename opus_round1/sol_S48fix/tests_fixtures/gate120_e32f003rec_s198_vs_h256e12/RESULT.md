# gate120_e32f003rec_s198_vs_h256e12 RESULT: cand_h256_e32f003rec_s198 vs base_h256_e12 (h256_e12 LOCK)
- Written by forge_queue.ps1 v3-6day. Started 2026-10-25 12:50:00 PC (Vienna wall clock); fastchess exit code 0; attempt 1. Settings: fastchess 1.8.2, 10+0.1 timemargin=1000, Threads=1 Hash=16 OwnBook=false, 8moves_v3.pgn order=random start=321001, srand 344808634, 1500-game cap, concurrency 7, SPRT normalized [0,10] a=b=0.05, BelowNormal, CPUs 4-15, -recover (see RUN_INFO.json).
- Games: 928  W/L/D (candidate view): 184 / 121 / 623  Points 495.5 (53.39 %)
- Pentanomial Ptnml(0-2): [5, 74, 252, 119, 14]  complete pairs = 464
- Elo: 23.62 +/- 11.90   nElo: 44.52 +/- 22.35   LOS 100.00 %
- LLR: 2.99  bounds (-2.94, 2.94)  [elo0=0, elo1=10, normalized]
- Time losses: 0   Crashes/disconnects/stalls/illegal: 0   fastchess 'Warning;' lines: 0   (clean requires 0 and 0): CLEAN
- Orphan games (Games - 2*complete pairs): 0 
- Avg search depth (PGN comments, non-book moves): base_h256_e12: avg depth 21.06 over 59403 moves; cand_h256_e32f003rec_s198: avg depth 21.23 over 59439 moves
- PC nps (pre-gate paired bench d20, CPU 6): not measured for this gate
- Candidate options (candidate side only): none. Base side: none (enforced: static arg check + engine_io.log setoption check, see ENGINE_OPTIONS_CHECK.txt).
- Engine option check (engine_io.log, final): 2026-10-25 13:54:47 Vienna(PC clock) | gate120_e32f003rec_s198_vs_h256e12 engine option check PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 5610 setoption lines. seen: base_h256_e12|Hash=16 x935; base_h256_e12|OwnBook=false x935; base_h256_e12|Threads=1 x935; cand_h256_e32f003rec_s198|Hash=16 x935; cand_h256_e32f003rec_s198|OwnBook=false x935; cand_h256_e32f003rec_s198|Threads=1 x935 PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 5610 setoption lines. seen: base_h256_e12|Hash=16 x935; base_h256_e12|OwnBook=false x935; base_h256_e12|Threads=1 x935; cand_h256_e32f003rec_s198|Hash=16 x935; cand_h256_e32f003rec_s198|OwnBook=false x935; cand_h256_e32f003rec_s198|Threads=1 x935
- **Verdict: H1 accepted (SPRT [0,10] normalized, a=b=0.05: no measurable regression; not an Elo claim; needs a confirm gate before lock)**

Source: last 'Results of' block in D:\grok-pc-data\forge_push\gate120_e32f003rec_s198_vs_h256e12\gate120_e32f003rec_s198_vs_h256e12.log. Never read this as stronger unless the verdict says H1 accepted and the run is CLEAN. UNPROVEN until then; any H1 needs a confirm gate on new openings + new seed before lock.
