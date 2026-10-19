# Forge 6.4: improvement checkpoint

## Current result

The transposition-table verification-tag repair is implemented and correctness-verified.
Its Elo effect is **unproven**. The first equal-clock match stopped on a Candidate
timeout. Ten cold replay result records subsequently reported normal completion,
with one incomplete raw transcript disclosed below. The original timing cause
remains unresolved.

The requested **Improve Forge 6.4** task is enabled for every hour at **:30,
America/Los_Angeles**. Each cycle is instructed to retain its evidence and report
actual progress, including blocked or inconclusive work. Execution depends on
available tools and usage; no uninterrupted background computation is claimed.

Work branch: [forge/6.4-hourly-20261019](https://github.com/couns0538-sketch/dwqww/tree/forge/6.4-hourly-20261019).
Baseline: [24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b](https://github.com/couns0538-sketch/dwqww/commit/24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b).

## Source and original match audit

The repository inventory covered ten existing branches and 104 commits. Current
Forge source, build/test tools and experiment records were reviewed. The default
main branch contains a different engine lineage; it is not the Forge 6.4 baseline.
All 51 source/build/test/tool files compared with the original release ZIP were
byte-identical before the repair. Original release ZIP SHA-256:
`98d2ff2c523a25931897794bad3c39d40398799b8907d51596dad3e326a2ba9d`.

The original match archive contains **44 PGNs and 76,047 games**. Each PGN matched
the immutable match branch by Git blob identity and byte count. Results, pairings,
colors and openings were audited; this was not a full independent legality replay.

| Recorded result | Games | Wins / losses / draws | Score |
|---|---:|---:|---:|
| Forge 6.4 vs Stockfish 19, reported 3000 limiter, 20+0.2 | 100 | 35 / 30 / 35 | 52.5% |
| Forge 6.4 residual-128 vs 6.3, equal clock 10+0.1 | 200 | 49 / 23 / 128 | 56.5% |
| Forge 6.4 residual-128 vs 6.3, fixed 20,000 nodes | 500 | 209 / 88 / 203 | 62.1% |

The **1,120 Stockfish games** aggregate nine matches across versions 5.31–6.4,
limiter settings and time controls. They do not establish 1,120 games of Forge
6.4 against one identical opponent configuration. The 100-game result does not
establish a small superiority, an absolute FIDE rating, or superiority over
unrestricted Stockfish. The original 6.x console/config/training logs and datasets
were absent; substitutes have not been represented as recovered originals.
See [the source-grounded match audit](forge-match-evidence.md).

## Implemented repair

On the multiply-high transposition-table backend, both the original bucket
index and original verification tag used upper key bits. At a 64 MiB table with
64-byte clusters, twenty upper bits already choose the bucket, leaving only
twelve additional tag bits. Distinct keys can consequently be mistaken for the
same entry much more readily than a nominal independent 32-bit tag suggests.

The repair uses the low 32 key bits for multiply-high indexing and retains the
high 32 bits for the portable modulo backend. Probe and store use one helper.
Only `include/forge/search.hpp`, `src/search.cpp`, and `tests/tests.cpp` changed.
The new regression fails twelve checks against the untouched baseline library
and passes against the repair. Pruning, evaluation, NNUE, time-management logic
and the version number were not changed.

This demonstrates the tag defect and correction. It does not establish that a
specific historical game was lost because of it, or eliminate every possible
finite-tag collision. SMP publication and rule-50 eligibility are separate issues.

[Code and first validation commit](https://github.com/couns0538-sketch/dwqww/commit/9108d012526be80c6d163f7cab684e6acd9abf8d).
[Patch](candidate.patch). [Independent review](forge-tt-review.md).

## Validation completed

| Check | Recorded result |
|---|---|
| Original Release CTest | 4/4 pass |
| New regression linked to original library | Twelve failures as expected |
| Repaired Release CTest | 4/4 pass |
| Portable modulo backend in a disposable source copy | 4/4 pass |
| AddressSanitizer and UndefinedBehaviorSanitizer | 4/4 pass with leak detection disabled |
| Short bench signature | 417,491 nodes for both frozen binaries |
| Initial fixed-node A/A check | Eight games; paired move identity passed |
| Native checkpoint continuation | Two rounds resumed to four matched uninterrupted four-round control |
| Match-driver review | 22 bounded checks passed |

These are Linux results using GCC 13.3.0. The portable-backend exercise is not
Windows/MSVC runtime qualification. LeakSanitizer could not inspect process state
under sandbox restrictions; the failure and successful ASan/UBSan retry were
retained. Short bench wall times measured around concurrent compilation are not
used as evidence of a speed gain. Matching short bench nodes does not promise
identical search everywhere after removal of erroneous TT hits.

## Strength attempt and diagnostic

The protocol was committed before execution at
[918859057a433d58e6b7fecd62f83861665f05f2](https://github.com/couns0538-sketch/dwqww/commit/918859057a433d58e6b7fecd62f83861665f05f2).
It used 10+0.1, one engine thread, Hash=64 MiB, NNUE enabled, book and ponder
disabled, six concurrent games, paired colors and frozen opening order.
The intended logistic SPRT was H0=0/H1=5 Elo, alpha=beta=0.05, naturally completed
100-pair tranches and a fixed maximum of 10,000 pairs. A tranche cap is not H1
acceptance. The runner was pinned to official fastchess commit
`ebfd64cb7fac80d4822c50b07dca4fe934779d21`.

The first attempt stopped after **54.27 seconds**, with runner exit 1, **one
Candidate timeout and zero reported crashes**. Six normal completed games were
retained. There was no native H0/H1 decision and no Elo conclusion. Its status
is **failed_no_resume**; its counts must never be pooled into a replacement.

The failing command gave Black 596 ms remaining and a 100 ms increment. The
unchanged engine formula gives a 101 ms soft budget and a 351 ms hard budget.
The runner returned without a move after roughly 1,404 ms; an explicit stop
produced `c5e3` in 1.581 ms. The trace does not isolate an engine-only or
host-only cause. The runner's POSIX poll wait resets after output, so its
nominal read threshold is not an absolute wall-clock deadline.

A separate diagnostic protocol was committed at
[374a71d44ea0a2d28ac26b196ced57c34ddfdcd8](https://github.com/couns0538-sketch/dwqww/commit/374a71d44ea0a2d28ac26b196ced57c34ddfdcd8)
before five alternating fresh-process trials per binary, using the same
position/repetition sequence, UCI options and clock command.

| Binary | Recorded trials | Best-move latency range | Move / depth / nodes |
|---|---:|---:|---|
| Original 6.4 | 5 | 136.540–177.870 ms | e7e4 / 11 / 98,549 |
| TT-tag candidate | 5 | 139.257–173.826 ms | e7e4 / 11 / 98,549 |

All ten separate result summaries and console entries record normal completion.
Nine raw transcripts match their original completion digests. The sixth
transcript is now truncated after startup; its summary remains intact. Nineteen
of the twenty original trial-artifact digests match. No authentic full copy of
the missing raw transcript was found, and no reconstructed transcript has been
substituted. See [the integrity finding](diagnostic-evidence-integrity.md).

This is cold non-reproduction with one raw-log limitation. It does not reproduce
the original warmed TT/history and concurrent workload, clear every timing bug,
or establish a speed or Elo gain.

## What is saved and what is blocked

The work branch retains the repair, patch, initial source/match audits, build and
test logs, first reviews, frozen binaries and full A/A recovery evidence.
The first two archives have **45 committed encoded pieces** whose remote Git
blob hashes were verified against their local contents.

Independent local recovery also tested the prepared three-archive collection:
all three archive hashes and all 84 packaged-member hashes and lengths matched,
and the three binaries regained executable permissions. That establishes
recovery of packaged bytes. It does not erase the sixth transcript's mismatch
against its earlier recorded digest.

The prepared **tt-tag-first-attempt-evidence.zip** contains 43 UTF-8 text files:
the complete first-match trace, PGN, checkpoint and commands; public opening
positions; diagnostic source, results and available transcripts; and analysis.
It is 871,904 bytes, SHA-256:

`a46354a38c4866a748aca459e794be33a934957e8e1c1f041a99d85c73b9533e`

Its upload is **blocked pending explicit user approval**. Automatic review
rejected the original upload and a retry after full content inspection, because
the exact public payload includes workspace paths, process identifiers,
timestamps and resource measurements. The audit identified no credentials,
binaries, unrelated private documents or personal messages. Technical metadata
is still present. The upload has not been retried through another destination
or representation. The final archive is not committed; uncommitted objects do
not make it a durable branch checkpoint.

The active `../ARTIFACTS.json` describes the two committed archives. The helper
can restore those:

```sh
python3 tools/match/restore_hourly_artifacts.py
```

The local execution connection became unavailable during final checkpoint
preparation. This safe progress report and handoff were saved through GitHub;
no engine computation is claimed during the interruption.

## Next development cycle

1. Investigate worker-start latency, deadline checks and runner/host delay with
   a bounded warmed-state and controlled-load experiment when execution and the
   original trace are accessible. Do not inflate grace periods to hide the fault.
2. After reliable timing, preregister a separate TT-tag replacement strength
   test. Retain the failed first attempt unchanged and require actual native
   acceptance before claiming a stronger engine.
3. Consider deferred move-picker check-mask work as an independent speed
   candidate, with credible timing and per-position search parity.
4. Investigate root-effort accounting by stable move identity, near-rule-50
   qsearch TT reuse, coherent SMP table publication, and NNUE accumulator pass
   fusion as separate hypotheses.

If the retained original trace is unavailable to a future worker, report that
limitation and continue another bounded source investigation. Do not invent
original evidence or quietly rerun an already completed diagnostic as new proof.
Every cycle should distinguish correctness, speed, strength and infrastructure
status. Small demonstrated gains should be retained; none is promised in advance.
