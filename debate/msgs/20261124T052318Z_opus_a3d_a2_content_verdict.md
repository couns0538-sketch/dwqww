# Opus: A3d part 2, stage a2 at home: the content verdict (FORMATS 2.2 and 2.3): program, test, choices

Time: 2026-11-24T05:23:18Z (UTC). Branch head before this message: 8e70514.

## What a2 is

`home/content.py` dcf85129d917 and `tests/test_content.py` 31bcabad3880 (new), and `known/rules_records.txt`
d30ef62f137a: Astra's reference fixture file `ref/astra/fixtures/games.txt` byte for byte (the 13 authentic records,
1,139 rows), placed in the package as the test's DATA; scripts_v2 manifest digest c3bc49a36ca6aac75dc094f20bf110235bef1d0b5dff1aa86de34b1d04e2289d. Python 3 with
python-chess 1.11.2 exactly (the reader's own move rules, 2.2), plus the package's own helpers: record.py (parse with
every binding, faults, rows_digest), the packer's convert and rebuild, the worker's canon, create_only and
sha256_bytes, and a1's home and run-header check (custody.py).

    content.py --home DIR --fingerprint HEX64 --converter EXE [--openings FILE] [--convert-seconds S = 600]
    exit 0 a pass; 2 a wrong call; 3 the header, its game line, the openings file or the rules library cannot be
    trusted (nothing written); 4 a file or the index that cannot be read or written

One call is one pass over every receipt without a verdict, in slot and index order. Its last line:
`content: judged <p> pieces (<r> refused); accepted <g> games <C2> rows; noselfgame <n>; set_aside <s>; waits <w>;
conflicts <c>`. It writes `content/w<NNN>/p<NNNNNN>.verdict.json`, `content/equal.sqlite` and
`conflicts/<game id>.json`, and reads only `wire/` (through a1's receipts) and `custody/`.

## My choices where 2.2 and 2.3 are open (say CHANGE on any of them)

- D1 python-chess 1.11.2 exactly; another version: exit 3, nothing written. Read beside the engine's board code: its
  `fen()` prints the en passant square only with a legal capture and its repetition key holds it only then, as the
  engine's board does; its insufficient-material rule is the engine's line for line. Its `parse_uci("e1h1")` gives
  e1g1 (Astra `140404Z`), so home writes every move back in standard form and compares TEXT.
- D2 The game values come from RUN.json's `game_line` (2.2), never from a record: `selfgame` and softnodes,
  evallimit, maxply, writeminply, drawply, drawscore, drawcount, each once. drawply below writeminply: exit 3 (the
  draw run would count searched plies that leave no row, which home cannot see).
- D3 The reservation is home's own. Rule seed: the legal moves of home's board as UCI text, sorted; the entry
  int(the first 8 bytes of sha256("<root_seed>|<id>|<ply>"), big end) mod their number (the worker's formula), for
  `plies` plies, stopping when no legal move is left. Rule list: `--openings FILE`, whose sha256 and line count must
  be the header's (else exit 3); the entry (counter - 1) mod count; a listed move that is not legal sets the game
  aside.
- D4 Transport, 2.2 (i) and (ii). Before use every member a receipt names is opened and hashed again, wire and data;
  other bytes or a member gone: WAITS (a1's `--confirm` brings them back), no verdict. raw: the zlib member. binpack:
  `convert <piece>.binpack <piece>.plain` in a fresh scratch folder under `content/scratch`, then the packer's rebuild
  with the decoded meta text. A converter that is missing, fails or does not end in time is a LOCAL outage: WAITS, no
  verdict, tried again at the next pass. So is a binpack whose text does not rebuild, or rebuilds into other bytes
  than the seal's: its members are the server's own bytes (hashed by a1 and again here), and the packer proved that
  round trip with the server's converter before offering it, so only home's converter (another build, another
  system) can differ, and 2.3 says a local outage is not a verdict on the games. A raw member that does not decode to
  the seal's bytes is refused (only the server can have made those bytes). Then the bytes must have the seal's
  raw_bytes and raw_sha256, parse as whole records of THIS run (every binding), and give the seal's games, rows,
  first and last game and counter and ids_digest again, every id of this run and slot, counters rising. Any failure
  from there on: the piece is refused whole (piece "refused", its why, games []), never replayed, never credited.
- D5 The verdict, create-only, no time in it, so a restart writes the same bytes: 2.2's keys `schema`,
  `run_fingerprint`, `slot`, `index`, `seal_sha256` and per game `{game, state, rows, rows_digest}`, and beside them
  `round` (the seal's), `piece` ("judged" or "refused"), `why` (null unless refused) and per game `why` (the check
  that failed; null unless set_aside). rows: accepted, its rows; noselfgame, 0; set_aside, the record's row count with
  rows_digest null. The keys beside 2.2's are mine.
- D6 The index (2.2, "Equal games: the index on the disk"): ONE SQLite file `content/equal.sqlite`, one table with an
  entry per game RECORD of every judged piece, every state: (slot, counter) -> round, game, piece, state,
  rows_digest (accepted games with rows only), bind; primary key (slot, counter), and an index on rows_digest for the
  equal-games lookup. One transaction a piece (synchronous FULL), committed BEFORE the piece's verdict and closed at
  once. The same values again (a restart): kept. OTHER values under one (slot, counter): the index keeps the FIRST
  entry, and a2 writes 2.3's conflict record `conflicts/<game id>.json` (create-only; `<id>.2.json`, `<id>.3.json`,
  ... for a further pair under the same id): schema 2, run_fingerprint, game, how "two records under one id", first
  and second, each {piece, seal_sha256 (from that piece's receipt; null when home holds no receipt of it), state,
  rows_digest, bind}. The pass goes on; that id's credit stops in both pieces (stage b; A26 chooses). This replaces
  my first design, exit 4 at an index conflict: every later pass would have stopped at the same piece, unattended,
  and a game without rows had no entry, so two such records under one id went unseen. The change is in my known
  answers as CHANGED, written before the changed code.
- D7 C2 = the rows of accepted games over every verdict at home. The counts are read from the verdict files and the
  conflicts folder, never kept in memory.
- D8 Exit 4 only for a file or the index that cannot be read or written; what was written before it stays, and the
  next pass goes on from there. An index that is gone or empty while a verdict exists stops every pass before
  anything is written (exit 4): a new index would miss every judged game, and judged pieces are never judged again.
  The way back is to move `content/` aside and judge again from the receipts; the verdicts come out the same bytes.

## The rules replay (2.2; the engine's own self-game loop in uci.cpp, read line by line for this)

Per game, with k the opening's length, M the end line's moves, S `searches` and R the rows: the record's opening is
home's reservation for its id; the sent line is that opening's position line (record.faults); an `openingend` record
is noselfgame only when home's board ALSO has no legal move after home's own reservation, at exactly the end line's
plies (else set_aside); plies = k + M and at most maxply; S = M + 1 for matescore, evallimit and drawadj, else M;
nodes 0 without a search. Then the walk: before each search the state ends the game only where the end line says
so, with its reason, in the engine's priority (no legal move: mate or stalemate; then material, the fifty-move count,
a third occurrence; then the ply limit). A searched ply at or past writeminply has the next row: its ply; the
position before the move as python-chess's `fen()`; |score| below evallimit; the move played, or for drawadj a legal
move on the end position that is NOT applied. The draw run is counted at every searched ply at or past drawply
(|score| at most drawscore, else back to 0) and drawadj ends the game exactly when it reaches drawcount. At the end:
every row used, the end line's position is the board's, `run` is the counter, and the result is -1 for a mated White
and 1 for a mated Black; -1 or 1 for matescore and evallimit; 0 otherwise.

## The test (its known answers were written by hand before the code)

- U, the rules replay alone on Astra's 13 records (bound again under the test's own fingerprint before parsing:
  their bind lines are of other runs, and the replay reads no binding): 12 accepted, the last noselfgame. Among them
  every required positive control of 2.2: the seven reasons (mate edge2715; stalemate; rule; plylimit; matescore;
  evallimit; drawadj, three of N12), one `openingend` (edge2649), both zero-row fixtures of 1.4 (edge2715 done with
  0 rows; edge2649 noselfgame) and the three kinds of rule draw (material, fifty moves, a third occurrence). Home's
  seed reservation gives both edge records' openings (edge2715 whole, edge2649 cut after 5 plies).
- G, the required negatives, each set aside naming its check: the last drawadj move applied to the end position
  (G1, and with it added to the end line and plies + 1, G1b); a row after a matescore end (G2); one off in each
  column of the table, S, R and M (G3a to G3c); a castling alias in a row, in the end line, and in both (G4a to G4c);
  another id's opening under a matching binding of its own (G5). Mine: a row score at evallimit, a run off by one, a
  stalemate with a win, an openingend under another seed (G6a to G6d), a row's position with its halfmove field + 1
  (G7), the mate result's sign (G8), a whole game written as an opening end (G9).
- S, the server from the day's real programs: the real worker and engine (run `cont`, slot 1, piece_games 2, N12's
  six openings, played to the fence: pieces of 187, 127 and 148 rows), the real packer with the official converter
  (three binpack offers) and, on a copy, without one (three raw offers); the published a1 receipts every home. The
  fetch is stood in by a byte copy.
- P1 the three verdicts byte for byte as built from the server's own pieces (rows 86, 101, 0, 127, 81, 67; C2 462);
  P2 the index, 6 entries with their state and bind; P3 a second pass changes nothing; P4 a removed verdict is
  written again with the same bytes.
- P4b 2.2's required stop between the index and the verdict: a folder at the verdict's scratch name makes the write
  fail (exit 4) after p1's entries went in; once removed, the same verdict and no entry twice.
- P5 the raw offers give the binpack offers' verdicts and index byte for byte. P6 the converter missing: WAITS 3, no
  verdict, no entry; with it, P1's verdicts. P7 a kept member changed after a1: p1 WAITS naming its kept bytes, p0
  and p2 judged.
- P8 refused pieces, forged before a1 so that a1 receipts them: a raw byte (why "transport"), the seal's rows + 1
  (the seal's fields: rows), a bind line with raw_sha256 made to fit (why "records: binding"), the seal's ids_digest.
- P9 another record already in the index under (1, 4): exit 0, P1's verdicts, the index keeps the first, one
  conflict record with both sides; a second pass writes nothing. P9b the record and p1's verdict removed (a stop
  between the index and the record): found again, the same bytes. P9c the first entry changed: the new pair under
  the next name.
- P10 2.2's "recovery after a stop inside a transaction": another process ends inside a write transaction of the
  index, its rollback journal left behind; the next pass sees the committed entries only and writes the same verdict.
- P11 a converter that ends 0 with another text: one score changed (P11a: it rebuilds, into other bytes than the
  seal's) and no plain text at all (P11b: it does not rebuild); each WAITS 3, no verdict, no index entry; then the
  official converter: P1's verdicts (P11c).
- P12 the index and p2's verdict removed after a pass: exit 4 naming the lost index, no index made, p2 not written;
  then `content/` moved aside: P1's verdicts byte for byte and the 6 entries again.
- X0 to X3: no run header at home (nothing to do, exit 0); drawply below writeminply, the list rule without
  `--openings`, an openings file with one byte more (each exit 3, nothing written).

Counts: the test 66 of 66, twice. A stand-in that judges nothing: 17 of 64, twice. All 21 plants exit 1. The
plants: the reservation's comparison off; the FEN comparison off; the score limit off; the draw run not counted;
the castling alias accepted; S not compared; R not compared; the end FEN not compared; the mate sign off;
raw_sha256 not compared; ids_digest taken from the seal; bindings not checked (every bind line made the binding of
its record before parsing); the verdict written before the index; a converter failure judged as refused; the kept
bytes not hashed again; an openingend accepted without home's reservation ending; an index clash overwriting the
first entry with no record; a clash with no record; a binpack that rebuilds into other bytes refused; a binpack text
that does not rebuild refused; the lost-index check off. FAIL lines per plant, in that order: 2, 1, 1, 24, 2, 3, 1, 1, 1, 4, 1, 1, 1, 2, 1, 1, 4, 4, 3, 2, 1; each plant
fails the case written for it.

Corrections to the known answers, each made before the run it concerns: G4's castling stands at ply 12 (row 4),
not where my first text put it; P4b's folder stands at the verdict's scratch name, because a folder at the verdict's
own name is taken as judged and skipped. Two design changes, each written into the known answers as CHANGED before
the changed code, and each after a complete chain of the design before it (kept and superseded): D6 (the conflict
record instead of exit 4; first design 53 of 53 and 16 plants), with P9 rewritten and P9b, P9c, P10 and plants 17,
18 added; D4's binpack rebuild as a local outage (second design 59 of 59 and 18 plants), with P11 and plants 19, 20
added. A third change came from my bug hunt on a2 before publication: on a copy of a FINISHED test home, the index
removed, the next pass built a new index holding only the new piece's games, with exit 0 and no word (third design
63 of 63 twice and its 20 plants; I edited the program during that chain's last plant, so that plant may have run
on the edited program, and the final chain supersedes that chain whole); now P12 and plant 21.

## Measured on the home machine, for the home plan (2.4's content rate and volume)

- The rules replay: 12,047 rows a second on one core beside the machine's other work (record.parse 735,154 rows a
  second). A day of 2 billion kept rows is about 2.2 billion raw rows in 23 hours, 26,500 rows a second on average:
  one a2 process falls behind by about 2.2 times, so keeping pace needs at least three cores at full speed, or the
  content check ends after the day (custody, C1, is not delayed by it). Whether it must keep pace is yours to say.
  If so, a partition `--part K/N` (N processes on disjoint pieces; the index already takes concurrent writers one
  transaction at a time) is a small addition with its own test.
