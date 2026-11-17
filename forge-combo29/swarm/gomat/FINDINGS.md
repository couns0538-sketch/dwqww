# `go mate N` — the whole surface, measured

Audit base commit `6b98f217` (`Checkpoint standalone NNUE v3 work and evidence`).
Engine: `forge`, `id name Chess Engine Forge 6.4.24 candidate`, built with
`-DCMAKE_CXX_COMPILER=/usr/bin/g++` and `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`
as the build trap requires. All measurement on `Threads 1`, `Hash 32`, `OwnBook false`.

**Honesty pins on this build, before any measurement** (`scripts/pins.py`, raw
output `evidence/pins.log`): 312,866 / 862,329 / 3,024,920 and perft 5
4,865,609 — all four match. Net-off bench also matched the `check_pins.sh`
values (375,354 / 907,205 / 2,448,617).

**Nothing in this document was typed by hand.** Every position came from a
generator (`scripts/corpus.py`, `scripts/run_edges.py`, `scripts/run_overclaim_scan.py`)
or from a committed position set (`first200.fens`, `set_G.epd`). Every mate claim
is replayed in python-chess, and every "no mate" claim is a total enumeration of
root moves or an exhaustive minimax at a stated window (`scripts/mateoracle.py`).
Two of my own checks were wrong on the first run and both are recorded below
rather than deleted.

---

## The answer in one paragraph

`go mate N` is a **bounded mate-preference search**, not a mate solver and not a
depth cap. It finds every forced mate at distance 1–4 exactly and reports the
distance correctly, 32 of 32 proven endgames. It **always terminates**, at
`2N-1` plies, and the bound is real: 36 of 36 no-mate requests returned. It
**obeys a clock**, and a short clock silently costs you the mate. On real
positions it is **not a comparable label** with `go depth 2N-1`: 1140 of 1600
cells differ, the median node ratio at `N=4` is **188×**, and the 163× figure in
the findings is **not an outlier there — it is roughly the median**. Its failure
mode is benign in shape (a plain cp score, a full-length PV, no mate-shaped line)
but it has one real defect: at the edge of its window it can report a mate
distance that is **wrong and unprovable at the depth it searched** (2 of 6 hits
on a 400-position scan, 1 in 1200 requests).

---

## 1. Does it find known forced mates at 1/2/3/4?

Corpus: 32 sparse endgames, generated, each with **oracle-proved exact DTM** and
no faster mate (`scripts/corpus.py`, `evidence/corpus.json`). Every one was
verified by exhaustive minimax, not by a hand-written FEN.

| true mate | `go mate 1` | `go mate 2` | `go mate 3` | `go mate 4` |
|---|---|---|---|---|
| in 1 (8 pos) | 8/8 correct | 8/8 correct | 8/8 correct | 8/8 correct |
| in 2 (8 pos) | 0/8 (cp) | 8/8 correct | 8/8 correct | 8/8 correct |
| in 3 (8 pos) | 0/8 (cp) | 0/8 (cp) | 8/8 correct | 8/8 correct |
| in 4 (8 pos) | 0/8 (cp) | 0/8 (cp) | 0/8 (cp) | 8/8 correct |

**80 of 80 mate-scored cells on this corpus report the distance exactly right**
(`scripts/check_overclaim_class.py`, `evidence/overclaim_class.json`). No wrong
distance, no missed mate at or under N.

So the mode is **sound at and under N on positions where a mate exists**, and it
is **all-or-nothing across N**: a mate in 3 is a cp score under `go mate 2`, not a
hint. That is the useful form for a user: `go mate N` answering `mate k` with
`k <= N` is a claim you can act on.

### What it reports when no mate exists

**Not a mate-shaped line, and never a truncated one.** On 20 no-mate cells across
5 proven no-mate positions, every answer was a plain `score cp`
(`evidence/surface.json`, section A/B). PV length against the reported depth:
**17 of 20 exactly `2N-1` plies**, and the other **3 are LONGER, never shorter**
(kiwipete at N=1 gives a 6-ply PV at depth 1; two others give 6 at depth 5) —
a qsearch extension, not a truncation. Across the 1600 real cells the split is
`mate_mode_cp_fullline 1357`, `mate_mode_cp_shortline 231`, `mate_mode_mate 12`
(`evidence/edges.json`, section H).

