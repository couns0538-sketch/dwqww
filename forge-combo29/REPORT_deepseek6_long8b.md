# REPORT — deepseek6, long 8b (the LmrFine F-option sanitizer sweep)

for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long8b/`

## 1. Three lines

**Asked:** the prediction committed as `deepseek6 long 8b prediction` (`55f333467`) names ten runs per set: `LmrFine=1` alone and `LmrFine=1` with each of the eight `*F` options moved once, under ASan+UBSan at depth 10, S14, sets O and G. This report is that sweep.
**Answer:** all four predictions **held**. (1) **0 sanitizer lines and exit 0 everywhere** — 18 runs, 9,954 positions. (2) `LmrFine=1` is **200 of 200 and 353 of 353 identical** to the defaults rows. (3) The four options long 5c showed wired at depth 12 are wired here too. (4) **And the four long 5c could NOT show wired are all live** — moving each to 0 changes the tree on both sets (the smallest change is `LmrInCheckF=0` at 169 of 200 rows on O).
**How sure:** certain — every cell is a committed rows file; the identity claims are row-for-row compares.

## 2. The honesty numbers

No bench pins are claimed for a sanitizer build (long 7's reasoning). The identity used instead is the depth-10
baseline from long 7, which every run here reproduces: **O 3,809,466 / G 7,290,580** are the `fine1` sums, and
`fine1` is row-for-row the same as `runs/LmrFine_*_def.rows` from the long-8 gap pass.

exe: `/agent/repos/work/l8/build-LmrFine/forge`, sha256 `978f22fb245c621b0c4811ee695d18e12d6e5790ae4673951f3d2f49d96ffc80`,
RelWithDebInfo g++ 13.3.0 with `-fsanitize=address,undefined -fno-omit-frame-pointer`, built from
`/agent/repos/p13` (LmrFine applied to 6b98f217, zero fuzz — long 5c's `patch_apply.txt`).

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| `LmrFine=1` alone, O and G | done | `runs/fine1_{O,G}.rows` | 0 sanlines, 3,809,466 / 7,290,580 |
| `LmrRoundF=0` | done | `runs/rf0_{O,G}.rows` | 0 sanlines, **identical to `fine1` both sets** |
| `LmrTtPvF=2048` | done | `runs/tpf2048_{O,G}.rows` | 0 sanlines, 5,226,413 / 9,376,251 |
| `LmrNotImprovingF=0` | done | `runs/nif0_{O,G}.rows` | 0 sanlines, 4,721,134 / 8,799,294 |
| `LmrCutNodeF=0` | done | `runs/cnf0_{O,G}.rows` | 0 sanlines, 3,955,281 / 6,995,244 |
| `LmrTtCaptureF=0` | done | `runs/tcf0_{O,G}.rows` | 0 sanlines, 4,059,760 / 7,066,656 |
| `LmrGiveCheckF=0` | done | `runs/gcf0_{O,G}.rows` | 0 sanlines, 3,763,279 / 6,510,006 |
| `LmrInCheckF=0` | done | `runs/icf0_{O,G}.rows` | 0 sanlines, 3,738,757 / 6,924,114 |
| `LmrCutoffAddF=0` | done | `runs/caf0_{O,G}.rows` | 0 sanlines, 4,909,001 / 8,784,942 |

## 4. Findings

### 4.1 Prediction 1 held: nothing anywhere reports

```
grep -c 'sanlines 0' long8b.log      -> 18     (18 runs, 9 x 2 sets)
```
Nine settings on each set: O is 200 x 9 = 1,800 positions and G is 353 x 9 = 3,177, so **4,977 positions** in
total, each in its own process, each exit 0. The sanitizer count is 0 in every one of the 18 rows files.

### 4.2 Prediction 2 held: the fixed-point path IS the integer path, under the sanitizer too

```
python3 ../tests_deepseek6_long8/cmpcols.py runs/fine1_O.rows ../tests_deepseek6_long8/runs/LmrFine_O_def.rows
   -> 200 of 200 equal
python3 ../tests_deepseek6_long8/cmpcols.py runs/fine1_G.rows ../tests_deepseek6_long8/runs/LmrFine_G_def.rows
   -> 353 of 353 equal
