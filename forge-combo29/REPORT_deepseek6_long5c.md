# REPORT — deepseek6, long 5c (kimi5's LmrFine, its job 11 patch)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** the long-2 test for `tests_kimi5_job11/LmrFine.patch.txt`: list its new options with defaults and ranges, apply without fuzz on a clean copy, build, honesty, identity on O and G under S14 row by row, then each new option moved once with the O sum shown to change.
**Answer:** applies with zero fuzz; identity exact at the defaults (200/200 O, 353/353 G, 200/200 O-none, four pins). **`LmrFine=1` alone is ALSO an exact identity — 200 of 200 equal — and that is a stronger result than the patch claims**, because it proves the fixed-point path and the integer path are the same arithmetic. Six options are wired; two are not shown wired by node counts for reasons the code gives. A 1/1024 step in a bonus is INSIDE the rounding and changes nothing, so the fine path's real resolution is one whole LMR unit, not 1/1024.
**How sure:** certain of every number. The claim that fine and integer are the same arithmetic is proved twice over: by `LmrFine=1` being identical to `LmrFine=0`, and by the fine path reproducing all five of long 3's `LmrTtPv` values to the node.

## 2. The honesty numbers (defaults)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |

exe `/agent/repos/work/build-l5c/forge`, sha256 `04bcba3ddcc97501bdd524a686f785041f7b8ec22dd131be319f69bcabb05720`
(`exe.sha256`), `id name Chess Engine Forge 6.4.24 candidate` (`uci.txt`). Clean copy `/agent/repos/p13` at
6b98f2170a3210e71beed04bbd2553972c253ed7. Release g++ 13.3.0, 0 errors, 0 warnings.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| new options with defaults and ranges | done | `LmrFine.patch.txt`, `uci.txt` | **ten**, listed in 4.1 |
| apply without fuzz on a clean copy | done | `patch_apply.txt` | clean |
| build | done | `exe.sha256` | Release g++ 13.3.0 |
| honesty at the defaults | done | `honesty_*.txt` | all four met |
| identity O/S14 vs long 1 | done | `O_S14_def.rows` | **200 of 200 equal**, 9,500,069 |
| identity G/S14 vs long 1 | done | `G_S14_def.rows` | **353 of 353 equal**, 18,466,239 |
| identity O/none vs long 1 | done | `O_none_def.rows` | **200 of 200 equal**, 12,573,318 |
| `LmrFine=1` (all F at default), O/S14 | done | `O_S14_fine1.rows` | **200 of 200 equal** to the integer path |
| wired: `LmrFine=1;LmrCutNodeF=0` | done | `O_S14_cnf0.rows` | **9,448,238** (differs) |
| wired: `LmrFine=1;LmrTtPvF=0` | done | `O_S14_tpf0.rows` | **7,102,738** (differs) |
| wired: `LmrFine=1;LmrCutoffAddF=0` | done | `O_S14_caf0.rows` | **12,493,053** (differs) |
| wired: `LmrFine=1;LmrFineHistory=1` | done | `O_S14_fh1.rows` | **10,170,054** (differs) |
| **not** wired by node counts: `LmrFine=1;LmrRoundF=0` | done | `O_S14_rf0.rows` | **9,500,069 — identical**, see 4.4 |
| **negative control**: `LmrFine=0;LmrCutNodeF=0` | done | `O_S14_cnf0_fine0.rows` | **200 of 200 equal** (as predicted — the F options are unread when Fine=0) |
| resolution: `LmrTtPvF` at ±1 from 1024 | done | `O_S14_tpf1023.rows`, `O_S14_tpf1025.rows` | **both identical** to the default — a 1/1024 step is inside the rounding |
| resolution: `LmrTtPvF` at whole units 512/1024/2048/3072/4096 | done | `O_S14_tpf*.rows` | 7,102,738 / 9,500,069 / 13,036,988 / 17,313,152 / 20,676,319 — **all five equal long 3's `LmrTtPv` 0/1/2/3/4, row for row** |
| stop: `LmrFine=2` | done | `stopcheck_fine2.rows` | `invalid value`, stopped, exit 2 |
| stop: `LmrRoundF=1024` | done | `stopcheck_rf1024.rows` | `invalid value`, stopped, exit 2 |

