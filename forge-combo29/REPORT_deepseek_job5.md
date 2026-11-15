# REPORT - deepseek job 5

Branch `for-fable-and-opus/deepseek-work`. No engine source changed. New files only in
`forge-combo29/tests_deepseek_job5/` plus this report. For part B I used a private
traced copy; its diff is `tests_deepseek_job5/trace_patch.txt`.

## 1. Table

| part | done / partly / not done | evidence files | result in one line |
|---|---|---|---|
| A1 evaluator + 3 test nets | done | `forge_v4.py`, `logs/A1-net-manifest.txt` | three nets, each **6,446,344 bytes**, FNV-1a `645866a0beb90c06` / `f355c862d7957dcf` / `e3c276d6fc2a5009` |
| A2 5,040 values per net | done | `logs/v4_values_seed{1,2,3}.txt` | 5,040 integers per file, one per line, in the order of job 2's `positions-5040.txt` |
| A3 intermediates for 20 positions, seed 1 | done | `logs/v4_detail_s1.jsonl` | 20 JSON lines with ob, direct, the 16 y1, the 32 y2, dense, cp |
| A4 what the spec left open | done | `logs/A4-ambiguities.txt` | 9 items, listed in section 3 |
| B1 smallest earlier search that changes the score | done | `logs/B1-witnesses.json`, `logs/B-summary.txt`, `b1_minimal.py` | **one** earlier search suffices; 35 of 40 candidates change the score, mostly for the worse |
| B2 which entries the second search reads | done | `logs/B-summary.txt`, `trace_patch.txt` | 17,575 hits, 6,924 distinct keys, **0 written by the first search** |
| B3 collisions vs transpositions | done, conclusion negative | `logs/B-summary.txt` | **not** a transposition and **not** a key collision between the roots; the mechanism is not established |
| job 4 correction: one visit or two | done | `logs/A-correction-two-visits.txt` | **two visits**; `HindsightDepth` is not the cause (it defaults to false) |

## 2. Findings

**F1. Job 4's part A sentence was wrong, and the correction changes the mechanism.**
Fable was right that `HindsightDepth` cannot be responsible: it is a UCI option whose
default is false (`src/search.cpp:100`, `src/uci.cpp:224`). Re-reading my trace **in
the order it was printed**, the `RET qsearch_depth0 ... ply 1 depth 0` line comes
**before** the `NODE ply 1 depth 1` line. So they are **two visits**, not one: the
depth-0 visit is the **depth-1 iteration**, where the root (depth 1) hands its only
child depth 0 and the child goes straight to quiescence; the `NODE depth 1` line is the
depth-2 iteration visiting the same position properly. The mating move `Kf7` is never
generated in the depth-1 iteration because that node is only quiesced. What makes this
position special is that even at depths 12 and 16 the deeper iterations still prefer
another branch, so `Kf7` is not found until depth 18. That is the corrected statement.

**F2. The stale-table effect is not caused by reading the first search's entries.**
This is the main result of part B and it is a negative one. I instrumented every TT
probe hit in a private build (`trace_patch.txt` prints key, tag, depth, bound, score).
For the standard pair (witness `8/8/8/1K6/8/8/1k6/2R1R3 w` at depth 12, then the target
at depth 12):

- 17,575 probe hits during the second search;
- **6,924 distinct keys**, and **0 of them were written during the first search**;
- the entries hit carry `depth=0`, bounds 1/2 and scores around ±1000-1300 cp, which
  are the quiescence stores (`src/search.cpp:1541`) made by the second search itself.

So nothing from the first search is read. What changes is only that the second search
starts with a non-empty table rather than an empty one, and its own depth-0 entries
then get reused across its own nodes. **Why a self-written quiescence entry flips a
mate distance I did not establish.** I am reporting a measurement, not a mechanism.

**F3. It is not a hash collision and not hash pressure.** 1, 4, 16, 64 and 256 MB all
behave identically (fresh `mate 4`, after the witness `mate 2`). The two roots share
**no** position: exhaustive trees to 6 plies have 0 common positions (70,138 vs
64,071 nodes), and their 32-bit tags differ (`b6f0e35d` vs `feca1fb4`).

