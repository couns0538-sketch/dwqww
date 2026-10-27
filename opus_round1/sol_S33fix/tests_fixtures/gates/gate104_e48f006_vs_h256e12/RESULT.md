# gate104_e48f006_vs_h256e12 RESULT: cand_h256_e48f006 vs base_h256_e12 (h256_e12 LOCK)
- Written by forge_queue.ps1 v3-6day. Started 2026-10-25 09:08:52 PC (Vienna wall clock); fastchess exit code 0; attempt 1. Settings: fastchess 1.8.2, 10+0.1 timemargin=1000, Threads=1 Hash=16 OwnBook=false, 8moves_v3.pgn order=random start=267001, srand 1585072642, 1500-game cap, concurrency 5, SPRT normalized [0,10] a=b=0.05, BelowNormal, CPUs 4-15, -recover (see RUN_INFO.json).
- Games: 698  W/L/D (candidate view): 130 / 71 / 497  Points 378.5 (54.23 %)
- Pentanomial Ptnml(0-2): [3, 47, 197, 92, 10]  complete pairs = 349
- Elo: 29.44 +/- 13.23   nElo: 57.67 +/- 25.77   LOS 100.00 %
- LLR: 2.95  bounds (-2.94, 2.94)  [elo0=0, elo1=10, normalized]
- Time losses: 0   Crashes/disconnects/stalls/illegal: 0   fastchess 'Warning;' lines: 0   (clean requires 0 and 0): CLEAN
- Orphan games (Games - 2*complete pairs): 0 
- Avg search depth (PGN comments, non-book moves): base_h256_e12: avg depth 21.71 over 48178 moves; cand_h256_e48f006: avg depth 21.74 over 48225 moves
- PC nps (pre-gate paired bench d20, CPU 6): not measured for this gate
- Candidate options (candidate side only): none. Base side: none (enforced: static arg check + engine_io.log setoption check, see ENGINE_OPTIONS_CHECK.txt).
- Engine option check (engine_io.log, final): 2026-10-25 10:20:11 Vienna(PC clock) | gate104_e48f006_vs_h256e12 engine option check PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 4218 setoption lines. seen: base_h256_e12|Hash=16 x703; base_h256_e12|OwnBook=false x703; base_h256_e12|Threads=1 x703; cand_h256_e48f006|Hash=16 x703; cand_h256_e48f006|OwnBook=false x703; cand_h256_e48f006|Threads=1 x703 PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 4218 setoption lines. seen: base_h256_e12|Hash=16 x703; base_h256_e12|OwnBook=false x703; base_h256_e12|Threads=1 x703; cand_h256_e48f006|Hash=16 x703; cand_h256_e48f006|OwnBook=false x703; cand_h256_e48f006|Threads=1 x703
- **Verdict: H1 accepted (SPRT [0,10] normalized, a=b=0.05: no measurable regression; not an Elo claim; needs a confirm gate before lock)**

Source: last 'Results of' block in D:\grok-pc-data\forge_push\gate104_e48f006_vs_h256e12\gate104_e48f006_vs_h256e12.log. Never read this as stronger unless the verdict says H1 accepted and the run is CLEAN. UNPROVEN until then; any H1 needs a confirm gate on new openings + new seed before lock.
