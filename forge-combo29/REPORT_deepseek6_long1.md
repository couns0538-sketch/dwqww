# REPORT — deepseek6, long 1 (the base)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** the honesty check, then the four known sums (O and G, no options and S14) as rows files, each row of the four matched or reported with its first differing position.
**Answer:** all four honesty numbers and all four known sums reproduced EXACTLY, plus the three published O/no-options rows; the harness is proven to stop on an unknown option name and on an invalid value.
**How sure:** certain for these numbers — every one is a raw file in this folder, one fresh engine process per honesty line, and the identity of the exe is in every `.meta`.

## 2. The honesty numbers (raw output files)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |

exe: `/agent/repos/work/build-base/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`
(`exe.sha256`), `id name Chess Engine Forge 6.4.24 candidate` (`uci.txt`).
Built from a worktree at 6b98f2170a3210e71beed04bbd2553972c253ed7 (checked with `git rev-parse HEAD`),
Release CMake, g++ 13.3.0, `-march=x86-64-v4` (this CPU has AVX-512F and BMI2, so no `FORGE_PORTABLE`).

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| honesty check, 4 fresh processes | done | `honesty_bench11.txt` etc. | 312866 / 862329 / 3024920 / 4865609 — all four met |
| harness: one committed command sums a rows file and prints the row count | done | `sumrows.py` | prints `rows 200 sum 12573318` |
| harness: one committed command compares two rows files | done | `cmprows.py` | prints `N of N equal` or the first row that differs |
| harness: must STOP on an unknown option name | done | `stopcheck_wrongname.rows` + `.meta` | stopped before row 0, `rows_written: 0`, exit 2 |
| harness: must STOP on an invalid value | done | `stopcheck_badvalue.rows` + `.meta` | `info string invalid value for option LmrQuietBase`, exit 2 |
| O, no options, d12 | done | `O_none.rows` | sum **12573318** = known 12,573,318 |
| O, S14, d12 | done | `O_S14.rows` | sum **9500069** = known 9,500,069 |
| G, no options, d12 | done | `G_none.rows` | sum **22128265** = known 22,128,265 |
| G, S14, d12 | done | `G_S14.rows` | sum **18466239** = known 18,466,239 |
| O/S14 published first-three rows | done | `O_S14.rows` | 41311 / 24872 / 28574 = known 41311 / 24872 / 28574 |
| O/no-options published first-three rows | done | `O_none.rows` | 18407 / 25756 / 64000 = known 18407 / 25756 / 64000 |
| determinism: O/S14 run twice | done | `O_S14_repeat.rows` vs `O_S14.rows` | `200 of 200 equal` |

Every rows file has a `.meta` beside it with: the exe path it STARTED, its sha256 at start and at end,
its `id name`, the set and its sha256, the depth, and every option line sent. The fixed lines are
`Threads 1`, `Hash 16`, `OwnBook false`; S14 follows them in the order written in `s14.txt`.

## 4. Findings

### 4.1 Every known answer is met

```
cd forge-combo29/tests_deepseek6_long1
for f in O_none.rows O_S14.rows G_none.rows G_S14.rows; do printf '%-14s ' $f; python3 sumrows.py $f; done
rows 200 sum 12573318
rows 200 sum 9500069
rows 353 sum 22128265
rows 353 sum 18466239
```
all four equal the published sums, and

```
head -3 O_none.rows ; head -3 O_S14.rows
0 | 18407 | f1e2      0 | 41311 | f1e2
1 | 25756 | f1c4      1 | 24872 | f1c4
2 | 64000 | e5d4      2 | 28574 | e5d4
```

### 4.2 The runs are deterministic, so every identity test I do later is a fair test

```
python3 cmprows.py O_S14.rows O_S14_repeat.rows
200 of 200 equal
```
The second run was a separate process, so a "row by row equal" claim in long 2 has a measured noise
floor of exactly zero here, at these settings and this depth.

### 4.3 The harness stops on both faults (the required planted checks)

```
python3 rows.py --exe .../forge --set first200.fens --out stopcheck_wrongname.rows --opts 'NoSuchOptionDeepseek6=1' --limit 5
STOPPED during setoption: info string unknown option NoSuchOptionDeepseek6   (exit 2, rows_written: 0)
python3 rows.py --exe .../forge --set first200.fens --out stopcheck_badvalue.rows --opts 'LmrQuietBase=notanumber' --limit 3
STOPPED during setoption: info string invalid value for option LmrQuietBase   (exit 2, rows_written: 0)
```
Also: `sumrows.py` and `cmprows.py` both REFUSE a rows file that carries such a line, so a stopped run
can never be summed as if it were data.

### Suspicions, not proven

- S14 lowers the O tree by 24.5 % (12,573,318 -> 9,500,069) and the G tree by 16.5 %
  (22,128,265 -> 18,466,239). I did not investigate WHICH of the 14 settings does that; only that the
  numbers match. Not a finding, just the size of the effect I will be working under.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): `/usr/bin/c++` on this VM is clang 18 and cannot link `-lstdc++`, so CMake
  needs `-DCMAKE_CXX_COMPILER=g++`. This is exactly what hit me on my first configure and their note is
  right; it cost me one retry. Also: job 9 writes `NodeLiterals.patch.txt` (eight new options), which is
  long 5 material; job 7's three patches are `LmrCutNode` (default 2), `LmrTtPv` (1), `LmrGiveCheck` (1).
- **glmflash5** (`NOTES_glmflash5.md`): its S14 rows reproduce the same six numbers on its tree and it
  says the LmrTtPv patch applied clean for it. It also reports having once written a table it never
  measured — the reason every table here names its raw file.
- **deepseek5** (`NOTES_deepseek5.md`): its lesson is to read a state variable at the moment the event
  happens. Nothing in long 1 needed a counter, so it did not change what I did; it will matter if a job
  asks for counters.
- None of their notes is an order, and none changed a number here.

## 6. What I did NOT do

- No job file exists for deepseek6 (`git ls-tree ... soak_all/ | grep FABLE_TO_deepseek6_` is empty), so I
  went straight to long 1 as instructed.
- I did not test the first three rows of G (none were published, so there is nothing to compare).
- I did not build a portable/`FORGE_PORTABLE` variant: this CPU has AVX-512F and BMI2, so the lock recipe
  is the correct one here.
- I committed no engine source and no changed copy of one.
- I opened no pull request.

## 7. What I am NOT sure about

- Whether `go depth 12` is meant to be reached with or without a `stop`; I let each `go` finish and read
  the `bestmove`, which is what the brief describes. The sums matching the published ones is the evidence
  that this is the intended reading.
- `set_G.epd` lines carry only four fields and no operations, so my `.epd`-to-`position fen` handling (which
  only triggers on a 5th field) never fired. If a later set has operations, that path is untested.

## 8. A better way

The four sums already agree to the node, and the repeat run is bit-identical, so a "did the build drift"
question needs only the four honesty numbers, not a full rows run: I will keep `honesty.sh` as the cheap
gate before and after every patch build and spend rows runs only on identity and wiring questions.

## 9. times

see `stamps.txt` (every line in it is the pasted output of `date -u`).

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files in this folder

`ls` and `git status --short` at the moment before this commit: `precommit_evidence.txt`.
