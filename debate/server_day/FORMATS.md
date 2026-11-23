# FORMATS.md: every file the server day writes, field by field

Editor: Fable. **Version 2.1**, written at 2026-11-23T21:09:50Z (Fable's clock). Version 2 (`82b9ac6`) got CHANGE from both
seats (Astra `133900Z`, `133940Z`, `134153Z`; Neon `133945Z`, `134130Z`): ten points, all accepted in my `204334Z`.
Since then: Astra `134405Z` (the draw rule, confirmed by Neon `134912Z` and by my read of the source),
`134704Z` (canonical order of equal games), `135234Z` (two zero-row fixtures), `135328Z` (a second machine, the
real deadline). Everything new is marked **[2.1]**. **PROPOSED: your votes, please, before the PC builds the
home side to it.** Nothing here exists in code yet unless a line says so.

## 0. Rules for all of them

- **One line = one record = canonical JSON:** ASCII, keys sorted, no spaces (`sort_keys=True,
  separators=(",",":")`), ended by one LF. No key twice. **[2.1] No floating-point number anywhere:** every
  number is an integer; a share is two integers (`kept_rows`, `raw_rows`), a rate is an integer in thousandths
  of a row a second, a time is a text `YYYY-MM-DDTHH:MM:SSZ`. A reader refuses a float, `NaN`, `Infinity`, a
  key twice and any byte outside 0x20..0x7e inside a line.
- **A fingerprint is the sha256 of exact bytes that are named.** No record contains its own fingerprint; it is
  always written OUTSIDE the bytes it covers.
- **Two kinds of file.** An IMMUTABLE file (header, schedule, identity, seal, offer, range seal, fence, terminal
  inventory, receipt, verdict, round output) is written once and never rewritten. An APPEND-ONLY file (journal,
  packer mode, progress) gets whole lines, each flushed. **At a restart only complete, valid, LF-ended lines
  count.** A damaged line that is NOT the last stops that slot and is kept as it is. An unfinished LAST line is
  dropped only when the durable evidence it would have described (named at each file below) agrees with the line
  before it; an interrupted append never makes a completed game.
- **[2.1] Publication is create-only** (Astra `133940Z`, `134153Z`; Neon `134130Z`). A file: written under a
  temporary name in the SAME folder, flushed to the disk, then `os.link(temporary, final)`, the folder flushed
  where the system has that, then the temporary name removed. When `final` exists already: equal bytes = done
  (the temporary copy is removed); other bytes = BOTH are kept (the newcomer as `<final>.conflict.<first 12 hex
  of its sha256>`) and that writer stops with a named fault. A folder (a round's output): renamed onto a name
  that must not exist. A plain rename over an existing name is never used for an immutable file. The machine
  check proves that hard links work on every volume used; the Windows writer at home gets its own rehearsal on
  the PC (two writers at once, and the power cut between link and removal).
- **[2.1] One grammar for names, with limits.** run `[a-z0-9]{1,32}`; slot 0..999, written `w` + 3 digits;
  counter 1..99,999,999, written `g` + 8 digits; game id `<run>-w<NNN>-g<NNNNNNNN>`; piece index 0..999,999,
  written `p` + 6 digits; a piece's key `w<NNN>/p<NNNNNN>`; round 1..9,999, written `r` + 4 digits; epoch
  1..9,999; schedule 1..999 (0 names the pilot's ranges). A name that does not fit, or a number outside its
  limit, is refused BEFORE it is used as a path or a number.
- **[2.1] Nothing travels plain** (the owner's requirement; Neon `134130Z` point 1). Every file that is fetched
  is a WIRE file: `<name>.zz` = zlib level 6 of the canonical bytes, made by the packer beside the canonical
  file, unless the file is packed already (`.meta.xz`, `.raw.zz`, `.binpack`: the PC measured five packed row
  files, 1,022,512 bytes, at 0.9375 with zlib 6 and 0.9303 with lzma 6, so a second pass over them is not
  made). **Identity is always the sha256 of the DECODED canonical bytes**; a receipt records the wire file's
  length and sha256 beside it, and the wire bytes as fetched are what home keeps.
- **On the day there is ONE immutable offer for a logical piece:** after a broken connection the same saved
  bytes are copied again. Another seal at an index that has one is a FORK (2.1).
- **Nothing travels to the server during the day.** No acknowledgement, no receipt. "Outstanding" is computed
  at home: seals SEEN at home minus custody receipts held. What home has not seen is UNKNOWN until the terminal
  inventory arrives; no report calls it zero.
- **The plain records stay on the server too:** `closed/p<NNNNNN>.raw` lies beside its offer for the whole
  lease (D2). **Every immutable record below except the header itself carries `run_fingerprint`, and every
  record that belongs to a slot, a piece, a round or a game carries those keys** (`slot`, `index`, `round`,
  `game`), so that no record is joined to another by its file name alone.
- **Every reader states what it verified.** "structure holds" is a different verdict from "content accepted".
  Only home gives the second.

### 0.1 [2.1] The plain record of one game, byte for byte (`closed/p<NNNNNN>.raw` is records one after another)

```
game <id> opening <m1> ... <mk>LF      k opening moves, each [a-h][1-8][a-h][1-8][qrbn]?; with k = 0 the line is `game <id> opening`
sent <the position line exactly as it was written to the engine>LF        or:  sent noneLF
<row>LF                                 0 or more, each exactly as the engine wrote it: sg <ply> <score> <move> <six-field position>
<end>LF                                 the engine's `sgend ...` line unchanged, or:  openingend plies <k> reason nomoves
bind <64 hex digits>LF
```

Printable ASCII and LF only; nothing before, between or after records. **The binding** = sha256 over the three
parts, in this order: the text `forge-serverday-bind-2` and LF; the run's fingerprint (64 hex digits) and LF;
every byte of the record from the `g` of `game` through the LF of the end line. So it covers the id, the
OPENING (Neon `131400Z`: this morning's did not), the sent line, every row and the end line, and it ties the
record to this run's header. `raw_sha256` of a seal is the sha256 of the piece's bytes as they lie.

**The rows digest of a game** (the first plan's W5 (e): "the hash of its ordered five-field rows") = sha256
over every row line with its LF, in order, followed by the line `result <-1|0|1>` and LF, with the result of
the end line. It names the five fields (ply, score, move, position, result) and nothing else: not the id, not
the opening. A game without rows has NO rows digest (2.2).

## 1. On the server

### 1.1 Run header `RUN.json` (one record; written before the PILOT, never again)
`schema` 2; `run`; `lease_start_utc`, `lease_end_utc`, `hard_cutoff_utc` (the latest D that D5 allows; a
schedule can only tighten it); `boot_id`; `package` (sha256 of the package's hash list, the one with three YES);
`engine_sha256`, `net_sha256`, `options_sha256` (the frozen option list in its order), `game_line`;
**[2.1]** `opening_rule`: `{"kind":"seed","plies":8,"root_seed":".."}` or `{"kind":"list","sha256":"..","count":N}`
(Neon `134130Z` 5.2: a structure, not a text); `slots` (ordered integers); `piece_games`; `pilot_ranges` (rows as
in 1.2, each with `"schedule":0`). It holds NO time or range that the pilot has to teach us. Fingerprint of the
run = sha256 of this file.

### 1.2 Schedule `SCHEDULE.<n>.json`, n = 1, 2, ... (immutable, each links to the one before)
`schema`, `run_fingerprint`, `n`, `prev` (sha256 of schedule n - 1; for n = 1 the text `first`), `evidence`
(sha256 of the pilot's report, or of the report that justifies this change), `cutoff_utc` and
`dispatch_end_utc` (never later than in the schedule before), and `ranges`: rows
`{"slot":K,"round":r,"first":a,"last":b,"short":false,"schedule":n}`, **one row a slot and round** (slots may
end a round at different counters; a slot that plays nothing has no row and is still named in 1.9).
**[2.1] All ranges of a slot, the pilot's included, are disjoint and rise with the round.** A later schedule
may ADD ranges and SHORTEN a range in which no game was dispatched yet; it never changes a range that has
started. A worker reads the highest valid schedule before every reservation.

### 1.3 Slot identity `w<NNN>/IDENTITY.json` (one record, written once by the slot's first worker)
`schema`, `run`, `slot`, `run_fingerprint`. A worker that finds another identity, or a journal without one,
stops before it changes anything. **At EVERY start a worker hashes the engine file it is about to run and stops
when it is not `engine_sha256` of the header** (six builds of one source passed every known answer and differ
in their bytes). **[2.1] A worker that starts under a `boot_id` other than the header's stops too** (the
machine was started again, or this is a copy of the spool on another machine: Astra `135328Z`, two restored
copies both played g00000097). Going on after that needs `RESUME.<n>.json` (immutable: `run_fingerprint`, the
old and the new boot id, every slot's `last_index` and `last_seal` as found, the machine check's verdict),
which only a NEW admission writes; the next epoch line names it. No program writes it by itself on the day.

### 1.4 Slot journal `w<NNN>/journal.txt` (append-only; the slot's working memory)
```
{"t":"epoch","epoch":E,"prev_epoch":E-1,"last_index":I,"last_seal":"<sha256 or genesis>","boot_id":"..","resume":null}
{"t":"done","game":"<id>","index":I,"end":<bytes of the open piece after this game>,"rows":N,"bind":"<sha256>"}
{"t":"noselfgame","game":"<id>","index":I,"end":..,"plies":P,"bind":".."}
{"t":"failed","game":"<id>","why":".."}          thrown away whole; the same id is played again
{"t":"refused","game":"<id>","why":"binding"}    A23: not credited, not retried
{"t":"unfinished","game":"<id>","why":"cutoff"}  ended by D5: no search after D, the id is named
{"t":"closed","index":I,"seal":"<sha256 of 1.5's file>"}
{"t":"ended","epoch":E,"last_index":I,"last_seal":"..","why":"cutoff|ranges done|finalizer"}
```
**Two kinds of game without rows, never mixed** (Astra `135234Z`, both are permanent fixtures): `done` with
`rows` 0 is a COMPLETED game whose end line is the engine's (root seed `edge2715`: the eighth reserved ply
mates, the game command IS sent, `sgend result -1 reason mate plies 8 run 0 searches 0 nodes 0 ...`);
`noselfgame` is an opening after which the worker's own board has no legal move, so no game command is sent
(root seed `edge2649`: mate after five plies, `sent none`, `openingend plies 5 reason nomoves`). One writer: the
slot's folder is locked for the life of the worker, and `epoch` rises by one at every start; the first epoch
line has `prev_epoch` 0, `last_index` -1 and the genesis text as `last_seal`; every later line belongs to the
epoch line above it. **[2.1] At a start** (Neon `134130Z` 5.3, 5.4): a dropped last line needs the open piece's
bytes up to the `end` of the line before it; a seal file that exists for an index WITHOUT its `closed` line is
verified against the plain bytes and the journal and the line is appended, never a second seal; an open piece
longer than the last `end` is cut back to it. **A free lock is NOT the end of a slot** (Astra `134153Z`: a
killed worker frees its lock and leaves no record): only the `ended` line is.

### 1.5 Piece seal `w<NNN>/closed/p<NNNNNN>.seal.json` (one record; the logical identity of a piece)
`schema`, `run`, `run_fingerprint`, `slot`, `epoch` (the epoch that closed it), `index` (rises by one through
the whole day, across epochs), `prev_seal` (sha256 of the seal file of `index - 1`; for index 0 the text
`genesis:<run fingerprint>:<slot>`), `raw_sha256`, `raw_bytes`, `games`, `rows`, `first_game`, `last_game`,
**[2.1]** `first_counter`, `last_counter` (an id does not name its piece; the counters do: they rise strictly
inside a piece and from piece to piece of a slot, and lie inside the slot's ranges), `ids_digest` (sha256 over
`<id> LF <state> LF <bind> LF` for every game in order, the ones without rows too), `round`, `schedule`.
`games` is at least 1: an empty piece is never sealed. A piece never holds games of two rounds: the last piece
of a slot's range is closed at the range's end, however short.

### 1.6 Offer `out/w<NNN>/p<NNNNNN>.offer.json` (packer; published LAST)
`schema`, `run_fingerprint`, `slot`, `index`, `seal_sha256`, `form` ("binpack" or "raw"), `members`: list of
`{"name","codec","bytes","sha256","wire_name","wire_bytes","wire_sha256"}` with `codec` one of "none", "lzma",
"zlib" (`bytes` and `sha256` are of the member as named; the `wire_*` fields are of the file that is fetched,
equal to them when the member is packed already). **The member names are fixed by the form:** `p<NNNNNN>.seal.json`
always; for "binpack" `p<NNNNNN>.binpack` and `p<NNNNNN>.meta.xz` (lzma 6); for "raw" `p<NNNNNN>.raw.zz` (zlib 6).
No other name, and no name with `/`, a backslash or `..`. EVERY file of the offer is a member. There is NO index
file: a fetch lists the offer files, and 1.9 is built from the seals. **[2.1] A piece without a single row
goes out as "raw" at once**, without the converter and without counting as a failure of it.

**The packer's mode `out/PACKER_MODE.jsonl`** (append-only): `{"t":"mode","mode":"normal"|"fallback","at_utc":"..",
"why":"..","piece":"w<NNN>/p<NNNNNN>"}`. The converter gets ONE bounded attempt a piece; three failures in a row
write `fallback`, which survives a restart; in that mode every piece is offered as "raw" at once and the
converter is probed now and then on a piece that is ALREADY offered, **[2.1] writing to a scratch folder only**;
a probe that passes writes `normal`. No sealed input is ever removed in either mode.

### 1.7 Range seal `ranges/r<NNNN>.w<NNN>.seal.json` (worker, when its last piece of the round is closed)
`schema`, `run`, `run_fingerprint`, `round`, `slot`, **[2.1]** `epoch`, `schedule`, `first`, `last`, `short`,
`complete` (false for a range that D cut), `first_index` (-1 when the range has no piece), `first_prev_seal`,
`through_index`, `through_seal`, **[2.1]** `games`, `rows`, `raw_bytes` (sums over the range's pieces), and
`dispositions`: the count of the range's ids in each final state (done, noselfgame, refused, unfinished,
never_dispatched), with every id that is not `done` listed.

### 1.8 [2.1] The end of the day on the server (Astra `133940Z`, `134153Z`; Neon `134130Z`)
1. **The fence first:** the guard publishes `FENCE.json` (`run_fingerprint`, `at_utc`, `cutoff_utc`, `why`) at D
   or at an earlier stop. No worker reserves a game once it exists; a worker inside a game ends it by D5 and
   records it `unfinished`.
2. **A slot is ended only by its durable `ended` line.** Each worker seals its last piece and its range seals,
   writes `ended`, releases its lock.
3. **A slot without that line and without a live writer** gets the seal-only FINALIZER under a new epoch: it
   verifies the open piece against the journal, seals what is complete, records the cut game `unfinished`,
   writes the range seals and `ended` with `why` "finalizer". It never starts an engine. What it cannot verify
   stays as it is and the slot is `unreconciled`: the day then closes PARTIAL for that slot's open range.
4. ONLY when every slot is `ended` or `unreconciled` does the packer make its last pass; only then is 1.9
   written. A packer never ends while a slot is neither.

### 1.9 Terminal inventory `TERMINAL.jsonl` (guard, after 1.8; D13)
Line 1 the run header again (same bytes as 1.1), line 2 the last schedule (same bytes), line 3 the fence. Then,
per slot in the header's order: `{"t":"slot","slot":K,"state":"ended"|"unreconciled","epochs":[..],"last_index":I,
"last_seal":".."}` (also for a slot with no output: `last_index` -1), one line a piece `{"t":"piece","slot":K,
"index":I,"seal":"..","raw_bytes":n,"offer":"<sha256>"|null,"offered_bytes":n,"packed_bytes":n|null}`
(**[2.1]** for a piece the packer never offered: `offer` null, `offered_bytes` 0, `packed_bytes` NULL, which
reads "unknown" and is never counted as zero work or as a verified margin; its `raw_bytes` are exact), one line
a range seal, and one line for every id that is not `done`:
`{"t":"id","game":"..","state":"noselfgame|refused|unfinished|never_dispatched","why":".."}`. Last line the
footer: the counts of slots by state, pieces, offered bytes, raw rows, and of ids in each state,
`completed_at_utc`, `cutoff_reached`, `stop_reason`, and `fingerprint`, the sha256 of every byte before that
line. A file without its footer is an incomplete inventory.

## 2. At home

**No home program holds the day's identities in memory as text** (the PC measured this morning's way: 1,018
bytes a credited game, 15.5 GiB at 16.4 million games, at every pass). Everything below is one small file a
piece or a round, plus ONE index on the disk (2.2).

### 2.1 Stage a1, custody receipt `custody/w<NNN>/p<NNNNNN>.receipt.json`
`schema`, `run_fingerprint`, `slot`, `index`, `epoch`, `first_counter`, `last_counter`, `offer_sha256`,
`seal_sha256`, `members` (as offered, with the wire length and wire sha256 as FOUND on the home disk), `kept`
(where the wire bytes lie unchanged; a path RELATIVE to the day's home folder), `at_utc`. Written only after
every member is on the home disk under its final name and was hashed again FROM the disk, wire bytes and
decoded bytes both. **A repeat of the same offer is confirmed again only after the kept bytes were opened and
hashed again; when they are gone or differ, they are fetched again first.** Other bytes under an index that has
a receipt: a FORK, both kept, that slot's credit stops, nothing is replaced. **Two counts:** RECEIVED (a
durable receipt, in any order) and **C1 = chain-eligible** (unbroken from the genesis); both are shown.
- **[2.1] Epochs are judged along the index, never by arrival** (Astra `133900Z`; Neon `134130Z` 2): for two
  held indices i < j of a slot, `epoch[i] <= epoch[j]`, checked piece by piece along `index` and `prev_seal`.
  "Older than the newest held" is NOT a reason to refuse. Tests: pieces with epochs [1, 1, 2] reach the same
  chain in all six arrival orders; epochs [1, 2, 1] by index never become chain-eligible in any order.
- **[2.1] One interval a piece** (Astra `133900Z`): the receipts of a slot give, from the disk, the interval
  `[first_counter, last_counter]` of every held piece. Two held pieces of a slot whose intervals overlap, or an
  interval outside the slot's ranges, open a conflict (2.3); nothing else needs the ids of another piece.

### 2.2 Stage a2, content verdict `content/w<NNN>/p<NNNNNN>.verdict.json`
**What this stage proves, exactly:** (1) TRANSPORT: the offered form gives back the sealed plain bytes
(`raw_sha256`) and every record's binding holds (0.1); that, and nothing else here, is what proves a score.
(2) RULES: with the reader's own move rules, the opening it computed for that id, every move's legality, every
row's position and ply, and the end. It does NOT repeat a search; an engine replay happens only for the first
hour's fixed games, for an A26 conflict and for small spot samples, and is recorded apart.

**[2.1] The rules replay, from the engine's source** (`uci.cpp`, the self-game loop, read by all three seats;
Astra `134405Z`). In its order: no legal move, a rule draw or the ply limit end a game BEFORE a search; then
the search; a mate score, then a score at or past the limit, end it BEFORE a row is written; the row is
written; the run of small scores is counted and at its length the game ends as `drawadj` BEFORE the move is
played; the move is played. **The reader takes the game command's values (first written ply, draw ply, draw
score, draw count, score limit, ply limit) from the run header's `game_line`, never from the record** (Astra
`140702Z`: an unchanged zero-row game fits several policies; the bytes of a game cannot select one). With R
rows, M moves in the end line, S = `searches`, and every searched ply at or past the first written ply (so in
the day's 8-ply openings; a searched ply before it leaves no row and R is smaller by those):

| `reason` | S | R | the last row's move |
|---|---|---|---|
| `mate`, `stalemate`, `rule`, `plylimit` | M | M | is move M of the end line |
| `matescore`, `evallimit` | M + 1 | M | is move M of the end line (the search that ended the game left no row) |
| `drawadj` | M + 1 | M + 1 | is NOT in the end line: it must be legal on the end line's position and is not applied to it |

Row k (from 0) has ply = opening length + k and the position before move k; `plies` = opening length + M; the
end line's position is the position after the M moves; `run` is the count of small scores at the end; the end
named by `reason` is checked on the reader's own board in the engine's priority (a `rule` draw: material, the
fifty-move count, a third occurrence). A move is compared as the engine's own text: python-chess takes `e1h1`
for `e1g1`, the engine does not (Astra `140404Z`), so tokens are compared after the reader has written its own
move in standard form. **Required positive controls, frozen:** one game of each of the seven reasons and one
`openingend`, among them a `drawadj` game (N12), both zero-row fixtures of 1.4, a stalemate, the three kinds of
rule draw. **Required negatives:** the last `drawadj` move applied to the end position; a row added after a
`matescore` end; a count off by one in each column of the table; a castling alias in a row AND in the end
line; an opening of another id with a matching binding of its own (refused by the reservation).

The verdict: `schema`, `run_fingerprint`, `slot`, `index`, `seal_sha256`, and per game in order
`{"game","state","rows","rows_digest"}`: `accepted` (both checks hold; `rows` may be 0 when the record holds the
engine's full end line and the replay agrees; then `rows_digest` is null), `noselfgame` (the reader's own board
has NO legal move after the opening IT computed for that id; with a legal move left it is `set_aside`), or
`set_aside` with the reason. Count C2 = rows of accepted games.

**[2.1] Equal games: the index on the disk** (the first plan's W5 (e); Astra `133900Z`, `134704Z`; Neon
`134130Z` 4). One index for the day, keyed by `rows_digest`, each entry `(round, slot, counter, game, piece)`.
- It is written for a piece BEFORE that piece's verdict is published; a stop between the two is a required
  test (the restart finds the entries and writes the same verdict; no entry twice).
- **Credit goes to the first ELIGIBLE game in the frozen order (round, slot, counter), never to the first
  arrival.** The others are `repeat` with `same_rows_as`, counted, never credited. A different history that
  shares a position is another digest and stays. A game without rows has no digest and keeps its own identity
  and disposition.
- Stages a1 and a2 go on in any order; who is credited is decided at publication (2.3), when every earlier
  round's eligibility is final. When A26 takes a candidate out before that, the next eligible one is chosen
  from the kept evidence.
- Required case (Astra's three games): round 1 holds g1 (+19) and g2 (the same row with +42), round 2 holds g1's
  rows under a fresh id; forward and reversed delivery give the same kept rows.
- The backend is a choice (Astra measured SQLite: 82,591 to 94,885 entries a second, 22.6 MB for 490,010); the
  acceptance is equality in both orders, recovery after a stop inside a transaction, and room: the live
  write-ahead and temporary bytes count in the volume bound, and a reader closes its transaction at once.

### 2.3 Stage b, round output `rounds/r<NNNN>/` (published ONCE, by a rename of the folder onto a free name)
Made in a private staging folder from the round's range seals and verdicts, in the fixed order (slot, counter),
reading each kept piece again FROM its custody bytes with its hash checked: `kept.<form>` (the filter's output,
packed) and `report.json`: `schema`, `run_fingerprint`, `round`, `status` ("complete" or "partial"), the sha256
of every range seal used, games and rows in, `missing_ids`, `set_aside_ids`, `conflict_ids`, `repeat_games`,
`kept_rows` and `raw_rows` (the share, as two integers), **C3**: games rescored by reason, tablebase probes made
and FAILED (must be 0), games left out by rule, **C4**: kept rows, the sha256 of `kept.<form>`, and the sha256
of every frozen input (filter code, config, net, options, the tables' list).
- **[2.1] A round waits while anything of it is still on the way** (Astra `133940Z`): it is published when
  every range seal and piece of it, and of every EARLIER round, is at home and judged, or when the terminal
  inventory has closed the day; then, and only then, as `partial` if something is missing. A round with a
  missing id, a set-aside game, a failed probe or a missing range seal is `partial` and credits nothing. A
  second publication of a round does not exist: the folder's name is taken.
- **[2.1] A conflict is a record of its own**, `conflicts/<game id>.json` (immutable): the id, both pieces'
  keys and seals, both bindings, how it was found (an interval overlap of 2.1, or two records under one id).
  Both pieces' credit for that id stops there. The first plan's A26 decides: the record of the LOWER piece
  number is the only candidate, and only with its binding and an independent engine replay from the
  reservation giving the same record; anything else is a deficit of that id, written into the round's report.

### 2.4 Progress `progress.jsonl` (append-only; home guard, one line an hour, also when the server is silent)
`at_utc`, `server` ("ok", "unreachable since ..", "stale since .."), C0 as SEEN at home (with the words
"unknown beyond"), RECEIVED, C1, C2, C3, C4, the three lags with the oldest piece of each, the rates of the
trailing hour and since the start for the server and each home stage (integers, thousandths of a row a second),
the needed rate, set-aside counts, repeats, conflicts, failed probes, games rescored in 10,000, rounds complete
through stage b, equal games in the last 10,000, free room above the floor on every volume of both machines,
and the row of D4 that holds. **The reconnect margin**: time left to the lease's end less the EARLIEST possible
finish of what is outstanding, in two forms that are never mixed: (a) from totals, max(outstanding offered
bytes / measured fetch rate, pending rows / measured content rate), printed with the words "impossible on this
bound" or "possibly feasible, unverified" and never as "safe"; (b) piece by piece, where measured times a
piece exist: fetch_finish[i], then content_finish[i] = max(fetch_finish[i], content_finish[i-1]) +
content_time[i], plus the terminal inventory. Only (b), from a rehearsal at full piece size, may say that a
late reconnect still ends in a clean release.

### 2.5 Closing report `CLOSING.json`
The count at D and the count after the drain, each with its time; the three classes (complete rounds; ids
without rows, both kinds apart; incomplete ranges with every missing id); repeats and conflicts with their
ids; D12's four states, each with its evidence or "not yet"; D13's verdict CLEAN or DECLARED PARTIAL with the
exact deficit (known missing bytes and unknowable rows are separate fields; an `unreconciled` slot is named).

## 3. The planted tests these formats must pass [2.1: in two lists, Neon `134130Z` 5.5]

**A. After these the day must still be able to close CLEAN** (the event is handled and leaves no deficit):
pieces 0 and 2 delivered before 1 (RECEIVED 2, then C1 of all three once 1 is there); a correctly linked
predecessor that arrives late; epochs [1, 1, 2] in all six arrival orders; an unchanged offer fetched again
(confirmed again from the kept bytes, no count moves); the kept copy removed before a repeat (fetched again);
the real third game of the six (a completed game without rows) and both zero-row fixtures, each in its own
state; slot 0 ending a round at g10 and slot 1 at g9; a torn LAST journal line after its verified repair; a
seal without its `closed` line; a worker that seals after the packer's earlier look; a stop between the index
entry and the verdict, between link and removal of a publication, between the offer and anything written after
it; a piece without rows (offered as "raw"); the converter failing three times (fallback mode, every piece
still offered); a round whose last piece arrives after a later round's; Astra's three equal games in both
delivery orders.

**B. These must WITHHOLD the clean verdict and name the slot, id or piece:** two different seals at one index;
epochs [1, 2, 1] along the index; two held pieces of a slot with overlapping counters; a counter outside the
slot's ranges; a game line without rows left out; a slot without output left out of the footer; the terminal
file cut before its footer; a spool of another run under a new run id; a spool copied to a second machine
(another boot id, no `RESUME`); a rebuilt engine with other bytes; a "no moves" record where 27 moves exist; a
record whose opening line was changed (the binding fails) and one whose opening AND binding were changed (the
reservation fails); a schedule that moves a started range; a converter that flips a result; a torn MIDDLE line
of a journal; a record with a key twice, a float, a control byte; a malformed game id; a search that runs past
D (Astra `135328Z`: processor time of the engine process read at D and after the stop); a reservation inside
the guard; a slot with a free lock and no `ended` line that the finalizer cannot verify; a never-offered piece
counted as zero work; a second publication of a round; an id with two different complete records.