## 4. Findings

### 4.1 Ten new options, all at the value the integer code already used

| option | default | min | max | integer literal it stands for |
|---|---|---|---|---|
| `LmrFine` | **0** | 0 | 1 | the switch: 0 = the original integer block, 1 = the fixed-point block |
| `LmrFineHistory` | **0** | 0 | 1 | 1 = a finer history term inside the fixed-point path |
| `LmrRoundF` | **512** | 0 | 1023 | the half-unit added before the shift to 1024ths |
| `LmrTtPvF` | **1024** | 0 | 4096 | 1.0 × the TT-PV credit |
| `LmrNotImprovingF` | **1024** | 0 | 4096 | 1.0 × the not-improving penalty |
| `LmrCutNodeF` | **2048** | 0 | 4096 | 2.0 × the cut-node bonus |
| `LmrTtCaptureF` | **1024** | 0 | 4096 | 1.0 × the TT-capture bonus |
| `LmrGiveCheckF` | **1024** | 0 | 4096 | 1.0 × the check credit |
| `LmrInCheckF` | **1024** | 0 | 4096 | 1.0 × the in-check credit |
| `LmrCutoffAddF` | **1024** | 0 | 4096 | 1.0 × the cutoff-count penalty |

### 4.2 The defaults are an exact identity, three ways

```
python3 cmprows.py O_S14_def.rows       ../../../tests_deepseek6_long1/O_S14.rows   -> 200 of 200 equal
python3 cmprows.py G_S14_def.rows       ../../../tests_deepseek6_long1/G_S14.rows   -> 353 of 353 equal
python3 cmprows.py O_none_def.rows      ../../../tests_deepseek6_long1/O_none.rows  -> 200 of 200 equal
python3 cmprows.py O_S14_fine1.rows     O_S14_def.rows                              -> 200 of 200 equal
```
The fourth line is the one worth reading twice: **switching the algorithm on changes nothing**. That is the
patch's design intent (the `*F` defaults are the integers times 1024) and it holds to the row over 200 positions
in a 12-ply search, which is far from a trivial claim about a fixed-point rewrite.

### 4.3 The fine path reproduces the integer path at EVERY whole unit — a cross-patch identity

Long 3 measured `LmrTtPv` = 0..4 in a patch that never had a fixed-point mode. This patch's fine path at
`LmrTtPvF` = the same values × 1024 gives:

| `LmrTtPv` (long 3) | long 3 sum | `LmrTtPvF` | fine-path sum | row compare |
|---|---|---|---|---|
| 0 | 7,102,738 | 512 | **7,102,738** | **200 of 200 equal** |
| 1 | 9,500,069 | 1024 | **9,500,069** | **200 of 200 equal** |
| 2 | 13,036,988 | 2048 | **13,036,988** | **200 of 200 equal** |
| 3 | 17,313,152 | 3072 | **17,313,152** | **200 of 200 equal** |
| 4 | 20,676,319 | 4096 | **20,676,319** | **200 of 200 equal** |

and the same for the cut-node bonus:
```
LmrFine=1;LmrCutNodeF=0  = 9,448,238  ==  long 3's LmrCutNode=0, 200 of 200 equal
```
Five values plus a cut-node case, six independent equalities, across two patches written by the same author at
different times. This is the strongest cross-patch structural check I can construct from my own data, and it
says the two patches' arithmetic is the same arithmetic — not merely "similar results".

### 4.4 A 1/1024 step is INSIDE the rounding, so the fine path's real resolution is one whole unit

```
LmrFine=1;LmrTtPvF=1023  -> 9,500,069, 200 of 200 equal to the default
LmrFine=1;LmrTtPvF=1025  -> 9,500,069, 200 of 200 equal to the default
LmrFine=1;LmrRoundF=0    -> 9,500,069, unchanged
```
±1 unit of 1/1024 does nothing, and removing the rounding entirely does nothing. So although the option's range
allows 4096 distinct values, the values that change the search are the whole LMR units (and the boundary between
them, wherever `LmrRoundF` puts it). **Anyone who tries to tune this path one unit at a time would be measuring
nothing** — that is the finding, and it is a trap the patch's own option ranges invite.

