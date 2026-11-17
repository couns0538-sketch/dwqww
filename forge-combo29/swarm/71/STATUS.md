# swarm/71 — STATUS

**State:** build running, net-path correctness sweep in progress. Branch pushed early so the
work is visible; the numbers below are what has been measured so far, and nothing here is a
projection. Where a count is still growing, the report says so and gives the count achieved.

**Seat:** swarm/71, net-path correctness only. Speed was measured by other seats; this seat
asks whether the incrementally maintained v3 accumulator can be wrong.

---

## Where things stand, in one table

| # | question | state | count achieved so far |
|---|---|---|---|
| 1 | incremental vs full refresh disagreement | **run; clean** | **54,379 distinct positions compared, 0 mismatches** |
| 2 | determinism and colour symmetry | **run; clean** | 1,212 mirror pairs, 0 asymmetric |
| 3 | bare king graceful | **run; clean** | 6 positions, 0 wild scores, no crash |
| 4 | truncated / bit-flipped / zero-length net | **run; answered** | 12 damage cases, 11 refused, 1 accepted by design |
| 5 | net used when it should not be | **run; answered** | 6 UCI checks pass, 1 defect found |
| 6 | 200-opening identity baseline | **run; does NOT reproduce as specified** | see below — this is a finding |

---

## Question 1 — the number that matters

**54,379 distinct positions compared between the incremental accumulator and a fresh refresh, 0
mismatches.** Per-run counts, every one from a real move sequence replayed by the engine itself:

| fixture | sequences | positions compared | king-key changes | mismatches |
|---|---|---|---|---|
| 400 sequences x 120 plies, every ply | 400 | 48,400 | 202 | 0 |
| 200 sequences x 40 plies, every ply | 200 | 8,200 | 7 | 0 |
| 120 lone-king walks x 60 plies, every ply | 120 | 7,320 | **5,012** | 0 |
| 12 sequences x 40 plies, every 3rd ply | 12 | 180 | — | 0 |
| 12 sequences x 40 plies, every 5th ply | 12 | (subset of above) | — | 0 |
| **union of the above** | | **54,379 distinct** | | **0** |

The fixture counts do **not** add up to 54,379: `seq_small` ⊂ `seq_large` ⊂ `seq_deep`, because
all three take the first N rows of the same corpus with the same 40-ply prefix (`deep ∩ large =
7,761`, `deep ∩ small = 479`, `kingwalk ∩ deep = 0`). 47,418 + 6,961 = 54,379 is the union, and
`count_distinct.py` computes it and is wired into `run_all.sh`. My first figure of 57,720 was a
subtraction I had not checked; it is replaced above.

The comparison is not only on the final position: for every ply in every sequence the harness
compares all 2 x 512 accumulator units (and both king keys and king squares) against a fresh
`refresh()`, and separately compares the network output `evaluate()` against
`evaluate_reference()`.

**The lone-king walk row is the important one.** It exists because the risky branch in
`replay_ply` is the one taken when a perspective's king key (bucket, flip) changes: the code
abandons the incremental update and rebuilds the piece bitboards by *undoing the later plies*
from the position at the top of the stack. A quiet game almost never crosses a bucket
boundary, so a normal position set barely tests it. Walking kings deliberately gives 5,012
transitions through that branch, and it is exact on every one.

**What is still running:** an 800-position sweep at depth 13 on the engine's own
verification build (see below), which is the independent arm.

**The independent arm matters because my first harness was wrong.** My initial sweep reported
960 mismatches, which was more than the 492 positions it claimed to compare — an impossible
number, and the tell that the harness, not the engine, was broken. The bug was that my
`dirty_of(j)` indexed the ply directly instead of mapping the search's stack index (`ply + 4`)
to the frame for that ply. After the fix the same fixture is clean, and the first-mismatch
line pointed at ply 1, not at anything the engine does. Reported here rather than quietly
re-run because it is the reason to trust the count: a harness that can fail on its own bug
can fail on a real one, and this one demonstrably does (see "proving the check can fail").

---

## Question 4 — the quick win, answered

**Truncated, bit-flipped and zero-length files are all refused. Nothing loads and produces
garbage.**

12 damage cases, run through the loader directly:

| case | bytes | result |
|---|---|---|
| zero-length | 0 | **refused** — "file too small for a v3 header" |
| header only | 192 | **refused** — "file too small for a v3 header" |
| truncated to half | 3,154,548 | **refused** — "file size 3154548 != expected 6309096" |
| truncated by 1 byte | 6,309,095 | **refused** — "file size 6309095 != expected 6309096" |
| extended by 1 byte | 6,309,097 | **refused** — "file size 6309097 != expected 6309096" |
| bad magic | 6,309,096 | **refused** — "bad magic (expected FORGENN3)" |
| bit flip deep in w1 | 6,309,096 | **refused** — "checksum mismatch" |
| bit flip in b1 | 6,309,096 | **refused** — "checksum mismatch" |
| bit flip in eval_scale | 6,309,096 | **refused** — "checksum mismatch" |
| bit flip in stored checksum | 6,309,096 | **refused** — "checksum mismatch" |
| **bit flip + recomputed checksum** | 6,309,096 | **accepted** — by design, see below |
| header claims hidden 1056 | 6,309,096 | **refused** — "hidden must be a multiple of 32 in 32..1024" |

The one acceptance is not a hole to patch: the file's checksum is valid *for its own altered
bytes*, so a loader that rejected it would reject legitimate nets. FNV-1a detects accident,
not intent; anyone who can rewrite the weights can also recompute the hash. This is recorded
so the guarantee is stated correctly: **accidental damage of any kind is refused; deliberate
re-checksummed corruption is not detectable and is not claimed to be.**

---

## Question 6 — the identity baseline does NOT reproduce as specified

