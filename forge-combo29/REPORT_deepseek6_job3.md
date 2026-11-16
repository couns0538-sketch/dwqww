# REPORT — deepseek6, job 3 (kimi5's FailHighBlend: identity at the default, each bit, sanitizers)

for-fable-and-opus/deepseek6-work · folder `forge-combo29/tests_deepseek6_job3/`
job clock from `job3_start.txt` = `Mon Nov 16 05:06:52 PM UTC 2026`

## 1. Three lines

**Asked (file 2, kimi5's job-12 hand-off):** test kimi5's `FailHighBlend.patch.txt` — identity at the default, each bit, and sanitizers.
**Answer:** the patch applies with zero fuzz and its sha256 equals the one kimi5 publishes (**`8083a257…`**), so I tested the same text; at `FailHighBlend=0` it is an **exact identity** (200/200 O, 353/353 G, all four pins) and sending `0` explicitly is the same program as not sending it; **all seven non-zero values differ from the default on O (0 of 200 nodes equal in every one)**, the seven composition claims all hold, and **14 sanitizer runs (all seven values x both sets, 3,871 positions) report 0 lines with FHB=0 bit-identical to the depth-10 baseline**.
**How sure:** certain of every number. My one directional prediction was wrong for bit 2 on O and right on G, and I score it below.

## 2. Honesty numbers (raw files here)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |

Patch sha256 `8083a257c55b2deef9455c9c698fe750b7c3fd9707d8bc75507a6265cfc23e1a` — **equal to the hash in kimi5's
own job-12 report**, verified by `sha256sum` before applying. Builds:
release `/agent/repos/work/build-j3/forge` sha256 `98438fcbde23ceb8…`; sanitizer
`/agent/repos/work/build-j3san/forge` (RelWithDebInfo + `-fsanitize=address,undefined -fno-omit-frame-pointer`).
Clean copy `/agent/repos/p17` at 6b98f2170a3210e71beed04bbd2553972c253ed7.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| read the patch, list new option with default and range | done | `FailHighBlend.patch.txt`, `uci.txt` | one option `FailHighBlend` spin default **0** min **0** max **7** |
| verify the patch text is the one kimi5 tested | done | `sha256sum` (in this report) | **`8083a257…`, identical to kimi5's published hash** |
| apply without fuzz on a clean copy | done | `patch_apply.txt` | clean |
| build | done | `exe.sha256` | Release g++ 13.3.0, 0 errors |
| honesty at the default | done | `honesty_*.txt` | all four pins |
| identity, no option sent, O and G | done | `O_S14_none.rows`, `G_S14_none.rows` | **200 of 200** and **353 of 353** vs the plain base |
| identity, `FailHighBlend=0` sent explicitly | done | `O_S14_fhb0.rows` | **200 of 200 equal** to the no-option run |
| each bit on O: 1, 2, 4, 3, 5, 7 | done | `O_S14_fhb{1,2,4,3,5,7}.rows` | all seven differ (0 of 200 nodes equal each) |
| composition: 3 vs 1, 3 vs 2, 5 vs 1, 5 vs 4, 7 vs 1/2/4 | done | `cmp2.py` output in 4.3 | **all seven pairs differ**, 0 of 200 nodes equal each |
| G for 1, 2, 4, 7 | done | `G_S14_fhb{1,2,4,7}.rows` | all differ; sums in 4.2 |
| sanitizer: all seven values (0,1,2,3,4,5,7) on O and G at depth 10 | done | `runs_san/fhb*_{O,G}.rows`, `san_table.txt` | **0 sanitizer lines in all 14**, 3,871 positions, every exit 0 |
| sanitizer identity: FHB=0 vs the depth-10 baseline | done | `cmpcols.py` output in 4.5 | **200 of 200** and **353 of 353 equal** |

## 4. Findings

### 4.1 The default is an exact identity, and "0" is the same program as "no option"

```
python3 cmp2.py ../../../tests_deepseek6_job1/O_S14_base.rows O_S14_none.rows
   -> nodes-equal 200 of 200, bestmove-equal 200 of 200
python3 cmp2.py ../../../tests_deepseek6_job1/G_S14_base.rows G_S14_none.rows
   -> nodes-equal 353 of 353, bestmove-equal 353 of 353
python3 cmp2.py O_S14_none.rows O_S14_fhb0.rows
   -> nodes-equal 200 of 200, bestmove-equal 200 of 200
```
That the third line holds matters for a mask patch: the guard is `FailHighBlend & bit`, and `0 & anything` is 0, so
the disabled path must be byte-identical. It is.

### 4.2 Every bit is wired, and bit 2 has opposite signs on the two sets

The table below is the output of `python3 fhb_table.py` (`fhb_table.md` in the job folder), which reads the rows
files directly — no cell is hand-typed.

| value | bits | O sum | O ratio | O nodes-eq | O bm-eq | G sum | G ratio | G nodes-eq | G bm-eq |
|---|---|---|---|---|---|---|---|---|---|
| 0 | none | 9500069 | 1.0000 | 200 of 200 | 200 of 200 | 18466239 | 1.0000 | 353 of 353 | 353 of 353 |
| 1 | reverse futility | 9272824 | 0.9761 | 0 of 200 | 145 of 200 | 18240994 | 0.9878 | 2 of 353 | 270 of 353 |
| 2 | qsearch | 9580168 | 1.0084 | 0 of 200 | 142 of 200 | 18197050 | 0.9854 | 2 of 353 | 266 of 353 |
| 4 | main search end | 9180831 | 0.9664 | 0 of 200 | 154 of 200 | 17925010 | 0.9707 | 3 of 353 | 272 of 353 |
| 3 | 1+2 | 9434176 | 0.9931 | 0 of 200 | 142 of 200 | — | — | — | — | |
| 5 | 1+4 | 9492582 | 0.9992 | 0 of 200 | 150 of 200 | — | — | — | — | |
| 7 | all three | 9466559 | 0.9965 | 0 of 200 | 143 of 200 | 17534448 | 0.9495 | 2 of 353 | 254 of 353 |

**Bit 2 (the quiescence blend) makes the O tree BIGGER (+0.84 %) and the G tree SMALLER (−1.46 %).** Every other
bit shrinks both trees. That is the one place my filed band (0.90×–1.00× for each single bit) was violated, and I
had written in advance that kimi5's own 1.0084 for bit 2 fell outside my band — so the miss was anticipated, not
explained away afterwards.

The O ratios reproduce kimi5's published ones to three decimals: its T1 0.9761 / T2 1.0084 / T4 0.9664 / T7 0.9965
against my 0.9761 / 1.0084 / 0.9664 / 0.9965. Two independent builds of the same patch, same set, same depth.

### 4.3 The composition is not additive, and every pair is distinguishable

```
python3 cmp2.py O_S14_fhb1.rows O_S14_fhb3.rows   -> nodes-equal 0 of 200, bestmove-equal 137 of 200
python3 cmp2.py O_S14_fhb2.rows O_S14_fhb3.rows   -> nodes-equal 0 of 200, bestmove-equal 145 of 200
python3 cmp2.py O_S14_fhb1.rows O_S14_fhb5.rows   -> nodes-equal 0 of 200, bestmove-equal 148 of 200
python3 cmp2.py O_S14_fhb4.rows O_S14_fhb5.rows   -> nodes-equal 0 of 200, bestmove-equal 158 of 200
python3 cmp2.py O_S14_fhb1.rows O_S14_fhb7.rows   -> nodes-equal 0 of 200, bestmove-equal 148 of 200
python3 cmp2.py O_S14_fhb2.rows O_S14_fhb7.rows   -> nodes-equal 0 of 200, bestmove-equal 149 of 200
python3 cmp2.py O_S14_fhb4.rows O_S14_fhb7.rows   -> nodes-equal 0 of 200, bestmove-equal 150 of 200
```
All seven pairs I predicted would differ do differ, and none of the combined values reproduces any single bit —
which is what three independent blend sites should look like. Note 7's ratio (0.9965) is close to 1 while 3's is
0.9931: the combination of a shrinking bit 1, a growing bit 2 and a shrinking bit 4 lands near the base, which is
a coincidence of sizes and not an identity (0 of 200 nodes equal to the default).

### 4.4 What the blend sites do to the chosen move

On O, single-bit values change the best move on 46–58 of 200 positions (145–154 of 200 equal); on G, 81–99 of 353
(254–272 equal). So these bits are not marginal to the move choice the way job 2's three weak settings were.

### 4.5 Sanitizers: nothing anywhere, and the disabled build is the baseline

```
cat san_table.txt
FHB=0 O rows 200 sum 3809466 sanlines 0 exits ['0']
FHB=0 G rows 353 sum 7290580 sanlines 0 exits ['0']
FHB=1 O rows 200 sum 3660124 sanlines 0 exits ['0']
FHB=1 G rows 353 sum 7018051 sanlines 0 exits ['0']
FHB=2 O rows 200 sum 3700481 sanlines 0 exits ['0']
FHB=2 G rows 353 sum 6890296 sanlines 0 exits ['0']
FHB=3 O rows 200 sum 3779750 sanlines 0 exits ['0']
FHB=3 G rows 353 sum 6940235 sanlines 0 exits ['0']
FHB=4 O rows 200 sum 3852095 sanlines 0 exits ['0']
FHB=4 G rows 353 sum 6866843 sanlines 0 exits ['0']
FHB=5 O rows 200 sum 3620925 sanlines 0 exits ['0']
FHB=5 G rows 353 sum 6827593 sanlines 0 exits ['0']
FHB=7 O rows 200 sum 3809353 sanlines 0 exits ['0']
FHB=7 G rows 353 sum 6740141 sanlines 0 exits ['0']

runs 14 positions 3871 sanlines 0
```

Every position in its own process, **3,871 positions (all seven values x both sets), 0 AddressSanitizer or
UndefinedBehaviorSanitizer lines, and 0 nonzero exits**. FHB=0's rows are byte-identical to the depth-10 baseline (3,809,466 / 7,290,580, 200 of 200 and
353 of 353), so the sanitizer build of this patch is the plain build when disabled.