**F4. The effect is common and non-monotonic in the earlier search's depth.** 35 of 40
candidate earlier positions change the target's score: `mate 2` ×4, `mate 3` ×20,
`mate 5` ×9, `mate 7` ×1, `cp 1637` ×1, unchanged ×5. With one fixed witness, the
earlier search at depth 1 → unchanged, depth 2 → `mate 3`, depths 4/6/8 → unchanged,
depth 12 → `mate 2`. The truth is `mate 2`, so most variants are worse than the fresh
answer and some are better.

**F5. The score change also changes the bestmove, and the FRESH search already plays a
non-mating move.** For the `cp 1637` witness: fresh search → bestmove `c8c5`, score
`mate 4`; after one unrelated earlier search → bestmove `c8f8`, score `cp 1637`.
Brute force says only `Qc6` keeps the mate (child truth -2); **both** `c8c5` and
`c8f8` throw it away. So this is not a fresh-vs-warmed correctness difference - both
searches fail to play the mate, and the table only changes *which* non-mating move is
chosen and how the score is reported. I state it as the closest I got to the job's
"wrong RESULT" bar (`logs/B4-bestmove-change.txt`) and explicitly do not claim the
table caused the wrong move.

**F6. The FORGENN4 evaluator agrees with an independent hand-written scalar
implementation** on a sample: for the first position of the 5,040 set and seed 1, the
numpy path and a line-by-line scalar path produce `direct 298114`, `dense 11680`,
`cp 7592`, and identical y1/y2 vectors. It also reproduces itself exactly (seed 2,
position 100 → `4816` recomputed → `4816`).

## 3. Part A4 - what the specification left open

Full text in `logs/A4-ambiguities.txt`; summarised:

1. **Header 145 vs 148**: `145 u8 zero[3]` then `148 u32 D1` leaves 145-147 zero, but
   the FORGENN3 header this descends from has 47 reserved bytes at 145. A reader who
   assumes "reserved is 47 from 145" builds a file 16 bytes shorter.
2. **Does "number of pieces" in step 3 include the kings?** FORGENN3 used
   `popcount(occupied)`, which does. The v4 text does not say. I counted kings.
3. **y2's rounding**: `clamp(s2,0,8128) / 64` has no `*127` factor while y1's does;
   it is right (8128/64 = 127) but easy to misread as `*127/8128`.
4. **int32 vs int64 in steps 5-7**: the 2^28 bound given as the justification is far
   larger than needed (a row sum is ≤ 518,160), so it does not explain itself.
5. **What `w_scale` and `act_max` are for**: they are in the header and the float
   table but never used by the integer steps. Informational or mandatory? I treated
   them as informational.
6. The draw-order sentence `rng.integers(low, high_inclusive + 1, ...)` is what makes
   "-40..40" unambiguous; without it the ranges could be read as half-open.
7. `w1d` bound is ±127 but the test net draws only -8..8: two different statements
   (validity vs this net) that the text does not distinguish.
8. The spec never says what a reader should do if flag bit 0 is set; I refuse the file.
9. "little-endian" is stated once and the checksum is over serialised bytes, not
   values - worth stating explicitly.

## 4. Which files of the repository I opened

For part A (the blind implementation): **none**. The evaluator was written from the
specification in `FABLE_TO_deepseek_5.md` alone. I had read `include/forge/nnue_v3.hpp`
and `src/nnue_v3.cpp` in job 3, and the spec says FORGENN4 is FORGENN3 plus a dense
part, so that prior reading is in my head; I did not open them again in this job and
FORGENN4's dense part has no counterpart in them.

For part B: `src/search.cpp` (the TT probe body, the store sites, the HindsightDepth
block), `include/forge/search.hpp` (`TTEntry`, `verification_key`), `src/uci.cpp` (the
`HindsightDepth` option declaration), `CMakeLists.txt`. Also `FABLE_TO_deepseek_1..5.md`.

## 5. Start and end of each part, recorded stamps

| part | start | end | wall |
|---|---|---|---|
| job 4 correction (two visits) | 12:44:52 | 12:45:10 | <1 min |
| A: evaluator written, nets made, struct bug fixed | 12:45:10 | 12:45:32 | <1 min |
| A2 values (3 nets × 5,040) | 12:45:32 | 12:45:34 | 2 s |
| A: scalar cross-check, perturbation tests | 12:45:34 | 12:56:00 | ~10 min |
| B1 minimal witness search | 12:45:47 | 12:45:50 | 3 s |
| B: hash-size, depth-progression, key and tree tests | 12:47:00 | 12:53:00 | ~6 min |
| B2 instrumentation and hit counting | 12:49:00 | 12:53:30 | ~5 min |
| A4 list and report | 12:53:00 | 13:05:00 | ~12 min |

