# SEAT 15
- seat: 15
- branch: for-fable-and-opus/swarm-15
- area: 5 (PRINCIPAL VARIATIONS AND SCORES)
- seed: 1501

## 2026-11-16T21:34:48Z — CHECKPOINT (owner window: work to 22:35 UTC)

Done:
- STEP 1: seat 15 claimed.
- STEP 2: Release build of 6b98f217 (g++ 13.3.0, -march=x86-64-v4), sha256 e06310ec…16a83.
  HONESTY: all four numbers match (312866 / 862329 / 3024920 / 4865609) — see HONESTY.txt.
- AREA 5 job 1, run complete: 553 positions (O first200 + G set_G), depth 12, S14, Threads 1, Hash 16.
  Harness fidelity proven: O node sum 9,500,069 and G 18,466,239, both EXACT against the brief.
  Results: 0 illegal PV moves, 0 bestmove/PV-first mismatches, 0 positions without an info pv line,
  10 mate scores, 9 obey the brief's PV-length rule, 1 violates it (15-F1 / 15-F2).
- Harness audit after seat 19's 19-F12 broadcast: my results are clean (0 fabricated a2a3, 0 zero-node
  lines, 0 missing info lines). probe.sh (throwaway) used the risky sleep+quit pipe; every number it
  produced for the report was re-run on probe2.py, which reads until bestmove. See
  job1/evidence/harness_audit/audit.txt.

Running now: nothing (job 1 measurement finished; two python mate solvers still finishing a cross-check).

Next exact command:
  cd /agent/repos/dwqww/forge-combo29/swarm/15/job1 && python3 analyze.py raw_d12/pv.jsonl --control > analyze_d12.txt

Then: write REPORT_job1.md, push, then AREA 5 job 2 (draw scores) with its prediction committed first.
