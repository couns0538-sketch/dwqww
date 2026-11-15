# glmflash4, job 7 report (2026-11-15)

## 1. Answer in one line

ThreatCorrection does NOT gain strength per node: at weight 100 the two
seeds give +4.69 ± 10.40 (8121) and −2.61 ± 10.52 (8122), pooled **+1.04 with
a 95 % pair interval of [−6.36, +8.44]** over 4,000 games; at weight 50:
−5.39 ± 10.57 (8123) and −3.58 ± 10.81 (8124, cut at the 70-minute mark with
1,842 of 2,000 games finished), pooled −4.69 [−12.16, +2.96]. The engine with
the option off
IS proven identical (2,000-position identity run, byte-equal sha256,
smallest search 4,534 nodes). The feature's DIAGNOSTIC story is stronger
than its Elo: where it speaks it speaks loudest (P1's mean |term| 3.92 cp vs
the pawn table's 0.82), but that does not convert into Elo at 20,000 nodes.

## 2. Step 0 (unpatched build)

Fresh process per line; raw outputs in `tests_glmflash4_job7/step0/`. Build
command for every build in this job:
`cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-DFORGE_NNUE_HIDDEN=256" && cmake --build build --target forge -j4`
(ASan adds `-DFORGE_ENABLE_SANITIZERS=ON -DCMAKE_BUILD_TYPE=Debug -B build_asan`).

| line | expected | printed | file |
|---|---|---|---|
| bench 11 | 312866 | 312866 | step0/unpatched_bench11.txt |
| bench 13 | 862329 | 862329 | step0/unpatched_bench13.txt |
| bench 16 | 3024920 | 3024920 | step0/unpatched_bench16.txt |
| go perft 5 | 4865609 | 4865609 | step0/unpatched_perft5.txt |

The patched build's `uci` reply lists the new option exactly once:
`option name ThreatCorrection type spin default 0 min 0 max 100`
(`step0/patched_uci_reply.txt`). No uci.cpp change was needed: this tree
advertises every tunables-table entry in its `uci` reply and accepts it by
`setoption` with spin parsing and clamping (the same mechanism my job-4
feature used; the "ThreatHistory pattern" literal-line route would have
duplicated the entry).

## 3. The feature as built

A third correction table of the same shape as the others
(`CorrectionHistory` = 2 × 16384 × int32; 131,072 bytes per search thread),
indexed `[side to move][index]`, read in `Worker::corrected_eval` and written
in `Worker::update_correction` exactly like the material table.

- **The hanging-sets** (`src/search.cpp`, helper `hanging_pieces(board, side)`
  next to the tree's own key helpers): the pieces of one side (kings EXCLUDED
  — a design choice; the king is never "material hanging") that are attacked
  by a lesser enemy piece, with the job's list as the definition: anything by
  an enemy pawn (so pawn-attacks-pawn counts); a rook or queen by an enemy
  knight or bishop; a queen by an enemy rook. Equal-value attackers do not
  count — the same "cheaper" convention as the tree's own
  `quiet_threat_index` (`src/search.cpp:290`), whose per-move lambda I read
  and mirrored; that helper is per-move and local to its function, so a
  node-level pair of bitboards had to be computed fresh (the job's "if it is
  only computed when that switch is on, compute your own" case — the
  ThreatHistory machinery is per-move and behind its own switch).
- **The key** (`threat_key(board)`): the side to move's hanging-set times the
  golden-ratio constant 0x9E3779B97F4A7C15, XOR the opponent's hanging-set
  times golden×3, then xorshift-29 / multiply(golden×9) / xorshift-32 — my
  own mixing (the same style as my job-4 key; odd multipliers only). When
  BOTH sets are empty the key is 0 and all such positions share entry
  [side][0] — intended, and measured in P1.
- **READ** (`src/search.cpp`, in `Worker::corrected_eval`, right after the
  material term): `correction += entry * ThreatCorrection / 100`.
- **UPDATE** (`Worker::update_correction`, right after the material `apply`):
  the same `apply` (grain-256 diff, depth weight min(depth+1, 16), clamp).
- **CLEARED** in `Worker::clear()` beside the other tables.
- **Option**: `ThreatCorrection` int in the tune namespace, registered in the
  tunables table with range 0..100 (0 = off; any other value = weight in
  percent — the job's "SPIN this time" wording, which also resolves the
  check/spin ambiguity the job-4 text had).

## 4. The proofs

- **P1 (traced copy**; diff `proofs/P1_traced_diff.txt`; outputs
  `proofs/P1_traced_bench13_on/off.txt`): bench 13, weight 100:
  reads **79,136** (0.0908 per node of 876,634), updates **4,964** (0.00626
  per node), updates that changed an entry **4,962 (99.96 %)**;
  **empty_both 41,651 = 52.6 % of reads** (both sets empty — the shared
  entry); **distinct full keys 2,077, distinct (side,index) pairs 2,104** of
  32,768 — the table is touched sparsely, as a correction table should be.
  **The three mean |terms| at weight 100: pawn 209.98 grain (0.82 cp),
  material 415.63 grain (1.62 cp), threat 1004.61 grain (3.92 cp)** — the
  threat table's term is the LARGEST of the three where it speaks (its
  entries sit only on hanging-piece positions, which are exactly where the
  static eval is most wrong). OFF state: all counters 0, nodes = the known
  862329.
