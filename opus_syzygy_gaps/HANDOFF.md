# Hand-off: exact pack to Code Review, then QA

This job queues nothing. Code Review reads first; QA alone schedules gates and publishes locks.

**Blocker: no channel.** This session reaches no Code Review or QA session or queue, and the job's prompt forbids queueing here. Couns forwards the exact pack: this folder, on branch `opus-syzygy-gaps-20261107`, at the commit named in `STATUS.md`.

## Check the pack first
```
git clone --filter=blob:none --no-checkout --branch opus-syzygy-gaps-20261107 https://github.com/couns0538-sketch/dwqww pack
cd pack && git config core.autocrlf false && git sparse-checkout set opus_syzygy_gaps opus_r13/p6 && git checkout
cd opus_syzygy_gaps && md5sum -c --quiet MANIFEST.md5 && sha256sum -c --quiet MANIFEST.sha256
```
Read `REPORT.md`, then `GAP_LEDGER.md`, `README.md`, `BENCH.md`, `REVIEW_LOG.md`.

## Code Review
- The patch to read: `patches/syzygy_gaps_after_p6.patch`. `patches/syzygy_gaps_after_w6p6.patch` has the same changed lines; one hunk has other context. `patches/syzygy_port_and_gaps_after_w6.patch` is P6 port + this change on the trial_w6 source, as one patch.
- The reviews in `REVIEW_LOG.md` were this job's own and are not Code Review: three by one Opus subagent, one bug hunt by a Fable subagent. Each was independent of the main agent's reasoning, but none had the role or the authority of Code Review.
- Judgement calls to look at:
  1. Store-side rule of `SyzygyRule50` bit 1: not at a root, not in qsearch. No failing scenario found, but the argument is by test, not by proof (`GAP_LEDGER.md`, Limits).
  2. Boundary walk inside `go`: budget 1000 moves, about 35 ms at worst on this PC. 919 of the 4569 purpose-built boundary rows stay undecided, mostly at clocks 60-89 (`GAP_LEDGER.md`, Limits). No false claim there, but the move may be worse. A higher budget costs latency at every such root.
  3. The deviation from the common rank convention at dtz + counter = 100 (`README.md`, Root ranks).
  4. WDL-only move filter: only the report is corrected.
  5. Cost of `SyzygyRule50` bit 1: a few true warm claims are withheld (`BENCH.md`).
  6. Unconfirmed, by reading only (bug hunter, `review/H1.md`): a mate score read from the hash at a much deeper ply than it was stored at can drift below the mate band into the TB band. It needs mates at a root ply above about 120. It is P6's behaviour, not this patch's, and was not tested.
  7. The claim harness judges a mate-band claim by the table's result at the node's clock (DTZ + clock), not by the mate distance. A mate claimed too long for the clock counts only when the result itself is wrong, so the counts at the two mate sites are lower bounds (`review/H1.md`, finding 2).

## QA
- Status of every on-path: **SEARCH/EVAL CHANGE, UNPROVEN.** No Elo claim. A QA SPRT is required; none was run or queued here.
- P6's own gates (USYZP, USYZPD4 and their confirms, idx 230-233 in the current `forge_gates.json`) have no results, so P6 itself is unproven as well. Ordering is QA's decision.
- Which exe: the live lock line is trial_w6, so the patch for a gate is `patches/syzygy_port_and_gaps_after_w6.patch` on the trial_w6 source, with the six trial_w6 defines and `FORGE_SYZYGY_TB_BOUNDS=1 FORGE_SYZYGY_ROOT_EXACT=1 FORGE_SYZYGY_RULE50=1`. This job built it with the kit v2.3 recipe (`tools/after_w6.sh`, hashes in `BENCH.md`), not with the clang recipe of `forge_clang_combo29_trial_w6.exe`, which is QA's.
- Options for the on-side: `SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3`, tables loaded. Defaults stay 0, so the same exe with the options at 0 is the P6 path.
- Expected pins are in `BENCH.md`: lock pins without tables at every option value; the P6 path with tables at options 0.
- `SyzygyProbeDepth` is not changed by this job. All fixtures use its default (1); only the option churn run (`tools/uci_churn.py`) sets other values.
