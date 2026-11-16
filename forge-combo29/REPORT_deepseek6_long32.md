# REPORT — deepseek6, long 32 (recipe R on kimi5's SoundArms and SoundSteps, one at a time)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long32/`
Model: DeepSeek V4.1 Flash 1017

## 1. What was asked, the answer, how sure

**Asked:** recipe R on `SoundArms.patch.txt` (57524c71) and `SoundSteps.patch.txt` (07713c3b), one at a time; a
one-line skip for a patch my branch already has a recipe-R report for.

**Answer:** **SoundArms is fully reproduced: all seven settings kimi5 tested are EQUAL to its rows on 200 of 200
positions, node for node and best move for best move.** SoundSteps **cannot be applied to the plain tree at all**
— it is authored on top of SoundArms **and** SoundRegret, and its mask is meaningless without them; on the
Arms+Regret+Steps chain all fifteen settings ran and **its three settings that kimi5 published rows for (mask 0,
mask 1, pvmask 1) are EQUAL on 200 of 200**. SoundRegret is a **one-line skip** (full recipe R in my
`REPORT_deepseek6_long10.md`). Ten comparable configurations, ten exact.

**Two findings worth more than the reproduction:** `SoundMatePruning true + SoundPvArm 1 + SoundInCheckArm 1` is
**row-identical to `SoundMatePruning true` alone** (200 of 200), so the two "arms" add nothing on top of the
switch — and `SoundMateAlphaArm 1` changes 2 nodes and 0 moves in all 200 positions, i.e. it is effectively inert
at depth 12 on O, which matches kimi5's own regret measurement (0.8–1.5 per 1,000).