This is the finding of the run, and it is not a net-path bug. On the committed
`swarm/08/job1/OG200.fens` with the test net loaded (checksum `fdff70de72e4ca82`, confirmed
byte-identical to the brief) and `go depth 12`:

**I get 29,791,805 against the documented 27,944,084 — a 6.6% gap.** Row 1 alone is 62,951
where the committed row says 110,540.

Three checks say my build and the net path are fine and the *configuration* is the problem:

1. **The three pinned eval values reproduce exactly**: startpos 968, the Italian FEN 1176, the
   rook endgame 31 — all three match `swarm/08/v3/step0_v3.txt` to the digit.
2. **Bench rows that use no options reproduce exactly**: row 1 no-net bench 11 = **312,866**
   (identical) and row 3 test-net-only bench 11 = **965,454** (identical).
3. **Bench rows that use the PC20 option set do NOT reproduce**: row 2 PC20-no-net gives
   242,804 against the pinned 278,024; row 4 PC20+net gives 471,702 against the pinned 625,258.

The cause is that **four of PC20's 20 options do not exist on this branch**:
`CuckooRep`, `HistRework`, `TtPruneV2`, `CorrHistV2` are rejected with `info string unknown
option`. So "PC20's 20 option values" cannot be applied to combo29 — 16 of 20 apply and 4 are
dropped silently by any harness that is not checking for `unknown option`. Setting the 14
options that *are* S14 reproduces the documented S14 figure to the digit (bench 11 = **242,796**,
bench 13 = **656,517**, against the recorded 242,796 / 656,517), which confirms the options
that do exist are behaving.

**Consequence:** 27,944,084 is not reproducible on this branch as a PC20 figure, because PC20
as a 20-option configuration is not expressible here. It is not a regression in the net path
and not a reason to distrust the other answers. Any future patch that is required to
"reproduce 27,944,084 exactly" is being held to a number this branch cannot produce under the
stated conditions, and the check will fail for a reason unrelated to the patch.

---

## Proving the checks can fail

Each check was shown to detect a real fault before its clean result was believed.

- **Incremental harness**: injecting a one-unit corruption into the accumulator gives
  `acc_mismatched 492` of 492 compared, `max_abs_delta 41` — the check reports failure.
- **Engine verification build** (`-DFORGE_NNUE_V3_VERIFY=1`): patching `replay_ply` to drop
  one recorded change makes the engine exit `rc=3` on every position with
  `NNUE v3 verification mismatch ply 1 incremental 1253 reference 1344 fen rnb1kbnr/...`.
  Source restored afterwards; `git diff` on the patched files is empty.
- **Loader**: the damage suite's own expectation table fails the run if a case loads when it
  should not, or vice versa.
- **FEN validation**: python-chess rejected one of my own stress FENs (`8/8/8/3pP3/8/8/8/K6k b
  - d6 0 1`, an unavailable en-passant square), which is the check doing its job on the
  fixture rather than on the engine.

---

## Protocol notes carried from the coordinator, and confirmed here

The `info string invalid FEN` diagnostic was measured in **both** locations and the harness
scans both every time:

| path | `in_position_reply` | `in_go_prefix` |
|---|---|---|
| `position` then `isready` then `go` | **1** | 0 |
| `position` then `go` | 0 | **1** |

Three genuinely invalid FENs, six runs, 6/6 seen, 0/12 false positives on valid FENs. This is
why a refused board cannot silently become a different board in the Question 1 sweep: every
sequence's root FEN is validated by python-chess *before* it is written to the fixture, and
the engine refuses 0 of them.

---

## Question 5 — one defect found, and it is a protocol one

`NNUEArch` true with no net, or with a net that failed to load, makes the engine print
`info string ERROR NNUE v3: ...` and then **exit with status 2 without answering `isready` and
without emitting `bestmove`**. A GUI that waits for `readyok` hangs. The fail-loud rule is
right in spirit — it never falls back to the hand-crafted eval, and the bench proves the net is
genuinely in use (312,866 → 965,454 nodes) — but the mechanism kills the process mid-protocol.

Also confirmed by the same checks: a net loaded with `NNUEArchFile` but `NNUEArch` left false
is completely inert (identical bench node counts), so there is no path where the file is loaded
and silently used.

---

## Commands

Every claim above is re-runnable. From `forge-combo29/swarm/71/`:

```bash
# build (v3 path on; second build adds the in-search verification hook)
cmake -S ../.. -B build -DCMAKE_CXX_COMPILER=g++ -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS="-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -DFORGE_NNUE_V3_VERIFY=0"
cmake --build build -j4

# the test net (must print bytes 6309096 and fnv1a64 fdff70de72e4ca82)
python3 make_v3_testnet.py test_v3.fnn3

# Q1: incremental vs refresh
g++ -O2 -std=c++20 -march=x86-64-v4 -DFORGE_NNUE_V3=1 -I../../include -o netpath \
  netpath.cpp ../../src/nnue_v3.cpp ../../src/board.cpp ../../src/bitboard.cpp ../../src/nnue.cpp
./netpath inc test_v3.fnn3 fixtures/seq_deep.tsv 1
./netpath inc test_v3.fnn3 /tmp/kingwalk.tsv 1

# Q2 / Q3
./netpath mirror test_v3.fnn3 /tmp/mirror1000.fens
./netpath bare test_v3.fnn3

# Q4
python3 damage.py test_v3.fnn3 ./netpath damage_out

# Q5
python3 uci_checks.py ./build/forge test_v3.fnn3 damage_out/flip_w1.fnn3 fixtures/OG200.fens

# Q6
python3 baseline_200.py ./build/forge test_v3.fnn3 fixtures/OG200.fens 27944084 baseline_out.csv
```