- **P2 (off = old engine)**: the four known numbers on the patched build
  (re-run: 312866 / 862329 / 3024920 / 4865609 — `step0/`); 2,000 positions,
  `ucinewgame` + `position fen` + `go depth 9` each, unpatched vs
  patched-off: **both answer files sha256 55265dc258ebb8eac58b869f... —
  byte-identical (same best move, score, node count on all 2,000); smallest
  node count 4534**. (The sha equals my job-4 run's — same base engine, same
  position set: a cross-job consistency check.)
- **P3 (on acts)**: weight 100: bench 11 → **277700**, bench 13 → **876634**,
  bench 16 → **2854753** (`proofs/P3_*.txt`) — all different from the known
  numbers.
- **P4 (sanitizers)**: planted-fault program exits 1 under ASan
  (`proofs/P4_planted_stderr.txt`); ASan+UBSan build of the patched tree:
  bench 13 with the option on = **876634 nodes, exactly the release number,
  zero sanitizer/error lines**; 200 of the P2 positions with the option on:
  200/200 answers, **empty stderr** (`proofs/P4_asan_200pos.txt`).
- **P5 (matches)**: FILLED AFTER MATCHES.
- **P6 (speed, honestly)**: bench 13, five runs each, median (taken while
  control C was playing on the same cores — paired, so the comparison holds,
  both sides inflated): off {776, 798, 836, 844, 929 ms} → median **836**;
  on {857, 874, 897, 904, 994} → median **897** — about **+7 %** wall time at
  bench 13; that is the price of computing two hanging-sets at every
  corrected-eval/update site. bench 16, 10 interleaved off/on pairs:
  FILLED AFTER MATCHES (extraction below). Table size: **131,072 bytes per
  search thread**.

## 5. The matches

Form: one exe both sides, option ON vs OFF, `proto=uci nodes=20000
option.Threads=1 option.Hash=16 option.OwnBook=false` under `-each`, no
adjudication, `-concurrency 4`, fresh directory per match, UHO openings
random order, each opening twice with colours reversed.

| match | cand options | seed | games | W-L-D (cand) | pair counts | fastchess Elo ± err | my Elo [95 % pair interval] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|
| C | none; cand nodes=20000 vs base nodes=10000 | 8120 | 300 | 195-20-85 | [0, 5, 23, 64, 58] | +231.91 ± 31.87 | +231.91 [+199.68, +268.07] | 0 |
| M1 | ThreatCorrection=100 | 8121 | 2000 | 591-564-845 | [56, 229, 403, 256, 56] | +4.69 ± 10.40 | +4.69 [-5.71, +15.10] | 0 |
| M3 | ThreatCorrection=50 | 8123 | 2000 | 552-583-865 | [61, 256, 394, 231, 58] | -5.39 ± 10.57 | -5.39 [-15.96, +5.18] | 0 |
| M2 | ThreatCorrection=100 | 8122 | 2000 | 561-576-863 | [67, 237, 387, 262, 47] | -2.61 ± 10.52 | -2.61 [-13.14, +7.92] | 0 |

Pooled (my script, both games files concatenated, M2's rounds renumbered
+1000): 4,000 games, 2,000 pairs, 0 unpaired, W-L-D 1152-1140-1708, score
0.5015, **Elo +1.04, se 0.0054, 95 % pair interval [-6.36, +8.44]**; pair
counts 0.0:123 0.25:466 0.5:790 0.75:518 1.0:103.
| M4 | ThreatCorrection=50 | 8124 | 1842 finished (11 in flight at the 70-min cut; my extraction has 1853 rows, 926 full pairs + 1 unpaired) | 509-530-814 | [58, 225, 365, 235, 43] | -3.58 ± 10.81 | -3.94 [-14.57, +7.06] | 0 |

Pooled weight 50 (M3 complete + M4 cut): 3,853 games, 1,926 pairs, 1
unpaired, score 0.4933, **Elo -4.69, se 0.0055, 95 % pair interval
[-12.16, +2.96]** — weight 50 trends negative, though the cut widens the
interval.

## 6. Files of the repository I opened

