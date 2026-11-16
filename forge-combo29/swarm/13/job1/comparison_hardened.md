## per-depth comparison (5000 positions)

depths compared: 1, 2, 3, 4

depth | engine records | ref records | pairs compared | equal | differing | engine-not-ok | ref-not-ok
---|---|---|---|---|---|---|---
1 | 5000 | 5000 | 5000 | 5000 | 0 | 0 | 0
2 | 5000 | 5000 | 5000 | 5000 | 0 | 0 | 0
3 | 5000 | 5000 | 5000 | 5000 | 0 | 0 | 0
4 | 5000 | 5000 | 5000 | 5000 | 0 | 0 | 0

TOTAL (position,depth) pairs in scope: 20000
TOTAL pairs actually compared (both sides OK): 20000
TOTAL differing pairs: 0

VERDICT: 20000 pairs compared, 0 differing. (A real measurement: the counts above show every pair was present and numeric on both sides.)

## Note on provenance
`comparison.md` in this folder was produced by the FIRST version of compare.py, which skipped
records missing from either side and therefore could not show its own denominator. After the
integrity audit (../INTEGRITY_AUDIT.md) I re-ran the HARDENED compare.py over the very same committed
raw files (`raw_engine.txt`, `raw_ref.txt`). It reports 20,000 of 20,000 pairs present, numeric and
compared, 0 differing. So job 1's result is unchanged but now carries its denominator, and this file
supersedes comparison.md as job 1's evidence.