So there is **no case of a mate-shaped line carrying a non-mate score** — the one
shape a corpus builder could mis-read does not occur — and no case of a mate
score whose PV was shorter than the distance it implies except the one defect in
§6.

**And it does not spin or stop early.** It stops at `2N-1` and says a cp score.

---

## 2. Does `go mate 1` terminate with no mate in 1? The bound.

Yes, and the bound is in the source: `mate_depth = mate_moves * 2 - 1`
(`src/search.cpp:2213`), `max_depth = clamp(min(limits.depth, mate_depth), 1, 64)`.

36 requests over 6 positions at N = 1..6, every one **TERMINATED**, every one at
exactly depth `2N-1` (`evidence/termination_a.json`):

| position | N=1 | N=2 | N=3 | N=4 | N=5 | N=6 |
|---|---|---|---|---|---|---|
| startpos | 0.001 s | 0.001 s | 0.006 s | 0.082 s | 1.878 s | 32.4 s |
| after 1.e4 | 0.001 | 0.001 | 0.007 | 0.108 | 2.598 | 41.9 |
| italian | 0.001 | 0.002 | 0.017 | 0.376 | 5.942 | **135.2** |
| queens-gambit | 0.001 | 0.001 | 0.010 | 0.164 | 3.008 | 59.5 |
| kiwipete | 0.002 | 0.003 | 0.032 | 0.517 | 7.319 | **101.1** |
| bare kings | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

**The bound is `2N-1` plies and it always binds.** For `go mate 1` on any
no-mate-in-1 position: **0.001–0.002 s**, 6 of 6. That is the number for a caller
who wants a cheap "is there a mate in 1" probe.

**The wall clock is not bounded, and that is the thing to carry away.** Depth
`2N-1` on a real middlegame is not cheap: `go mate 6` costs **101.1 s to 135.2 s**
and **230–342 million nodes** on two ordinary positions. `go mate 1` is free;
`go mate 6` is not, and neither the request nor the reply says so.

---

## 3. The disabled heuristics, and the TT — which ones change the ANSWER

Eleven source gates read `mate_moves_` and turn something off. Each was made
independently switchable (`scripts/variants.py`). The build step produced
**19 distinct binaries**: the control plus 18 distinct gate sets, from 20 arm
names (one name, `TT_BOTH`, is an alias for the gate set `TTq+TTmain` and is
reported as such rather than counted twice). `scripts/build_variants.py`
**hard-fails** if any two different gate sets produce the same binary, and the
control was proven bit-identical to the base engine on 64 requests
(`evidence/control_identity.json`: 0 differing of 64). Each arm ran the
37-position corpus at N = 1..4 (148 requests), scored on **answer changes**, not
node changes (`evidence/ablation.json`).

| arm (heuristic re-enabled) | source | answers changed | nodes range |
|---|---|---|---|
| RazorRfpNull (razoring + RFP + null move) | 1680 | **33 / 148** | 0.03× – 1365× |
| FutilityPrune (futility + LMP) | 1841 | **44 / 148** | 0.03× – 225× |
| Lmr (late move reductions) | 1991 | **39 / 148** | 0.02× – 319× |
| CheckExt (check extensions) | 1955 | **9 / 148** | 0.0004× – 2.5× |
| QSearchPrune (qsearch futility + SEE) | 1493 | 3 / 148 | 0.59× – 1.09× |
| Window (mate window clamp) | 1431 | 1 / 148 | 0.98× – 10.3× |
| TTq (qsearch TT cutoff) | 1452 | **0 / 148** | 0.53× – 1.0× |
| TTmain (main TT cutoff) | 1639 | **0 / 148** | 0.52× – 1.0× |
| Iir | 1784 | **0 / 148** | 0.93× – 1.0× |
| QuietExtinction | 1805 | **0 / 148** | 1.0× |
| SingularExt | 1929 | **0 / 148** | 1.0× |
| all eleven | — | 57 / 148 | 0.002× – 98.6× |