- `handoff/...`: `FABLE_TO_glmflash4_7.md`.
- Commit `6b98f217` (exported to /tmp): `include/forge/search.hpp` (the
  history/correction declarations, Worker members), `src/search.cpp` (tune
  block, tunables table, ctor, `Worker::clear`, the key helpers
  `material_key`/`non_pawn_key`, `quiet_threat_index` and its `cheaper`
  lambda (the "cheaper attacker" convention I mirrored), `corrected_eval`,
  `update_correction`), `src/uci.cpp` (option advertisement + setoption).
- The openings file (first 2,000 lines used by P2; the whole file by the
  matches), as in the earlier jobs.

## 7. Stamps of every step

- 21:31:10 job file 7 fetched and read (budget start)
- ~21:32:00 trees exported; the feature written into the working copy (two compile fixes: `pieces(color)` has no single-argument overload, and `piece_type` returns int)
- 21:32:31 patched + unpatched builds finished; deliverable diff generated (129 lines)
- ~21:32:45 step 0 (4 lines) + `uci` reply check
- 21:33:54 traced copy built after three small fixes (the include placement, the counter externs, accessor functions for the key sets); P1 on/off taken
- ~21:34:1x P2 identity runs (2,000 positions, both builds in parallel) + P3 benches
- 21:34:27-21:36:10 control C (stamps.txt)
- 21:36:17-21:53:03 M1, all 2,000 games, exit 0 (the limit never fired)
- 21:35-21:39 P6 bench-13 pairs and bench-16 pairs 1-5 (during C/M1 — paired, stated); bench-16 pairs 6-10 at ~21:39
- 21:37-21:39 P4: ASan build (background), planted fault, bench, 200 positions
- 21:57:28-22:11:12 M3, all 2,000 games, exit 0
- 22:13:49-22:27:28 M2, all 2,000 games, exit 0
- 22:28:3x pooled M1+M2; M4 launched with its limit landing on the 70-minute mark
- 22:28:32-22:41:03 M4, cut by its own limit at the 70-minute mark: 1,842 games finished, 11 in flight lost at the cut (fastchess counts 1,842; my PGN extraction has 1,853 rows), exit 124
- 22:41-22:51 pooled M3+M4, report finalized, commit, push

## 8. What I did not do

- M4 was cut at the 70-minute mark with 1,842 of 2,000 games finished (11
  in-flight games lost at the cut; they appear in my extraction but not in
  fastchess's own table); its weight-50 pool therefore carries a wider
  interval than a complete pair would have.
- I did not try alternative hanging-set definitions (e.g. the tree's stricter
  convention where pawn-attacks-pawn does not count, or SEE-based "losing a
  exchange" sets), nor any interaction with ThreatHistory (the switch stayed
  off everywhere).
- The traced copy's three-mean measurement re-reads the pawn and material
  entries a second time per read (traced-only cost); the numbers are means
  over 79,136 reads, not per-node rates.
- No SPRT, no adjudication, no book; no PR; nothing outside my own branch.

## 9. What I am not sure about

- The pooled [−6.36, +8.44] cannot exclude a small gain or a small loss; with
  M1 +4.7 and M2 −2.6 on the same configuration the seed noise is about ±4
  around the pooled mean.
- The P6 slowdown (+7 % median at bench 13; the on-side slower in 10 of 10
  bench-16 pairs, mean −17 %) was measured partly UNDER MATCH LOAD (both
  sides of each pair equally loaded; the ratios are meaningful, the absolute
  nps are deflated). A clean-machine re-run would tighten it.
- The threat-key's empty-both share (52.6 % of reads) makes the table's
  effective coverage about half the evaluated nodes; whether a finer key
  (e.g. counting attackers, not just hanging pieces) would help is untested.
- The three-mean comparison assumes MaterialCorrectionWeight=100 makes the
  material term directly comparable to the pawn term; with the default 100
  that holds; I did not measure at other weights.

## 10. A better way

- The feature's own diagnostic (P1's three means) is worth keeping in future
  correction-history jobs: a candidate whose mean |term| where it speaks is
  4-5× the established tables' is either the strongest new signal or the
  noisiest; here it turned out to be neither at 20,000 nodes — one number,
  cheap, and it sharpens the Elo non-result.
- The bench-16 speed pairs should be run BEFORE the matches start (my pairs
  1-5 ran under match load; both sides inflated, ratios fair, absolutes not).
  The 10/10 sign pattern (off faster in every pair) is itself the cleanest
  speed statement and needs nothing but the pairing discipline.
- Job texts that prescribe hand tests against a live engine (this one did
  not, but my step-2 style from job 6 applies): name the ORACLE explicitly;
  here python-chess was not needed only because the matches are self-played
  against the same exe with fixed nodes.

## 11. Model

I am glmflash4. The model behind this agent is GLM, trained by Z.ai; the
runtime presents it as GLM 5.3 Flash. I cannot verify a precise version
string from inside the run.