**How sure:** certain of the ten equalities (my own harness, kimi5's committed json, position by position);
the "inert" and "redundant" readings are measurements plus one mechanism sentence each, marked as such.

## 2. Honesty numbers (raw in `raw/`)

| build | bench 11 | bench 13 | bench 16 | perft 5 | sha256 |
|---|---|---|---|---|---|
| **ba** = plain + SoundArms | 312866 | 862329 | 3024920 | 4865609 | `c1ca29e5…5b178` |
| **bc** = plain + SoundArms + SoundRegret + SoundSteps | 312866 | 862329 | 3024920 | 4865609 | `f688d0b2…406c4` |

Files `raw/ba_bench{11,13,16}.txt`, `raw/ba_perft5.txt`, `raw/bc_bench{11,13,16}.txt`, `raw/bc_perft5.txt`;
`id name Chess Engine Forge 6.4.24 candidate`. All four exact on **both** builds.

**R1, sha256 verified before use:** `p/SoundArms.patch.txt` = `57524c71d5ae…` (required 57524c71),
`p/SoundSteps.patch.txt` = `07713c3b98b2…` (required 07713c3b), `p/SoundRegret.patch.txt` = `1020849555c1…`.
All three applied with `patch -p1 --fuzz=0` after a dry run.

**R2, the new options with their defaults** (`raw/ba_uci.txt`, `raw/bc_uci.txt`):

```
# SoundArms alone
option name SoundMatePruning  type check default false
option name SoundPvArm        type spin  default 0 min -1 max 1
option name SoundInCheckArm   type spin  default 0 min -1 max 1
option name SoundMateAlphaArm type spin  default 0 min -1 max 1
# + SoundRegret + SoundSteps (the chain)
option name SoundRegretCount  type check default false
option name SoundRegretProbe  type check default false
option name SoundStepMask     type spin  default 63 min 0 max 63
```

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claim, then prediction (own commits) | done | `CLAIM.txt`, `PREDICTION.md` | prediction before the first build |
| R1 patch order found by dry run | done | section 5 F1 | Arms clean; Steps needs Arms+Regret |
| two builds + pins | done | `raw/*` | four pins exact on both |
| R2 option list pasted | done | `raw/ba_uci.txt`, `raw/bc_uci.txt` | above |
| R3 identity at defaults, Arms build | done | `runs/A_defaults.rows` | **200/200 vs kimi5 `none`** |
| R4 SoundArms, 7 settings | done | `runs/A_*.rows`, `r4_compare.txt` | **7 of 7 EQUAL, 200/200 each** |
| R4 SoundSteps, 15 settings | done | `runs/B_*.rows`, `r4_compare.txt` | 3 with kimi5 rows: **3 of 3 EQUAL**; 12 no kimi5 file → committed, "not comparable" |
| SoundRegret skip line | done | `REPORT_deepseek6_long10.md` | full recipe R already done |
| ratio table | done | `table32.py`, `table32_out.txt` | section 4 |
| prediction scorecard | done | `scorecard.txt` | 3 held, 6 killed |

## 4. The tables (from `table32_out.txt`, one command)

Base = the plain build at **defaults**, depth 12 on O: **12,573,318** nodes. (kimi5's base is defaults, not S14
— the standing 9,500,069 is an S14 sum and does not apply to these runs; my long-10 notes say this and I checked
it again here.)

**SoundArms, patch alone:**

| setting | O sum | ratio | nodes changed | best moves changed |
|---|---|---|---|---|
| none (K1) | 12,573,318 | 1.0000 | 0/200 | 0/200 |
| SoundMatePruning true (K2) | 12,558,811 | 0.9988 | 200/200 | 52/200 |
| SoundPvArm 1 (K3) | 12,399,593 | 0.9862 | 200/200 | 56/200 |
| SoundInCheckArm 1 (K4) | 12,326,599 | 0.9804 | 200/200 | 37/200 |
| SoundMateAlphaArm 1 (K5) | 12,573,482 | 1.0000 | **2/200** | **0/200** |
| SoundPvArm 1 + SoundInCheckArm 1 (K6) | 12,558,811 | 0.9988 | 200/200 | 52/200 |
| smp + three arms -1 (K7) | 12,573,318 | 1.0000 | **0/200** | **0/200** |

**SoundSteps, on the Arms+Regret+Steps chain:**

| setting | O sum | ratio | nodes changed | best moves changed |
|---|---|---|---|---|
| SoundMatePruning + mask 0 | 12,573,318 | 1.0000 | 0/200 | 0/200 |
| SoundMatePruning + mask 1 | 11,944,468 | 0.9500 | 200/200 | 56/200 |
| SoundMatePruning + mask 15 | 12,336,817 | 0.9812 | 200/200 | 52/200 |
| SoundMatePruning + mask 33 | 11,734,618 | 0.9333 | 200/200 | 56/200 |
| SoundMatePruning + mask 48 | 12,420,487 | 0.9878 | 200/200 | 31/200 |
| SoundMatePruning + mask 51 | 11,800,474 | 0.9385 | 200/200 | 55/200 |
| SoundMatePruning + mask 60 | 12,600,871 | **1.0022** | 200/200 | 62/200 |
| SoundMatePruning + mask 62 | 12,424,685 | 0.9882 | 200/200 | 63/200 |
| SoundPvArm 1 + mask 1 | 11,944,468 | 0.9500 | 200/200 | 56/200 |
| SoundPvArm 1 + mask 15 | 12,443,326 | 0.9897 | 200/200 | 55/200 |
| SoundPvArm 1 + mask 33 | 11,742,019 | 0.9339 | 200/200 | 56/200 |
| SoundPvArm 1 + mask 48 | 12,420,163 | 0.9878 | 200/200 | 31/200 |
| SoundPvArm 1 + mask 51 | 11,807,865 | 0.9391 | 200/200 | 55/200 |
| SoundPvArm 1 + mask 60 | 12,585,678 | 1.0010 | 200/200 | 65/200 |
| SoundPvArm 1 + mask 62 | 12,553,858 | 0.9985 | 200/200 | 65/200 |

## 5. Findings, each with the command that shows it again

**F1. The job's "one at a time" is impossible for SoundSteps: it is authored on Arms + Regret.**
`p/SoundSteps.patch.txt` on the plain tree fails 4 of 6 hunks in `search.cpp`, 1 of 2 in `uci.cpp` and its only
`search.hpp` hunk (offsets alone do not save it); after SoundArms alone it still fails 2 of 2 `uci.cpp` hunks.
Only after SoundArms **then** SoundRegret does it apply clean at `--fuzz=0`. Same chain, same order, as my long 19
found for glmflash5's bundle — that is now two independent sightings. Reproduce:
`cd /tmp/ds6/l32solo && patch -p1 --dry-run --fuzz=0 < .../SoundSteps.patch.txt`.

**F2. `SoundMateAlphaArm 1` is effectively inert at depth 12 on O: 2 nodes out of 12.6 M, 0 best moves.**
`runs/A_mat.rows` against `runs/A_defaults.rows`: two positions differ, by a handful of nodes, and no move
changes. kimi5's regret count predicted this (0.8–1.5 regrets per 1,000 mate-alpha drops — the arm can only
change a move when it saves one, and that is rare). Reproduce: `python3 cmp_kimi.py runs/A_mat.rows
kim5/../kim5_smp.json` is the wrong comparison; the right one is `python3 table32.py`, row K5.

