seat 02
area 2 (UCI COMMANDS under ASan + UBSan)
branch for-fable-and-opus/swarm-02
seed 201 (run 2 seed 211)

## 21:12Z-21:55Z — engine, all three area-2 jobs
STEP 1+2: SEAT 02. Release build 6b98f217 sha256 e06310ec..., HONESTY PASS (312866 / 862329 / 3024920 / 4865609).
ASan+UBSan build sha256 b109a0a5..., BOTH proofs (nm 35 __asan_ / 15 __ubsan_; planted fault 3 lines, control 0).
JOB 1 (v3): 2,000 sequences, 5,827 go = 5,827 bestmove, 0 crash/hang/san/illegal. v1 WITHDRAWN (19-F12).
JOB 2: 5,000 race runs, 0 faults. JOB 3: 82 options x 6-7 values, 550 cases, 0 faults.

## 21:56Z-22:05Z — other seats' findings and both broadcast audits
S-C1 CONFIRMS 08-F2 (fixed 9.4 ms absolute Move Overhead loss, zeroed by the option).
S-C2 REFUTES the "silent" half of seat 11's S-F8 (engine prints `unknown option UseNNUE false`; ignore confirmed).
S-C3 CONFIRMS seat 10's warm-search rule, digits exact (56,720 / 4,951 / 4,516 / ucinewgame 56,720 / Clear Hash
40,569); NEW: `bench` is IMMUNE (467,411 in all four regimes), so only `go` searches are affected.
S-C4 CONFIRMS seat 20's S-F20 (LmpBase=8: d10 cp -2884, d12 cp -3114, d14 mate -9 vs default mate -7/-7/-6;
mate-in-1 untouched); NEW: mate -9 converges to mate -4 at d16/d18 for BOTH settings, so the cost is a two-ply
delay and ~2.1x nodes, not a worse final answer.
Audit of all my node-count results: warm_audit/AUDIT_my_results.md — none used Clear Hash as a baseline.

## 22:00Z — cycle 2(c)
JOB 1 RUN 2 (seed 211, fresh R set of 996 positions): 2,000 sequences, 5,779 go = 5,779 bestmove, 0 faults.
S-F2 reproduced independently: 59 `0000`-on-a-board-with-legal-moves from 42 empty-`searchmoves` lines. Two of
nine predictions FAILED and are recorded as failures (book share 786 vs my 0-200 band; driver-stopped 1,072 vs
400-900). REPORT_job1_run2.md.

FINDINGS: S-F2, S-F3, S-F4, S-F5 (engine behaviour, NEW); S-C1..S-C4 (checks of other seats); S-F1 (argv, since
confirmed as 10-C1); v1's withdrawn numbers documented in HARNESS_INVALIDATION.md.

All area-2 jobs and cycle item 2(c) are done. Continuing to check other seats' NEW findings until 22:30.
Exact next command:
  cd /agent/repos/dwqww && git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | wc -l
