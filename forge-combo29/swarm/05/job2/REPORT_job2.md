# REPORT job2 — seat 05, area 5 (PRINCIPAL VARIATIONS AND SCORES)

## 1. the three lines

**What was asked.** Draw scores at depth 10 (S14, Threads 1, Hash 16): 20 positions each of K v K, KN v K, KB v K,
KNN v K; 20 positions with a threefold repetition on the board reached by a move list; 20 with the fifty-move
counter at 99.

**The answer.** K v K, KN v K, KB v K and the threefold set all answer `cp 0` in 20 of 20 — **correct**. KNN v K
answers a non-zero `cp` in 20 of 20 (159…354) — **also correct**, mate is possible there so it is not a dead draw,
and I predicted this outcome as acceptable. The fifty-move set is where the result is **not** what I predicted:
at counter 99 every board answers `cp 0`, and so does counter 98 — but the same 20 boards at counter **0** are won
(+470 … +1259 cp, and two `mate` scores). Following the counter down, the score is still +472 at counter **90** and
becomes exactly 0 at counter **91**, for both a K+R and a K+Q win. That is a 50-move draw being decided **9 plies
early**; details in finding S-F3.

**How sure.** High on every number here (all read from committed raw files, 168 searches, no missing `bestmove`,
no refused position, no crash). High on S-F3 being real and reproducible (two materials, ten counter values each,
deterministic). NOT sure what the intended threshold is — see "suspicions".

## 2. honesty numbers

`../HONESTY.txt`: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609, **4 of 4 OK**,
exe sha256 `e06310ec...a83`. The same exe drove every search in this job (`out/meta.txt`).

## 3. the job, step by step

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| PREDICTION pushed alone before measuring | done | `PREDICTION.md` (commit `9ab6e836d`) | 11 numbered predictions |
| position sets generated with `random.Random(501)`, written before searching | done | `make_positions.py`, `positions/*.epd`, `positions/threefold_moves.txt` | 20 per set, all python-chess-legal |
| K v K, KN v K, KB v K, KNN v K at depth 10 | done | `out/{KvK,KNvK,KBvK,KNNvK}.raw.txt` | 80 searches |
| threefold reached by `position startpos moves` | done | `out/threefold.raw.txt`, `positions/threefold_meta.txt` | 20 searches, 20 real 3-fold positions |
| fifty-move counter 99, plus my controls at 98 and 0 | done | `out/fifty{0,98,99}.raw.txt` | 60 searches |
| table of every position's score/nodes/bestmove | done | `analyse_job2.py`, `out/summary_table.txt`, `out/answer_tables.txt` | all numbers from raw files |
| exact counter threshold | done | `threshold_probe.py`, `out/threshold_curve.txt`, `out/threshold_kq.txt` | cliff between 90 and 91 |
| control that the 0 in the threefold set is repetition-driven | done | `out/threefold_diagnosis.txt` + control in that file | same board as a plain FEN gives `mate -11` |
| outside view on the fifty-move boards | done | `out/sf_fifty_control.txt`, `out/sf_threshold_sweep.txt` | Stockfish 16 also says 0 from 88 upward |

## 4. findings

### S-F3 — the fifty-move draw is applied ~9 plies early, and it changes the root score
A K+R versus lone king win, `1K6/8/8/3R4/8/8/8/k7 w - - H 1`, at `go depth 10`, S14, Threads 1, Hash 16:

| halfmove H | score | nodes | bestmove |
|---|---|---|---|
| 0 … 75 | `cp 472` | 9308 | d5b5 |
| 80 | `cp 398` | 8657 | d5b5 |
| 85 | `cp 349` | 29104 | d5b5 |
| 88 | `cp 320` | 192711 | d5b5 |
| 90 | `cp 314` | 946042 | d5b5 |
| **91** | **`cp 0`** | **13791896** | d5d4 |
| 92 | `cp 0` | 1659545 | d5f5 |
| 95 | `cp 0` | 95459 | d5b5 |
| 99 | `cp 0` | 200 | d5d1 |
| 100 | `cp 0` | **0** | d5d1 |

The same cliff appears for K+Q: `8/5K2/7Q/4k3/8/8/8/8 w - - H 1` is `cp 747` at H=90 and `cp 0` at H=91 (and the
H=91 search takes 11.6 s / 126.7 M nodes against 5.2 s / 41.7 M at H=90 — the engine burns a huge tree before
deciding it is a draw). At H=100 the engine searches **0 nodes**, which matches the already-known
halfmove ≥ 100 behaviour; the new part is that the draw is being reached well before 100.

Reproduce:

```
python3 threshold_probe.py /tmp/build-rel/forge "1K6/8/8/3R4/8/8/8/k7 w - - 0 1" 0 75 80 85 88 90 91 92 95 99 100
python3 threshold_probe.py /tmp/build-rel/forge "8/5K2/7Q/4k3/8/8/8/8 w - - 0 1" 0 80 85 88 90 91 95 99
```

