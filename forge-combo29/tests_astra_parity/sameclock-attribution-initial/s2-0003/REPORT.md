# Same-clock difference attribution snapshot

Audit /workspace/work/parity-run/equality-final-v4/audits/S2-0003.txt, SHA256 ad9decb73bb87086694e7eedd5b28fe7e88cc0d10457a7966b8edd247417655a. 48209/100000 positions; full corpus complete: false. This snapshot does not waive any later finding or mark the gate passed.
Observed differences: 1; root clocks under80: 0. Partial difference observations: 0.

| Global index | Root clock | Before / frozen tuple | Final tuple | Fresh pair differences |
|---|---|---|---|---|
| 36729 | 90 | {"move":"a1b2","kind":"mate","score":-6,"bound":"","nodes":2565143,"depth":9} | {"move":"a1b2","kind":"mate","score":-5,"bound":"","nodes":2566746,"depth":9} | 10/10 |

Only source delta is TTEntry::score_usable early equality admission. Compiler metadata, compile flags and link command are identical; GNU14.2.0, strict floating-point, x86-64-v4, guard compiled in with runtime default off. Each difference links the exact Step1 index/FEN, which matched the frozen reference, and all eleven Step2 pairs.

eq = stored_clock == min(read_clock,100); rejected_mate = is_mate_score(score) && read_clock + (MateValue - abs(score)) >100; new result differs iff eq && rejected_mate, false to true.

This supports source-level causal attribution to the same-clock admission under the recorded deterministic protocol. It does not claim an observed runtime stored/read clock or a proof of the chess-theoretic truth of the mate score. Runtime entry proof, if required, needs the separately described private diagnostic. No engine was run for this review.

Full commands, build metadata, source diff, selected records and original/repeat transcripts are adjacent.
