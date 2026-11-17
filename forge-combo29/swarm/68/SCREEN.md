# SCREEN — the recipe

A re-runnable procedure for screening mate labels, and the reasoning for each
step. Every command is copy-pasteable from `forge-combo29/swarm/68/tools`.

## Step 0 — build

```bash
cd forge-combo29/swarm/68/tools
g++ -O2 -std=c++20 -o mateverify mateverify.cpp
```

The engine under audit:

```bash
cd forge-combo29 && CXX=g++ cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j4
```

> **Toolchain trap.** This VM's default `c++` is Clang 18 and its link fails with
> `cannot find -lstdc++`. Set `CXX=g++` or the build stops at compiler detection.

## Step 1 — establish ground truth before trusting any verdict

```bash
python3 retrograde.py all
```

Writes `kqvk_dtm.json` (345,404 resolved) and `krvk_dtm.json` (376,868
resolved), and **asserts** the published bounds:

- KQvK max DTM **19 plies = 10 moves**
- KRvK max DTM **31 plies = 16 moves**

The bounds are in different units in the brief; both are asserted explicitly.
If either assertion fires, the table is wrong and nothing downstream is usable —
that is the point of the assertion, and it caught a real bug in the first
version of this script.

## Step 2 — validate move generation

```bash
python3 perft_check.py
```

Expect **27/27**. Two independent references: the published perft table and
python-chess. A verifier whose move generation is wrong produces confident wrong
distances, so this is not optional.

## Step 3 — prove the verifier can fail

```bash
python3 dtm_validate.py
```

Three claims with separate denominators:
1. true distance → `CORRECT`;
2. wrong distance (±1, ±2) → `WRONG` with the **correct direction**;
3. negative control: a side-to-move-assumes-attacker checker must disagree, or
   the real verifier's agreement is structurally guaranteed rather than earned.

**Do not run the corpus until this passes.** Two seats reported wrong mate
numbers tonight; a verifier that has not failed on a planted error makes
"N wrong" uninterpretable.

## Step 4 — build a corpus that can contain mate labels

```bash
python3 build_corpus.py 400 corpus.fen 6801
```

Filter: material difference ≥ 5 and ≤ 12 pieces. Rationale: mate labels appear
in sparse, lopsided positions (19% hit rate here) and essentially never in
full-material middlegames (0/73 in the prior measurement). This is a **corpus
filter, not a label screen** — it selects candidates, and the verifier decides.

## Step 5 — collect engine mate scores

```bash
python3 collect_mates.py "$(pwd)/../../build/forge" corpus.fen 12 1 mates_mpv1_d12.jsonl 30
python3 collect_mates.py "$(pwd)/../../build/forge" corpus.fen 12 3 mates_mpv3_d12.jsonl 30
```

The harness enforces, rather than assumes:

| rule | how |
|---|---|
| Threads 1 | `setoption name Threads value 1`, recorded per position |
| MultiPV explicit | `setoption name MultiPV value N`, recorded per position |
| bounded `go` | always `go depth D`; never `infinite`, so no `stop` is ever needed |
| `bestmove` awaited | per-position wall-clock timeout; a timeout kills and restarts the engine so the next position cannot inherit a runaway search |
| FEN validated | python-chess `is_valid()` before sending; rejected FENs are counted and dropped, never sent |
| `invalid FEN` scanned in BOTH places | the `position` reply **and** the `go` output before the first `info depth` |

The last row is the one that corrupts a corpus silently. The diagnostic does not
appear in the search output, and a harness that inserts `isready` between
`position` and `go` swallows it into a reply it then discards. A refused
position leaves the engine on the **previous** board, so its mate score belongs
to a different position — and the verifier, correctly, reports that score as
wrong for the FEN that was sent. That is a fabricated wrong-mate case. Measured
here: **0/400 refused**, so the rate below is about the engine, not the fixtures.

## Step 6 — grade

```bash
# |N| <= 5 labels are the ones the verifier finishes quickly
python3 - <<'PY' > all_small.tsv
import json
for m in (1,2,3):
    for r in map(json.loads, open(f'mates_mpv{m}_d12.jsonl')):
        by = {x['multipv']: x for x in r['info'] if x.get('score_type')=='mate'}
        for k, rec in by.items():
            if abs(rec['score_value']) <= 5:
                print(f"{r['fen']}\t{rec['score_value']}\tmpv{m}:line{k}")
PY

# shard across cores: the verifier is stateless per line, so this is safe
for i in 0 1 2 3; do awk -v i=$i 'NR%4==i' all_small.tsv > /tmp/s$i.tsv; done
for i in 0 1 2 3; do ./mateverify --batch < /tmp/s$i.tsv > /tmp/s$i.out & done; wait
cat /tmp/s*.out > graded.jsonl
```

Report, from the same lines and with separate denominators:

- CORRECT / WRONG / INCONCLUSIVE;
- direction of every WRONG (`over` = label larger than truth);
- **the PV-length filter's verdict on the same lines**, so its blind spot is
  measured rather than asserted: how many lines **pass** the length filter and
  are still WRONG.

## Step 7 — read the verdicts correctly

- `CORRECT` means the exact DTM equals what the label implies. It does **not**
  mean the PV is the DTM line.
- `INCONCLUSIVE` means the node/time cap was hit. It is **not** a wrong label.
  Grading a corpus with inconclusives counted as failures inflates the rate.
- The **attacker must come from the sign of the score**, and the verdict prints
  which one it chose (`attacker_from: sign_of_exact_score`). For any negative
  `mate N` the attacker is the side **not** to move; a checker that assumes
  otherwise reports true claims as false.

## What this screen cannot do

- **It is slow**: 0.553 labels/s single-core, ~1.2/s on 4 cores. Fine as a batch
  job for a sample; not an inline transform for a whole corpus.
- **It does not scale to populated middlegames.** Board 222 (12 pieces, pawns)
  did not finish in 15 minutes. It is a sparse-endgame tool.
- **A cp score cannot be screened by it at all** — there is no mate distance in a
  cp score to check. Sparsity/imbalance selects positions likely to *have* mate
  labels; that is corpus selection, not label quality.

## Known traps, all encountered here

| trap | symptom | fix |
|---|---|---|
| default `c++` is Clang, no libstdc++ | cmake: compiler "is not broken" but link fails | `CXX=g++` |
| unmake restores the promoted piece | perft 2/7, everything after a promotion is corrupt | restore a PAWN when `promo` is set |
| TT mate score reused across plies | mate 12 reported at horizon 9 | clear TT per horizon; accept a cached mate only if `cachedDistance <= depth` |
| retrograde drops capture-escapes | KQvK max 6 moves, 0 draws | model piece-capture → KvK as a never-resolving draw |
| brief's bounds in mixed units | KQvK "10 plies" | assert 19 plies AND 10 moves |
| `invalid FEN` read from one stream | silent wrong-position scores | scan `position` reply **and** `go` output |
| side to move assumed to be the attacker | true negative-mate claims reported false | resolve from the sign, print the choice |
