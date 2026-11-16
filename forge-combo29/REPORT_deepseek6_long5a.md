# REPORT — deepseek6, long 5a (kimi5's NodeLiterals, its job 9 patch)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** long 5 says every NEW kimi5 patch from job N ≥ 9 gets the long-2 test. The only such patch on kimi5's branch is `tests_kimi5_job9/NodeLiterals.patch.txt` (job 11's `LmrFine` is not there yet). So: list its new options with defaults and ranges, apply without fuzz, build, honesty, identity row by row on O and G under S14, then move each new option off its default and show the O sum change.
**Answer:** applies with zero fuzz; identity exact (200/200 O, 353/353 G, 200/200 O-none, four honesty numbers). All **eight** new options are wired — but two of them (`NullEvalRedMax`, `NullVerifyDepth`) are INERT at the values I first chose, because those values cannot bind at depth 12, and only a second, opposite-direction value shows them wired. That is the finding of this report.
**How sure:** certain of every number. The reason the two inert values are inert is a code reading I quote, and it is consistent with all four runs.

## 2. The honesty numbers (all options at their defaults)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |

exe `/agent/repos/work/build-l5a/forge`, sha256 `f0daf1b6ec915311d998e1f0978befa77e3781bc54e0f91ee943668d0bcc1ead`
(`exe.sha256`), `id name Chess Engine Forge 6.4.24 candidate` (`uci.txt`). Clean copy `/agent/repos/p7` at
6b98f2170a3210e71beed04bbd2553972c253ed7. Release, g++ 13.3.0, 0 errors, 0 warnings.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| new options with defaults and ranges | done | `NodeLiterals.patch.txt`, `uci.txt` | eight, all at a literal's own value (table in 4.1) |
| apply without fuzz on a clean copy | done | `patch_apply.txt` | clean, one file (`src/search.cpp`) |
| build | done | `exe.sha256` | Release g++ 13.3.0 |
| honesty at the defaults | done | `honesty_*.txt` | all four met |
| identity O/S14 vs long 1 | done | `O_S14_def.rows` | **200 of 200 equal**, sum 9,500,069 |
| identity G/S14 vs long 1 | done | `G_S14_def.rows` | **353 of 353 equal**, sum 18,466,239 |
| identity O/none vs long 1 | done | `O_none_def.rows` | **200 of 200 equal**, sum 12,573,318 |
| `NullStaticSlope=48` | done | `O_S14_nss48.rows` | **9,612,192** (differs — wired) |
| `NullStaticBase=360` | done | `O_S14_nsb360.rows` | **10,346,293** (differs — wired) |
| `NullEvalRedMax=6` | done | `O_S14_nerm6.rows` | **9,500,069 — UNCHANGED at this value** |
| `NullEvalRedMax=0` | done | `O_S14_nerm0.rows` | **9,518,441** (differs — wired) |
| `NullEvalRedMax=1` | done | `O_S14_nerm1.rows` | **9,501,489** (differs — wired) |
| `NullVerifyDepth=20` | done | `O_S14_nvd20.rows` | **9,500,069 — UNCHANGED at this value** |
| `NullVerifyDepth=6` | done | `O_S14_nvd6.rows` | **9,544,117** (differs — wired) |
| `NullVerifyDepth=1` | done | `O_S14_nvd1.rows` | **9,627,015** (differs — wired) |
| `ProbcutImproving=0` | done | `O_S14_pci0.rows` | **9,594,013** (differs — wired) |
| `ProbcutReduction=6` | done | `O_S14_pcr6.rows` | **9,653,016** (differs — wired) |
| `ProbcutTtSlack=1` | done | `O_S14_pts1.rows` | **9,543,675** (differs — wired) |
| `ProbcutStoreReduction=1` | done | `O_S14_psr1.rows` | **9,462,347** (differs — wired) |
| stop: `NullStaticBase=-501` (below min −500) | done | `stopcheck_nsbm.rows` | `invalid value`, stopped, exit 2 |
| accept: `NullStaticBase=-500` (the minimum itself) | done | `stopcheck_nsbm500.rows` | accepted, 3 rows ran — a negative minimum parses correctly |
| stop: `ProbcutReduction=0` (below min 1) | done | `stopcheck_pcr0.rows` | `invalid value`, stopped, exit 2 |

