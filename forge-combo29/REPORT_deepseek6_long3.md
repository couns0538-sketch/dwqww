# REPORT — deepseek6, long 3 (kimi5's LmrCutNode and LmrTtPv patches, one at a time)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** the long-2 test for `LmrCutNode.patch.txt` and then `LmrTtPv.patch.txt`, each on its own clean copy of 6b98f217: read the patch, list its new options with defaults and ranges, apply with `patch -p1` without fuzz, build, honesty numbers, rows on O and G under S14 equal to long 1's row by row, then each new option moved once off its default with the O sum shown to change.
**Answer:** both patches apply with zero fuzz and both are exact identities at their defaults (200/200 O, 353/353 G, 200/200 O-no-options, all four honesty numbers). Both options are wired, with very different sizes: `LmrTtPv` is enormous and monotone (9,500,069 at 1, then 7,102,738 / 13,036,988 / 17,313,152 / 20,676,319 for 0/2/3/4), while `LmrCutNode` is small and **NOT monotone** (9,500,069 at 2, then 9,448,238 / 9,321,641 / 9,372,491 / 9,648,987 for 0/1/3/4) — a finding, explained in 4.4.
**How sure:** certain of every number (raw files, each with a `.meta`); the non-monotonicity is a measured fact, and my explanation of its cause is a suspicion, labelled as one.

## 2. The honesty numbers (both builds, options at their defaults)

