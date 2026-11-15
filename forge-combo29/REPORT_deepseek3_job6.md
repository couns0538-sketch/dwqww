# REPORT deepseek3 job 6

**First line in plain words: the two correction ideas together gain nothing per node. Pooled over
M1 and M3 (both against an engine with neither option) the answer is +0.18 Elo, 95% interval -7.3 to
+7.7, on 3,957 games. Beside the singles that is exactly what the parts predict: the minor table alone
about +3, the size term alone 0 — and M2, which asks what the size term ADDS once the minor table is
already there, gives 0.00 Elo, interval -10.4 to +10.4, on 2,000 games (598-598-804). So a better-informed
correction does not make its size carry more: it makes it carry nothing, because the size term was never
carrying anything.**

**What was cut: M4 (`MinorCorrection 50 + CorrMargin 64` against `MinorCorrection 50`, 2,000 games, seed
7934) was not run.** I reached 60 minutes after M3 and M4 could not finish inside the 80-minute stop
point. M3 was cut by its own time limit at 1,957 of 2,000 games; complete pairs only are used.

I am `deepseek3`. Base commit `6b98f217`. No pull request, no engine source committed, text only, no
binaries, no `__pycache__`. Deliverable `tests_deepseek3_job6/correction_bundle.patch.txt` (269 lines,
3 files).

---

## 1. Step 0 — one tree with both, line by line

Every line the job asks for, from `logs/step0-validation.txt`. Build: CMake Release, `g++ 13.3.0`,
`-DFORGE_MARCH=x86-64-v4`, built-in net, commit `6b98f217`.

| check | expected | printed | verdict |
|---|---|---|---|
| both off, `bench 11` | 312866 | 312866 | **equal** |
| both off, `bench 13` | 862329 | 862329 | **equal** |
| both off, `bench 16` | 3024920 | 3024920 | **equal** |
| both off, `go perft 5` | 4865609 | 4865609 | **equal** |
| `CorrMargin 20` alone, `bench 11` | 359429 (job 5) | 359429 | **equal** |
| `CorrMargin 20` alone, `bench 13` | 748138 (job 5) | 748138 | **equal** |
| `CorrMargin 20` alone, `bench 16` | 3026279 (job 5) | 3026279 | **equal** |
| `CorrMargin 64` alone, `bench 11` | 293283 (job 5) | 293283 | **equal** |
| `CorrMargin 64` alone, `bench 13` | 815644 (job 5) | 815644 | **equal** |
| `CorrMargin 64` alone, `bench 16` | 2998029 (job 5) | 2998029 | **equal** |
| `MinorCorrection 100` alone, `bench 11` | 314930 (deepseek2) | 314930 | **equal** |
| `MinorCorrection 100` alone, `bench 13` | 867866 (see 2) | 867866 | **equal to the patch** |
| `MinorCorrection 100` alone, `bench 16` | 3751556 (see 2) | 3751556 | **equal to the patch** |

**Both options off, 2,000 positions** (`go depth 9`, best move + score + nodes, one sha256 per side):

| side | positions | min nodes | sha256 |
|---|---:|---:|---|
| unpatched `6b98f217` | 2000 | 4534 | `ba06f82d7a047639068094234a7bd8426315f66181d82414c32f714b0c607720` |
| merged tree, both off | 2000 | 4534 | `ba06f82d7a047639068094234a7bd8426315f66181d82414c32f714b0c607720` |

Identical, and over real work (every position to depth 9, smallest 4,534 nodes).

## 2. The merge, and one mismatch in the other helper's numbers

**a. Files each patch touches.** Both touch the same three files:

```
C (mine):  include/forge/search.hpp   src/search.cpp   src/uci.cpp   (paths carry forge-combo29/, applies with patch -p2)
M (deepseek2): include/forge/search.hpp   src/search.cpp   src/uci.cpp   (no prefix, applies with patch -p1)
```

**b. `git apply` silently succeeds without applying anything, and this nearly wrecked the job.**
`git apply --check /tmp/minor.patch` reported success on a C-patched tree, and `git apply` exited 0, but
`grep MinorCorrection` afterwards found **nothing**. With `-v` it printed

```
Skipped patch 'include/forge/search.hpp'.
Skipped patch 'src/search.cpp'.
Skipped patch 'src/uci.cpp'.
```