**Two at a time, as asked** (`evidence/ablation.json`):

| pair | answers changed |
|---|---|
| Lmr + FutilityPrune | **55 / 148** |
| Window + Lmr | 40 / 148 |
| RazorRfpNull + Iir | 33 / 148 |
| SingularExt + CheckExt | 9 / 148 |
| QuietExtinction + QSearchPrune | 3 / 148 |
| TTq + TTmain | **0 / 148** |

**What this establishes and what it does not.**

* The **TT cutoff matters for cost but not for the answer** on this corpus: both
  TT arms change 0 of 148 answers, while halving or doubling nodes. So the TT's
  role in mate mode is a **speed** question, not a correctness one — and the
  finding that mate mode disables it should not be read as "the TT changes mate
  answers".
* The **pruning heuristics are load-bearing on the answer**, and enabling them
  makes mate mode *worse*, not better: on `M2-001`, `go mate 2` alone gives
  `mate 2 / g1b1 / 894 nodes`; with Lmr enabled, `cp 831 / g2h1 / 331 nodes` —
  **the mate is lost**. Same pattern for RazorRfpNull and FutilityPrune
  (`evidence/ablation.json`, `examples`). So the seven switches are not
  gratuitous: turning them back on **destroys mate detection on these endgames**.
* **`SingularExt` and `QuietExtinction` are inert here** (0 answers, 1.0× nodes
  exactly for QuietExtinction). A gate that is inert on a mate-rich corpus is a
  candidate for removal, but 0 of 148 on **sparse endgames** is not 0 of 148 on
  middlegames, and this document does not claim the latter.
* **A caution about the ablation itself.** The 163× node saving when pruning is
  re-enabled is the same order as the mate-mode overhead in §5. Pruning is what
  mate mode buys its search with; the ablation cannot separate "the gate is
  wrong" from "the gate is doing exactly what mate mode needs".

---

## 4. Does `go mate N` obey the clock?

**Yes — and a short clock silently changes the answer**
(`evidence/termination.json`, `evidence/clock_label.json`).

On a proven mate-in-4 board, `go mate 4`:

| request | depth | score | bestmove | wall |
|---|---|---|---|---|
| no clock | 7 | **mate 4** | e6e3 | 0.104 s |
| `wtime 5000 btime 5000 winc 100 binc 100` | 7 | mate 4 | e6e3 | 0.107 |
| `wtime 1000 btime 1000 winc 10 binc 10` | 7 | mate 4 | e6e3 | 0.174 |
| `wtime 200 btime 200` | 5 | **cp 891** | **d4h4** | 0.014 |
| `movetime 500` | 7 | mate 4 | e6e3 | 0.117 |
| `movetime 50` | 7 | **cp 939** | **e6c6** | 0.040 |
| `movetime 5` | 3 | **cp 822** | **g2h1** | 0.001 |

**A clock that does not cover the `2N-1` search loses the mate, and the reply does
not say so.** 3 of 7 clock forms produced a different answer from the clockless
request on this board. The mode is not "clock-aware" in the sense a caller needs:
it is a fixed-depth search that a clock can truncate mid-iteration.

### And the truncation mixes two depths into one label

`search.cpp` publishes on abort, when the partial PV's first move differs from the
last finished one:

```c
emit(depth, result.score, result.pv);   // depth = UNFINISHED iteration
                                        // score = LAST FINISHED iteration
```

Measured on a movetime ladder (`evidence/clock_label.json`), 5 of 21 cells report
a score the clockless search does **not** give at the same reported depth:

| board | movetime | reported depth | reported | reference at that depth |
|---|---|---|---|---|
| mate-in-4 | 80 ms | 7 | **cp 939** | **mate 4** |
| mate-in-4 | 20 ms | 6 | cp 891 | cp 939 |
| kiwipete | 5 ms | 1 | **cp 0** | cp −76 |
| kiwipete | 10 ms | 1 | **cp 0** | cp −76 |
| kiwipete | 320 ms | 7 | cp −104 | cp −117 |

