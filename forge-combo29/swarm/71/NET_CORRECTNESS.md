# NET_CORRECTNESS — the v3 network path, audited for correctness

Six questions, each with the command that reproduces it. Scope: the v3 NNUE path only
(`forge::nnue::v3`), which had been measured for *speed* by other seats and never for
*correctness*.

Build under test: `forge-combo29/swarm/71/build/forge`, GCC 13.3, `-O3 -march=x86-64-v4`,
`-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -DFORGE_NNUE_V3_VERIFY=0`. A second build
`build_verify/forge` is identical but with `FORGE_NNUE_V3_VERIFY=1`, which makes the engine
compare every incremental evaluation against a fresh reference and `std::_Exit(3)` on a
mismatch.

Test net: regenerated from `make_v3_testnet.py` (the deterministic generator committed at
`swarm/08/v3/`), **6,309,096 bytes, FNV-1a `fdff70de72e4ca82`** — byte-identical to the net
named in the brief, verified by `cmp` in `run_all.sh`.

Reproduce everything: `./run_all.sh` (writes `out/run_all.log`).

---

## Q1. Does the incremental update ever disagree with a full refresh?

**No. 54,379 distinct positions compared, 0 mismatches.**

| fixture | sequences | plies/seq | stride | positions compared | king-key changes | acc mismatches | eval mismatches |
|---|---|---|---|---|---|---|---|
| `seq_deep.tsv` | 400 | 120 | 1 | **48,400** | 202 | **0** | 0 |
| `seq_large.tsv` | 200 | 40 | 1 | **8,200** | 7 | **0** | 0 |
| `seq_large.tsv` | 200 | 40 | 3 | 3,000 | 172 | **0** | 0 |
| `kingwalk.tsv` | 120 | 60 | 1 | **7,320** | **5,012** | **0** | 0 |
| `seq_small.tsv` | 12 | 40 | 1 | 492 | — | **0** | 0 |

**Distinct positions compared: 54,379.** The per-run counts do not add up to that, and the
difference is worth stating because it is easy to get wrong: `seq_small` is a prefix of
`seq_large`, which is a prefix of `seq_deep` (all three take the first N rows of the same
corpus with the same 40-ply prefix), so the fixtures overlap almost entirely. Measured
overlaps: `deep ∩ large = 7,761` (all of `large`), `deep ∩ small = 479` (all of `small`),
`kingwalk ∩ deep = 0`.

```
COUNT seq_deep.tsv      distinct_positions 47418
COUNT seq_large.tsv     distinct_positions  7761
COUNT seq_small.tsv     distinct_positions   479
COUNT kingwalk.tsv      distinct_positions  6961
COUNT union_distinct_positions 54379
```

47,418 + 6,961 = **54,379**, because `deep` already contains `large` and `small` entirely. The
stride-3 row re-compares plies already counted at stride 1, so it adds nothing to the union.
`count_distinct.py` computes this and fails loudly on an unparseable fixture, so the literal
cannot drift; it is wired into `run_all.sh`.

### What "compared" means

For every ply the harness (a) drives the accumulator along the same incremental path the
search uses — `prepare`, `refresh_cached` at the root, `make_valid`/`replay_ply`/`apply_changes`
after that, with `DirtyPieces` built by `nnue::dirty_from_move` exactly as `Worker::record_move`
does — and (b) computes a fresh `refresh()` from the piece placement on the same board. It then
compares:

- all `2 x 512` accumulator units, unit by unit;
- both `KingKey`s (bucket and flip) and both king squares;
- the network output `evaluate()` against `evaluate_reference()`.

A single differing unit anywhere in either perspective fails the position.

### Why the `kingwalk.tsv` row is the one that matters

`replay_ply` has two paths. When a perspective's king key is unchanged it applies the recorded
piece changes to the parent's accumulator — cheap, and what almost every node does. When the
king key **changes** (the king moved into another rank band, or crossed the mirror line) it
abandons the incremental update: it reconstructs the piece bitboards for that ply by *undoing
the later plies of the sequence* from the board at the top of the stack, then refreshes from
those pieces through the cache.

That reconstruction is where an off-by-one in the undo order would hide, and a normally-played
game almost never triggers it: the 200-sequence, 40-ply fixture produces **7** transitions in
8,200 positions. So the harness constructs the worst case instead — 120 games in which both
kings are walked aggressively with all other pieces removed, giving **5,012 transitions in
7,320 positions**, 68% of positions. It is exact on every one.

### Independent arm: the engine's own verification build

`verify_search.py` drives `build_verify/forge` over real searches. Inside
`Worker::static_evaluate_v3`, every incremental value is compared with `evaluate_reference` and
a mismatch terminates the process with status 3 and a message naming the ply, both values and
the FEN.

| run | positions | budget | nodes | mismatches | abnormal exits |
|---|---|---|---|---|---|
| `verify200_d12.json` | 200 | `depth 12` | 37,475,198 | **0** | 0 |
| `verify_deep800.json` | 800 | `depth 13` | (see `out/`) | **0 so far** | 0 |