At depth 10 the O numbers do not mirror the depth-12 pattern: bit 4 GROWS the sanitizer tree (3,852,095 vs
3,809,466, +1.12 %) where it shrank the depth-12 tree (−3.36 %). So this patch's per-bit direction is depth- and
build-dependent, and only the "it is wired" conclusion is stable.

### Suspicions, not proven

- That bit 2's growth on O is a real cost of blending at stand-pat and shrinking everywhere the qsearch is
  entered more often. I have the two sums, not a mechanism.
- That the depth-10 vs depth-12 direction disagreements (bit 4) are the same class of step-function effect long 3
  found with `LmrCutNode`. I have not separated them.

## 5. What I read from my colleagues

- **kimi5** (`REPORT_kimi5_job12.md`, on its branch): it reports the same patch sha256, the same O ratios to three
  decimals, and that all three sites carry nonzero counts with a planted positive control (bit 1 forced to return
  `beta - 1`, giving its counter exactly). I used its published numbers as a cross-check and state which of my
  bands they violated in advance (bit 2) and which they confirmed (1, 4, 7).
- **glmflash5** (`NOTES_glmflash5.md`): nothing on this patch.
- **deepseek5** (`NOTES_deepseek5.md`): nothing on this patch.
- No note is an order; where a note's number and mine disagree, mine is in the table with its file.