**The first row is the damaging one**: a clocked `go mate 4` prints `depth 7` with
depth 5's score, so a consumer reading the last line sees depth 7 completed and no
mate, when depth 7 is what would have found it. `depth` in a clocked mate reply is
not the depth that produced the score beside it.

(Note on a withdrawn reading: an earlier run of this check reported 21 of 21 cells
"mixed". That was a tuple-vs-list comparison in my own checker, not an engine
defect. Fixed before it reached this document; the 5 of 21 above is the corrected
number, and the checker now normalises both sides.)

---

## 5. The comparability warning, as a table with the distribution

1600 cells: 400 real positions (200 from `first200.fens`, 200 from `set_G.epd`) ×
N = 1..4 × both modes (`evidence/compare_real.json`).

### Answers disagree, and the disagreement grows with N

| N | label depth | differing answers | median node ratio | q95 | max |
|---|---|---|---|---|---|
| 1 | 1 | 12 / 400 | 1.29× | 3.2× | 11× |
| 2 | 3 | **357 / 400** | 7.94× | 16.7× | 42× |
| 3 | 5 | **387 / 400** | 35.9× | 91× | 160× |
| 4 | 7 | **384 / 400** | **188×** | 519× | **1562×** |

**1140 of 1600 cells differ in move or score. 571 of 1600 differ in MOVE.**

### The 163× case, in its distribution

This is the correction the assignment asks for. On the proven-DTM corpus the
163× figure is a genuine outlier (128 cells, median 1.19×, max 166.9× — that max
**is** the case: `M4-005`, 732,794 nodes vs 4,391, i.e. 166.9×). On **real
positions at N=4 the
median is 188×**, so a 163× cell there is *below* the median:

| rank at N=4 (of 400) | position | ratio | mate mode | depth mode |
|---|---|---|---|---|
| 1 | set_G.epd:169 | 0.3× | mate 2 / 37 nodes | mate 2 / 141 |
| 101 | first200.fens:176 | 77× | cp −72 / 337,447 | cp −66 / 4,377 |
| **201 (median)** | first200.fens:194 | **188×** | cp −35 / 609,020 | cp +10 / 3,238 |
| 301 | set_G.epd:63 | 323× | cp 83 / 1,710,671 | cp 50 / 5,293 |
| 400 | set_G.epd:13 | **1562×** | cp 267 / 3,602,532 | cp 262 / 2,306 |

Ratio bands at N=4: `[0,1)` 2 cells, `[1,10)` 24, `[10,100)` 93,
`[100,1000)` **279**, `[1000,∞)` 2.

**So the honest statement is not "163× is an outlier".** It is: *on endgames
where a mate exists, mate mode costs 1–5×; on ordinary positions it costs
**100–500× as a rule**, and one board in 400 costs 1562×.* The 163× figure is a
good outlier on an endgame corpus and a slightly *below-median* cell on real
positions. A node-count fingerprint for spotting mate rows in an existing corpus
still works — but the threshold is ~100× on real positions, not the 163× anchor,
and a 163× row on a real position is unremarkable.

### Two cells where mate mode got the better answer

`set_G.epd:60` at N=3: mate mode `mate 3 / c4a6 / 2,062 nodes`; depth mode
`cp 1848 / c4a6 / 764` — **mate mode found the mate the depth search missed, for
2.7× the nodes.** `set_G.epd:175` at N=2: `mate 2 / e3b3 / 2,588` against
`cp 2662 / h4h5 / 245`. So the extra work is not pure waste; it buys mate
detection the depth search does not have. Both verified by PV replay.

---

## 6. Defect: a mate distance that is wrong and unprovable at the searched depth

This is the one finding in this audit that is a **defect** rather than a
characterisation.

### The instance

`8/7Q/8/8/K7/8/8/5k2 w - - 0 1`, oracle exact DTM = **5 moves (9 plies)**:

```
go mate 4  ->  depth 7  score mate 6  nodes 687776  pv h7h2 f1e1 a4b4 e1f1 b4b3 f1e1 h2g2
go mate 5  ->  depth 9  score mate 5  nodes 2592168 (correct, PV replays to mate)
```