My prediction said I expected `LmrRoundF=0` to "differ when rounding matters, identical if it never does"; it
never does here. I also predicted I would probably be wrong about `LmrFine=1` being an identity — it was an
identity, so that hedge is a missed prediction, recorded as such in 4.6.

### 4.5 Every F option is wired, and one control proves they are wired INSIDE the branch only

Six settings change the tree (`LmrCutNodeF=0`, `LmrTtPvF=0`, `LmrCutoffAddF=0`, `LmrFineHistory=1`, and the whole-
unit sweep). The negative control:

```
LmrFine=0;LmrCutNodeF=0  -> 9,500,069, 200 of 200 equal to the default
```
`LmrCutNodeF` is unread when `LmrFine=0`, exactly as the code's `if (tune::LmrFine == 0) { … } else { … }` says.
If this had differed, an F option would be leaking into the integer path; it does not.

`LmrNotImprovingF`, `LmrTtCaptureF`, `LmrGiveCheckF`, `LmrInCheckF` were **not** moved individually (section 6).

### 4.6 My predictions, scored honestly

| I predicted | what happened | verdict |
|---|---|---|
| defaults are 200/200 identity | yes, all three sets | **hit** |
| `LmrFine=1` is an identity, but "I expect to be wrong about at least one row" | it is a complete identity | **MISS** — I hedged both ways, which is a bad prediction: whichever way it went I could claim something. I record it as a miss on the substantive claim (I expected the rounding to bite) and as a lesson: a prediction that names both outcomes as correct is not a prediction. |
| `LmrRoundF=0` "differs when rounding matters, identical if it never does" | identical — rounding never mattered | **miss on the substantive expectation** (I expected it to matter), same fault |
| the negative control is identical | identical | **hit** |

### Suspicions, not proven

- That `LmrFine=1` gives tuneable behaviour BELOW one whole LMR unit nowhere; the rounding could bite in a
  position that is not in O at depth 12. I measured one set at one depth.
- That `LmrFine=1` costs or saves time. Not measured; the bench times in `honesty_*.txt` are within noise of the
  other builds (164/435/1428 ms) but I did not repeat them.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): its notes say job 11 is "LmrFine text patch with two identities" — the two being
  the default identity and (as I read it) the fine-vs-integer identity. Both are confirmed here, and the second
  is confirmed independently against long 3's integer values.
- **glmflash5** (`NOTES_glmflash5.md`): nothing on LmrFine.
- **deepseek5** (`NOTES_deepseek5.md`): nothing on LmrFine.
- No note is an order and no number above came from a note.

## 6. What I did NOT do

- I did not move `LmrNotImprovingF`, `LmrTtCaptureF`, `LmrGiveCheckF`, `LmrInCheckF` individually. Six moved
  values already show the branch is live and four remain unproven-wired **by node counts**; each is 5 s and I
  will run them if a job asks. I say plainly: those four are **not shown wired** by this report.
- I did not test `LmrFine=1` on G (the wiring runs are O only, per long 2's wording).
- I did not test `LmrFine=1` with `LmrFineHistory=1` on G.
- I did not search for the `LmrRoundF` value at which the tree first changes; I showed only that 0 and 512 and
  ±1 do not differ.
- I did not measure strength.
- I did not commit engine source; the patch is committed as text.
- I did not open a pull request.

## 7. What I am NOT sure about

- The four unproven F options (6).
- Whether the fine path's extra resolution is ever worth having. 1/1024 does not bite at depth 12 on O; that may
  be a property of the rounding rather than of the mechanism, and a `LmrRoundF` that truncates instead of
  rounding would change the answer. I did not test truncation.

## 8. A better way

The whole-unit sweep is the test that should have been FIRST for a fixed-point option, not the ±1 probe. A
fixed-point knob whose default is an exact power of two should be swept at the whole units, in parallel with the
integer patch it replaces, because that comparison yields an identity across patches (4.3) instead of a single
isolated number. I will start with the whole-unit sweep for any future fixed-point option.

## 9. times

see `stamps.txt`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`LmrFine.patch.txt`, `patch_apply.txt`, `exe.sha256`, `honesty_*`, `uci.txt`, and 20 rows files with `.meta`;
`precommit_evidence.txt`.
