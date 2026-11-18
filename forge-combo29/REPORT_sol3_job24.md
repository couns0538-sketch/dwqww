# sol3 Job 24 — piece-position assertions and a failed control gate

## (1) Step 0 — both plain builds passed

Case A, Linux cloud. Plain r15d and kF each returned 312,866 and
862,329 nodes for default bench 11 and 13 and 4,865,609 for
`go perft 5` from startpos. With PC20, Threads 1, Hash 16 and
synthetic net768, both returned 882,074 and 4,275,906 nodes for
the two benches. Each net bench printed active checksum
`30ab43b4ba5db5f3`. Each command ran in a fresh process.
[Plain outputs and hashes](sol3/job24/step0)

## (2) A-kF2 — independent piece-position references

A-kF2 applies on top of Job 23 A-kF. Its patch SHA-256 is
`65011354c09788248b9ba12574f312da5b5b13be1ec2e85fc090b21c8361d23a`.
GCC 14.2.0 (Debian 14.2.0-19) and CMake 4.2.3 used the Job 23
ASan/UBSan flags, assertions enabled and `-march=x86-64-v4`.

A1s and A2s evaluate a local copy of the piece slots after the
move. Opposite-side attacks to each king come from reverse
contact offsets and square-by-square slider rays. A2s runs
before the quiet legality decision can reject a candidate.
A4 computes the three fields from placement before each quiet
return. A7 uses that field calculation after each normal or null
unmake that restores a valid cache. It runs with the restored
side to move. Direct piece bitboards supply king coordinates.
The comparators receive copies of the measured fields. The
reference calls only placement helpers and leaves the engine
board and its flags untouched.
[A-kF2 patch](sol3/job24/step1/A-kF2.patch.txt) · [Build flags and hashes](sol3/job24/step1/build) · [Source sites](sol3/job24/step1/source_sites.txt) · [Source independence readback](sol3/job24/step1/source_independence_readback.txt)

The requested grep of A-kF2.patch.txt follows. The `actual_*`
parameters, diagnostic labels and call-site fields belong to
the comparison side. The placement reference uses its own
`own_blockers`, `opposing_blockers` and `landings` fields.

```text
$ grep -nE 'king_lines|ensure_king_lines|check_squares|pinned|discoverers' A-kF2.patch.txt
18:+                             Bitboard actual_discoverers, const std::array<Bitboard, 7>& actual_targets) const;
223:+                                Bitboard actual_discoverers, const std::array<Bitboard, 7>& actual_targets) const {
232:+    if (actual_pins != reference.own_blockers) fail("pinned", actual_pins, reference.own_blockers);
233:+    if (actual_discoverers != reference.opposing_blockers) {
234:+        fail("discoverers", actual_discoverers, reference.opposing_blockers);
238:+            fail("check_squares_" + std::to_string(type), actual_targets[type], reference.landings[type]);
252:-    if (undo.king_lines.valid) king_lines_ = undo.king_lines;
253:-    else king_lines_.valid = false;
254:+    if (undo.king_lines.valid) {
255:+        king_lines_ = undo.king_lines;
257:+        job24_verify_fields("A7", move, king_lines_.pinned, king_lines_.discoverers, king_lines_.check_squares);
260:+        king_lines_.valid = false;
269:-    if (undo.king_lines.valid) king_lines_ = undo.king_lines;
270:-    else king_lines_.valid = false;
271:+    if (undo.king_lines.valid) {
272:+        king_lines_ = undo.king_lines;
274:+        job24_verify_fields("A7", Move::none(), king_lines_.pinned, king_lines_.discoverers, king_lines_.check_squares);
277:+        king_lines_.valid = false;
305:+                        board_.job24_verify_fields("A4", move, pinned_, discoverers_, check_squares_);
```

[Raw grep](sol3/job24/step1/A-kF2.cache_grep.txt)

## (3) Known answers and controls

The run settings below are PC20, synthetic net768, Threads 1,
Hash 16 and MultiPV 1. All started with an active net768
checksum of `30ab43b4ba5db5f3`. A dash in the nodes column
means the abort occurred before a node label was emitted.

| Run | Fixture and limit | Searches / bestmoves | Reported nodes | Engine exit | Assert stops | Checker reports |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| [K1, A-kF2](sol3/job24/step2/known) | W1 1–200, depth 9 | 200 / 200 | 4,097,080 | 0 | 0 | 0 |
| [A-wrong2](sol3/job24/step2/wrong2) | P row 1, depth 9 | 1 / 0 | — | -6 | 1, A1s | 0 |
| [A-kF2-blind](sol3/job24/step2/new-blind) | First X, P row 11, depth 4 | 1 / 0 | — | -6 | 1, A7 | 0 |

K1 matched all 200 FEN, last-info node and bestmove labels from
Job 22 AU-kF-d9, with a fresh process and a reset and ready
barrier before each row. Its stderr was empty. The initial
launcher attempt exited 127 because this image lacks
`/usr/bin/time`. It launched no engine. I retained that receipt
and used two clock reads to time the successful engine run.
[K1 gate](sol3/job24/step2/k1_gate.json) · [Preserved launcher attempt](sol3/job24/step2/known-launch)

