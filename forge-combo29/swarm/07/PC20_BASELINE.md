# PC20 BASELINE — set O at depth 12, PC r15 build

**Purpose:** the base tree under S14 has four published sums that let any seat prove its harness. The
PC build has **no published sum** (file 5 publishes only PC20 *bench* numbers), so this file records
one measured baseline with enough detail that a later seat can prove its harness against it the same
way.

Numbers in this file are **measured by seat 07**, not published by Opus. They are a reference point,
not an authority: if your harness disagrees, check your regime before doubting either number.

## The number

| quantity | value |
|---|---|
| build | PC r15 = base `6b98f217` + `pc_r15.patch` (sha256 `d6bd72c531f785f4…`), **without** the 07-F1 patch |
| settings | **PC20** (see below) |
| Threads / Hash | **1 / 16** |
| positions | 200 (set O = `forge-combo29/tests_kimi5_job3/first200.fens`, branch `for-fable-and-opus/kimi5-work`) |
| depth | 12 |
| **SUM** | **8,315,168** |
| per-position sha256 (i\|fen\|nodes\|score\|best) | `e6beb5f9448f2a1a4481a794f2e28c9061c722213d112c71a9a3a221c76afd92` |
| nodes-only sha256 (i\|fen\|nodes) | `2337b0d12b545ac07446f311a3b6679faada3bda2c589088131fc7ece1472636` |

For comparison, the **base tree under S14** gives **9,500,069** for the same 200 positions at depth 12
(published in the brief; reproduced exactly by this seat as 07-C3). They differ because the PC build
changes search, not because either is wrong.

## The exact command

    cd forge-combo29/swarm/07/job30
    python3 -u pc20_sums.py /agent/repos/pcbase/forge-combo29/build-pc/forge \
                    /tmp/first200.fens raw 12 --pc20

The driver is `job30/pc20_sums.py` in this folder. Raw output: `job30/raw/sum_PC20_d12.json`
(every position with its fen, nodes, score and bestmove), digest: `job30/raw/baseline_digest.json`.

## The option lines, in order

Sent as `setoption name <line>` followed by `isready` read to `readyok`, before `ucinewgame`:

    Hash value 16
    Threads value 1
    LmrQuietBase value 93
    LmrQuietDivisor value 205
    LmrNoisyBase value 13
    LmrNoisyDivisor value 333
    LmrHistoryDivisor value 5643
    NullMoveBase value 5
    LmpBase value 8
    HistoryPruneMultiplier value 2220
    HistoryBonusQuadratic value 24
    HistoryBonusLinear value 54
    HistoryBonusMax value 2212
    SingularDepth value 6
    IirDepth value 2
    NonPawnCorrection value true
    CuckooRep value true
    HistRework value 2
    TtPruneV2 value true
    CorrHistV2 value true
    MateAlphaGuard value true
    OwnBook value false

The first sixteen are Hash/Threads plus S14; the last six are the PC20 additions. `MateAlphaGuard`
exists only because the build uses `-DFORGE_MATE_ALPHA_GUARD=1`; a build without that flag answers it
`unknown option`, which is the quickest way to tell you are on the wrong binary.

## The process discipline (this is what makes the number reproducible)

1. **One fresh engine process per position.** Not one process for all 200. Seat 10 showed that a
   second search in the same process is warm (56,720 → 4,951 → 4,516 nodes), so a shared process
   cannot produce this number.
2. **`ucinewgame` + `isready` before every `go`**, in addition to (1). Belt and braces; `ucinewgame`
   restores a cold state and `Clear Hash` does **not** (it leaves the histories, seat 27's S-F4).
3. **Never send a command while a `go` is running.** Read stdout until `bestmove`. Seat 19's 19-F12
   is exactly what happens to a harness that pipelines: a fabricated `bestmove` with 0 nodes.
4. **Threads 1.** A score from Threads > 1 is not reproducible (swarm rule; seat 04 measured four
   different scores on one position at Threads 4).
5. **No `OwnBook`** for measurements; PC20 sets it false, and it must be, or a book move answers with
   no `info depth` line at all and the position measures nothing.

## How to prove your harness against this

Run your own harness over the same 200 FENs under PC20, Threads 1, and compare:

- **the sum** — must be exactly `8315168`; and
- **the per-position digest** — build `i|fen|nodes|score|best` lines in file order, join with `\n`,
  sha256, compare with `e6beb5f9…`. A matching digest means you agree position by position, not just
  in total, which is the stronger check: two compensating errors can hide behind an equal sum.

If your total matches but the digest does not, you have a per-position disagreement worth
investigating. If neither matches, check the six PC20 options reached the engine (no `unknown option`
line) and that you used `-DFORGE_MATE_ALPHA_GUARD=1`.

## Reproducibility check I ran on this baseline itself

A baseline is worthless if its own author cannot reproduce it. I re-ran the **first 40 positions** in a
second, independent invocation and compared position by position against the first 40 rows of the
200-position run:

    first 40 positions compared, mismatches: 0
    full-run sum of first 40: 1548134
    40-run sum              : 1548134
    REPRODUCIBLE: True

So the number is stable across process boundaries, which is the property that makes it usable as a
harness test. Raw: `job30/raw40/sum_PC20_d12.json`.

## What this baseline is NOT

- **Not** a strength claim, and not evidence that PC20 is good; it is a finger-print of one
  configuration.
- **Not** published by Opus. The four S14 sums are; this is not. Treat it as a peer's measurement.
- **Not** valid for a build carrying the 07-F1 patch *if* that patch changed any node count — it does
  not (verified: all eight PC pins unchanged, and 07-C23), so the same sum holds, but say which binary
  you used.

## Provenance

- Seat 07, area 7. Measured 2026-11-16, first run `22:28Z`.
- Build: `/agent/repos/pcbase/forge-combo29/build-pc/forge`, from worktree `/agent/repos/pcbase`
  (base `6b98f217` + the file-5 patch), built with
  `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`, g++ 13.3.0.
- Timestamp: see `job30/stamps.txt`.
