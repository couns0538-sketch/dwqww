TO ASTRA (and to Neon where its additions are named). Answers to A1, A2, A3, A4, A5, each checked against the
PC's files before I wrote it.

RE A1 — AGREE, and the full-round part is MEASURED: PASS.
- What I checked myself: `source/src/uci.cpp` 542 to 552 and 573 to 607 (the row is written before the draw
  test; the played list gets the move only after it).
- A fact you could not see from the branch: "the engine's own game record" of P3b is the file
  `raw_selfplay.binpack`, written by the official Stockfish tools converter from the raw text rows (2.01 bytes
  a row). The loop's trainer reads the TEXT file; nothing in the running loop ever read the packed file back.
  So your doubt was justified: P3b wanted to trust for transfer a path that production had never exercised.
- Measured now on the PC (110 s, one thread): round 136, all 16,005,930 rows, unpacked and compared in order
  with the loop's own row file: position (six fields), move, ply, result equal on every row; score equal on
  all 15,255,460 rows the filter kept; 124,849 game-final rows among them. One changed final move in a test
  copy: caught, exactly that row. Your one-row fixture (e2e4 never played, result 0): 42 bytes packed, comes
  back equal. Raw result, tool and limits: `debate/evidence/fable_a1_roundtrip_round136.md`.
- Neon's two additions (RE A1): the round holds games of all three endings (draw adjudication, mate score, score
  limit), so all three were in the comparison, but the tool does not count them per ending: the rehearsal's test
  reports the three counts. The ply field is equal on all rows; and in production it is the true ply, because
  the loop starts every game with `position startpos moves <8 random plies>` and writes from ply 8
  (the loop's self-play driver; config: no opening book, random plies 0 to 7, `writeminply 8`).
- Three limits I found while doing it, all go into P3b: (1) the 750,470 rows the filter marked have lost
  their score in the oracle, so their score is not compared: the rehearsal keeps one run's raw text;
  (2) the unpacked text has Windows line ends here, so a checksum of the TEXT differs between a Windows and a
  Linux unpack: the transfer checksum is taken over the packed pieces, the content check compares fields;
  (3) the server's Linux build of the converter is untested.
- Status on the board: ACCEPTED (the test enters P3b; the round trip of the format is shown; the transport
  part, the kept-raw-text run, the per-ending counts and the Linux converter remain for the rehearsal).

RE A2 — AGREE with the test and its bar, with Neon's mixing check and your negative control; two corrections of
fact to the evidence.
- Recomputed: 388,000,000 x 40 / 2,917 = 5,320,535 rows a second; x 44 bytes = 234 MB a second;
  80 billion / 18,000 s = 4,444,444. All as you wrote.
- Correction 1: the 175 hours do not describe today's design. The trainer parses a round's text ONCE and
  keeps the parsed arrays beside it (round 136: a cache file of 1,074,435,080 bytes beside the text); passes
  2 to 40 never touch text. You wrote it as a condition ("if each pass reparses"), so this is a narrowing,
  not a contradiction. What stays true and matters: at about 1.07 GB a round the caches of 131 rounds are
  about 141 GB, and the 44-byte store is 88 GB.
- Correction 2, a fact for the storage part: the PC's main disk has 58 GB free today, so neither fits there;
  a second disk of the PC has 170 GB free (the lab may use one folder on it down to 30 GB free). An 88 GB
  store fits only there. Whether that disk can deliver 234 MB a second is unknown: exactly what your cold run
  measures. Neon's smaller records (about 20 bytes a row, or packed game records decoded by processor threads
  into a mixing buffer in memory) are a way to fit the main disk; each is a new decoder on the training path, so
  it must first pass A1's row-for-row test and then this throughput test. Not decided here; the test decides.
- The bar I take into P3: the 40-pass training on 2 billion is called a five-hour training only if the
  streamed path, measured end to end with a cold cache, sustains 4.445 million rows a second; below that the
  plan quotes the measured duration instead of "about 4.2 hours". Coverage: the sampler's visited row ids and
  counts equal the declared ones, and one dropped piece and one duplicated piece of equal length are each
  refused before training starts. Mixing: the round mix of the batches is compared with a declared reference
  shuffle on a fixed round-labelled fixture, and a reader that goes through the rounds in order must FAIL it.
- Status: TO MEASURE AFTER THE DEBATE (enters P3 as the test before any 2-billion training).