A-wrong2 selected only direct attacks from the moved piece
in A1s. The first search, on P row 1 (DQ), stopped on the legal
`e4c2` discovery. Python-chess confirmed the stationary
queen on e1 gave check. The control exited SIGABRT before
bestmove. Its entire stderr was two lines.

```text
job24 assert A1s move e4c2 fast 1 ref 0
job24 fen 4K3/8/8/8/4b3/8/8/k3q3 b - - 19 114
```

[A-wrong2 patch](sol3/job24/step1/A-wrong2.patch.txt) · [A-wrong2 gate](sol3/job24/step2/wrong2_gate.json)

The same pinned-empty patch applied with zero fuzz to A-kF2
and Job 23 A-kF. It sets the stored pinned mask to zero at the
return of `Board::ensure_king_lines`, before the picker copies
it. Both variants built with the same instrumentation flags.
The single required first-position trial used a fresh process.
It stopped at A7 on unmake of `g2f3`. The root FEN was
`7R/5pk1/p5p1/3pb3/2pP2pP/5P2/1q1Q2K1/1r6 w - - 0 42`.
The entire child stderr was two lines.

```text
job24 assert A7 move g2f3 field pinned fast 0 ref 2048
job24 fen 7R/5pk1/p5p1/3pP3/2p4P/5p2/1q1Q2K1/1r6 w - - 0 43
```

In that restored position, python-chess confirms that the
black pawn on f3 checks White, `g2f3` is a legal evasion, and
the lone pinned white piece is the queen on d2. The engine's
saved mask was zero. The position-only computation recovered
bit 11, 2,048. The child exited SIGABRT before bestmove.

The required first stop was A2s or A4. The observed A7 stop
failed that gate, so I stopped after the first class-X trial.
K2/R1 did not run. A-kF-blind was built and all of its
20 scheduled searches remained pending at the stop.
[Pinned-empty patch](sol3/job24/step1/pinned-empty.patch.txt) · [Exact control gate](sol3/job24/step2/new_blind_gate.json) · [Independent local-board check](sol3/job24/step2/new_blind_local.json) · [Raw UCI audit](sol3/job24/step2/transcript.audit.json)

| Class-X rank | P row | A-kF2-blind | A-kF-blind |
| ---: | ---: | --- | --- |
| 1 | 11 | A7, exit -6 | Did not run |
| 2 | 12 | Did not run | Did not run |
| 3 | 13 | Did not run | Did not run |
| 4 | 14 | Did not run | Did not run |
| 5 | 15 | Did not run | Did not run |
| 6 | 16 | Did not run | Did not run |
| 7 | 17 | Did not run | Did not run |
| 8 | 18 | Did not run | Did not run |
| 9 | 19 | Did not run | Did not run |
| 10 | 20 | Did not run | Did not run |
| 11 | 22 | Did not run | Did not run |
| 12 | 24 | Did not run | Did not run |
| 13 | 26 | Did not run | Did not run |
| 14 | 28 | Did not run | Did not run |
| 15 | 30 | Did not run | Did not run |
| 16 | 32 | Did not run | Did not run |
| 17 | 34 | Did not run | Did not run |
| 18 | 36 | Did not run | Did not run |
| 19 | 38 | Did not run | Did not run |
| 20 | 40 | Did not run | Did not run |

[Fixed class-X schedule with FENs](sol3/job24/plan/blind.tsv)

## (4) Prediction

The independence gate stopped the job before the forecast.
There is no prediction commit to grade.

## (5) R2

| Planned fixture and limit | Games | Searches / bestmoves | Nodes | Exits | Assert stops | Checker reports |
| --- | --- | --- | --- | --- | --- | --- |
| A-kF2, top 20 P or X positions by piece count, softnodes 2000 | Did not run | — | — | — | — | — |

[Fixed R2 starts](sol3/job24/plan/r2.tsv)

## Facts

The successful K1 launcher interval was 62.584 seconds
for the 200 depth-9 results. The interval includes the process
lifecycle and UCI barriers.
[K1 timing receipt](sol3/job24/step2/known/time.txt)

## Suspicions

In a checked position the evasion stage can initialize the
picker's lines before a move is made. That path fits the
checked restored FEN and the A7 stop during unmake.
[Source sites](sol3/job24/step1/source_sites.txt)

## What I did not do

I did not weaken or bypass A7 to obtain the requested label.
I did not run the remaining blind positions, K2 or R2 after
the failed gate. Engine source changes exist only as text
patches applied in scratch.

## What I am not sure about

The failure captured the restored FEN and the immediate
move. The earlier path that set the saved cache was not
recorded. The results leave the behavior of the old blind
build on all 20 positions open.

## What this check cannot see

> Positions that P and the 20 games do not reach; the PC's clang 23 build with a profile and its trained net; more than one search thread.