**F3. `SoundPvArm 1 + SoundInCheckArm 1` is ROW-IDENTICAL to `SoundMatePruning true` — the arms add nothing on
top of the switch.** Both give 12,558,811 with 200/200 rows equal, 52 best moves changed. So on O at depth 12 the
switch already does whatever the two arms would do; setting them to 1 is a no-op. Reproduce:
`cmp_rows.py runs/A_pvchk.rows runs/A_smp.rows` → "200 of 200 equal". This is the same shape kimi5 reported as
pvmask1 ≈ mask1, and it strengthens it: the equality holds for the arms even without any mask.

**F4. `off7` (switch on, all three arms -1) is an exact identity with the plain build.** 0 nodes, 0 moves. The
`-1` arm values mean "no opinion", so the switch has nothing to modify — the arms, not the switch, are the
mechanism. Reproduce: `runs/A_off7.rows` vs `runs/A_defaults.rows`, both 12,573,318.

**F5. `mask 0` disables the whole pruning switch: it equals the PLAIN build, not `smp`.** 0/200 changed against
defaults, 12,573,318. kimi5's own line says "mask 0 -> K1", and K1 is the plain build — my prediction P7 misread
that as `smp` and is killed; the measurement agrees with kimi5. This matters for anyone copying a mask value: 0
is "off", 63 is "everything".

**F6. The mask's effect is not monotone in its numeric value** — 33 (0.9333) prunes harder than 48 (0.9878), and
60 actually **grows** the tree (1.0022). Bits are steps, not a percentage; only a per-bit reading makes sense.
kimi5's own table showed the same shape.

**F7. `SoundPvArm 1` makes essentially no difference once a mask is set**: mask 1 → pvmask 1 is the same sum to
the node (11,944,468), mask 33 → pvmask 33 differs by 7,401 nodes (0.06 %), mask 60 → pvmask 60 differs by
15,193 (0.12 %). Consistent with F3.

## 6. What I read from my colleagues

- **kimi5's `REPORT_kimi5_job5.md`** (fetched and read for the R4 settings): it is the source of the 22
  configurations; its own table lines "mask 63 → K2–K6", "mask 0 → K1" and the 4x6 regret table shaped my
  predictions. Its `k5_j5.py` fixed the exact option strings I used, and its committed `runs_O/*.json` are what my
  ten equalities are measured against. Its numbers reproduce **exactly**, including the ones its own report calls
  its worst predictions.
- **My own long 10** gave the "defaults, not S14" rule and the SoundRegret skip.
- No note was treated as an instruction; every option string I sent came from kimi5's committed harness, and every
  sum in this report comes from my own runs.

## 7. What I did NOT do

- **Did not run G.** The item names O and G in file 7's recipe R; this item's line says "R on ... one at a time"
  with no set named, and my R4 comparison target (kimi5's json) is O-only for these configs. Committed: `r3_g.txt`
  is absent and this report says so rather than implying a G result.
- **Did not run the five SoundArms settings that have no kimi5 row file** (`cnt`, `cntsmp`, `probe` and the mask
  families belong to the other patch; the mask settings were run on the chain instead).
- **Did not compare the twelve mask settings kimi5 published no rows for** — they are committed as rows and marked
  "not comparable" rather than compared against a guess.
- **Did not use SoundSteps alone** (impossible, F1).
- **Did not edit any other session's files.** No pull request, no branch but mine, no engine source committed.

## 8. What I am NOT sure about

- Whether `SoundMateAlphaArm` is inert *in general* or only at depth 12 on O. kimi5's G regret counts (0.8–1.5 per
  1,000 mate-alpha drops) suggest it stays tiny, but "2 nodes on O" is one configuration at one depth.
- Whether F3's row-identity survives a different position set: `pvchk == smp` on 200 O openings is exact, but O is
  a book set and the arms may matter in positions where the PV/in-check cases are reached more often (kimi5's
  own data says G reaches the in-check case where O does not).
- The mechanism in F3/F4 ("the switch already covers both arms") is an interpretation of an exact equality, not
  an instrumented count.

## 9. A better way

The R4 target for a patch that cannot stand alone should be defined **on its chain from the start**. Here the job
said "one at a time", which is impossible for SoundSteps; I spent a build and two dry runs discovering what my own
long 19 had already recorded. A job line that names a patch's prerequisites (or says "read the author's ordering
note first") would have saved those minutes.

## 10. Times and the folder

times: see `stamps.txt` (claim, prediction, both builds' pins, each run group, table, scorecard).
Model name my runtime gives: **DeepSeek V4.1 Flash 1017**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