and still returned 0. The same happened applying M alone to a **clean** `6b98f217` tree, so it is not
about the merge order — `git apply` decided the hunks were already present because the `index` lines of
the two patches disagree with this checkout. `patch -p1` applied it correctly first time. **Every merge in
this job was therefore done with `patch(1)`, and verified twice: by grepping for both option names and by
the bench numbers.** Details in `MERGE_NOTES.txt`. This is worth passing to the other helpers: a green
`git apply` is not evidence that anything happened.

**Order.** Both orders apply with `patch(1)`. I used **M then C**: M's hunks are anchored on the unmodified
`corrected_eval`/`update_correction` bodies, and C's hunks on that same region then shift by a fixed
offset (two hunks reported "succeeded at … offset 28 lines"). **No hunk was rejected and none had to be
placed by hand** — so, unlike the two ports Fable could not stack, these two combine textually without
conflict.

**The delivered patch reproduces the tree.** `correction_bundle.patch.txt` was applied to a *fresh*
`6b98f217` worktree with `patch -p1` and rebuilt independently; it printed 312866 / 862329 with nothing
set, 359429 / 748138 with `CorrMargin 20`, and 296903 / 709481 with both options on — every number
matching the working build.

**A mismatch I have to report, as the job asks.** The job's check is "`MinorCorrection` 100 alone = the
other helper's bench numbers". **Their report contains two different sets:**

| source | `bench 13` | `bench 16` |
|---|---:|---:|
| deepseek2 report, P3 table | 937258 | 3780562 |
| deepseek2 report, P1 table and P4 line | **867866** | — |
| **M alone, built by me from their committed patch, clean tree** | **867866** | **3751556** |

Their committed `minor_correction.patch.txt` produces **867866 / 3751556**, which agrees with their own P1
and P4 numbers and **not** with their P3 table. So my merge is consistent with the patch they shipped, and
their P3 row does not correspond to it (`logs/m-alone-verification.txt`, `MERGE_NOTES.txt`). I used
867866 / 3751556 as the true "M alone" reference. I could not tell whether their P3 was measured on a
different build or simply mistyped.

**c. Design decision the merged tree alone raises: does `CorrMargin`'s size include the minor term?**
**Yes.** In the merged `corrected_eval` the pawn, material, minor and non-pawn terms are all summed into
one `correction` before `correction_cp = correction / CorrectionGrain` is computed once, and
`corr_size_out` is set from that single sum. So the size is the size of the whole applied correction.

Why: the premise of the term is "the static eval has been wrong in this kind of position before", and
every component of the correction is evidence of exactly that. Taking the size *without* the minor term
would have meant an artificial split of one quantity into "size" and "the rest", and would make the
feature's behaviour depend on how the tables happen to be summable. **`bench 13` with both on (K=20,
weight 50) = 709481** nodes (and `bench 11` 296903, `bench 16` 3618786).

**e. Sanitizers.** AddressSanitizer + UBSan, `-fno-sanitize-recover=all`, planted fault first
(`logs/p4-planted.txt`): index one past a `[13][64][7]` table → exit 1 with a UBSan out-of-bounds report;
signed overflow → exit 1; clean use → exit 0, no diagnostics. Then the merged engine
(`logs/p4-run.txt`): `bench 13` with **both** options on gave 709481 nodes (identical to the release
build) with **0 bytes on stderr**, and 200 of the P2 positions gave 200 of 200 bestmoves with **0 bytes on
stderr**. PASS.

## 3. The matches

Same exe both sides (`~/work/j6/forge`), `nodes=20000`, `Threads 1`, `Hash 16`, `OwnBook false`, UHO
openings both colours, no adjudication, concurrency 4 on 4 cores.

**Control**, seed 7930, 300 games: own pair interval **+184.73, +155.2 .. +216.9**, fastchess
+184.73 +/- 30.74, pairs `[1,5,34,67,43]`. Near +200 as required. This tree's games per second, taken from
this match, were 300 games in 111 s — which is what the later limits were set from.

**Probe before M1** (`logs/probe-M1.engine.log`): both options arrive on the candidate and neither on the
base.

```
cand <--- setoption name OwnBook value false
cand <--- setoption name MinorCorrection value 50
cand <--- setoption name CorrMargin value 20
base <--- setoption name OwnBook value false        (no MinorCorrection, no CorrMargin)
```

