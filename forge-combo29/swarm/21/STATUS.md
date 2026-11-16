## 2026-11-16T21:44Z
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21, seed 2101

**Done**
- STEP 2 build + honesty 4/4 exact; ASan+UBSan build with BOTH required proofs; Rule-1
  planted cases for the harness (fake illegal bestmove + fake never-readyok).
- job1: 20,000 mutated FENs, ASan+UBSan — 18,775 refused / 1,225 accepted / 39
  python-invalid / 0 crash / 0 hang / 0 sanitizer / 0 real illegal bestmove.
- job2: CHECK of 30-F6 → CONFIRMS; plus its evidence line is broken (20 vs 20).
- job3: 24 extreme-field cases — fullmove 0 refused where python-chess accepts; halfmove
  ≥ 100 (incl. 2^31) → 0-node `cp 0`; all 6,073 real positions accepted.
- job4: 1,000-ply move lists — legal list exact, illegal at ply 1/10/500 keeps the legal
  prefix at perft 1 AND perft 2 (21-C2).

**Findings**: 21-F1..F10, 21-C1 (CONFIRMS 30-F6), 21-C2 — FINDINGS.md.
All three area-1 jobs are now done once.

**Next (THE CYCLE 2c)**: area 1 job 1 again with the next seed and a new position set
(R with SEED + 10 = 2111), saying in the report what differs from the first run.
Exact next command: `cd forge-combo29/swarm/21 && mkdir -p job5 && python3 job5/gen2.py` (script not yet written)
