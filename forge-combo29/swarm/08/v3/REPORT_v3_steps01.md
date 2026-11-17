# FABLE file 7 — Steps 0 and 1 — seat 08

## Step 0: PASSES COMPLETELY

| settings | bench 11 | bench 13 | file 7 says | match |
|---|---|---|---|---|
| no net, no setoption | **312866** | **862329** | 312866 / 862329 | exact |
| PC20, no net | **278024** | **587276** | 278024 / 587276 | exact |
| test net only | **965454** | **4151906** | 965454 / 4151906 | exact |
| PC20 + test net | **625258** | **3652372** | 625258 / 3652372 | exact |

Eval under PC20 + test net: **968 / 1176 / 31** — all three exact.
Net file: **6,309,096 bytes, fnv1a64 fdff70de72e4ca82, sha256 1db8525e…** — all three exact.
Load line: checksum `fdff70de72e4ca82`, `max|w1| 64 max|b1| 96 max|w2| 16`, **kernel avx512**.
Build: `-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`, g++ 13.3.0, Release, no `-march` override.
**Machine: 4-core x86-64 with AVX-512F and BMI2**, so the AVX-512 v3 kernel runs here as on the PC's Zen 5.

## Instrumentation, and why the profile is ADMISSIBLE
`perf` is **not installed** on this machine and `apt` is unavailable (no root). So the profiler is **gprof**
(`-pg -fno-omit-frame-pointer`, linker `-pg`).

**The reason the numbers below can be trusted is a single check: the `-pg` build reproduces bench 13 = 3,652,372
nodes under PC20 + test net exactly, the pinned number from file 7.** A profiler that changes behaviour measures
itself, so an instrumented build must first be shown to be the same engine on the workload being profiled. It is.

## Step 1: the profile, `bench 13` under PC20 + test net, Threads 1

Sampled self time, top functions (`profile/gprof_flat.txt`):

| group | self % | detail |
|---|---|---|
| **all `nnue::v3`** | **21.46 %** | — |
|   `v3::apply_changes_pair` (the incremental UPDATE) | **8.47 %** | 2,382,071 calls |
|   `v3::evaluate` (forward pass) | **7.34 %** | 2,556,881 calls |
|   `v3::refresh_from_pieces` (full recompute) | **6.78 %** | 617,443 calls |
|   `v3::load` | 1.13 % | 1 call (startup) |
| search proper (`Worker::search` + `qsearch` + `MovePicker::next` + `pick_best` + `generate_evasions`) | **38.41 %** | — |
| movegen / legality / make-unmake / `see_ge` | 15.80 % | — |

Top individual functions: `Worker::search` 9.04 %, **`v3::apply_changes_pair` 8.47 %**, `MovePicker::next` 7.91 %,
`Worker::qsearch` 7.91 %, `generate_evasions` 7.34 %, **`v3::refresh_from_pieces` 6.78 %**, `pick_best` 6.21 %,
**`v3::evaluate` 5.08 %**.

## MY PREDICTION IS KILLED, and I say so first
I predicted the incremental update would dominate at **35–50 %**, with my kill range "under 20 %". **Measured 8.47 %**
— dead, by a factor of four. The forward pass I predicted at 15–30 % (measured 7.34 %, also below its 5–45 % band by
the low end) and refresh at 5–20 % (measured 6.78 %, inside).

**What I got wrong, and why:** I reasoned that the update runs at every node while the forward pass runs only at eval
leaves, so the update should dominate. That reasoning ignores that **`evaluate` is called 2,556,881 times against
`apply_changes_pair`'s 2,382,071** — almost the same count. The v3 path evidently evaluates at nearly every node, so
my "fewer evals than updates" premise was simply false. The measured call counts refute the mechanism, not just the
number.

**My second prediction — that a cache-side change would not yield a large win because the incremental update already
IS a cache — is now better supported than when I wrote it**, since the update is only 8.47 % of the time: even
eliminating it entirely could not give more than that. I keep that prediction as written, including the part that says
a large win would surprise me.

**My second kill condition did NOT fire, and it cleared by only 11.6 points:** search proper is **38.41 %** against a
50 % threshold. The claim it licenses is therefore weaker than "the harness is fine" — the net IS being exercised, but
search is the single largest block and only a little more of it would have failed the gate. I state the margin because
a threshold barely cleared should not be reported as comfortably met.

## Step 1b: the 200-opening baseline (also Step 2's identity table)
200 positions (first 100 of O + first 100 of G), `go depth 12`, `ucinewgame` + `isready` before each, PC20 + test net:
**node sum 27,944,084**, every position with a node count, per-position rows in `profile/openings_baseline.txt`.

**This table is the identity baseline**: any patch must reproduce every row exactly, per file 7.

## The architecture fact, which outlasts the percentage
I predicted the incremental update would dominate because it runs at every node while evaluation runs at leaves. **The
call counts say otherwise: `evaluate` runs 2,556,881 times against the update's 2,382,071** — the v3 path evaluates at
nearly every node. So the asymmetry I assumed does not exist, and that is a statement about how this architecture
works, not about one percentage. **The premise was false, not the estimate.**

## The consequence is a NEGATIVE RECOMMENDATION
**No single v3 function exceeds 8.5 %, so there is no hot spot, so do not spend effort on a v3 micro-patch.** The
larger shares are **search at 38.41 %** and **movegen at 15.80 %**, which is where any real speed work should go —
and those are seats 19 and 29's existing territory, not the v3 novelty. Redirecting effort away from a 3 % patch is
worth more than the patch would have been.

## What this means for Step 2, before I write any patch
The v3 path is **21.46 %** of bench-13 time and no single v3 function exceeds 8.5 %. The three v3 functions are
unusually **balanced** (8.47 / 7.34 / 6.78), which means:
- there is no single hot spot to attack, so a big win from one patch is unlikely — consistent with my second
  prediction;
- the larger opportunity on this bench is in **search proper (38.41 %) and move generation (15.80 %)**, which is
  seat 19's and 29's existing territory rather than the v3 novelty;
- and since this is a **bench** measurement, the coordinator's constraint applies: **no speed patch is recommendable
  from the bench alone.** A candidate needs a real-position arm (fixed `go nodes`, ABBA, n ≥ 120, per-position
  spread) before it means anything.

## Show it again

    cd forge-combo29/swarm/08/v3 && bash step0_v3.sh ~/builds/v3/forge ./test_v3.fnn3 /tmp/s0.txt
    # profile: build with -pg, run bench 13 under PC20+net, then: gprof -b -p <exe> gmon.out
    python3 profile_openings.py /tmp/openings.txt ~/builds/v3/forge
