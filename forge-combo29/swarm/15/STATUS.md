# SEAT 15
- seat: 15
- branch: for-fable-and-opus/swarm-15
- area: 5 (PRINCIPAL VARIATIONS AND SCORES)
- seed: 1501

## 2026-11-16T22:01:57Z — checkpoint: all three area-5 jobs done, one check done

DONE (everything pushed, reports written):
- STEP 1 seat 15. STEP 2 build of 6b98f217, sha256 e06310ec…16a83, honesty 4/4 exact (HONESTY.txt).
- **job 1 COMPLETE** (REPORT_job1.md): 553 positions (O+G) depth 12 S14. 0 illegal PV moves,
  0 bestmove/PV-first mismatches, 10 mate scores, 9 obey the PV-length rule, 1 violates it.
  Harness fidelity: O 9,500,069 and G 18,466,239 node sums EXACT.
- **job 2 COMPLETE** (REPORT_job2.md): 120 positions depth 10 S14. KvK/KNvK/KBvK/threefold all cp 0.
  KNN v K nonzero in 19/20 (+309 max) => 15-F3; DeadMaterial true zeroes all 20.
  Dead-draw roots print an EMPTY pv ("time 0 pv") => 15-F4, which silently defeated my first parser.
- **job 3 COMPLETE** (REPORT_job3.md): 20 terminal roots x 3 go kinds under ASan+UBSan, both
  sanitizer proofs present (nm 35/15 + a planted overflow counted by the same runner). 60/60
  bestmove 0000, 0 sanitizer lines, exits 0. But 64 info lines with nodes 0 and score "mate 0" => 15-F5.
- **CHECK 15-C1 CONFIRMS seat 05's S-F8**: go infinite at a terminal root never answers (12 s),
  but sending stop answers 0000 at once. Bounded go answers in 0.001 s; live-board control answers.

FINDINGS: 15-F1, 15-F2, 15-F3, 15-F4, 15-F5, 15-C1. Two of them (15-F3, 15-F4) already CONFIRMED by
seat 05 (S-C5, S-C6), and seat 05 found 15-F1 independently (their S-F1).

Running now: nothing.

Next exact command:
  cd /agent/repos/dwqww/forge-combo29/swarm/15 && git fetch -q --depth 1 origin for-fable-and-opus/swarm-05 && git show FETCH_HEAD:forge-combo29/swarm/05/FINDINGS.md | head -20

Then: cycle step 2(a) again — pick an unconfirmed NEW finding of another seat and check it;
otherwise re-run job 1 of area 5 with SEED 1511 and a fresh R set, and say what differs.
