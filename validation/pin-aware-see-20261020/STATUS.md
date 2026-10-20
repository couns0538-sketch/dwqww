# Forge 6.4.15 pin-aware SEE

Source `8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad` preserves parent 6.4.14
`21538ec5416c909fc98a08688242a0b3b9710b25` and all accepted work. Hypothetical
non-king recaptures now have to leave their king safe in the current virtual
occupancy. The target remains occupied, allowing legal captures along a pin;
consumed origins and the captured victim's stale bit are masked. The original
king branch, LVA order, thresholds, evaluation and NNUE weights are unchanged.

Release, ASan/UBSan and TSan each passed all nine CTest suites, including perft,
TT, rule50, legal witnesses, UCI, ponder and OwnBook checks. Eight additional
active-search UCI transitions passed under TSan, with default deadlock checking,
legal bestmoves, captured output and joined shutdown. Frozen source and all six
built engine/core/test artifact hashes remained unchanged within each run.
Compiler warnings already present in unchanged search.cpp are retained.

The actual API prototype matches its independent legal-capture oracle on 302
legal cases, correcting eight parent errors. Ten further targeted controls
exercise EP-opened pins, legal quiet moves, checks, three-recapture pin release
and the king fallback; all pass and nine parent errors are corrected. Two
additional promotion-recapture controls fail the exact oracle in both builds
(-400 versus -1200), explicitly retained as an inherited approximation. This
bounded corpus does not establish universally exact SEE or chess strength.

Permanent tests cover 23 authored cases in both colors, checking legal moves,
exchange values, adjacent threshold boundaries and unchanged board state.
Compiled against the actual frozen parent core, these produce exactly 16
expected assertion failures; all pass in every candidate native profile and
the Windows core tests. Source review and all failed fixture attempts remain.

The Windows x64 Zen5/static build passed eight Wine checks and 929 independent
artifact checks. ZIP/tree/SHA256SUMS, all frozen source hashes, raw originals
and the exact tested executable agree. The user package is
`releases/forge-6.4.15-candidate-windows-zen5.zip`, SHA256
`1eb3a128e4e905921e0440482076b0fd47bf0194e08a91eb099efe7fbce5df42`.
Exact tested PE: `9e5335f917decbdc9ef6ee76e71ec85d5ff7695d5078e90e76c3dac8498bc5dc`.
NNUE network SHA256 stays
`41487f328ff51f27417564df45b6f3139d038b7e940dedb121340bd61be9a4d3`.

Observed bench11 signatures are 385792 Linux and 382424 Windows, versus the
parent's 419798 / 351063. Search parity is not expected for this behavior
change. The native capture ran once with concurrent build work; its duration
and printed NPS are not a performance comparison. Added attack-query work and
actual equal-clock Elo are unmeasured. Zero candidate strength games.

Decision: retain an isolated finite-correctness candidate; no integration,
positive Elo, speed, native Ryzen performance or Stockfish acceptance. The
parent's original unexplained 60-second bare-bench timeout and the hosted
baseline forfeit remain unresolved. A passing candidate capture does not erase
them. The separately prepared SPRT is unlaunched and not a retry of that match.

Next experiment: an equivalent dynamic forbidden-origin mask may reduce the
per-recapturer king-attack queries. Require byte-exact API and actual search
parity, operation-count evidence and full correctness gates before applying it.
The promotion-recapture approximation remains a separate future hypothesis.