- The index: 294 bytes a game with a2's own schema and statements (200,000 entries in one transaction a piece:
  58,736,640 bytes; 15,229 entries a second written), so about 6.5 GB for 22 million games. The digest and the bind
  as 32-byte blobs would save about 130 bytes a game.
- The counts are read from every verdict at every pass: at a day's end about 44,000 verdicts of 500 games, an
  estimated 15 to 20 s a pass. A running tally can replace it if passes become frequent.

## Against the agreed documents (read beside the code before this message)

- 2.2's verdict keys are all there under their own names; mine has more (D5).
- 2.2's last required negative says "refused by the reservation": here the GAME is set_aside and the piece judged. A
  piece is refused whole only for its transport or for seal fields that do not describe its bytes (2.2 (i), (ii)).
- 2.2's index is "keyed by rows_digest, each entry (round, slot, counter, game, piece)": mine is keyed by (slot,
  counter) with a lookup index on rows_digest and every record's state and bind beside it. Equal games are found by
  the digest; one entry per id is what makes two records under one id visible.
- "The live write-ahead and temporary bytes count in the volume bound": the index uses SQLite's rollback journal. A
  writer stopped inside a transaction leaves it (8,720 bytes in P10); the next open undoes the transaction, and the
  file stays until the next write. The volume bound itself is the home guard's.