### S-F4 — the 20-position fifty-move set at counter 99 is all zeros, exactly as predicted in form but not in cause
All 20 boards of `positions/fifty99.epd` answer `cp 0`; so do all 20 at 98; the same 20 at 0 are +470…+1259 cp with
two `mate` scores (`out/fifty0.raw.txt` vs `out/fifty98.raw.txt`). Prediction #10 said these sets MUST differ and
they do; prediction #7 expected 98 to still show the win and it does not, so **#7 is wrong** and S-F3 is the reason.

### S-F5 — repetition detection itself looks right (a clean result, with a control)
All 20 threefold positions (reached only through `position startpos moves …`) answer `cp 0` with **0 nodes** and an
empty PV, e.g. index 1 `8/K7/8/1p6/1P5k/8/8/3nq3 w - - 8 129` — black is a queen and knight up. The control: the
*same board given as a plain FEN* (so the engine has no history) searches normally and returns `mate -11` in 31616
nodes. So the zero is driven by the move-list history, i.e. by repetition detection, and not by the board. Every
one of the 20 was verified by python-chess to be a genuine `is_repetition(3)` position
(`out/threefold_diagnosis.txt`), so scoring it 0 is correct.

### S-F6 — KNN v K is scored as a win, which is right, and K v K / KN v K / KB v K are 0 with 0 nodes
Recorded for completeness: `cp 159…354` for KNN v K (20/20 searched), `cp 0` and 0 nodes for the three dead draws
(60/60). No mate score anywhere in those four sets, so prediction #8 holds.

## 5. suspicions, NOT proven
- **Which constant causes the 91 cliff.** I did NOT read the source for this (area 7 owns that file). Two readings
  fit every number I have: (a) the engine converts "halfmove + search depth" into a 50-move verdict, so a 10-ply
  search starting at 91 cannot avoid the 100 boundary and therefore calls the position drawn; or (b) a score
  damping term tied to the counter. Reading (a) is the more likely, and it would also explain why H=91 costs
  126 M nodes: the search still explores but every line ends in a draw score. I have no test that separates them.
- **Whether Stockfish's behaviour validates Forge's.** Stockfish 16 also reports `cp 0` from H=88 upward on the same
  board (`out/sf_threshold_sweep.txt`), i.e. it too gives up before 100, though at a slightly different point. So
  "it returns 0 early" is NOT unique to Forge and I do not claim engine-specific guilt — what I can state is only
  that Forge's own score jumps discontinuously between 90 and 91 on a position where a mate exists and that this is
  a very large discontinuity (314 cp → 0) for a one-ply change in a FEN counter.
- **That the KNNvK non-zero scores are "correct evaluations".** I only checked that mate is not impossible there, not
  that a correct engine values it below +360.

## 6. what I did NOT do
- I did not read `search.cpp` or `eval.cpp`; the cause of S-F3 is not established.
- I did not test counters between 91 and 99 for all 20 boards (only the two probe boards) — the set-level table uses
  0, 98 and 99 only.
- I did not test whether repetition detection also fires on a 2-fold (`is_repetition(2)`); every position I built is
  a genuine 3-fold.
- I did not test KNN v K with the two knights far apart (a position where mate is impossible) — those may or may not
  be scored 0; the 20 I have are all non-zero.
- The threefold set contains 3 positions that are also dead draws by material (indices 11, 12, 17,
  `positions/threefold_meta.txt`); for those the 0 is over-determined and cannot be attributed to repetition.

## 7. what I am NOT sure about
- Whether Forge's 91 boundary is a **bug** or a deliberate "score a doomed fifty-move position as a draw early to
  save time" heuristic. If it is deliberate, then it is still worth knowing that it fires at 91 rather than at the
  last ply before 100, and that at H=91 it costs 126 M nodes to decide.
- Whether the 0 at H=91 would persist at greater depth or whether a deeper search would find the mate inside the
  remaining counter. My H=91 run was depth 10 only.
- Whether the fifty-move boundary is computed from the counter alone or from counter + remaining depth; the two
  probes are consistent with either.

## 8. times
See `stamps.txt` (pasted `date -u` lines).

## 9. last command's output

```
$ git status --short
(clean at the commit that added this report)
$ ls
PREDICTION.md  analyse_job2.py  make_positions.py  out  positions  run_job2.py  stamps.txt
threshold_probe.py
$ ls out | tr '\n' ' '
KNNvK.raw.txt KBvK.raw.txt KNvK.raw.txt KvK.raw.txt answer_tables.txt fifty0.raw.txt
fifty98.raw.txt fifty99.raw.txt meta.txt runlog.txt sf_fifty_control.txt sf_threshold_sweep.txt
summary_table.txt threefold.raw.txt threefold_diagnosis.txt threshold_curve.txt threshold_kq.txt
threshold_probe.txt
```