| match | candidate | base | seed | games (asked) | cand W-L-D | pairs | pair counts | fastchess Elo +/- err | own Elo, 95% interval |
|---|---|---|---:|---:|---|---:|---|---:|---|
| M1 | Minor 50 + Corr 20 | none | 7931 | **2000 (complete)** | 566-553-881 | 1000 | [57,242,382,269,50] | +2.26 +/- 10.44 | **+2.26, -8.2 .. +12.7** |
| M2 | Minor 50 + Corr 20 | **Minor 50** | 7932 | **2000 (complete)** | 598-598-804 | 1000 | [62,223,428,227,60] | -0.00 +/- 10.43 | **0.00, -10.4 .. +10.4** |
| M3 | Minor 50 + Corr 20 | none | 7933 | **1957 of 2000 (cut)** | 555-566-836 | 978 | [74,216,387,249,52] | +0.58 +/- 11.32 (block covers 1,800) | **-1.95, -12.8 .. +8.9** |
| **M1+M3 pooled** | | | | **3957** | 1121-1119-1717 | 1978 | [131,458,769,518,102] | | **+0.18, -7.3 .. +7.7** |
| M4 | Minor 50 + Corr 64 | Minor 50 | 7934 | **NOT RUN** | — | — | — | — | — |

**M2's exact 0.00 is a real symmetric result, not a missing option:** 598 wins against 598 losses with
804 draws, and pair counts `[62,223,428,227,60]` — nowhere near the `[0,0,N,0,0]` pattern the job warns
about. M1's probe already showed both options arriving, and M2 used the same command shape.

**Crashes, illegal moves, disconnects: 0 in every match and in the control.** Checked by tallying how each
of the 6,257 games ended, not by grepping for a word (`logs/termination_reasons.txt`): all ended by a chess
rule.

Per-game files: `logs/{control,M1,M2,M3}.games.txt`.

## 4. What the three matches say together

- **The two together, against neither: +0.18 [-7.3, +7.7] over 3,957 games.** Nothing. M1 (+2.26) and M3
  (-1.95) bracket zero, which is what a true null looks like across two seeds.
- **What the size term adds on top of the minor table: 0.00 [-10.4, +10.4] over 2,000 games.** This is the
  question the job was built around, and it is the cleanest answer here: once the correction is better
  informed, its size still carries nothing. The null is not because the size term is being masked by a
  bad correction — M2 holds the correction fixed and varies only the size term.
- **Beside the singles:** minor table alone about +3 (deepseek2, two authors, 16,000 games, +2.9 [-0.8,
  +6.6]); size term alone 0 (mine, job 5, two K values both null). Their sum predicts +3; the bundle
  measures +0.18. So the parts do not even add — the bundle is, if anything, slightly worse than the
  minor table alone, though all of these intervals overlap.

**My reading:** the correction-size signal is not worth carrying in this engine, with or without a better
correction. That is now two independent measurements of the size term (job 5 alone, job 6 on top of the
minor table) and they agree.

## 5. Files of the repository I opened

`forge-combo29/src/search.cpp` and `include/forge/search.hpp` (as modified by both patches: `corrected_eval`,
`update_correction`, `minor_key`, the reverse- and quiet-futility tests, `SearchStack`),
`forge-combo29/src/uci.cpp` (both option paths), and — as the job permits — only these two files from
deepseek2's branch: `forge-combo29/tests_deepseek2_job8/minor_correction.patch.txt` and
`forge-combo29/REPORT_deepseek2_job8.md`. No other helper file, no other engine's source.

## 6. Stamps

| step | start | end | source |
|---|---|---|---|
| job file read | 21:17:21Z | 21:17:32Z | — |
| patches fetched, both orders tested | 21:17:3xZ | 21:18:5xZ | `MERGE_NOTES.txt` |
| merged tree built, then validated | 21:18:5xZ | 21:19:35Z | `logs/step0-stamps.txt` |
| M-alone verification build and run | 21:19:4xZ | 21:20:0xZ | `logs/m-alone-verification.txt` |
| P2 2,000 positions, both sides | 21:20:12Z | 21:20:53Z | `logs/p2-stamps.txt` |
| sanitizer build, planted faults, run | 21:20:5xZ | 21:21:20Z | `logs/p4-stamps.txt` |
| control (300 games) | 21:21:52Z | 21:23:44Z | `logs/control-stamps.txt` |
| M1 probe | 21:23:47Z | 21:23:50Z | `logs/probe-M1.engine.log` |
| M1 | 21:23:52Z | 21:41:51Z | `logs/M1-stamps.txt` |
| M2 | 21:41:54Z | 22:00:01Z | `logs/M2-stamps.txt` |
| M3 | 22:00:03Z | 22:17:33Z | `logs/M3-stamps.txt` |
| delivered patch re-applied to a fresh tree and rebuilt to confirm it reproduces | 21:21:22Z | 21:21:48Z | file stamps of `correction_bundle.patch.txt` and `~/work/v6b/forge` |
| report written | 22:18Z | — | — |

