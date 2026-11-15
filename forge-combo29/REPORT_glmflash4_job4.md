# glmflash4, job 4 report (2026-11-15)

## 1. Answer in one line

MinorCorrection does NOT gain strength per node. Weight 100, pooled over its
two seeds (M1 -4.69 ± 10.49, M2 +8.86 ± 10.59; 4000 games, 2000 pairs):
**+2.08 with a 95 % pair interval of [-5.37, +9.54]**. Weight 50, pooled over
M3 +0.35 ± 10.44 and M4 +5.39 ± 10.47: **+2.87 [-4.53, +10.26]**. The engine
with the option off IS proven identical to the old engine: the 2000-position
fixed-depth answers hash to the same sha256 on both builds. Nothing was cut:
the control and all four matches ran their full 2000-game counts (exit 0,
0 abandoned).

## 2. Step 0 (unpatched build)

Fresh process per line; raw outputs in `tests_glmflash4_job4/step0/`. Build
command used for every build in this job:
`cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && cmake --build build --target forge -j4`
(the ASan build adds `-DFORGE_ENABLE_SANITIZERS=ON -DCMAKE_BUILD_TYPE=Debug -B build_asan`).

| line | expected | printed | file |
|---|---|---|---|
| bench 11 | 312866 | 312866 | step0/unpatched_bench11.txt |
| bench 13 | 862329 | 862329 | step0/unpatched_bench13.txt |
| bench 16 | 3024920 | 3024920 | step0/unpatched_bench16.txt |
| go perft 5 | 4865609 | 4865609 | step0/unpatched_perft5.txt |

The patched build's `uci` reply lists the new option exactly once:
`option name MinorCorrection type spin default 0 min 0 max 100`
(`step0/patched_uci_reply.txt`).

## 3. The feature as built

One new correction table of the SAME shape as the existing ones
(`CorrectionHistory` = `std::array<std::array<int32_t, 16384>, 2>`, 16384
entries per side, grain 256, limit 8192 — `include/forge/search.hpp:390-391`),
indexed by the side to move like the other four correction tables.