`mate 6` implies **11 plies**. The search reported `depth 7` and its own PV is
**7 plies**, ending in a quiet move — **it does not replay to mate**. A score of
mate 6 cannot be proved by an 7-ply search: it needs 4 plies it never searched.

### Mechanism, as arithmetic a reader can check

`qsearch` clamps `alpha = max(alpha, mated_in(ply))`, `beta = min(beta, mate_in(ply+1))`
with `mated_in(p) = -32000+p`, `mate_in(p) = 32000-p` (`src/search.cpp:211-212`,
`1431-1433`). When a fail-high reaches that beta, the stored value **is** a
mate-encoded number whatever its provenance. The iteration loop then breaks on
`score >= mate_in(mate_moves*2-1)` (`src/search.cpp:2552`), i.e. `score >= 32000-(2N-1)`,
which a `mate M` score satisfies whenever `2M-1 <= 2N-1`. The value passes the
"found it" test on its **encoding**, not on its being a proven mate.

**A separate, certain fact from the same reading:** the window can never empty
from ply, because that needs `2*ply >= 63999` and `MaxPly` is 128. So
`if (alpha >= beta) return alpha;` at `search.cpp:1434` is **unreachable** in mate
mode. That is a dead branch, not a defect, but it is worth knowing before anyone
"fixes" the clamp.

### How wide is it?

400 generated endgames × N = 2,3,4 = **1200 requests**, **6 hits** where
`M > N` (`evidence/overclaim_scan.json`, `evidence/overclaim_classified.json`).
Rate **6/1200 requests**, and it needs `N >= 3` (3 hits at N=3, 3 at N=4).

The 6 split into two classes, and **only the second is a false claim**:

| class | count | meaning |
|---|---|---|
| A — found further, and right | 4 | distance equals truth but exceeds N. Report is TRUE; the request was not honoured as advertised. |
| B — **wrong distance** | **2** | distance ≠ truth; PV does not replay. **False claim.** |

Class B cases, both proved: `8/8/8/2Q4K/8/5k2/8/8 w` — `go mate 4` says `mate 7`,
truth is **6** (and `mate 7` is too *long*, which for a winning side is not even
the benign direction); `8/k3K3/8/3R4/8/8/8/8 w` — same shape. The same request at
the truth's own N returns the truth **6 of 6 times**, so the error is
**edge-local**: it happens in the partial iteration at the cap, not in the search
generally.

### What a user should do

**Trust `mate k` for `k < N`. Treat `mate N` on a `go mate N` reply as a bound,
not a proof, and check the PV length against `2k-1` before acting on it.** A
PV shorter than `2k-1` plies is the detectable signature, and it caught 1 of 1 in
the invariant scan of 301 mate-scored cells (`evidence/mate_invariant.json`).

---

## Suspicions, not proven

* **The unreachable window-empty branch may mask a second problem.** If the
  clamp was meant to refuse a bound, the branch that would do it never runs. I
  did not build the variant that makes it reachable, so this is a reading, not a
  measurement.
* **`mate 0` is ambiguous.** On a checkmated root every mode prints
  `score mate 0 ... pv` with an empty PV (`evidence/surface.json`, section G). A
  consumer parsing `score mate <n>` sees a mate claim of zero; the conventional
  encoding for "side to move is mated" is `mate 0`, so this is likely correct —
  but nothing in the reply distinguishes "mated at the root" from "a mate score
  of zero", and I did not find a third case that would separate them.
* **Class A may be the majority at higher N.** 4 of 6 hits were class A. If the
  rate rises with N, `go mate 6` may routinely answer `mate 7`, which would make
  the mode unusable as an oracle. Only N = 2,3,4 were scanned.
* **The 2 class-B positions are both K-with-queen-or-rook vs lone king.** Two
  positions of one material shape is not a characterisation; it is a lead.

## What I did NOT do

* **No `stop`-during-search stress.** 2 of 2 attempts returned a clean bestmove
  and the next request worked (`evidence/surface.json` section D), but that is a
  smoke test, not the 1,000-iteration race test area 2 does.