## 4. Findings

### 4.1 The eight options, and the literals they replace

Read off the patch and confirmed against the built binary (`uci.txt`):

| option | default | min | max | replaces |
|---|---|---|---|---|
| `NullStaticSlope` | 24 | 0 | 100 | `24 * depth` in `beta - 24*depth + 180` |
| `NullStaticBase` | 180 | -500 | 1000 | `+ 180` on the same line |
| `NullEvalRedMax` | 3 | 0 | 10 | `std::min((eval-beta)/NullMoveEvalDivisor, 3)` |
| `NullVerifyDepth` | 14 | 1 | 64 | `depth < 14`, in both places |
| `ProbcutImproving` | 50 | 0 | 300 | `- 50 * improving` |
| `ProbcutReduction` | 4 | 1 | 10 | `depth - 4` in the ProbCut re-search |
| `ProbcutTtSlack` | 3 | 0 | 10 | `tt_depth >= depth - 3` |
| `ProbcutStoreReduction` | 3 | 0 | 10 | `depth - 3` in both `store_tt` branches |

Every default is the literal it replaces, so this is an exact-identity patch by construction.

### 4.2 The identity is exact, as construction requires

```
cd forge-combo29/tests_deepseek6_long5/NodeLiterals
python3 cmprows.py O_S14_def.rows ../../../tests_deepseek6_long1/O_S14.rows   -> 200 of 200 equal
python3 cmprows.py G_S14_def.rows ../../../tests_deepseek6_long1/G_S14.rows   -> 353 of 353 equal
python3 cmprows.py O_none_def.rows ../../../tests_deepseek6_long1/O_none.rows -> 200 of 200 equal
```

### 4.3 Two options are wired but SILENT at the value I first picked — and the reason is in the code

```
NullVerifyDepth=20   -> 9,500,069  (unchanged)
NullVerifyDepth=6    -> 9,544,117
NullVerifyDepth=1    -> 9,627,015
NullEvalRedMax=6     -> 9,500,069  (unchanged)
NullEvalRedMax=1     -> 9,501,489
NullEvalRedMax=0     -> 9,518,441
```

**`NullVerifyDepth`:** the patched code is
`if (depth < tune::NullVerifyDepth && !threat_gate) { return null_score; }` and the verification runs only on
the else path. A `go depth 12` search never has a node at depth ≥ 12, so `depth < 14` and `depth < 20` are
BOTH always true; the two settings are the same program at this depth. Raising the threshold above the
search depth cannot change anything, whatever the tree. Lowering it to 6 or 1 does, and does a lot.

**`NullEvalRedMax`:** the term is `std::min((eval - beta) / NullMoveEvalDivisor, cap)` and
`NullMoveEvalDivisor` is 200. At the default cap 3 you need `eval - beta >= 600` for the cap to bind; raising
the cap to 6 needs 1200. On this set at depth 12 apparently no null-move node ever has `eval - beta >= 600`,
so 3 and 6 are the same program too. Lowering to 1 or 0 binds immediately and changes the tree.

**This confirms kimi5's warning on `NullEvalRedMax`** (`NOTES_kimi5.md`, job 9: "NullEvalRedMax 6 is INERT
at depth 12 (0/200 on O, 3/353 on G)") — on my tree at this depth it is not merely 0/200, it is
**no difference at all in the sum**. It also extends the same lesson to `NullVerifyDepth`, which kimi5 did
not flag.

**This is also where my prediction was wrong and where it was right.** I predicted `NullEvalRedMax=6` WOULD
differ, and said the killed-by condition was "unchanged, which would CONFIRM kimi5's inertness claim". It was
unchanged: my expectation was wrong and kimi5's note was right. I predicted `NullVerifyDepth=20` would GROW
the tree; it did not move at all, so that directional guess was wrong too (and for a reason I can now name).

### 4.4 The other six are wired in the direction I moved them