**Total: about 20 minutes of the 60 allowed.** (Job clock start 12:44:52.)

## 6. What I did not do

- **I did not establish why a self-written quiescence entry changes a mate distance.**
  B3's answer is that it is neither a transposition nor a root collision; the mechanism
  is open. The job allows this outcome ("if every hit is a true transposition, say so")
  but it does not cover "no hits came from the first search", which is what happened.
- I did not run the 10,000-search collision census the job asks for in B3's
  "if there are collisions" branch, because my measurement found no collisions to count.
- I did not test whether the effect survives `ucinewgame` in the middle of a game
  (it does clear the table, so by construction it does).
- I did not verify the FORGENN4 evaluator against any second implementation except my
  own scalar rewrite, and not over the full 5,040 for that; the cross-check is one
  position plus the recomputation spot-check.
- I did not test `H` other than 512, `KB` other than 8 or `OB` other than 8 for
  FORGENN4: the spec's test-net recipe fixes all three, and I made only those nets.
- I did not test D1/D2 header values other than 16/32, nor a file with `eval_scale`
  other than 400.
- I did not change the branch's engine source.

## 7. What I am not sure about

- **The negative in F2 is the least satisfying result in this report.** "No entries
  from the first search were read" is a strong claim from one instrumented pair. It
  rests on the print being on every `probe_body` hit and on the key set comparison; if
  a hit happened through `probe_owned` (the zero-lock path) I would still see it, since
  both go through `probe_body`. What I did not do is run it on the other 34 witnesses.
- **My earlier claim that `HindsightDepth` reduced the depth was wrong and is
  withdrawn.** It is possible the same kind of error is still in F1's remaining
  sentence about depths 12-18, which I did not trace.
- **A4 item 1 could be an error in my reading rather than in the spec.** If the PC's
  writer puts the four new fields somewhere else, the sha256 will differ and this list
  will show which item was misread - which is exactly what the sha256 comparison is for.
- **The perturbation test is weak evidence that the evaluator is right.** It shows the
  comparison can fail (w1d and w2d changes move 1 and 4 of 200 values), but `w1[0][0][0]
  += 40` moved 0 of 200, which I attribute to that feature not being used by those
  positions rather than to a dead path - I did not prove that.
- **I do not know whether FORGENN4's `+ dense` is meant to be added before or after the
  `/ 255` in step 4.** The spec writes `cp = (direct + dense) * eval_scale / 16320`
  where `direct` already includes its `/ 255` and `dense` is a raw sum, so the two are
  on the same 16320 scale only if `dense` is also in that scale. I implemented it
  literally as written.

## 8. A better way

**8.1 Make the FORGENN4 test net carry a tiny intermediate digest.** The sha256
comparison locates a disagreement to a *file*, and A3 locates it to *one position's*
intermediates. A cheaper protocol: include in the spec a handful of (position, ob,
direct, dense, cp) tuples computed by the reference. Then a wrong implementation is
caught on the first line of its own output instead of after making a 6.4 MB net and
running 5,040 positions. Check that it is better by giving the spec to two implementers
with and without the tuples and timing how long the first disagreement takes to find.

**8.2 For the table question, instrument the *store* side, not the probe side.** My
instrumentation showed what the second search read, and found nothing from the first.
That leaves the mechanism open. Printing, for each store, whether it *replaced* an
entry written in the first search would show whether the first search's presence
changes replacement decisions (and hence which of the second search's own entries
survive). That is the next experiment I would run, and it is one print.

**8.3 State the "no harm" bar before the job.** This job says "no claim about harm
unless you can show a search that returns a wrong RESULT". A cheaper and stricter bar:
a position where a fresh search and a warmed search return *different best moves*, with
the fresh one mating and the warmed one not. My B1 data already has candidates for
that (a `cp 1637` where a mate exists) and it would take one more comparison per case;
I did not run it.