This arm is worth having separately because it exercises the *search's* control flow — its ply
stack, its null-move frames, its TT cutoffs — rather than a harness's idea of a move sequence.

### It is a harness bug, not an engine bug, that the first run found

The first sweep reported `mismatched 960` over `compared 492`. More failures than comparisons is
impossible, and that is what exposed the fault: `dirty_of(j)` in my harness indexed the frame by
ply directly, while the search passes a **stack index** (`ply + 4`) and expects the change list
that led to *that* stack entry, i.e. frame `j - 4`. With the offset wrong, every replay applied
a neighbouring ply's changes. After the fix the same fixture is clean and the reported first
mismatch (ply 1) disappears.

Recorded here because it changes how to read the zero: a harness that produced 960 false
failures is a harness that can distinguish a wrong answer from a right one.

---

## Q2. Is the output deterministic and symmetric?

**Deterministic: yes. Colour-symmetric: yes.**

| set | pairs compared | asymmetric | max |delta| |
|---|---|---|---|
| 1,000 positions from random legal games (seed 71) | 1,000 | **0** | 0 |
| 200 committed opening positions (`OG200.fens`) | 200 | **0** | 0 |
| 12 hand-built stress FENs (castling both sides, ep, kings on files a/h/e) | 12 | **0** | 0 |

The mirror transforms placement (rank flip + colour swap), side to move, castling rights and the
en-passant square, so a correct HalfKA net with `FlagMirror` set must return the identical
integer. Comparing integers — not floats, not scores rounded to cp — means a single unit of
asymmetry would show.

Determinism is implied by the same measurement being repeatable across runs and by the
accumulator identity in Q1: the incremental path and the reference path are two independent
computations that agree exactly, and both are pure integer arithmetic on the same weights.

---

## Q3. Does the net handle a bare king gracefully?

**Yes.** No crash, no wild score.

```
4k3/8/8/8/8/8/8/4K3 w - - 0 1   eval     23
4k3/8/8/8/8/8/8/4K3 b - - 0 1   eval     23
8/8/8/8/8/8/8/K6k w - - 0 1     eval     68
k7/8/8/8/8/8/8/7K b - - 0 1     eval   -135
4k3/8/8/8/8/8/8/3qK3 w - - 0 1  eval    -57
4k3/8/8/8/8/8/8/3QK3 b - - 0 1  eval   -127
```

All six are within ±200 cp of zero on a network whose weights are random noise, which is the
expected behaviour of a net with no material signal: the bias and the two king features
dominate and nothing overflows. `BARE compared 6 refused 0 wild 0`, threshold ±2000 cp.

The same position with the side to move flipped (`4k3/.../4K3 w` vs `b`) returns the same value,
which is the K-vs-K symmetry the net should have.

---

## Q4. What happens if the net file is truncated or corrupted?

**It refuses to load, and says why. Nothing loads and produces garbage.**

| case | bytes | verdict | message |
|---|---|---|---|
| zero-length | 0 | **refused** | `file too small for a v3 header` |
| header only | 192 | **refused** | `file too small for a v3 header` |
| truncated to half | 3,154,548 | **refused** | `file size 3154548 != expected 6309096` |
| truncated by 1 byte | 6,309,095 | **refused** | `file size 6309095 != expected 6309096` |
| extended by 1 byte | 6,309,097 | **refused** | `file size 6309097 != expected 6309096` |
| bad magic | 6,309,096 | **refused** | `bad magic (expected FORGENN3)` |
| bit flip deep in `w1` | 6,309,096 | **refused** | `checksum mismatch` |
| bit flip in `b1` | 6,309,096 | **refused** | `checksum mismatch` |
| bit flip in `eval_scale` | 6,309,096 | **refused** | `checksum mismatch` |
| bit flip in stored checksum | 6,309,096 | **refused** | `checksum mismatch` |
| bit flip + **recomputed** checksum | 6,309,096 | **accepted** | loads, checksum `a1ab778dfa69b9f9` |
| header claims hidden 1056 | 6,309,096 | **refused** | `hidden must be a multiple of 32 in 32..1024` |

`DAMAGE summary cases 12 accidental_damage_refused 11 adversarial_accepted 1 violations 0`.

**The single acceptance is correct behaviour, not a gap.** The loader verifies an FNV-1a 64
checksum over every preceding byte. A file whose weights were altered *and* whose checksum was
recomputed is self-consistent: no checksum scheme can reject it, because the attacker had the
same information the loader does. FNV-1a is there to catch damaged storage and truncated
transfers — which it does perfectly, 11 for 11 including a single-bit flip anywhere in the
6.3 MB payload. Deliberate re-checksummed corruption is outside what this format claims to
detect, and the report does not claim otherwise.

Structural validation is separate from the checksum and does real work: magic, version,
`header_bytes`, `inputs`, `hidden` (multiple of 32 in 32..1024), `king_buckets` 1..32,
`output_buckets` 1..16, unknown flag bits, `qa`/`qb` fixed at 255/64, `eval_scale` 1..10000,
47 reserved header bytes zero, exact file size, king/output bucket map entries in range,
`|w2| <= 127`, and `max|b1| + 32 * max|w1| <= 32767` (the accumulator-overflow bound the
kernels rely on).

