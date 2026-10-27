# gate95_e12f_vs_h256e12 RESULT: cand_h256_e12f vs base_h256_e12 (h256_e12 LOCK)
- Written by forge_queue.ps1 v3-6day. Started 2026-10-24 23:20:53 PC (Vienna wall clock); fastchess exit code 0; attempt 1. Settings: fastchess 1.8.2, 10+0.1 timemargin=1000, Threads=1 Hash=16 OwnBook=false, 8moves_v3.pgn order=random start=240001, srand 973474437, 1500-game cap, concurrency 5, SPRT normalized [0,10] a=b=0.05, BelowNormal, CPUs 4-15, -recover (see RUN_INFO.json).
- Games: 1500  W/L/D (candidate view): 192 / 191 / 1117  Points 750.5 (50.03 %)
- Pentanomial Ptnml(0-2): [13, 128, 463, 137, 9]  complete pairs = 750
- Elo: 0.23 +/- 8.53   nElo: 0.48 +/- 17.58   LOS 52.12 %
- LLR: -0.56  bounds (-2.94, 2.94)  [elo0=0, elo1=10, normalized]
- Time losses: 0   Crashes/disconnects/stalls/illegal: 0   fastchess 'Warning;' lines: 0   (clean requires 0 and 0): CLEAN
- Orphan games (Games - 2*complete pairs): 0 
- Avg search depth (PGN comments, non-book moves): base_h256_e12: avg depth 21.79 over 94326 moves; cand_h256_e12f: avg depth 21.81 over 94329 moves
- PC nps (pre-gate paired bench d20, CPU 6): not measured for this gate
- Candidate options (candidate side only): none. Base side: none (enforced: static arg check + engine_io.log setoption check, see ENGINE_OPTIONS_CHECK.txt).
- Engine option check (engine_io.log, final): 2026-10-25 01:44:43 Vienna(PC clock) | gate95_e12f_vs_h256e12 engine option check PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 9000 setoption lines. seen: base_h256_e12|Hash=16 x1500; base_h256_e12|OwnBook=false x1500; base_h256_e12|Threads=1 x1500; cand_h256_e12f|Hash=16 x1500; cand_h256_e12f|OwnBook=false x1500; cand_h256_e12f|Threads=1 x1500 PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 9000 setoption lines. seen: base_h256_e12|Hash=16 x1500; base_h256_e12|OwnBook=false x1500; base_h256_e12|Threads=1 x1500; cand_h256_e12f|Hash=16 x1500; cand_h256_e12f|OwnBook=false x1500; cand_h256_e12f|Threads=1 x1500
- **Verdict: Cap with no decision (LLR -0.56 inside (-2.94, 2.94)); nothing claimed**

Source: last 'Results of' block in D:\grok-pc-data\forge_push\gate95_e12f_vs_h256e12\gate95_e12f_vs_h256e12.log. Never read this as stronger unless the verdict says H1 and the run is CLEAN. UNPROVEN until then; any H1 needs a confirm gate on new openings + new seed before lock.
