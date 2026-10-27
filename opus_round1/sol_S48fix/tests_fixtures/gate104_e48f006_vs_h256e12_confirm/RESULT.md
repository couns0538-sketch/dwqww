# gate104_e48f006_vs_h256e12_confirm RESULT: cand_h256_e48f006 vs base_h256_e12 (h256_e12 LOCK)
- Written by forge_queue.ps1 v3-6day. Started 2026-10-25 15:37:30 PC (Vienna wall clock); fastchess exit code 0; attempt 1. Settings: fastchess 1.8.2, 10+0.1 timemargin=1000, Threads=1 Hash=16 OwnBook=false, 8moves_v3.pgn order=random start=318001, srand 1524622280, 1500-game cap, concurrency 5, SPRT normalized [0,10] a=b=0.05, BelowNormal, CPUs 4-15, -recover (see RUN_INFO.json).
- Games: 1500  W/L/D (candidate view): 211 / 180 / 1109  Points 765.5 (51.03 %)
- Pentanomial Ptnml(0-2): [6, 132, 447, 155, 10]  complete pairs = 750
- Elo: 7.18 +/- 8.49   nElo: 14.87 +/- 17.58   LOS 95.13 %
- LLR: 1.23  bounds (-2.94, 2.94)  [elo0=0, elo1=10, normalized]
- Time losses: 0   Crashes/disconnects/stalls/illegal: 0   fastchess 'Warning;' lines: 0   (clean requires 0 and 0): CLEAN
- Orphan games (Games - 2*complete pairs): 0 
- Avg search depth (PGN comments, non-book moves): base_h256_e12: avg depth 21.73 over 99578 moves; cand_h256_e48f006: avg depth 21.74 over 99605 moves
- PC nps (pre-gate paired bench d20, CPU 6): not measured for this gate
- Candidate options (candidate side only): none. Base side: none (enforced: static arg check + engine_io.log setoption check, see ENGINE_OPTIONS_CHECK.txt).
- Engine option check (engine_io.log, final): 2026-10-25 18:06:25 Vienna(PC clock) | gate104_e48f006_vs_h256e12_confirm engine option check PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 9000 setoption lines. seen: base_h256_e12|Hash=16 x1500; base_h256_e12|OwnBook=false x1500; base_h256_e12|Threads=1 x1500; cand_h256_e48f006|Hash=16 x1500; cand_h256_e48f006|OwnBook=false x1500; cand_h256_e48f006|Threads=1 x1500 PASS [final]: base only Threads/Hash/OwnBook; candidate exactly  + Threads/Hash/OwnBook, options advertised. 9000 setoption lines. seen: base_h256_e12|Hash=16 x1500; base_h256_e12|OwnBook=false x1500; base_h256_e12|Threads=1 x1500; cand_h256_e48f006|Hash=16 x1500; cand_h256_e48f006|OwnBook=false x1500; cand_h256_e48f006|Threads=1 x1500
- **Verdict: Cap with no decision (LLR 1.23 inside (-2.94, 2.94)); nothing claimed**

Source: last 'Results of' block in D:\grok-pc-data\forge_push\gate104_e48f006_vs_h256e12_confirm\gate104_e48f006_vs_h256e12_confirm.log. Never read this as stronger unless the verdict says H1 accepted and the run is CLEAN. UNPROVEN until then; any H1 needs a confirm gate on new openings + new seed before lock.
