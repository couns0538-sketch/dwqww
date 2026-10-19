# Forge development report

Accepted development reference remains9108d012526be80c6d163f7cab684e6acd9abf8d
on forge/6.4-hourly-20261019. New isolated correctness candidate6.4.4 has source
816423b1ddac23a00244449deef59dba736055a9. No accepted equal-clock Elo gain or
superiority over unrestricted Stockfish has been established.

The6.4.3 candidate replaced racy shared TT pointers with coherent striped-lock
snapshots and opaque probe-time destinations, preserving one-thread replacement
behavior. Actual baseline four-thread TSan reproduced the race. Its repair
passed38 legality-checked instrumented searches, table stress, full Release and
ASan suites and exact cold/warm behavior parity.

The6.4.4 candidate adds score halfmove context using existing TT padding. It
repairs the observed near-limit-426-versus-draw error and reverse score/evaluation
reuse errors. The current tests fail7assertions against the frozen parent and
pass here. Entry/cluster sizes remain16/64bytes. Reuse below90 remains heuristic;
this does not solve all history-dependent transposition questions.

Validation: Release7/7 and ASan/UBSan7/7 CTest suites; TSan8table groups, actual
rule50 regressions and11legal UCI lifecycle searches; frozen Windows core, TT,
rule50, UCI and ponder under Wine. Node signatures remain419798Linux and
351063Windows. GCC14.2 and Windows Clang23.1.3 C++20 probes passed.

Performance is inconclusive. A complete same-binary calibration used72sessions
and216searches at1/2/4threads. One-thread wall ratios ranged0.6566–1.4704;
identical engine-internal work took339–1730ms. Independent audit verified
matching transcripts, frozen inputs and counters. A full A/B run on this
calibration was deferred. No kernel, NPS or deeper-search result is an Elo result.

No new valid strength SPRT ran in this cycle. Earlier shared-VM timed attempts
failed; they remain preserved. The prior6.4.1 versus exact original-ZIP fixed-node
SPRT accepted H0 after178normal games (66W/44D/68L, independentGLR-3.02565;
design[0,+20], alpha/beta.05,10000nodes). It is neither equal-clock evidence nor
a result for6.4.4. Native Windows/Ryzen equal-clock validation remains pending.

Both correctness fixes are kept as tested candidates; neither was promoted to
the accepted branch. Insufficient proposals and failed fixtures/packaging
approaches are retained. Whole-engine speed and strength remain inconclusive.

Source and evidence are published on the isolated development branches. The
ledger is [EXPERIMENTS.json](EXPERIMENTS.json); complete raw archives and Windows
provenance are linked from [rule50 status](rule50-context-20261019/STATUS.md) and
[TT status](tt-coherence-20261019/STATUS.md). Standalone Windows artifacts and
the version-pinned6.4.2 portable validator are in releases/.

Next: implement the prepared legal-witness path, preserving the full fallback.
Its unmodified-parent baseline passed18947 Boolean comparisons across23curated
fixtures, the10000-position corpus and deterministic legal walks. Verify exact
behavior and bounded kernel measurements before broader performance/strength
claims. Continue useful isolated work while stable target-hardware testing is
unavailable; unattended restarts and hourly reporting are not configured.