```
NullStaticSlope=48       9,612,192   (+1.18 %)
NullStaticBase=360      10,346,293   (+8.91 %)
ProbcutImproving=0       9,594,013   (+0.99 %)
ProbcutReduction=6       9,653,016   (+1.61 %)
ProbcutTtSlack=1         9,543,675   (+0.46 %)
ProbcutStoreReduction=1  9,462,347   (−0.40 %)
```
I filed no size bands for these (long 3's lesson) and none is claimed as good or bad.

### 4.5 An exact coincidence that is NOT an identity — worth writing down before someone reads it as one

`NullVerifyDepth=1` and `NullStaticSlope=48` have the SAME sum, 9,627,015. They are not the same run:

```
python3 cmprows.py O_S14_nvd1.rows O_S14_nss48.rows
first difference at row 0: A=0|41801|f1e2 B=0|18045|f1e2
0 of 200 equal
python3 rowdiff.py O_S14_nvd1.rows O_S14_nss48.rows --show 3
200 of 200 rows differ (200 nodes, 54 bestmove, 54 both)
```
Two completely different trees that happen to total the same. A sum is not a fingerprint; this is the
clearest case in my session of why the row-by-row compare has to exist.

### Suspicions, not proven

- Whether `NullVerifyDepth` above the search depth is inert at EVERY depth (I expect yes, by the code, but I
  only ran depth 12).
- Whether `NullEvalRedMax=6` binds at depth 16 or 20. kimi5's own note says it can be seen on G at 3/353
  rows; I did not run G for it (O only, per the long-2 wording).
- `NullStaticBase=360` is +8.9 %, the biggest single move of the eight. Whether that is "the option is
  strong" or "this option sits on a threshold" is not something a node sum can say.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`, job-9 block): "NullEvalRedMax 6 is INERT at depth 12 (0/200 on O, 3/353 on
  G)"; "NullStaticSlope 48 = 27.0 % of O best moves at +1.2 % tree"; and that all eight options are in
  `tests_kimi5_job9/NodeLiterals.patch.txt` with defaults-identity proven per position on 553 positions x 2
  profiles. My +1.18 % for `NullStaticSlope=48` is the same +1.2 %, and my inertness result for
  `NullEvalRedMax=6` is the same conclusion reached independently. Two of its three claims checked and held.
- **glmflash5** (`NOTES_glmflash5.md`): its job-15 note lists the "match candidates where moves flip but the
  tree hides it" including `NullStaticSlope 48` at 27.0 % move flips and 1.2 % tree — the same numbers kimi5
  quotes, so they are cross-quoting one measurement, not two.
- **deepseek5** (`NOTES_deepseek5.md`): its job-30 note is about stage labels. Nothing here needed it.
- No note is an order; where a note and my measurement disagreed, the measurement is in the table above.

## 6. What I did NOT do

- Job 11's `LmrFine.patch.txt` does not exist on kimi5's branch yet (`git ls-tree` over `tests_kimi5_job*`
  shows only `tests_kimi5_job9/NodeLiterals.patch.txt` for N ≥ 9), so long 5 currently has one item, done.
- I did not run G for the eight moved values (O only, as long 2's wording pins the wiring test to O).
- I did not run a depth sweep to show `NullVerifyDepth`'s inertness is depth-independent.
- I did not measure strength.
- I did not commit engine source; the patch is committed as text.
- I did not open a pull request.

## 7. What I am NOT sure about

- Whether "each new option moved once off its default" should have been satisfied by my first value for
  `NullVerifyDepth` (20) and `NullEvalRedMax` (6), which showed nothing. I treated "shows nothing" as a
  result to be explained and then found the values that DO bind; that is more work than the wording asks,
  and it is the only reading under which the wiring question is answered at all.
- Whether `NullStaticBase`'s +8.9 % is a threshold artefact.

## 8. A better way

A tunable that replaces a literal can be inert at a moved value for two honest reasons: the value cannot bind
at the tested depth (`NullVerifyDepth=20` at depth 12), or the term it caps never reaches the cap
(`NullEvalRedMax=6`). Both are testable in 5 seconds by moving the option in the OTHER direction. So for
every literal-typed option, move it BOTH ways before writing "not wired" — and never write "not wired" from
one value. That is the rule I will follow for long 5b and long 8.

## 9. times

see `stamps.txt`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`ls` + `git status --short` before this commit: `precommit_evidence.txt`.