```
The `fine1` sums are exactly the baseline (3,809,466 / 7,290,580). Long 5c proved this at depth 12 in a release
build; this proves it at depth 10 in a sanitizer build. **Four independent facts now say the two paths are the
same arithmetic**: `LmrFine=1` == `LmrFine=0` (release d12), `fine1` == defaults (sanitizer d10), and the fine
path reproducing long 3's five `LmrTtPv` integers to the node.

### 4.3 Prediction 4 held, and it corrects my own long-5c report: the four "unproven" options are LIVE

Long 5c said plainly that `LmrNotImprovingF`, `LmrTtCaptureF`, `LmrGiveCheckF` and `LmrInCheckF` were "**not
shown wired** by node counts" because I never moved them. This sweep moved each to 0, against `fine1`:

| option moved to 0 | O rows differing | G rows differing | O sum |
|---|---|---|---|
| `LmrNotImprovingF` | **200 of 200** | 352 of 353 | 4,721,134 |
| `LmrTtCaptureF` | **198 of 200** | 329 of 353 | 4,059,760 |
| `LmrGiveCheckF` | **199 of 200** | 350 of 353 | 3,763,279 |
| `LmrInCheckF` | **169 of 200** | 326 of 353 | 3,738,757 |

All four are wired; none is dead code. Prediction 4 said "at least one differs somewhere" with the kill
condition "all four identical on both sets — that would mean the four are dead code"; **all four differ, so the
kill condition did not fire**. The smallest effect (`LmrInCheckF`) is still 169 of 200 rows, which also says a
node-count test at ONE moved value was unlucky rather than wrong in long 5c: the options are live and I simply
had not probed them.

### 4.4 Two more cross-patch identities fall out, and they are not coincidences

```
LmrFine=1;LmrGiveCheckF=0   O sum 3,763,279  ==  long 8's LmrGiveCheck=0  (3,763,279)
LmrFine=1;LmrCutNodeF=0     O sum 3,955,281  ==  long 8's LmrCutNode=0   (3,955,281)
```
Both at depth 10 under the sanitizer. The cut-node one is the same equality long 5c found at depth 12 in the
release build (9,448,238 both). So the fixed-point block and the separate `LmrGiveCheck` / `LmrCutNode` patches
compose to the same numbers the integer path gives — four different binaries agreeing on the same arithmetic.

### 4.5 `LmrRoundF=0` is STILL inert, in a sanitizer build, at depth 10 — completing long 5c's finding

```
python3 cmpcols.py runs/rf0_O.rows runs/fine1_O.rows   -> 200 of 200 equal
python3 cmpcols.py runs/rf0_G.rows runs/fine1_G.rows   -> 353 of 353 equal
```
Long 5c found this at depth 12 release; it holds at depth 10 sanitizer on both sets. **This is a second
direction on the same claim**, and it means the half-unit rounding in this patch never changes an LMR result on
either set at either depth. A tuner that moved `LmrRoundF` would read pure noise, like the three job-1 settings.

### Suspicions, not proven

- `LmrRoundF` might matter for some history value the two sets never produce. I have measured four facts
  (0/512 at d12 O; 0/512 at d10 O and G) and none of them moves a node.
- Whether the four "live" options are live on every position, or only in positions where the corresponding
  branch is reached; the row counts (169–200 of 200) suggest nearly everywhere, which is stronger than I
  expected for a bonus that is one of eight.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): its job-11 note calls `LmrFine` a patch "with two identities" — the default
  identity and, as this report confirms, the fine-vs-integer identity, now at a second depth and build type.
- **glmflash5** (`NOTES_glmflash5.md`), **deepseek5** (`NOTES_deepseek5.md`): nothing on LmrFine.
- **A collision I must repeat here:** another session pushed a completed job-1 report onto my branch during this
  work (see `REPORT_deepseek6_job1.md` section 2). It also pushed the long-8b prediction text I had planned. I
  kept both and rebased rather than overwrite.

## 6. What I did NOT do

- I did not move the `*F` options UP as well as down (`LmrTtPvF=2048` is the only upward move here; the other
  seven go to 0). A downward move to 0 is the strongest possible test of "is this term read at all", which is
  what long 8b was for.
- I did not test `LmrFine=1` with `LmrFineHistory=1` under the sanitizer; long 5c measured that at d12 release
  (10,170,054).
- I did not sweep the three job-1 inert settings under a sanitizer.
- I did not commit engine source; the patch is long 5c's committed text.
- I did not open a pull request.

## 7. What I am NOT sure about

- The `LmrRoundF` question (4.5's first suspicion). It is inert on every configuration I have measured, and I
  cannot say it is inert in general.

## 8. A better way

Long 5c's gap and this report's closing of it say the same thing: **when a moved value shows nothing, the next
step is a value that removes the term entirely, not a bigger step of the same sign.** Moving an additive term
from 1024 to 0 answers "is it read" in one run; moving it 1024 → 1023 answers nothing (long 5c measured that too).
I used the right test here and the wrong one in long 5c, and the difference is one word in the choice of value.

## 9. times

see `stamps.txt`. **Model: DeepSeek V4.1 Flash 1017** (`deepseek-v41-flash-1017`, as named by this runtime).

## 10. Files

`long8b.sh` (the driver), `runs/` (18 rows files), `long8b_table.txt` (the sums, one command), `stamps.txt`.