- **Key** (`src/search.cpp:1065`, helper `minor_key` in the anonymous
  namespace next to the tree's own `material_key`/`non_pawn_key`): the four
  placement bitboards (white knights, white bishops, black knights, black
  bishops — NO kings, as the job says) are each multiplied by a distinct odd
  constant (successive odd multiples of the golden-ratio constant
  0x9E3779B97F4A7C15: ×1, ×3, ×5, ×7), XOR-folded, then finalized with one
  xorshift-29/multiply(×9)/xorshift-32 round. No table, no stored state; the
  key is computed at each node where it is used. Constants are derived in the
  source from the one golden-ratio constant; nothing is copied from any other
  engine.
- **READ** (`src/search.cpp:1242-1243`, in `Worker::corrected_eval`, directly
  after the material table's term): `correction += entry * MinorCorrection / 100`
  — the exact pattern of the material term (`* MaterialCorrectionWeight / 100`).
- **UPDATE** (`src/search.cpp:1262`, in `Worker::update_correction`, right
  after the material table's `apply`): the same `apply` lambda (grain-256
  scaled diff, depth weight `min(depth+1, 16)`, clamp to ±CorrectionLimit).
- **CLEARED** (`src/search.cpp:1033`, in `Worker::clear()`, the single place
  where all correction tables are zeroed, reached from the constructor and
  `Searcher::clear()` → `ucinewgame`).
- **Option**: `MinorCorrection` is an int in the tune namespace
  (`include/forge/search.hpp:295`, `src/search.cpp:79`) registered in the
  tree's tunables table (`src/search.cpp:142`, range 0..100). This tree
  advertises every tunables-table entry in its `uci` reply and accepts it by
  `setoption` with spin parsing and clamping, so no `uci.cpp` change was
  needed at all. DESIGN CHOICE, said plainly: the job text asks for a SPIN
  whose value is the weight in percent (feature section) and also for a
  "type check" switch (deliverable section); these cannot both carry the
  weights 100 and 50 that M1-M4 must play, so I built the spin (0 = off,
  1..100 = weight percent) and the `uci` reply line is the spin's.

Design choices the job left open, and what I tried and dropped:
- Table size: the same 16384×2 int32 shape as the other correction tables
  (131,072 bytes per search thread) rather than a new size — "a third table
  of the same shape".
- Update/read weight: exactly the material table's mechanics (weight percent
  on read; the shared depth-weighted `apply` on write) — no separate scaling
  invented.
- The key mixes the four bitboards by MULTIPLICATION (the house idiom the
  tree's own `non_pawn_key` uses) rather than by per-square Zobrist arrays —
  no new tables, no initialization order dependencies.
- Dropped: indexing the table by BOTH sides' minors jointly per side
  (i.e., four tables like the non-pawn pair) — the job says ONE table; the
  [side] index follows the house shape.

## 4. The proofs

- **P1 (counters, traced copy)**: `proofs/P1_traced_diff.txt` is the traced
  copy's diff on top of the feature patch (three counters, reset in
  `Worker::clear()`, printed by `bench`). Numbers (`proofs/P1_traced_bench13_on.txt`):
  `bench 13` with MinorCorrection=100: nodes 922324,
  **reads 85378 (0.0926 per node), updates 5951 (0.00645 per node), updates
  that changed an entry 5949 (99.97 % of updates)**. With the option OFF the
  same traced build prints reads 0, updates 0, changed 0 and the known
  862329 (`proofs/P1_traced_bench13_off.txt`) — the feature is not reached
  when off. The traced binary's node count equals the untraced patched
  build's (922324), so tracing changed no search.
- **P1 key quality** (`proofs/P1_key_collision_test.txt`; harness
  `key_test.cpp` committed in the job folder — its `minor_key` body is copied
  verbatim from the patch): over the first 100,000 EPD positions and
  **26,030,935 neighbor positions** differing in exactly one minor piece
  (relocation to an empty square, or removal), **64-bit key collisions: 0**;
  collisions in the 16384-entry table index: 1,464 (0.0056 % ≈ the birthday
  expectation 26M/16384 ≈ 1587 for ANY key into a shared 16384-entry table —
  the same load the existing tables carry).
- **P2 (off = old engine)**: the patched build with the option off prints all
  four known numbers itself (312866 / 862329 / 3024920 / 4865609 —
  `step0/patched_off_*.txt`). 2000 positions (first 2000 EPD lines; per
  position `ucinewgame`, `position fen`, `go depth 9`) on the unpatched
  build and on the patched build with the option off: **one sha256 over all
  answers of each side — both files hash to
  55265dc258ebb8eac58b869f9c3e65f4912c26d3d11d9c75080b9f05919480a7
  (identical bytes: same best move, same score, same node count on all 2000
  positions)**. Smallest node count 4534 (no vacuous rows). Determinism
  control: the unpatched build re-run on the first 150 positions reproduced
  its own answers byte-identically (`proofs/P2_*` files; the driver is
  `scripts/identity_run.py`).
- **P3 (on acts)**: with MinorCorrection=100: bench 11 → 333818, bench 13 →
  922324, bench 16 → 4596576 (`proofs/P3_bench*_on.txt`) — all different
  from the known numbers.
- **P4 (sanitizers)**: the planted-fault program
  (`planted_fault.cpp`, heap-buffer-overflow write) compiled with ASan
  reports the fault and exits 1 (`proofs/P4_planted_fault_stderr.txt`) —
  the tool is proven before it is trusted. Then the ASan+UBSan build of the
  patched tree (`build_asan`, `-DFORGE_ENABLE_SANITIZERS=ON`): bench 13 with
  the option on runs clean — no error/sanitizer/runtime line in the engine
  output (`proofs/P4_asan_bench13_on.txt`, nodes 922324, same as release) —
  and 200 of the P2 positions with the option on produce 200 answers with an
  EMPTY stderr (`proofs/P4_asan_200pos.txt`, `P4_asan_200pos_stderr.txt`).
- **P5 (matches)**: FILLED AFTER MATCHES.
- **P6 (speed, honestly)**: bench 13, five runs each, median: off
  {557, 589, 615, 651, 848 ms} → median 615 ms; on {593, 605, 613, 627, 702
  ms} → median 613 ms. The medians differ by less than the run-to-run
  spread; the key's cost is below this machine's measurement resolution at
  bench 13. bench 16 nps, 10 interleaved off/on pairs, fresh process each
  (`proofs/P6_bench16_*.txt`): off mean 1,584,054 nps (min 1,185,778, max
  1,773,106); on mean 1,474,413 (min 1,218,927, max 1,582,298). The spreads
  overlap; the on-tree is also a DIFFERENT, larger tree (4,596,576 nodes vs
  3,024,920), so this is a rough figure, as the job says. Table size:
  131,072 bytes per search thread (2 sides × 16384 × 4 B).

## 5. The matches

Form as the job gives it (one exe both sides, option ON against OFF,
`proto=uci nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false`
under `-each`, no adjudication, `-concurrency 4`, fresh directory per match).

| match | cand options | seed | games | W-L-D (cand) | pair counts | fastchess Elo ± err | my Elo [95 % pair interval] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|
| C | none; cand nodes=20000 vs base nodes=10000 | 8110 | 300 | 189-24-87 | [0, 7, 25, 64, 54] | +213.35 ± 33.56 | +214.85 [+182.91, +250.39] | 0 |
| M1 | MinorCorrection=100 | 8111 | 2000 | 565-592-843 | [59, 253, 402, 228, 58] | -4.69 ± 10.49 | -4.69 [-15.19, +5.80] | 0 |
| M3 | MinorCorrection=50 | 8113 | 2000 | 580-578-842 | [60, 233, 408, 243, 56] | +0.35 ± 10.44 | +0.35 [-10.10, +10.80] | 0 |
| M2 | MinorCorrection=100 | 8112 | 2000 | 601-550-849 | [59, 218, 400, 259, 64] | +8.86 ± 10.59 | +8.86 [-1.73, +19.47] | 0 |
| M4 | MinorCorrection=50 | 8114 | 2000 | 589-558-853 | [53, 232, 412, 237, 66] | +5.39 ± 10.47 | +5.39 [-5.08, +15.86] | 0 |

Pooled figures from my script (both games files concatenated, the second
seed's rounds renumbered +1000):
- weight 100 (M1+M2): 4000 games, 2000 pairs, 0 unpaired, W-L-D 1166-1142-1692,
  score 0.5030, Elo +2.08, se 0.0055, 95 % pair interval [-5.37, +9.54];
  pair counts 0.0:118 0.25:471 0.5:802 0.75:487 1.0:122.
- weight 50 (M3+M4): 4000 games, 2000 pairs, 0 unpaired, W-L-D 1169-1136-1695,
  score 0.5041, Elo +2.87, se 0.0054, 95 % pair interval [-4.53, +10.26];
  pair counts 0.0:113 0.25:465 0.5:820 0.75:480 1.0:122.

## 6. Files of the repository I opened

- `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_glmflash4_4.md`.
- Commit `6b98f2170a3210e71beed04bbd2553972c253ed7` (exported to /tmp, outside the git work tree): `include/forge/search.hpp` (history/correction type declarations, Worker members), `src/search.cpp` (tune block, parameters table, ctor, `Worker::clear`, key helpers, `corrected_eval`, `update_correction`), `src/uci.cpp` (option advertisement and `setoption` handling). The book file: first 2000 lines read by the P2 driver from the zip downloaded from github.com/official-stockfish/books.

## 7. Stamps of every step

- 19:46:50 job file 4 fetched and read (budget start)
- ~19:49:30 pristine + working exports created under /tmp (outside the git work tree)
- 19:52:05 patched Release build finished (binary mtime); deliverable diff generated (96 lines)
- ~19:52:20 unpatched reference build finished
- 19:52:24 step 0, four lines, all pass; patched `uci` reply captured
- ~19:52:40 P3, three benches with the option on
- ~19:53:00-19:53:34 traced copy: first attempt reused the copied build directory with a stale CMake cache and produced NO traced data (discarded); rebuilt clean; P1 counters taken at 19:53:34, off-state counters right after
- 19:54:00 P4 planted-fault proof; ASan build (started ~19:53, `-j2`, alongside the P2 runs) finished ~19:54:4x; ASan bench 13 + 200 positions ~19:54:5x
- 19:54:28 P2: both 2000-position identity runs complete (started ~19:53, run in parallel); determinism re-check (150 positions, unpatched twice) ~19:54:45
- ~19:55:10 key collision test compiled and run (100,000 positions, 0.46 s)
- ~19:56:10 P6 bench 13 ×5 off/on; ~19:56:4x P6 bench 16, 10 interleaved pairs
- 19:55:37-19:57:33 C, 300 games (match-dir stamps.txt)
- 19:57:36-20:11:12 M1, 2000 games, exit 0
- 20:11:2x-20:24:51 M3, 2000 games, exit 0
- 20:24:5x-20:39:03 M2, 2000 games, exit 0
- 20:39:08-20:52:40 M4, 2000 games, exit 0 — finished before the 70-minute mark; nothing was cut in this job
- 20:53-20:58 pooled statistics, report finalized, commit, push

## 8. What I did not do

- I did not test other key designs (kings included, per-side tables like the
  non-pawn pair, Zobrist arrays instead of the multiplied bitboards) beyond
  the design choices documented in section 3; one design was built and
  measured.
- I did not test interaction with the tree's own NonPawnCorrection switch,
  nor weights other than 100 and 50.
- No SPRT, no adjudication, no book — the fixed-node form as prescribed.
- No PR was opened; nothing outside my own branch was pushed or changed.

## 9. What I am not sure about

- The pooled intervals cannot exclude small effects: weight 100 could hide
  up to ~+9.5 and weight 50 up to ~+10.3. With M1 -4.7 and M2 +8.9 on the
  SAME configuration, seed noise of about ±7 Elo is visible in the data; a
  real gain near +5 would need more games to separate from that.
- The P6 speed figure is rough by construction (different search trees,
  overlapping nps spreads); I claim only "no large slowdown is visible".
- The 1464 table-index collisions are the birthday expectation for any key
  into a 16384-entry table; I did NOT measure the existing tables' own
  collision rates to compare (they share the mask width, so I expect the
  same rate — expectation, not measurement).

## 10. A better way

- The P2 identity protocol (2000 fixed-depth positions, one process per
  build, sha256 over the answers) turned out CHEAP — about 90 seconds per
  build, and the two builds run in parallel — much cheaper than a fresh
  process per position. Worth prescribing as the standard "off = old engine"
  check for any gated feature.
- The traced-copy pattern (counters as tune-namespace globals, reset in
  `Worker::clear()`, printed by `bench`) is reusable for any "is the feature
  reached, and does it write" question; P1 answered in one bench run.
- Pitfall worth a line in future job texts: `cp -r` of an already-configured
  build tree carries a stale CMakeCache that points at the OLD directory; a
  reconfigure there fails (or worse, silently reuses the stale binary). My
  first traced run did exactly that and produced no traced data; the rule
  is `rm -rf build` in every copy before configuring.
- fastchess `-pgnout` appends by default (reported in my job-3 report); this
  job used a fresh directory per match, and the `[Event` count of every PGN
  equals its game total (checked in each evidence file's counts block).

## 11. Model name and version

I am glmflash4. The model behind this agent is GLM, trained by Z.ai; the
runtime presents it as GLM 5.3 Flash. I cannot verify a precise version
string from inside the run.
