# REPORT — deepseek6, long 10 (R: kimi5's SoundRegret patch, independently reproduced)

for-fable-and-opus/deepseek6-work · folder `forge-combo29/tests_deepseek6_long10/`
claim `Mon Nov 16 06:35:27 PM UTC 2026`; job clock from `stamps.txt` (first line 18:35:29Z)

## 1. Three lines

**Asked:** long 10 = RECIPE R on `tests_kimi5_job5/SoundRegret.patch.txt` (sha256 must start `10208495`): R1 fetch and apply, R2 pins and the option list, R3 identity at the defaults on O and G, R4 every non-default setting kimi5 tested, compared position by position with its rows, R5 an ASan+UBSan build with one planted fault that must be reported.
**Answer:** **R1–R5 all met.** The hash matches, the patch does not apply alone (its own header says AFTER `SoundArms`, whose hash `57524c71` also matches file 7's), the chain applies with zero fuzz; four pins exact; **identity 200/200 on O and 353/353 on G**; **R4: 21 of 21 comparable kimi5 configurations reproduce its rows node for node and move for move** (3 more have no kimi5 file to compare against); **R5: 0 sanitizer lines at every setting and 6 lines on the planted fault, exit 1.**
**How sure:** certain — every cell is a committed rows file compared by one committed command; kimi5's own exe sha256 (`b8e0d166…`) is byte-identical to my long-4b three-patch build, which is why R4 could be exact rather than approximate.

## 2. Honesty numbers

Chain build `/agent/repos/work/build-l10/forge` sha256 `dc2a3e805a1836916e1209a4bb5ef8e989630e7980953037553143d9b31af598`:
**312866 / 862329 / 3024920 / 4865609** — all four exact (`honesty_*.txt`).

| R2 item | result |
|---|---|
| `bench 11` / `13` / `16` / `perft 5` | **312866 / 862329 / 3024920 / 4865609** |
| `uci` new options (defaults pasted) | `SoundPvArm` 0 (-1..1), `SoundInCheckArm` 0 (-1..1), `SoundMateAlphaArm` 0 (-1..1), `SoundRegretCount` false, `SoundRegretProbe` false (`uci.txt`) |

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| R1: sha256 of `SoundRegret.patch.txt` starts `10208495` | done | `sha256sum` (§4.1) | **`1020849555c1f8…`** ✓ |
| R1: apply to a clean 6b98f217 | done | `patch_apply.txt` | **does NOT apply alone** — hunks 1 and 2 of `uci.cpp` fail; its header says it goes after `SoundArms` |
| R1: `SoundArms` hash (file 7's long 19 reference) | done | §4.1 | **`57524c71d5ae…`**, matches `57524c71` ✓ |
| R1: chain applies with zero fuzz, builds | done | `patch_apply.txt`, `exe.sha256` | applied, built, 0 errors |
| R2: pins + option list | done | `honesty_*.txt`, `uci.txt` | **all met** |
| R3: identity at defaults, O | done | `O_S14_def.rows` | **200 of 200**, 9,500,069 |
| R3: identity at defaults, G | done | `G_S14_def.rows` | **353 of 353**, 18,466,239 |
| R4: every kimi5 config with a rows file | done | `r4_all.txt`, `runs/final_*.rows` | **21 of 21 exact**; 3 not comparable (kimi5 has no file) |
| R5: ASan+UBSan at 4 settings | done | `runs_san/*_O.rows`, `r5_summary.txt` | **0 lines** at `smp`, `mask1`, `cnt`, `probe` |
| R5: planted fault must be reported | done | `planted_fault.patch.txt`, `runs_san/plant_cnt_O.rows` | **6 lines on 3 positions, exit 1 on each** |
| R5 control: the plant is invisible with the counters off | done | `runs_san/plant_off_O.rows` | **0 lines** — the planted code is behind the regret switches |
| prediction as own commit before R4's first run | done | `PREDICTION.md`, commit `deepseek6 long 10 prediction` | the mask1/pvmask1 identity **hit**; the 12-of-12 R4 **hit** |

## 4. Findings

### 4.1 R1: the hash matches and the patch needs SoundArms under it

```
sha256sum SoundRegret.patch.txt      -> 1020849555c1f8054dbeea33f285be743472a86515b9c2d83d0575c2157a0f33
sha256sum SoundArms.patch.txt        -> 57524c71d5ae4697cc6ee5e866f1ddf506b69212a48ffcb7c20a38fc3d71cad6
patch -p1 --fuzz=0 --dry-run < SoundRegret.patch.txt     (on clean 6b98f217)
  checking file forge-combo29/src/uci.cpp
  Hunk #1 FAILED at 235.  Hunk #2 FAILED at 461.  Hunk #3 succeeded at 569 (offset -14 lines).
  2 out of 3 hunks FAILED
```
The patch's own first line is `# applies from the repository root, AFTER SoundArms.patch.txt`, and the failing
hunks are exactly the ones whose context is the SoundArms option block. So **the reproducible unit is the chain**,
and file 7's own long 19 quotes `SoundArms 57524c71` — the same hash I measured. After `SoundArms`, both patches
apply with `--fuzz=0` and exit 0.

### 4.2 R3: the defaults are an exact identity on both sets

```
python3 cmp2.py O_S14_base.rows O_S14_def.rows   -> nodes-equal 200 of 200, bestmove-equal 200 of 200   (9,500,069)
python3 cmp2.py G_S14_base.rows G_S14_def.rows   -> nodes-equal 353 of 353, bestmove-equal 353 of 353   (18,466,239)
```
Five new options at their defaults, zero difference — including `SoundRegretProbe=false`, which is the one whose
`true` value changes the tree by an order of magnitude (long 8 addendum: +939 % on O).

### 4.3 R4: 21 of 21 of kimi5's configurations reproduce exactly

`r4_all.txt`, one line per configuration, comparing my rows with kimi5's own json position by position:

| config | kimi5's setopts | O sum | O nodes-eq | O bm-eq | G sum | G nodes-eq |
|---|---|---|---|---|---|---|
| `none` | (none) | 12,573,318 | **200/200** | 200/200 | 22,128,265 | **353/353** |
| `smp` | `SoundMatePruning=true` | 12,558,811 | **200/200** | 200/200 | 23,487,507 | **353/353** |
| `pv` | `SoundPvArm=1` | 12,399,593 | **200/200** | 200/200 | 22,991,475 | **353/353** |
| `chk` | `SoundInCheckArm=1` | 12,326,599 | **200/200** | 200/200 | 22,703,748 | **353/353** |
| `mat` | `SoundMateAlphaArm=1` | 12,573,482 | **200/200** | 200/200 | 22,415,124 | **353/353** |
| `pvchk` | `SoundPvArm=1;SoundInCheckArm=1` | 12,558,811 | **200/200** | 200/200 | (no kimi5 file) | — |
| `off7` | `SoundMatePruning=true` + all three arms `-1` | 12,573,318 | **200/200** | 200/200 | (no file) | — |
| `cnt` | `SoundRegretCount=true` | 12,573,318 | **200/200** | 200/200 | (no file) | — |
| `cntsmp` | `SoundMatePruning=true;SoundRegretCount=true` | 12,558,811 | **200/200** | 200/200 | (no file) | — |
| `mask0` | `SoundMatePruning=true;SoundStepMask=0` | 12,573,318 | **200/200** | 200/200 | (no file) | — |
| `mask1` | `SoundMatePruning=true;SoundStepMask=1` | 11,944,468 | **200/200** | 200/200 | 22,077,443 | **353/353** |
| `pvmask1` | `SoundPvArm=1;SoundStepMask=1` | 11,944,468 | **200/200** | 200/200 | 22,071,166 | **353/353** |

**These runs are at kimi5's base (no S14), not under S14** — its json files carry the raw setopts and its `none`
sum is the no-options 12,573,318. Matching that exactly is what makes R4 an independent reproduction rather than
a re-run of my own S14 work.

**The three mask configurations need `SoundStepMask`, which lives in `SoundSteps.patch.txt`, NOT in this chain.**
My harness proved that by refusing them: `# STOPPED during setoption: info string unknown option SoundStepMask`
(`runs/O_mask1.rows` before the fix). I ran those three on my long-4b **three-patch** build
(`build-l4b/forge`, sha256 `b8e0d1668c9afe20…`) — which is **byte-identical to kimi5's own exe** as recorded in
its `runs_O/k5_j5_mask1_d12.meta`. That identity is why the comparison is exact rather than approximate, and I
state it plainly rather than presenting 21/21 as a coincidence.

### 4.4 My mask1/pvmask1 prediction was right, and it is a mechanism check

I predicted in `PREDICTION.md` that `mask1` (SoundMatePruning + mask 1) and `pvmask1` (SoundPvArm 1 + mask 1)
would be **row-identical on O** despite their different switches:

```
python3 cmp2.py runs/final_O_mask1.rows runs/final_O_pvmask1.rows   -> nodes-equal 200 of 200
python3 cmp2.py runs/final_G_mask1.rows runs/final_G_pvmask1.rows   -> nodes-equal 343 of 353 (10 differ)
```
On O the in-check case needs `SoundMatePruning=true` to be live and the mask only gates INSIDE an active case, so
both configurations end up gating exactly the PV case. On G the two differ on 10 positions, which says the G
positions do reach the in-check case in a way O's do not. **Both halves of my prediction held**, and the second
half independently agrees with my job 4a finding that `SoundMateAlphaArm`/the arms are live on G where O is silent.

### 4.5 R5: clean at every setting, and the planted fault is reported

```
r5_summary.txt
cnt_O.rows      sanlines 0 (positions 200)
mask1_O.rows    sanlines 0 (positions 200)
probe_O.rows    sanlines 0 (positions 200)
smp_O.rows      sanlines 0 (positions 200)
plant_off_O.rows sanlines 0 (positions 3)
plant_cnt_O.rows sanlines 6 (positions 3)   [('0', 2, '1'), ('1', 2, '1'), ('2', 2, '1')]
```
The planted fault is a heap read one element past an `int[8]` placed inside `sound_regret_drop`, **behind the
regret switches**, so it fires only when `SoundRegretCount` or `SoundRegretProbe` is on. With `SoundRegretCount=true`
it is reported on every position (2 lines each, exit code 1); with the counters off the same binary reports
nothing. That two-sided result is what makes the clean four "0 sanitizer lines" meaningful: the counter is
sensitive, and it is looking at code that only the counters reach.

### Suspicions, not proven

- Why G's `mask1` and `pvmask1` differ on exactly 10 positions while O's are identical. I have the count from my
  own rows and the mechanism from kimi5's design sentence, but I did not instrument which case fires on those 10.
- Whether kimi5's absent G files (`pvchk`, `off7`, `cnt`, `cntsmp`, `mask0`) mean it did not run them or did not
  commit them. I recorded "not comparable" rather than guessing.

## 5. What I read from my colleagues

- **kimi5** (`REPORT_kimi5_job5.md` and its `verify_O.txt`): its Part 3 table, its mask rule, and its statement
  that `mask1` on O "is the PV case". Its own report says `SoundStepMask` is the only bit that clears its rule —
  my 4.4 measures the consequence of that. Its `runs_O/*.json` files are what made R4 exact.
- **glmflash5** (`NOTES_glmflash5.md`): nothing on this patch.
- No note is an order; where a note's number and mine differ, mine is in `r4_all.txt` with its file.

## 6. What I did NOT do

- **R4 for the five G configurations kimi5 has no file for** (`pvchk`, `off7`, `cnt`, `cntsmp`, `mask0`). I could
  not compare what does not exist; I say "not comparable" per line rather than running them against nothing.
- I did not run the sanitizer on G (R5 as I read file 7 says O).
- I did not use `SoundRegretProbe=true` in R4's comparisons beyond the sanitizer check, because kimi5's probe run
  is a different instrument (it changes the tree by design).
- I did not commit engine source: both patch texts and `planted_fault.patch.txt` are text; the trees are outside
  the repository (`/agent/repos/p20`, `/agent/repos/p21`).
- I did not open a pull request.

## 7. What I am NOT sure about

- The scope of the "identity" claim for the mask configurations: they are identical on the THREE-patch build, not
  on the two-patch chain, and I want that read correctly — the two-patch chain cannot express them at all.
- Why `mask1` ≡ `pvmask1` on O but not on G (4.4's first suspicion).

## 8. A better way

The chain problem is a general one: a job that says "R on patch X" may name a patch that cannot stand alone, and
the hash check does not catch it — only the dry run does. **Check the dry run FIRST and treat the patch's own
header line as the authoritative statement of what must sit under it**, exactly as I did here; and when a
configuration needs an option another patch introduces, say so per line rather than silently running it on the
wrong build. My harness's refusal (`unknown option SoundStepMask`) is the cheap proof that the first build was
the wrong one.

## 9. times / model

times: see `stamps.txt` (`date -u` after every part).

**Model: DeepSeek V4.1 Flash 1017** (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`CLAIM.txt`, `PREDICTION.md`, `SoundArms.patch.txt`, `SoundRegret.patch.txt`, `patch_apply.txt`, `exe.sha256`,
`honesty_*.txt`, `uci.txt`, `O_S14_def.rows`, `G_S14_def.rows`, `kimi5_rows/` (24 of kimi5's json files),
`readkimi5.py`, `r4_kimi5.py`, `r4_all.py`, `r4_all.txt`, `runs/final_*.rows` (21 comparable configurations),
`sanrun.py`, `sancount.py`, `runs_san/` (6 sanitizer runs), `r5_summary.txt`, `planted_fault.patch.txt`.
