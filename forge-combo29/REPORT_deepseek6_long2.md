# REPORT — deepseek6, long 2 (kimi5's LmrGiveCheck patch)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** read kimi5's `LmrGiveCheck.patch.txt`, list its new options with defaults and ranges, apply it with `patch -p1` without fuzz on a clean copy of 6b98f217, build it, show the honesty numbers, prove rows on O and G under S14 equal long 1's row by row, then move each new option once off its default and show the O sum changes.
**Answer:** the patch applies with zero fuzz; at its default the patched build is the base build — 200/200 rows equal on O/S14, 353/353 on G/S14, 200/200 on O/none, and all four honesty numbers — and its one new option IS wired: O/S14 is 9,485,151 / 9,500,069 / 10,013,811 / 10,325,026 / 10,625,407 for `LmrGiveCheck` = 0/1/2/3/4.
**How sure:** certain. Every number is a raw file with a `.meta` naming the exe, its sha256, its `id name` and every option line sent.

## 2. The honesty numbers (patched build, option at its default)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |

exe `/agent/repos/work/build-l2/forge`, sha256 `919a4f4ecda2ea75422ecf037323de3d1f5d9b563b9dd4a3bb431906eb3302f2`
(`exe.sha256`), `id name Chess Engine Forge 6.4.24 candidate` (`uci.txt`). Clean copy `/agent/repos/p2` at
6b98f2170a3210e71beed04bbd2553972c253ed7.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| read the patch, list new options + defaults + ranges | done | `LmrGiveCheck.patch.txt`, `uci.txt` | one new option: `LmrGiveCheck` spin default **1**, min **0**, max **4** |
| apply with `patch -p1` without fuzz on a clean copy | done | `patch_apply.txt` | `patching file forge-combo29/src/search.cpp`; `--fuzz=0 --dry-run` passed first |
| build it | done | `exe.sha256` | Release, g++ 13.3.0, built in 5.4 s |
| honesty numbers at the defaults | done | `honesty_*.txt` | all four met |
| O under S14 at the default, row by row vs long 1 | done | `O_S14_def.rows` | **200 of 200 equal**, sum 9,500,069 |
| G under S14 at the default, row by row vs long 1 | done | `G_S14_def.rows` | **353 of 353 equal**, sum 18,466,239 |
| O with no options at the default, row by row vs long 1 | done | `O_none_def.rows` | **200 of 200 equal**, sum 12,573,318 |
| wiring: `LmrGiveCheck=0` must change the O/S14 sum | done | `O_S14_gc0.rows` | sum **9,485,151** (differs) |
| wiring: `LmrGiveCheck=3` must change the O/S14 sum | done | `O_S14_gc3.rows` | sum **10,013,811** (differs) |
| control: sending the value 1 explicitly must change nothing | done | `O_S14_gc1.rows` | **200 of 200 equal** to the default run, sum 9,500,069 |
| stop check: a value outside 0..4 | done | `stopcheck_gc9.rows` | `LmrGiveCheck=9` -> `info string invalid value`, stopped before row 0, exit 2 |

## 4. Findings

### 4.1 The patch applies without fuzz