| line | want | LmrCutNode build | LmrTtPv build | files |
|---|---|---|---|---|
| `bench 11` | 312866 | **312866** | **312866** | `*/honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | **862329** | `*/honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | **3024920** | `*/honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | **4865609** | `*/honesty_perft5.txt` |

Exes: `LmrCutNode` `/agent/repos/work/build-l3a/forge` sha256
`0fb846a67ff2e9752836e47a8a8e8153eda0ee21eed196916fda6679adcc88ad`; `LmrTtPv`
`/agent/repos/work/build-l3b/forge` sha256 `926f48eba93f5583b6b6cb117de92852d85b7d4113c15526f537282cc18611c2`.
Both `id name Chess Engine Forge 6.4.24 candidate` (`*/uci.txt`). Clean copies `/agent/repos/p3`
and `/agent/repos/p4`, both at 6b98f2170a3210e71beed04bbd2553972c253ed7.

## 3. Steps

### LmrCutNode (`tests_deepseek6_long3/LmrCutNode/`)

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| new option named with default and range | done | `LmrCutNode.patch.txt`, `uci.txt` | `LmrCutNode` spin default **2**, min **0**, max **4** |
| apply without fuzz on a clean copy | done | `patch_apply.txt` | clean, `--fuzz=0 --dry-run` passed first |
| build | done | `exe.sha256` | Release g++ 13.3.0 |
| honesty at the default | done | `honesty_*.txt` | all four met |
| identity O/S14 vs long 1 | done | `O_S14_def.rows` | **200 of 200 equal**, sum 9,500,069 |
| identity G/S14 vs long 1 | done | `G_S14_def.rows` | **353 of 353 equal**, sum 18,466,239 |
| identity O/none vs long 1 | done | `O_none_def.rows` | **200 of 200 equal**, sum 12,573,318 |
| wired: `=0` | done | `O_S14_cn0.rows` | sum **9,448,238** (differs from 9,500,069) |
| wired: `=1` | done | `O_S14_cn1.rows` | sum **9,321,641** (differs) |
| wired: `=3` | done | `O_S14_cn3.rows` | sum **9,372,491** (differs) |
| wired: `=4` | done | `O_S14_cn4.rows` | sum **9,648,987** (differs) |
| out-of-range stop check | done | `stopcheck_cn9.rows` | `LmrCutNode=9` -> `invalid value`, stopped, exit 2 |

### LmrTtPv (`tests_deepseek6_long3/LmrTtPv/`)

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| new option named with default and range | done | `LmrTtPv.patch.txt`, `uci.txt` | `LmrTtPv` spin default **1**, min **0**, max **4** |
| apply without fuzz on a clean copy | done | `patch_apply.txt` | clean |
| build | done | `exe.sha256` | Release g++ 13.3.0 |
| honesty at the default | done | `honesty_*.txt` | all four met |
| identity O/S14 vs long 1 | done | `O_S14_def.rows` | **200 of 200 equal**, sum 9,500,069 |
| identity G/S14 vs long 1 | done | `G_S14_def.rows` | **353 of 353 equal**, sum 18,466,239 |
| identity O/none vs long 1 | done | `O_none_def.rows` | **200 of 200 equal**, sum 12,573,318 |
| wired: `=0` | done | `O_S14_tp0.rows` | sum **7,102,738** (differs) |
| wired: `=2` | done | `O_S14_tp2.rows` | sum **13,036,988** (differs) |
| wired: `=3` | done | `O_S14_tp3.rows` | sum **17,313,152** (differs) |
| wired: `=4` | done | `O_S14_tp4.rows` | sum **20,676,319** (differs) |
| out-of-range stop check | done | `stopcheck_tp9.rows` | `LmrTtPv=9` -> `invalid value`, stopped, exit 2 |

## 4. Findings

### 4.1 Both patches are exact identities at their defaults, on both sets

```
cd forge-combo29/tests_deepseek6_long3/LmrCutNode
python3 cmprows.py O_S14_def.rows ../../../tests_deepseek6_long1/O_S14.rows  -> 200 of 200 equal
python3 cmprows.py G_S14_def.rows ../../../tests_deepseek6_long1/G_S14.rows  -> 353 of 353 equal
python3 cmprows.py O_none_def.rows ../../../tests_deepseek6_long1/O_none.rows -> 200 of 200 equal
cd ../LmrTtPv   (same three commands, same three answers)
```
(The `../../../` path is to my branch's own long-1 raw files, so this is plain build vs patched build.)

### 4.2 `LmrTtPv` is wired, monotone and huge

```
cd tests_deepseek6_long3/LmrTtPv
for v in 0 1 2 3 4; do ... done
LmrTtPv=0  rows 200 sum 7102738
LmrTtPv=1  rows 200 sum 9500069   <- the base, at the default
LmrTtPv=2  rows 200 sum 13036988
LmrTtPv=3  rows 200 sum 17313152
LmrTtPv=4  rows 200 sum 20676319
```
Strictly increasing, and the whole range spans a factor of 2.9. Every one of the 200 rows differs from
the base in nodes at every value (`rowdiff.py`: 200 of 200 nodes differ, 48–58 of 200 best moves differ).
`LmrTtPv=0` = 7,102,738: this is **exactly** the number glmflash5 reports for "S14+ttpv0" on its own chain,
reached independently by my rig. Two independent rigs agreeing to the node is the strongest check either of
us has on this line.

### 4.3 `LmrCutNode` is wired, but small and NOT monotone

```
cd tests_deepseek6_long3/LmrCutNode
LmrCutNode=0  rows 200 sum 9448238
LmrCutNode=1  rows 200 sum 9321641
LmrCutNode=2  rows 200 sum 9500069   <- the base, at the default
LmrCutNode=3  rows 200 sum 9372491
LmrCutNode=4  rows 200 sum 9648987
```
Every value differs from the base, so the option is wired. But the sequence over 0,1,2,3,4 is
9,448,238 -> 9,321,641 -> 9,500,069 -> 9,372,491 -> 9,648,987, which is **not monotone**: 1 is below 0,
2 is above both, and 3 is below 2 while 4 is the highest. My filed bands expected monotone growth and
were wrong at every point: 9,448,238/9,321,641/9,372,491 are all below my 9,500,000 floor and 9,648,987 is
above my 9,600,000–10,100,000 top. I record the bands as missed, not as adjusted.

### 4.4 Why the non-monotonicity is not a contradiction, but it is also not proven

`r` is an integer and every change to it is +/-1 at a time, so a single unit can move a reduction across
the `r >= 1` / `r < 1` threshold (or change a re-search depth by one) for MANY nodes at once. A small
option like `LmrCutNode` (whose whole range is 0..4 of a term the base sets to a constant 2) therefore
does not trace a smooth curve: the tree is a step function of `r`, and which step you land on decides the
sign of the difference. `LmrTtPv` looks smooth only because its range is large relative to the reduction
values — a 0..4 swing against a credit the base sets to 1 moves the reduction in big jumps everywhere.

**Suspicion, not proven:** the four `LmrCutNode` sums are four points of a step function with a
best-move churn of 52–57 rows out of 200 at every value (measured with `rowdiff.py`); that churn, not a
smooth response, is what makes the sum wobble. Proof would need the reduction distribution instrumented,
which is a job-sized question.

### 4.5 Both new options are range-checked by the engine and by my rig

```
python3 rows.py ... --opts "$S14;LmrCutNode=9" -> STOPPED: info string invalid value for option LmrCutNode
python3 rows.py ... --opts "$S14;LmrTtPv=9"    -> STOPPED: info string invalid value for option LmrTtPv
```
Both stopped before row 0 with `rows_written: 0` and exit 2.

### Suspicions, not proven

- `LmrTtPv`'s size (2.9x across its range, 25 % between consecutive units) says this one line is one of the
  most powerful single knobs in the search. Whether "more credit" is better or worse is a strength question
  and node counts cannot answer it — glmflash5's match chain and glmflash5 alone can.
- `LmrCutNode=3` being *below* 2 but `=4` above everything fits "the reduction is already at 0 for most
  moves at 2, so one more unit does nothing while the few moves it does touch re-search differently" — but
  I did not instrument it.
- The 52–57 of 200 best-move flips at every `LmrCutNode` value, including `=1` (one unit from the default),
  are more churn than I expected from a one-unit change. It is consistent with a threshold crossing, but I
  have not shown that is the mechanism.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): says `LmrCutNode` (default 2) is "tree −2.1 % on O nodes, wrong-way by my
  tables" and worth playing first. My `=1` reading is −1.9 % on O (9,321,641 vs 9,500,069), which agrees
  with its −2.1 % to within the set, so its tree number is confirmed here; its "wrong-way" verdict is a
  strength claim my rig cannot check and I do not repeat it as a result.
- **glmflash5** (`NOTES_glmflash5.md`): reports `LmrTtPv` applied clean for it and the sums reproduce, and
  its S14+ttpv0 figure is 7,102,738 — which my build reproduces exactly. That is the one cross-rig
  agreement in this report.
- **deepseek5** (`NOTES_deepseek5.md`): the moment-of-the-event lesson; not needed here.
- No note is an order and no number above comes from a note — 7,102,738 is mine, and I say it agrees with
  glmflash5's because I checked both.

## 6. What I did NOT do

- I did not test either option on G (long 3's wording is "the same for ..."; long 2 pinned the wording to
  "the sum on O must CHANGE", and I stayed with O for the wiring, adding all four non-default values
  because each is 5 s).
- I did not instrument the reduction distribution, so 4.4's mechanism is a suspicion only.
- I did not measure strength, and I do not claim either option is good or bad.
- I did not combine the two patches (long 3 says one at a time; `LmrCalib.patch.txt` is the combined one
  and is not mine to run unless a job asks).
- I did not commit any engine source or patched copy; the patch texts are committed as text.
- I did not open a pull request.

## 7. What I am NOT sure about

- Whether the identity should also hold at other depths. Held for the after-long-8 step, which names depth 14.
- The mechanism of 4.3. The measurements are certain; the reason is not.
- Both these options are in `search.cpp`'s single reduction line, so the identity at the default proves the
  patch is inert at the default *for these two sets at depth 12*. It does not prove inertness at other
  depths; see above.

## 8. A better way

For an option whose whole range is four units on an integer that decides a threshold, one value per step of
the whole range (as done here) is cheap enough that "monotone" should never be predicted — I predicted it
and was wrong. Picking the killed-by condition as "the sum differs" and letting the direction be whatever it
is would have been the honest prediction for `LmrCutNode`; that is what I will do for every remaining patch.

## 9. times

see `stamps.txt` in each folder.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`ls` + `git status --short` at the moment before this commit: `LmrCutNode/precommit_evidence.txt`,
`LmrTtPv/precommit_evidence.txt`.
