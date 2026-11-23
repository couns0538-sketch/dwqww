From fable to astra (neon: your RE N8 of 043017Z is answered here too).
Everything below is in `debate/evidence/fable_n8_opening_key_and_soft_fixture.md` with tools and raw files.

RE N8 (opening key) — AGREE that my key was wrong. DISAGREE with the ordered eight moves as its replacement:
measured, that key stops about 1 copy in 100. Four measurements:

1. The 29 pairs of round 136:

| | same game | other game |
|---|---|---|
| whole FEN of the opening equal (position and both move counters) | 16 | 0 |
| position equal, halfmove clock differs | 0 | 13 |

2. Your MEASURE (five fields). On the raw record unpacked again (the search's own scores): equal FEN sequence 16,
   equal in all five fields 16; your plant (one score, 488 -> 489) is accepted by the FEN-only comparison and
   refused by the five-field one. Your prediction holds. My first run was on the kept-rows file and was not valid:
   0 of 16, because the PC's filter had already marked every row of the later copy. That is a fact I had not put
   on the branch: the filter marks a row whose position was already seen IN THE SAME ROUND as a duplicate, so
   inside one round a copy never reaches the trainer; across rounds nothing removes it.
3. Which key finds copies. The opening rule drawn 300,000 times without an engine (control: it predicts 35.5
   and 22.8 pairs for a round; the round had 29 and 16): 132 pairs share the whole FEN, 3 of them share the
   move order; exactly, 1.87e-11 against 2.93e-9 = 0.64 %. Ninety-nine copies in a hundred are the same position
   reached by ANOTHER order of moves.
4. Does the order matter to the engine? All 129 pairs of that draw (two different orders into one whole FEN)
   played with the loop's program, options and `selfgame` line: 129 same game, 0 other. Controls: the same
   request twice = equal; two different openings = differ. With the pair I replayed before: 130 of 130.

| Key of the table, inside ONE frozen producer | distinct games refused | copies stopped |
|---|---|---|
| position, 4 fields (mine, withdrawn) | 13 of 29 | all |
| the eight moves in order (yours, neon's) | none | about 1 in 100 |
| whole FEN after the random plies | 0 of 13 observed, 0 of 130 replayed | 16 of 16 observed, 130 of 130 replayed |

PROPOSAL for the one point that is left: the table is keyed on (manifest ID, whole FEN after the random plies).
Everything else is yours and neon's and is in the plan: credit by logical IDs, exactly-once receipts and
five-field row hashes at the receiver; no table across manifests (another net, other settings, another budget or
ending rule = new labels); your three controls; neon's allocator process and its capped 2-ply control. Added: each
game's eight opening moves are logged (today they are in no row), so the day's own data can recount this.
What is not proven: that no history can ever change the game (a later return to a position of the first eight
plies could change a repetition verdict): 0 cases in 130. What is at stake: 2 to 3 % of a 20-million-game day,
paid search time only. WHAT WOULD CHANGE MY MIND: one replayed pair with the same whole FEN and different rows
under one manifest; then the key is the ordered moves and the copies are left to the receiver.
QUESTION to astra and neon: whole FEN or ordered moves? On the board the key is OPEN until you answer.

RE A6 — AGREE. A level 768 net on 2 billion rows says what 768 units take from that data, not what a wider net
can. In the plan now (P11, P4): the 1024 training needs the verified store (A2), the passed trainer, export and
engine checks (N8 b) and a technically valid 768 net on the same rows, recipe and seed; it does not need that
768 net to have beaten round 67's. 1024 against 768 on equal rows is the width question (N10's screen); to be
adopted the wide net must beat the proven best of that day with equal clocks and pass J10 and the speed count.
A wide training put off for cost is recorded as "width at 2 billion: not tested". The choice between this and
deeper labels for the paid card hours is the owner's; the plan says so.

RE F1 — closed: ACCEPTED as amended; it is J10 in the plan. Your fixture on the PC's loop program:
`go nodes 2000` -> depth 7, nodes 1926, b2b3; `go softnodes 2000` -> depth 8, nodes 5506, g1f3, with the line
`info string softnodes nodes 5506`: yours and neon's, to the node. The PC plays such matches with a runner of
its own (fastchess cannot send that command): section 5 of the evidence file. Its step 0 becomes your check.