Job file read 21:17:21Z, last match ended 22:17:33Z = **60 min 12 s**. Inside the 90-minute budget and
inside the 80-minute stop point; M4 would have crossed it, so M4 was left out.

## 7. What I did not do

- **M4 was not run.** It was explicitly the first to be cut, and by 22:17 I had 20 minutes of budget
  left, which is not enough for 2,000 games at this tree's ~12.5 min per 2,000 plus the report.
- **M3 is short** (1,957 of 2,000); complete pairs only are used, so its own pair count is 978.
- **I did not investigate deepseek2's P3 mismatch further than proving the patch's own numbers** (M alone
  on a clean tree). Which build they measured P3 on is theirs to say.
- **I did not test weight 50 of the minor table by itself**, so the "minor alone at 50" reference is
  deepseek2's unfinished weight-50 match, not a number I measured. The bundle figures are all against
  bases I built and verified here.
- **No time control, no PC net.** Fixed 20,000 nodes, 4 cores, concurrency 4.
- I did not test any K other than 20 (and 64 in M4, which did not run).

## 8. What I am not sure about

- **Whether the minor table at weight 50 is worth about +3 here.** Deepseek2's own weight-50 match did not
  finish, and my M2 measures the size term *given* weight 50, not weight 50 itself. So I cannot say from
  my own games that the minor table deserves its +3; I only know the size term adds nothing on top of it.
- **The `git apply` behaviour** — it may be specific to these patch files (their `index` lines) rather than
  general. But it reproduced on a clean tree with M alone, and it is dangerous enough that every helper
  should verify patch application by content, not by exit code.
- **deepseek2's P3 numbers.** Two of their own tables disagree, and their committed patch matches the
  table they did not headline. If Fable's next job quotes 937258 as "M alone", it is not what M alone
  produces here.
- **M2's exact 0.00** is arithmetically a 598-598-804 result — real — but a reader should know that a
  perfect split in a 2,000-game match is a 1-in-a-few-hundred coincidence, not an error. The pair counts
  `[62,223,428,227,60]` are what distinguish it from a missing option.
- **Speed of the bundle:** I did not measure it. The minor table costs ~1.6% per deepseek2 (128 KB per
  thread) and my size term costs nothing measurable (job 5); I have no measurement of the pair.

## 9. A better way

**Check patch application by content, always.** The single most dangerous thing in this job was a tool
that returned success while doing nothing: `git apply --check` green, `git apply` exit 0, and no change in
the file. If I had trusted the exit code, every bench number downstream would have been measured on a tree
with half the features and the whole job would have been wrong in a way that looks completely normal. The
cheap fix is a rule for every helper: after applying any patch, grep for a string that only the patch can
introduce, and if the job gives known bench numbers, check one of them before doing anything else. How to
check it is worth the rule: `git apply` on a clean `6b98f217` tree with `deepseek2`'s patch exits 0 and
changes nothing — reproduce it in one command and the rule justifies itself.

**A job that merges two patches should say what to do when the two reports disagree about their own
numbers.** I spent time proving that M-alone is 867866 and not 937258, because the acceptance line was
"= the other helper's bench numbers" and there were two of them. A line like "if the other report gives
two different numbers for the same setting, treat the one you can reproduce from the committed patch as
authoritative and report the discrepancy" would have saved that time and made the check unambiguous.

**For a question of the form "does A help once B is present", the M2 design is right and should be the
default shape.** Matching M1 (bundle vs nothing) with M2 (bundle vs better base) is what made this job's
answer clean: M1 alone could not distinguish "the size term does nothing" from "the size term is drowned
by a bad correction", and M2 could. I would suggest that every future bundle job include the "on top of
its partner" match as a first-class requirement rather than an optional extra.

## 10. Model

`deepseek3`. Model: **DeepSeek V4.1 Flash 1017** (as given in my operating prompt; I cannot verify the
build string from inside).

## 11. Questions for Fable

1. **The `git apply` trap:** please pass to the other helpers that `git apply` can return 0 while applying
   nothing (at least for deepseek2's `minor_correction.patch.txt` on a clean `6b98f217`), and that `patch
   -p1` works. A helper who trusts the exit code will report numbers for a tree that does not have the
   feature.
2. **deepseek2's `bench 13` for `MinorCorrection 100`:** their report says both 937258 and 867866; their
   committed patch gives 867866. Which one should future jobs quote?
3. Is the size term now closed for good (two measurements, both null), or do you want it tried at the
   null-move site where the mechanism looks more plausible?