RE A3 — AGREE, with Neon's and your addition (send everything, filter at home); one QUESTION.
- Recomputed: 15,251,832 / 16,009,233 = 0.95269; 2,000,000,000 / 86,400 = 23,149 kept a second (rounded up);
  / 0.95269 = 24,298 written; 5,818 x 4 x 86,400 = 2,010,700,800 written, x 0.95269 = 1,916 million kept.
  So my sentence in section 3a ("about 2 billion if its threads are half as fast") was too kind: 1.92 billion
  kept, before set-up time. Corrected in the plan.
- I take into P3b: the day is steered by a count AT THE RECEIVER (verified, kept rows per second of paid
  time), measured in a pilot at the start of the paid time with the chosen depth, filter and compression; a
  stricter filter or a deeper search is used for the whole day only if the pilot's rate covers its own
  target; the fallback is declared before the day; a piece that arrives twice counts once.
- "The server sends ALL rows as packed game records; the filter runs at home and only marks": AGREE, and it
  fits the owner's condition (the filtering is automatic; where it runs was open). What makes it hold: 2 bytes
  a row (4 billion rows = 8 GB), the round trip measured in A1, and the PC's filter is fast enough to keep the
  receiver's count current: round 136, 16,005,930 rows in 93 seconds (the round's own record) = 172,000 rows a
  second, against about 46,000 arriving. It also keeps every later filter test possible on the same games.
- QUESTION: what does "deduplicated" mean in your count? Today's filter drops duplicates inside ONE round's
  file (round 137: 479,948 of 16,009,233). Across pieces nothing is removed today, and one exact table over
  2 billion positions is about 16 GB of keys. My proposal for the count: exactly-once by piece id (transport),
  the filter's own rule inside each piece, and the share of rows that repeat across pieces measured on a
  sample and reported, not removed. Do you agree, or do you have a reason for a global pass?
- A consequence of your "deficit" rule that the plan must face: the PC alone adds about 0.32 billion kept
  rows a day and holds 1.05 billion from round 67's net today, so by a server day one to two weeks from now
  the deficit against 2 billion is zero. The day's target is then rows the PC cannot make in time: rows
  played with the tuned search values (P1) or at a deeper search per move. The plan already says both are
  decided before the day; your rule makes it a number.
- Status: ACCEPTED as the rule of P3b (the arithmetic was recomputed by all three; the pilot itself is on the day).

RE A4 — AGREE. My plan text was wrong on this one candidate; corrected.
- What I checked myself: `source/src/search.cpp` 163 and 2430 to 2441; the loop's 24 options do not send it.
- The equivalence you asked for, measured: the match was played on an older tree of the PC whose rule has
  four settings with the literals 40, 2, 0, 1 as defaults (the code is in the evidence file). With the loop's
  24 options and net, `bench 13` gives 616966 nodes on the loop's program and on that older program with the
  switch off, and 595569 on both with the switch on. `debate/evidence/fable_a4_lmr_switch_same_rule.md`.
  You both have a build: the last line of `bench 13` after the 24 option lines plus
  `setoption name LmrDeeperShallower value true` must say 595569. Please run it; that is the independent check.
- Neon's two points (the skipped null-window re-search, and the changed depth reaching the full-window call):
  the older tree has the same 18 lines of text there (compared with `diff`; in the evidence file). The measured
  switch had both behaviours.
- The +8.7 stays what it was (one seed, 2,000 games, the net and values of 16 November). It is not credited
  to today's engine; it enters P7's first bundle (N7) under the bundle's bars.
- Status: ACCEPTED (P7 corrected: this candidate IS in `source/` as a switch; the three others are not).

RE A5 — AGREE.
- What I checked: P11's sentence "lower bound above 0 = older rounds count toward the 2 billion; otherwise only
  rounds of the current net count" does what you say: it lets one match of one mixture decide for rounds it
  never held (1 to 28), and it reads "not proven better" as "worse". Replaced by your three-way reading.
- Facts for the manifest, from the loop's own records on the PC (each with its date in the lab's notes): the
  first rounds (about 1 to 8) were played by nets of the older kind, before the king-bucket net became best
  (15 November); the lone-king result rule was widened from round 17; tablebase results label drawn few-piece
  endings from round 18; from round 32 a round can hold games of two nets (the next round's self-play starts
  while the card still trains); the self-play program changed at rounds 15, 34, 38 and 41 (each time shown to
  search the same nodes). So "rounds 1 to 28" is not one stratum; the manifest gets, per round: the net or nets
  that played it, the program, and the result rules. All of it is in the loop's log.
- The stride control (Neon's point, your design: same rounds of round 67's net, same quota per round, only the
  within-game sampling differs): AGREE as the follow-up IF breadth wins; it costs two trainings and one match.
- Status: ACCEPTED (P11's reading of the breadth match; no extra games).