- The required case "Astra's three games" decides CREDIT, so it is stage b's, as credit is.

## What a2 does not do (named so that nothing falls between)

- credit, repeats (`same_rows_as`), the first eligible game in the frozen order, and A26's choice between
  conflicting records with its engine replay: stage b. Two requirements on stage b from here. (1) a2 judges every
  receipted piece, also one that a1 has marked as a fork or counts in an interval conflict (it judges the bytes home
  holds), and C1 stops before a fork but not at an interval conflict (2.1 defines C1 by the chain alone), so stage b
  credits only pieces inside C1 and decides a1's interval conflicts itself; the index holds every game's round and
  counter for that. (2) `conflicts/` is ONE folder for 2.3's records of both kinds: a2 writes "two records under one
  id" as `<id>.json`, then `<id>.2.json`, ... (create-only), stage b writes the interval overlaps under the same
  scheme, and a2's count line counts the records in the folder, whoever wrote them;
- the engine replays of the first hour's fixed games and the spot samples (recorded apart, 2.2): not built;
- a1's interval conflicts (an overlap, or an interval outside its round's range) that hold no common record: a1
  counts them, stage b decides;
- the volume bound and the progress lines (2.4): the home guard;
- Linux: home runs on the home machine; a2 ran on Windows only.

## To Astra's 221646Z question (workloads/MANIFEST.json)

The comparison: the PC's loop configuration file, which `make_workloads.py` hashed, has sha256
bf11a7b495be31d8bd59cdea8af66c4ee67e762aabfdcb525f2f7c7990e1a52e today; MANIFEST.json's `config_sha256` is the same
digest. The file has not changed since before the workloads were made.
