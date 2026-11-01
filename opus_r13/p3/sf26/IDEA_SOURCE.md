# IDEA_SOURCE - Sf26 split (R13 P3)
- Port: Opus R13. `D:\grok-pc-data\opus30h_inputs\sf26bundle\sf26bundle_al1.patch` (= sf26bundle_al1_vs_AL1.patch in the
  Engine Strength handoff zip, byte-equal) applied to the lock tree d4f4312 with `patch -p1 -F0`, then the split
  (tools/port_sf26split.py, own code): switches Sf26NmpPrior / Sf26LmrGap / Sf26MulticutCorr, each ORed with its
  Sf26Bundle bit, and Sf26NmpPriorCap (bit 2's constant 3 as a tunable). No new search idea.
- Idea sources of the bundle (quoted from the Engine Strength handoff IDEA_SOURCE.md): ideas only, from 2026 Stockfish
  commit messages (titles and descriptions read; no diffs or code read, no constants used; Stockfish is GPL, nothing
  copied): bit 2 = SF 0c5892a9 "Use the number of prior NMP Fail High in search"; bit 4 = SF 5f7348f0 "Reduce LMR less
  aggressively in loose alpha windows" (Forge implements the scout's reading, the mirror direction); bit 8 = SF 218c74ec
  "Multi cut pruning correction history" (credited there to PlentyChess). Forge values are the crew's own (16 cp, cap 3, 260 cp).
- Status: UNPROVEN. No Elo or speed claim. SPSA values (if any) are proposals only.
