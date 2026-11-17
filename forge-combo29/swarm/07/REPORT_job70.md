# REPORT job70 — S-F35/S-F37 CONFIRMED, and a self-inflicted false refutation caught

Date: 2026-11-17 (see `job70/stamps.txt` for the `date -u` reads)
Seat 07. Branch `for-fable-and-opus/swarm-07`.

## What was asked

Replicate seat 16's S-F35 / S-F37: "the colour-mirror asymmetry of node counts is
COMPLETELY explained by move-generation order." Their claim: stock **34/120** mirror
pairs equal, canonicalised **120/120**.

## What happened — read this part before the result

My first attempt at this replication produced **34/120 vs 34/120**: no improvement,
86 residue cases, stock and canon giving *identical* node pairs case for case. I was
one step from writing that up as a REFUTATION.

The patch was inert in my build. `EXPERIMENT_mirror_order.patch.txt` wraps its work in

```c
#ifndef FORGE_EXPERIMENT_MIRROR_ORDER
#define FORGE_EXPERIMENT_MIRROR_ORDER 0
#endif
```

so applying the patch and building it compiles the **stock** code path. My `/tmp/mirord`
build had the canonicalisation `#if`-ed out. I had measured a stock binary against a
stock binary, and the 34/34 identity was the tell I almost read as evidence *for* my
refutation instead of evidence *against* my build.

Rebuilt with `-DFORGE_EXPERIMENT_MIRROR_ORDER=1` (confirmed present in
`build2/CMakeFiles/forge.dir/flags.make`). The build is provably live because the
honesty pins moved:

| arm | bench 11 | bench 13 | bench 16 | perft 5 |
|---|---|---|---|---|
| stock PC r15 | 312866 | 862329 | 3024920 | 4865609 |
| canonicalised (`775fb0f6…`) | **376974** | **894336** | **3110320** | 4865609 |

Perft unchanged (node-generation legality untouched), bench moved in all three regimes
— a move-order change with no legality change. That is exactly the signature the patch
should have. `job70/raw/pc_pins.json` is the run; the 3 "MISMATCH" lines there are the
**expected** outcome and are the proof of a live build, not a failure.

## Result on a live build

```
STOCK PC r15/PC20 : 34/120 mirror pairs equal
CANONICALISED     : 120/120 mirror pairs equal
canon residue     : 0
```

`job70/raw/mirror_order_check.json` (residue list empty). 60 set-G positions × 2 depths
= 120 mirror pairs, same protocol seat 16 used, my own harness, my own build.

**S-F35 / S-F37 stand.** Independently reproduced to the digit, including the baseline.
The colour-mirror asymmetry in node counts is entirely a move-generation-order artefact;
canonicalise the order and it vanishes. Nothing about search itself is asymmetric.

## The rule this cost me, and it is not a small one

**A patch that ships its own switch defaulted to 0 is not applied by building it.**
Applying cleanly and compiling cleanly proves nothing about whether the code is in the
binary. Before reporting that a patch "did nothing," find the observable that the code
path must move and confirm it moved — here, bench nodes. `perft` was the wrong check:
it is exactly the thing a move-order patch leaves alone, so it would have passed on the
inert build and reassured me.

This is the mirror of the standing rule "if a defect should vanish with more budget and
it does not, suspect the checker." The checker was mine: not the measurement harness,
but the build. A refutation is a claim about someone else's work, and it carries the
same evidence burden as a confirmation — I nearly filed one on evidence that was
silent about the thing under test.

Corollary worth keeping: **an exact match to someone's baseline is not neutral.** Mine
matched their 34/120 precisely, which felt like corroboration of a shared measurement and
was in fact the fingerprint of not having changed anything.

## Files

- `job70/raw/mirror_order_check.json` — 34/120 vs 120/120, empty residue
- `job70/raw/pc_pins.json` — the live-build evidence (bench 11 = 376974)
- `job70/run.log` — the run
- `job70/run.log.INERT_ATTEMPT.txt` — my failed first attempt, kept deliberately: the
  34/34 line is the mistake, and it stays on the record
- `job70/stamps.txt`
- binary `775fb0f61e6ce73f602ce6635255e93c09f6c0764f018289c849e9e80db016e0
  /tmp/mirord/build2/forge`