* **No Threads > 1.** Everything is `Threads 1`. Mate mode with helpers is
  untested and the `bare_king_mode` path is compiled out at one thread.
* **No middlegame ablation.** The ablation corpus is sparse endgames; the
  inertness of `SingularExt` and `QuietExtinction` does not generalise.
* **No fix proposed.** I did not write a patch. The window clamp and the
  encoding-passing-the-break-test are both plausible sites and a patch would need
  its own before/after on the 1200-request scan.
* **No `go mate` beyond N=6**, so the wall-time extrapolation past ~135 s is
  arithmetic, not measurement.

## What I am NOT sure about

* **Whether class B is the same mechanism as the `mate 6` at N=4 instance.** The
  arithmetic fits both, and all three have a PV shorter than their implied
  distance, but I did not instrument the search to watch the clamp fire.
* **The exact real-position rate of class B.** 1200 requests on **endgames** gave
  2. Real positions may differ in either direction and were not scanned (the
  scan's oracle cannot finish on a middlegame).
* **Whether `mate k` with `k < N` is always sound.** 80 of 80 on the proven
  corpus, and 9 verified PV replays on real positions, all correct — but the
  proven corpus is 32 positions, and that is a sample of endgames, not a proof.

---

## Reproducing

```
scripts/pins.py                build/forge              # the four honesty pins
scripts/corpus.py              -> evidence/corpus.json # generated, oracle-proved DTM
scripts/run_gomat.py           -> evidence/raw_modes.json
scripts/build_variants.py      -> /tmp/ab + BUILDS.txt # 19 distinct binaries
scripts/control_identity.py    -> control is the base engine, 64/64
scripts/run_ablation.py        -> evidence/ablation.json
scripts/run_termination.py     -> evidence/termination.json
scripts/run_compare.py         -> evidence/compare_real.json, compare_mate.json
scripts/run_surface.py         -> evidence/surface.json
scripts/run_edges.py           -> evidence/edges.json
scripts/run_overclaim.py       -> evidence/overclaim.json
scripts/run_overclaim_scan.py  -> evidence/overclaim_scan.json
scripts/classify_overclaims.py -> evidence/overclaim_classified.json
scripts/check_mate_invariant.py-> evidence/mate_invariant.json
scripts/check_overclaim_class.py -> evidence/overclaim_class.json
scripts/run_clock_label.py     -> evidence/clock_label.json
scripts/run_overclaim_arms.py  -> evidence/overclaim_arms.json
scripts/verify_findings.py     -> verifies this document's figures (42 checks)
```

`verify_findings.py` reads each figure **out of this document** by a regex that
names its surrounding phrase and compares it to the evidence file. It carries its
own control: on every run it plants a wrong number for six of the checks and
**requires each plant to fail**. Its first version compared evidence to evidence
and never read the document at all, so planting `1139 of 1600` left it green —
the vacuous-control shape, caught by testing the checker instead of trusting it.
Its limit, stated because findings §6 says a check cannot close it: it verifies
number-versus-measurement, and says nothing about whether the sentence around a
correct number means what the number supports.

## Two errors of my own, kept

1. **A first runner sent `ucinewgame` AFTER `position`,** so all 37 positions
   searched startpos and every one returned identical numbers. Caught by the
   identical-node-count tell-tale, not by any assertion. Fixed
   (`run_gomat.py:search`), and the comment there says why.
2. **A first ablation build passed the gate definitions only to a text file,** so
   all 13 variants were **byte-identical to the control** — a clean-looking table
   of "no gate matters". Caught by sha256. `build_variants.py` now refuses any
   arm whose binary matches the control's, and `control_identity.py` re-proves
   the control equals the base engine on 64 requests.
3. **A first `verify_findings.py` never read the document.** It compared each
   expected figure to the evidence file, which cannot fail on a wrong document,
   and planting `1139 of 1600` left it green. Rewritten to extract each figure
   from the document by a phrase-anchored regex, with six plants it must catch
   on every run.

A fourth, smaller one — a tuple-vs-list score comparison that reported 21/21
mixed labels — is recorded in §4 where it belongs, because it would have inflated
a real finding.