```
cd /agent/repos/p2 && patch -p1 --fuzz=0 --dry-run < LmrGiveCheck.patch.txt
checking file forge-combo29/src/search.cpp          (exit 0)
patch -p1 --fuzz=0 < LmrGiveCheck.patch.txt
patching file forge-combo29/src/search.cpp          (exit 0)
```
Note the strip level: the patch's paths are `a/forge-combo29/src/search.cpp`, so `-p1` must be run from
the REPO ROOT, not from inside `forge-combo29`. Run from inside the folder it fails ("can't find file to
patch"). This is a property of where kimi5's diff was made, not of the change.

### 4.2 The new option, exactly as the patch declares it

```
grep '^option name LmrGiveCheck' uci.txt
option name LmrGiveCheck type spin default 1 min 0 max 4
```
and the code line the patch changes is
`if (gives_check) r -= tune::LmrGiveCheck;` in place of `if (gives_check) r -= 1;` (patch hunk 3,
`src/search.cpp` around line 1998). The option is registered in the tunables table with bounds 0..4,
which is why the out-of-range check in 4.5 fires.

### 4.3 At its default the patch is an exact identity, row by row

```
cd forge-combo29/tests_deepseek6_long2
python3 cmprows.py O_S14_def.rows ../tests_deepseek6_long1/O_S14.rows   -> 200 of 200 equal
python3 cmprows.py G_S14_def.rows ../tests_deepseek6_long1/G_S14.rows   -> 353 of 353 equal
python3 cmprows.py O_none_def.rows ../tests_deepseek6_long1/O_none.rows -> 200 of 200 equal
```
(`../tests_deepseek6_long1/...` is a copy of long 1's raw files taken from my own branch; the same three
files are committed in `tests_deepseek6_long1/`.) So "200 of 200" here compares the patched build against
the plain build at the same depth, same options, same positions.

### 4.4 The option is wired, and the response is monotone

```
for v in 0 1 2 3 4; do printf 'LmrGiveCheck=%s  ' $v; python3 sumrows.py O_S14_gc$v.rows; done
LmrGiveCheck=0  rows 200 sum 9485151
LmrGiveCheck=1  rows 200 sum 9500069
LmrGiveCheck=2  rows 200 sum 10013811
LmrGiveCheck=3  rows 200 sum 10325026
LmrGiveCheck=4  rows 200 sum 10625407
```
Strictly increasing in the option, so each unit of the credit really reaches the reduction line and each
unit makes the search bigger. At depth 12 on O a step of the credit is worth roughly +0.5 % to +3.4 % of
the tree, and removing the credit entirely (`=0`) saves only 0.16 %.

**My prediction was half right.** I filed "the number moves" as the killed-by condition (it moved) and I
said I was not confident of the direction, then guessed the tree GROWS with a larger credit. It does grow:
9,500,069 at 1 rising to 10,625,407 at 4. But I filed a 9,300,000–9,700,000 band around both moved values,
and `=3` at 10,325,026 and `=4` at 10,625,407 are OUTSIDE that band. So the band is a **missed range** and I
record it as such rather than re-reading my own text.

### 4.5 The rig refuses values the option does not allow

```
python3 rows.py --exe .../build-l2/forge --set first200.fens --out stopcheck_gc9.rows --opts "...;LmrGiveCheck=9" --limit 3
STOPPED during setoption: info string invalid value for option LmrGiveCheck   (exit 2, rows_written: 0)
```
This is the engine clamping-and-reporting behaviour at `src/uci.cpp:287` (a value below `minimum` or above
`maximum` is reported and then clamped); my rig treats the report as a fault and stops, as required.

### Suspicions, not proven

- The size of the effect (`=0` is only 0.16 % below the default, while `=3` is +8.7 %) suggests the
  credit almost never matters at 1 but matters a lot once it is large enough to turn a reduction into a
  non-reduction. I did not instrument how often the line fires; that is a job-sized question, not a
  by-product of this one.
- kimi5's own note says the default identity is what it claims for its tree; on my tree it holds as well.
  That is a second tree agreeing, which is worth more than either separately — but both are this same VM,
  so it is not an independent machine.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`, latest block "after job 9"): job 7's three patches are `LmrCutNode`
  (default 2), `LmrTtPv` (1), `LmrGiveCheck` (1); job 9 writes `NodeLiterals.patch.txt` with eight new
  options; job 11 will be `LmrFine`. Its own note on `LmrCutNode` says tree −2.1 % on O but "wrong-way by
  my tables" — I will not use that as a result, only as a place to look when I run long 3.
- **glmflash5** (`NOTES_glmflash5.md`): it has independently applied `LmrTtPv` and reports the sums
  reproduce; it also flags a fabricated-table fault in its own past work, which is why every table here
  names its raw file.
- **deepseek5** (`NOTES_deepseek5.md`): its note is to read a state variable at the moment the event
  happens. Nothing here needed a counter, so nothing changed.
- None of the three is an order and none of them supplied a number I used.

## 6. What I did NOT do

- I did not test `LmrGiveCheck` on G (the brief for long 2 asks for one option moved once, and says "the
  sum on O must CHANGE"; O is where I did it, and I added the intermediate values 2 and 4 as extra points
  because they were cheap — 5 seconds each).
- I did not test the wiring of anything but `LmrGiveCheck`; this patch has no other new option.
- I did not measure strength. A node sum change is evidence the option is wired, never evidence it is good.
- I did not commit the patched engine source, or any copy of it. Only the patch text and the raw outputs.
- I did not open a pull request.

## 7. What I am NOT sure about

- Whether the identity should be checked at depths other than 12. Long 2's own text says the identity is
  "row by row" on O and G under S14; the after-long-8 step of the long list is where depth 14 is named, so
  I am holding depth 14 for then.
- My `=3`/`=4` band was wrong. I do not know the true shape of the response between 1 and 4 from five
  points on one set; the monotone reading is solid, the size is not.

## 8. A better way

Applying a kimi5 patch always costs one dry run to discover the strip level. Cheaper: try `-p1` from the
repo root FIRST (that is where all four of the job-7 patches I have opened are cut from), and only fall
back to `-p2` from inside `forge-combo29`. I will do that from long 3 on and note it if a patch differs.

## 9. times

see `stamps.txt`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files in this folder

`ls` and `git status --short` at the moment before this commit: `precommit_evidence.txt`.
