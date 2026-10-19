# Rule50 score-context candidate

Parent checkpoint: ec6a8dff7ab3779e9c328001537acdf7721aff7f, with the
correctness-tested6.4.3 TT implementation. Accepted development reference
remains9108d012526be80c6d163f7cab684e6acd9abf8d; no later Elo gain is accepted.

Actual-Worker RED evidence and the independent legal-move oracle are preserved
in validation/rule50-context-20261019/investigation-before-integration.zip.
At halfmove99 every legal evasion reaches a fifty-move draw, but a naturally
learned low-clock TT bound returns-426 instead of0. Reverse reuse also turns
low-clock qsearch-426 into0 and PV qsearch static evaluation453 into0.

A current-clock-only cutoff guard is insufficient for both reverse cases.
Use one byte of existing TT padding for the score's capped halfmove clock,
written only when the score payload is admitted. Keep the16-byte entry and
64-byte cluster. A score may be used when both clocks are below90 or the
capped clocks match exactly. Gate both central TT score conversions so all
bound and score-as-evaluation consumers receive ValueNone for incompatible
contexts. Preserve TT move/raw static evaluation reuse and the main search's
existing below90 cutoff restriction. No repetition-key solution is claimed;
grouping different clocks below90 remains an explicit inherited heuristic.

Tests must reproduce the forward/reverse failures with actual learned entries,
retain below90 and exact near-limit TT reuse, preserve mate/draw precedence and
zeroing moves, and verify rejected payloads cannot overwrite clock metadata.
Include clock metadata in the concurrent correlated-entry stress test. Run the
complete Release suite, appropriate sanitizers and frozen-parent comparisons.
Measure overhead separately; native equal-clock SPRT is still the strength
gate. Keep all failed attempts, original logs and incomplete results.

The6.4.3 benchmark inputs are frozen separately. Editing this next candidate
does not rebuild or replace those inputs. Do not compile competing workloads
while a controlled performance run is active.
