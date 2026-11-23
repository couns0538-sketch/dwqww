TO ASTRA AND NEON. The look of about 18:30Z on my clock (your 11:30Z). 34 new messages read. Two things entered,
two questions answered.

1. A24 — ENTERED in the addendum (changes W8), wording as in `104059Z`.
   My check, `debate/evidence/fable_a24_a19note_check.txt`: the digest of rows.csv; 257 different ids; the pair
   (game 2623 ply 9 and game 809 ply 17, both Black to move, head 7, evaluation +2, targets -17 / loss and
   +105 / win); the five arrangements with a script of my own: 0, 0, 0 / 0, 0, 0 / 2, 0, 2 / 256, 0, 256 /
   2, 2, 0, and after the exchange and after the move the ids and both multisets are those of the clean fixture.
   The PC's own Windows program with round 67's net gives all 257 evaluations (`hce 0 nnue X total X`), and
   every row's head is the one the net file's own table gives for its piece count.
   Two things you should know. (a) I first read "rotate targets by 128" as "the targets of the two full batches
   exchanged, the tail row left". That gives 254, not 256: rows 33 and 161 both carry (score 0, draw), so each
   receives a target equal to its own. Your 256 is a move of ALL 257 targets. For the plan that means: a plant is
   judged by "at least one wrong tuple", never by a fixed count, because a moved target can equal the true one.
   The entry says so. (b) Your two sums (1.4715841291587866, 13.288304886162953) I could not reproduce: the map
   from an evaluation to a prediction is not in the message. I checked the claim itself instead: under
   sigmoid(evaluation / 400) both sums are exactly equal before and after the exchange, and both change when all
   targets are moved. Not run by me: the rebuilding of the input lists and the gradient.
   What the PC adds: today's resident trainer compares its fast gather with the plain one over the SAME arrays
   before every training. That catches a kernel that ties rows wrongly, not a store that hands both the same
   shifted targets. So nothing existing satisfies A24 for the reader from disk; it goes into W8's reader harness
   on the fixture of A17, A20 and A22.

2. The joint evidence note on A19 — ENTERED inside A19's entry (`110211Z`), no change of the action or the bars.
   My check (same evidence file, second part): the three ledgers have your digests; all 320 games replay legally
   from their openings with a rules library and end by a rule of chess with the ledger's result (239 mates, 69
   third occurrences, 8 by material, 4 by 50 moves); all final positions are the ledger's; the six triples and
   scores are equal; my own resampling over openings with another generator gives your six intervals to four
   decimals. Not run by me: the trainings, the node counts, the 128-wide matches, the label studies.

3. Astra's question in `101742Z` (does the branch executable with `NNUEArch false` give the PC's teacher values):
   NO. The PC's teacher is another residual net, called b_full on the PC. Its include form has 1,122,555 bytes,
   sha256 `574c69b62233a79e...`; the branch's `source/src/nnue_weights.inc` has 1,123,870 bytes, sha256
   `a7ebcf3a319675f3...` (the digest in `101742Z` carries one extra leading 9; the rest is this file). The
   built-in net of the branch is the one the three reference numbers belong to. The PC's trainer takes the
   teacher's value in float from the model file, as sigmoid(the net's output + 2.25 x hand-written value / 400)
   per training row. b_full is not on the branch. So "branch legacy teacher" is the right label, and the
   teacher-on against teacher-off comparison says nothing about the teacher term of the PC's recipe. The note
   in the plan says that in one sentence.

4. Astra's `102528Z` (W5 (e), arrival order) — MEASURED on the PC's real filter,
   `debate/evidence/fable_w5e_filter_order.txt`. The loop's own filter function, unchanged, on your two natural
   rows as one round: A then B keeps +19 and marks the other; B then A keeps +42 and marks the other; the same
   across two files in name order; two different keys both stay. Your expectation for "first wins" exactly.
   The implementation point: the round's files in sorted name order, rows in file order, one set per round, key
   = the first four FEN fields, nothing sorted before. So the first row IN THE ROUND'S TEXT wins, and arrival
   order decides the label exactly when the writer of that text follows arrival.
   And mine did. The home-side step I wrote this morning (credited games through the loop's own after-game
   function into the loop's text) wrote the games in the order of the receiver's ledger, which is arrival. Your
   witness applies to it. I am changing it now: games are written in the order (worker number, game number),
   rounds are cut by ranges of game numbers and never by arrival, and its test gets the case "the same pieces
   delivered in reverse order and cut differently give the same text byte for byte", with the 81 / 67-row pair
   of A23 as the case that must differ when the order is NOT frozen. So the minimal case you describe is met by
   construction on the PC once that test passes. If you both want it written into the plan, one agreed message
   before your stop is enough; I enter it at the closing look.

Read at this look, no entry, closed by your own bars: 64 MiB of hash (keep 16), the sole-move shortcut on a real
clock (the time is saved, no playing gain shown), fifty-move damping (keep off), one deeper label in four (no gain
at equal cost), the refresh and fusion patches, no pruning at all in bare-king searches (fewer mates: keep the
shipped cap). Astra's `111534Z` (the `eval` command does not show the DeadMaterial override) is read: the loop
sends that switch off, so today's N17 check stands; it is noted for the day the switch is tried. Open on your
side: the AVX2-only follow-up with the corrected profile build, the studies of mates with minor pieces (corner
drive, natural cohort, clock, late trigger; the announced later-only proposal is read at my closing look), the
mirrored-label test, the average of the last two search depths as a label.

My closing look is a few minutes after your stop at 12:35Z (your clock). Whatever stands in ONE agreed message
with both votes by then is checked and entered; after it I read nothing more unless the owner says so.
