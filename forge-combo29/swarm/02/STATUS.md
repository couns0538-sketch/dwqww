seat 02
area 2 (UCI COMMANDS under ASan + UBSan)
branch for-fable-and-opus/swarm-02
seed 201 (run 2 uses 211)

## 2026-11-16T21:12Z-21:55Z — engine + all three area-2 jobs
STEP 1+2: SEAT 02; release build 6b98f217 sha256 e06310ec..., HONESTY PASS (312866 / 862329 / 3024920 / 4865609).
Sanitizer build sha256 b109a0a5... with BOTH required proofs (nm 35 __asan_ / 15 __ubsan_; planted fault counted
3 lines, control 0).
JOB 1 (v3, third harness): 2,000 sequences, 5,827 go = 5,827 bestmove, 0 crash/hang/san/illegal. v1 WITHDRAWN
for 19-F12 (HARNESS_INVALIDATION.md). REPORT_job1.md.
JOB 2: 5,000 race runs (stop/ponderhit/ucinewgame/setoption Hash/quit), 0 faults. REPORT_job2.md.
JOB 3: 82 options x 6-7 values, 550 cases, idle and during search, 0 faults. REPORT_job3.md.

## 2026-11-16T21:56Z — checks of other seats and the two broadcast audits
S-C1 CONFIRMS 08-F2 (movetime loses a fixed 9.4 ms absolute to Move Overhead; zeroed by the option).
S-C2 REFUTES the "silent" half of seat 11's S-F8: the engine DOES answer `info string unknown option UseNNUE
false`; the ignore mechanism is confirmed, the silence is not.
S-C3 CONFIRMS seat 10's warm-search rule: startpos depth 12 = 56,720 cold, 4,951 then 4,516 warm, 56,720 after
`ucinewgame`, 40,569 after `Clear Hash` — seat 10's digits exactly. NEW beyond it: `bench` is IMMUNE (three
bench 12 in one process, with ucinewgame and with Clear Hash all 467,411).
Audit of every node-count result of mine: warm_audit/AUDIT_my_results.md — none used Clear Hash as a baseline;
S-C1's 72-searches-per-process cells are warm identically in all four cells and are latency, not node counts.

## 2026-11-16T22:00Z — cycle item 2(c)
JOB 1 RUN 2 (seed 211, fresh R set of 996 positions): 2,000 sequences, 5,779 go = 5,779 bestmove, 0 faults.
S-F2 REPRODUCED independently: 59 `0000`-on-a-board-with-legal-moves answers from 42 empty-`searchmoves` lines.
Two of my nine predictions failed (book share 786 vs my 0-200 band; driver-stopped 1,072 vs my 400-900 band) and
both are recorded as failures in the report. REPORT_job1_run2.md.

FINDINGS: S-F2, S-F3, S-F4, S-F5 (NEW engine behaviour); S-C1, S-C2, S-C3 (checks of other seats); S-F1 (argv,
since confirmed by seat 10 as 10-C1); the withdrawn v1 numbers are documented, not hidden.

Next (if time remains before 22:30): check seat 01's S-F17/S-F18 or seat 21's 21-F9 (the halfmove>=100 mate
loss) — both unchecked by a C line as far as I have seen. Otherwise: hold and keep STATUS current.

Exact next command:
  cd /agent/repos/dwqww && for s in 01 21; do git fetch -q --depth 1 origin for-fable-and-opus/swarm-$s && git show FETCH_HEAD:forge-combo29/swarm/$s/FINDINGS.md | grep -E '^\| *[0-9A-Z]*-C[0-9]+' | head -5; done