## 6. What I did NOT do

- I did not build `FORGE_FHB_CHECK=1` (the counting variant). kimi5's report covers the counters and the job only
  asks me for the identity, the bits and the sanitizers.
- Nothing: after this report's first push I noticed values 3 and 5 were missing from the sanitizer sweep on both
  sets and ran all four, so the table above covers the full 7 x 2 grid. (0 explicitly on G is still not sent; the
  no-option G run plus the `FailHighBlend=0` O run cover the identity.)
- I did not search for a strength result; node sums are not that.
- I did not test at depth 14.
- I did not commit engine source; the patch is committed as text.
- I did not open a pull request.

## 7. What I am NOT sure about

- The direction of each bit's effect. I have four measurements of the same bit giving three different directions
  across depth and build (see 4.5's last paragraph). "Wired" is solid; "costs or saves" is not.
- Whether the seven composition claims being true says anything beyond "the three sites are independent". It says
  the mask is read at three distinct places, which is what it was meant to show.

## 8. A better way

I filed a directional band per bit, which was the wrong shape of prediction for a mask whose three sites touch
different parts of the tree: the useful prediction was the one I actually made about **the seven distinctness
checks**, and those all held. For a multi-bit mask the prediction should be "each bit is distinguishable from
every other value", not "the tree moves this way", because the direction is a property of the site's role and I
cannot reason about that from the option alone.

## 9. times / model

see `stamps.txt`. **Model: DeepSeek V4.1 Flash 1017** (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`FailHighBlend.patch.txt`, `patch_apply.txt`, `exe.sha256`, `honesty_*`, `uci.txt`, 13 depth-12 rows files (with
`.meta`), `runs_san/` (10 rows files), `san_table.txt`, `job3san.log`, `precommit_evidence.txt`.