---

## Q5. Is the net used when it should not be?

**No silent use. One protocol defect on the fail-loud path.**

| check | result |
|---|---|
| net genuinely in use (`NNUEArchFile` then `NNUEArch true`) | bench 11 **312,866 → 965,454** nodes |
| file loaded but `NNUEArch` left false | bench 11 **312,866 → 312,866** — completely inert |
| damaged net + `NNUEArch true` | `ERROR NNUE v3: ...`, **exit 2, 0 info-depth lines, 0 bestmove** |
| `NNUEArch true` with no file at all | `ERROR NNUE v3: NNUEArch is on but no v3 network is loaded`, **exit 2, 0 info-depth lines** |

The inert case is the one that matters for the question as asked: loading a file with
`NNUEArchFile` alone changes nothing at all — identical node counts, not merely a similar
benchmark. There is no path where the file is loaded and quietly used.

**The defect:** on the fail-loud path the engine terminates with status 2 mid-protocol. It
answers the `setoption`/`isready` that *preceded* the request, prints the error, and then exits
without answering the `isready` that follows or emitting a `bestmove` for a subsequent `go`. A
GUI that sent `NNUEArch true` and waited for `readyok` hangs forever. The intent — never fall
back silently to the hand-crafted eval — is right and is met; the mechanism kills the process
where a `bestmove 0000` or a persistent error state would be recoverable.

This is the only defect the audit found, and it is a UCI-protocol defect, not an evaluation one.

### The FEN diagnostic, as corrected

The `info string invalid FEN` message appears in **both** possible places, and which one you see
depends on whether `isready` separates `position` from `go`. The harness scans both, always.

| path | in `position` reply | in `go` output before `info depth` |
|---|---|---|
| `position` → `isready` → `go` | **yes** | no |
| `position` → `go` | no | **yes** |

Three genuinely invalid FENs × both paths = 6 runs, 6/6 seen. Twelve valid FENs × both paths =
12 runs, **0 false positives**. This is the property that makes the Q1 sweep trustworthy: a
refused FEN would otherwise make the engine search the previous board, and every mismatch would
be a fixture bug.

---

## Q6. Does the 200-opening identity baseline reproduce?

**No — 29,791,805 against the documented 27,944,084. The cause is not the net.**

| quantity | measured | documented | match |
|---|---|---|---|
| node sum, 200 positions, depth 12 | **29,791,805** | 27,944,084 | **no (+6.6%)** |
| row 1 nodes | 62,951 | 110,540 | no |
| eval, startpos | **968** | 968 | **yes** |
| eval, Italian `r1bqkbnr/...` | **1176** | 1176 | **yes** |
| eval, rook endgame `8/5pk1/...` | **31** | 31 | **yes** |
| bench 11, no net, no options | **312,866** | 312,866 | **yes** |
| bench 11, test net, no options | **965,454** | 965,454 | **yes** |
| bench 11, PC20, no net | 242,804 | 278,024 | no |
| bench 11, PC20 + net | 471,702 | 625,258 | no |
| bench 11, S14, no net | **242,796** | 242,796 | **yes** |
| bench 13, S14, no net | **656,517** | 656,517 | **yes** |

The pattern is unambiguous: everything that does **not** involve the PC20 option set reproduces
exactly, including the three eval values to the digit and the net's own bench row. Everything
that does involve PC20 is off.

**Cause: four of PC20's twenty options do not exist on this branch.** Sending all twenty and
checking each reply:

```
PC20_SIZE 20
PC20_UNKNOWN_COUNT 4
PC20_UNKNOWN CuckooRep HistRework TtPruneV2 CorrHistV2
```

Each returns `info string unknown option`. `grep` over `src/` and `include/` finds no reference
to any of the four, so they are not merely unadvertised — the behaviour is absent. PC20 is
therefore **not expressible** on combo29 as a 20-option configuration, and a harness that sends
all twenty while ignoring the `unknown option` replies is silently running a 16-option
configuration.

The control that confirms the options which *do* exist are working: the 14-option S14 set
reproduces the documented S14 figures **exactly** (242,796 and 656,517).

**Consequence for anyone gating on the number:** 27,944,084 cannot be produced on this branch
under the stated conditions. A patch required to "reproduce 27,944,084 exactly" will fail for a
reason unrelated to the patch. Either the baseline is restated against the 16 options combo29
actually has, or it is measured on a branch where PC20 exists.

---

## Method notes

- **Threads 1**, `Hash 16`, fixed `depth` or `nodes` budgets throughout. No `go infinite`.
- Every search awaited to `bestmove` under a wall-clock timeout; a timeout is a reported error,
  never a silently skipped position.
- FENs validated with python-chess **before** use; the engine's own refusal count is printed and
  is 0 on every fixture.
- Denominators printed as literals, never computed on the fly and never rounded.
- Each check demonstrated to fail before its clean result was accepted: injected accumulator
  corruption → `acc_mismatched 492`; patched `replay_ply` → verify build exits `rc=3` with
  `incremental 1253 reference 1344`.
