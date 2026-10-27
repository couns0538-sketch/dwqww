# gate120_e32f003rec_s198_vs_h256e12_confirm RESULT: cand_h256_e32f003rec_s198 vs base_h256_e12 (h256_e12 LOCK)
- Written by forge_queue.ps1 v3-6day. Started 2026-10-25 13:55:36 PC (Vienna wall clock); fastchess exit code 0; attempt 1. Settings: fastchess 1.8.2, 10+0.1 timemargin=1000, Threads=1 Hash=16 OwnBook=false, 8moves_v3.pgn order=random start=348001, srand 1983003762, 1500-game cap, concurrency 7, SPRT normalized [0,10] a=b=0.05, BelowNormal, CPUs 4-15, -recover (see RUN_INFO.json).
- Games: 1418  W/L/D (candidate view): 210 / 151 / 1057  Points 738.5 (52.08 %)
- Pentanomial Ptnml(0-2): [5, 103, 444, 142, 15]  complete pairs = 709
- Elo: 14.46 +/- 8.61   nElo: 30.43 +/- 18.08   LOS 99.95 %
- LLR: 2.98  bounds (-2.94, 2.94)  [elo0=0, elo1=10, normalized]
- Time losses: 0   Crashes/disconnects/stalls/illegal: 0   fastchess 'Warning;' lines: 0   (clean requires 0 and 0): CLEAN
- Orphan games (Games - 2*complete pairs): 0 
- Avg search depth (PGN comments, non-book moves): base_h256_e12: avg depth 21.52 over 94668 moves; cand_h256_e32f003rec_s198: avg depth 21.55 over 94692 moves
- PC nps (pre-gate paired bench d20, CPU 6): not measured for this gate
- Candidate options (candidate side only): none. Base side: none (enforced: static arg check + engine_io.log setoption check, see ENGINE_OPTIONS_CHECK.txt).
- Engine option check (engine_io.log, final): 2026-10-25 15:36:45 Vienna(PC clock) | gate120_e32f003rec_s198_vs_h256e12_confirm engine option check PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 8544 setoption lines. seen: base_h256_e12|Hash=16 x1424; base_h256_e12|OwnBook=false x1424; base_h256_e12|Threads=1 x1424; cand_h256_e32f003rec_s198|Hash=16 x1424; cand_h256_e32f003rec_s198|OwnBook=false x1424; cand_h256_e32f003rec_s198|Threads=1 x1424 PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 8544 setoption lines. seen: base_h256_e12|Hash=16 x1424; base_h256_e12|OwnBook=false x1424; base_h256_e12|Threads=1 x1424; cand_h256_e32f003rec_s198|Hash=16 x1424; cand_h256_e32f003rec_s198|OwnBook=false x1424; cand_h256_e32f003rec_s198|Threads=1 x1424
- **Verdict: H1 accepted (SPRT [0,10] normalized, a=b=0.05: no measurable regression; not an Elo claim; needs a confirm gate before lock)**

Source: last 'Results of' block in D:\grok-pc-data\forge_push\gate120_e32f003rec_s198_vs_h256e12_confirm\gate120_e32f003rec_s198_vs_h256e12_confirm.log. Never read this as stronger unless the verdict says H1 accepted and the run is CLEAN. UNPROVEN until then; any H1 needs a confirm gate on new openings + new seed before lock.
