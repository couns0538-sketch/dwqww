# FORMATS.md: every file the server day writes, field by field

Editor: Fable. **Version 2.3**, written at 2026-11-23T22:04:16Z (Fable's clock): 2.2 (sha256 `02bd23ad...`) has AGREE from
Astra and from Neon. 2.3 changes nothing that 2.2 fixed; it adds what all three agreed after it, each marked
**[2.3]**: Neon's four closures (`143000Z`: a wire file and a publisher for every fetched control file; the
seal's own fields recomputed at home; the packed form proved against the plain bytes before the rules replay;
`instance` with empty and placeholder values), Astra's retry of a round after a LOCAL outage (`144620Z`; Neon
`145000Z` AGREE), the record's two judgments with Astra's 23 vectors as known answers (0.1), and the thirteen
readings that writing the version 2 worker forced, each its own marked line so that a seat can say CHANGE to
one of them. **PROPOSED: your votes on these exact bytes, please.**
Version 2.2 was written at 2026-11-23T21:19:17Z (Fable's clock): 2.1 (`5f8a1f6`, sha256 `637d13f3...`) has
Astra's AGREE to both byte definitions of 0.1 and to its wire, chain, identity, equal-games and rules text, and
her CHANGE on three close and restart cases (`141212Z`); those three are 2.2's only changes, marked **[2.2]**.
Version 2.1 was written at 2026-11-23T21:09:50Z (Fable's clock). Version 2 (`82b9ac6`) got CHANGE from both
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
  **[2.3] Who publishes each wire file** (Neon `143000Z` 1), always create-only and beside its canonical file:
  the PACKER publishes `RUN.json.zz`, `SCHEDULE.<n>.json.zz`, `RESUME.<n>.json.zz`, `FENCE.json.zz` and
  `ranges/r<NNNN>.w<NNN>.seal.json.zz` as it finds their canonical files, and every member's wire file of an
  offer; the GUARD publishes `TERMINAL.jsonl.zz` after the footer. An offer's own wire file
  `p<NNNNNN>.offer.json.zz` is published LAST: after the plain offer and after every member's wire file.
  **The fetcher lists and fetches only `*.offer.json.zz`** (and the control files' `.zz`), so it can never
  take an offer whose members are still being written.
- **[2.3] Every immutable record carries `schema` 2** (reading 1). The lines of the append-only files carry
  none: a journal line's kind is its `t`.
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

**Known answers [2.2]** (Astra `141212Z`; recomputed on the PC with code of its own before this line was
written): for the first game of the published native fixture `ref/astra/fixtures/games.txt` (86 rows, result 0)
and a run fingerprint of 64 times the letter `a`, the binding is
`94b4fd15bf103b2800fb212ef9d76967b90ed6500e85f4737f6ad6cc72eaeaee` and the rows digest
`5902be33a13066ba77ff8f0f3f8cb29ce7eed8d5167bc471816899e253f6f70f`. Changing only the id or the opening changes
the binding and leaves the rows digest; changing a score or the result changes both. An index that outlives
a run stores the recipe's version (2) beside every digest.

**[2.3] Two judgments of a piece, never mixed.** (1) Its BYTES are refused whole, at the first byte or line
that does not fit: a byte outside printable ASCII and LF (a CR is one), a last line without its LF, an empty
line, a name outside the grammar of section 0, a line out of the order game / sent / rows / end / bind, a row
or an end line that is not in its shape (also under a binding that holds), a binding that does not hold in this
run. Bytes that fail are not a sequence of records of this run. (2) The MEANING of one record whose bytes hold
is judged apart, and a fault there sets that RECORD aside, never the piece: a sent line that is not the
position line of the record's own opening; an `openingend` with rows, with a sent line other than `none`, or
naming another length than its opening has; an opening that is not the one the reader computed for that id.
The writer uses the same judge of the parts as the reader, so a worker cannot seal a record its readers refuse.
**Known answers:** `cases/astra/record_v2_vectors.json` (11,361 bytes, sha256
`4fb382d0c350b0b20aa7d5184f5f55427669ff82ffc1b8963366c552a235032c`): 13 records that must be accepted with the
binding, length, hash, row count and rows digest it names, and ten byte streams that must be refused, each by
the check it names (another run; the id changed under the same bind; a score changed under the same bind; the
last LF missing; an LF between two records; CR LF; a run name in upper case; counter 0; a slot of four digits;
this morning's binding).

## 1. On the server

### 1.1 Run header `RUN.json` (one record; written before the PILOT, never again)
`schema` 2; `run`; `lease_start_utc`, `lease_end_utc`, `hard_cutoff_utc` (the latest D that D5 allows; a
schedule can only tighten it); `boot_id`; **[2.2]** `instance` (what names THIS machine and no copy of its
disk: the machine id, the hardware's product UUID and board serial, as the machine check read them); `package` (sha256 of the package's hash list, the one with three YES);
`engine_sha256`, `net_sha256`, `options_sha256` (the frozen option list in its order), `game_line`;
**[2.1]** `opening_rule`: `{"kind":"seed","plies":8,"root_seed":".."}` or `{"kind":"list","sha256":"..","count":N}`
(Neon `134130Z` 5.2: a structure, not a text); `slots` (ordered integers); `piece_games`; `pilot_ranges` (rows as
in 1.2, each with `"schedule":0`). It holds NO time or range that the pilot has to teach us. Fingerprint of the
run = sha256 of this file.
**[2.3] `instance`, exactly** (Neon `143000Z` 4): an object `{"machine_id":..,"product_uuid":..,"board_serial":..}`.
A value that is missing, unreadable, empty or a placeholder (`Not Specified`, `To Be Filled By O.E.M.`, `Default
string`, `None`, a UUID of zeros only) is written `null`. Beside it `instance_provable`: true only when the
machine id AND at least one of the two hardware values are not `null`. Two instances are EQUAL only when both
are provable, the machine ids are equal, at least one hardware value is not `null` on both sides and equal, and
no value differs; a value that is `null` on one side only is a difference, and a `null` never equals a `null`.
**[2.3] The list rule** (reading 8): with `kind` "list" the opening of counter c is entry (c - 1) mod `count`.
The paid day's header carries the SEED rule; the launcher refuses a list rule with more than one slot (two
slots would play the same openings).

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
old and the new boot id, `instance` as read NOW, every slot's `last_index` and `last_seal` as found, the checks
below with their evidence); the next epoch line names it. **[2.2] (Astra `141212Z`) The approved package's BOOT
GUARD writes it without a person, and only when all of this holds:** `instance` equals the header's (a boot id
alone cannot tell a restart from a copied spool); the lease and the absolute cutoff are unchanged and the clock
is trustworthy again (synchronised, and not before the last journal time); package, engine and net hash as in
the header; every slot's chain verifies from its genesis; no fence exists. Then the workers go on under a new
epoch. After D the same guard does seal-only recovery (1.8), never a search. Another or an unprovable instance
writes nothing and stays held until it is fenced and admitted anew. Two required cases, apart: a genuine
restart of the same machine (goes on by itself), and the spool copied to another machine (held).
- **[2.3] `RESUME.<n>.json`, its keys** (reading 6): `schema`, `run_fingerprint`, `n` (1, 2, ...), `prev` (sha256
  of RESUME n - 1; for n = 1 the text `first`), `old_boot_id`, `new_boot_id`, `instance`, `instance_provable`,
  `slots` (rows `{"slot":K,"last_index":I,"last_seal":".."}` for every slot of the header), `checks` (each
  check of the paragraph above with its evidence), `at_utc`. A worker reads `run_fingerprint`, `new_boot_id` and
  its own row of `slots`, and stops when any of them is not what it finds. An instance that is not provable
  (1.1) gets no `RESUME` from the guard: it holds for a person.
- **[2.3] When the engine is hashed** (reading 10): before the worker writes anything, whenever the start may
  run an engine, and again at every start of an engine process. A seal-only start (1.8) runs no engine and so
  hashes none.
- **[2.3] A started range that a later schedule changed** (reading 11) stops the worker BEFORE its epoch line;
  the lock and `IDENTITY.json` may exist by then, nothing else of that start does.

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
- **[2.3] The cut leaves its evidence** (reading 9; found while the worker was written). BEFORE the open piece
  is cut back: when the bytes beyond the last `end` begin with a whole game line of an id of this run and slot
  (judged by the grammar of section 0), that id lies in a range of the slot and has no `done`, `noselfgame` or
  `refused` line, the worker appends a `failed` line for it whose `why` says that its bytes were cut at a
  restart, makes that line durable, and only then cuts. The id is played again while the dispatch end allows
  it; otherwise it is `unfinished`. Bytes beyond the last `end` that are anything else are cut without a line.
- **[2.3] A `failed` id that was never played again is `unfinished`** in its range seal and in 1.9 (reading 7).
- **[2.3] `resume` in an epoch line** (reading 6): the first epoch line a slot writes under a boot that needed
  a `RESUME` names that file by its sha256; later epoch lines under the same boot carry `null`.
- **[2.3] `why` of the `ended` line** (reading 4): "finalizer" when this start found the dispatch end passed or
  the fence there and so played nothing; "ranges done" when every range of the slot is complete; otherwise
  "cutoff".
- **[2.3] No program concludes anything from a heartbeat** (reading 13). A worker may write one for people to
  look at. That a slot's writer lives is its lock; that a slot has ended is its `ended` line. Not the worker's
  work at all: the count rules of an end line (home, 2.2), whether the clock can be trusted (the boot guard,
  1.3), the wire copies (the packer).

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
**[2.3] Exactly** (readings 2 and 3): `dispositions` is an object with the five counts under those five names
and `"not_done"`: a list of `[<id>, <state>]` pairs in counter order. A range without a piece has
`first_index` -1, `first_prev_seal` null, `through_index` -1 and `through_seal` null.

### 1.8 [2.1] The end of the day on the server (Astra `133940Z`, `134153Z`; Neon `134130Z`)
1. **The fence first:** the guard publishes `FENCE.json` (`run_fingerprint`, `at_utc`, `cutoff_utc`, `why`) at D
   or at an earlier stop. No worker reserves a game once it exists; a worker inside a game ends it by D5 and
   records it `unfinished`. **[2.3]** (readings 5 and 12) The fence stops RESERVATIONS and never cuts a game:
   a game in progress ends by itself, or at D by D5. Its `cutoff_utc` is the D in force (the highest valid
   schedule's), copied, never a new time. Without a fence a worker reserves no game at or after the schedule's
   `dispatch_end_utc`, and every wait of a worker (for the engine, a lock, the disk) ends at D.
2. **A slot is ended only by its durable `ended` line.** Each worker seals its last piece and its range seals,
   writes `ended`, releases its lock.
3. **A slot without that line and without a live writer** gets the seal-only FINALIZER under a new epoch: it
   verifies the open piece against the journal, seals what is complete, records the cut game `unfinished`,
   writes the range seals and `ended` with `why` "finalizer". It never starts an engine. What it cannot verify
   stays as it is and the slot is `unreconciled`: the day then closes PARTIAL for that slot's open range.
   **[2.3]** (reading 9) It writes `unfinished` only on EVIDENCE: bytes of that game's record in the open piece
   beyond the last `end`, or a `failed` line never followed by a final line of the same id. An id of the range
   without evidence is `never_dispatched`. The journal has NO reservation line (it would cost one durable
   append a game); a seat that wants one says CHANGE.
4. ONLY when every slot is `ended` or `unreconciled` does the packer make its last pass; only then is 1.9
   written. A packer never ends while a slot is neither.

### 1.9 Terminal inventory `TERMINAL.jsonl` (guard, after 1.8; D13)
Line 1 the run header again (same bytes as 1.1). **[2.2]** Then the WHOLE schedule chain, one line a schedule
from 1 to n in order, each the same bytes as its file (the latest link alone cannot prove the ranges written
under an earlier one), or the single record `{"t":"schedule","n":0}` when no schedule was written after the
pilot's ranges (a pilot may stop before `SCHEDULE.1` exists; what it played still gets a reconciled release and
an exact shortfall). Then the fence. Then,
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
**[2.3]** `offer_wire_bytes`, `offer_wire_sha256` (of `p<NNNNNN>.offer.json.zz` as found on the home disk),
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

**[2.3] Before the rules replay, in this order** (Neon `143000Z` 2 and 3). (i) The offered form is turned back
into the plain bytes: for "raw" the decoded `p<NNNNNN>.raw.zz`; for "binpack" the `binpack` and the `meta.xz`
TOGETHER must give back `closed/p<NNNNNN>.raw` byte for byte. In both forms the result's sha256 is the seal's
`raw_sha256` and its length the seal's `raw_bytes`; a piece that fails here is not replayed and not credited.
(ii) From those bytes alone the reader recomputes `games`, `rows`, `first_game`, `last_game`, `first_counter`,
`last_counter` and `ids_digest` (`state` is `noselfgame` for a record that ends with `openingend`, otherwise
`done`), and each must equal the seal's field. A seal whose fields do not describe its own bytes is refused
whole, whatever its chain says.

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
  every range seal and piece of it, and of every EARLIER round, is at home and judged. **[2.2] (Astra
  `141212Z`) The terminal inventory proves that the SOURCE has finished sealing, not that home holds
  everything:** it can arrive before a valid offered piece, so it alone never makes a round `partial`. A round
  stays pending while a piece or range seal that a seen seal or the inventory names can still be fetched. A
  `partial` publication needs the home guard's `DRAIN.json` (immutable: `at_utc`, `why`: "lease ended",
  "source gone since .." or "declared stop", and every piece still missing with its wire sha256 and bytes, as a seen seal or the inventory names them); it never
  interrupts a transfer that runs or a check on data already in custody. Required case: one sealed range of
  two offered pieces and the inventory, in ALL SIX arrival orders (Astra `141417Z`: a rule that publishes on
  the inventory's arrival made four of the six partial), each a second apart, every piece passing: ONE complete
  round. A round with a
  missing id, a set-aside game, a failed probe or a missing range seal is `partial` and credits nothing. A
  second publication of a round does not exist: the folder's name is taken.
- **[2.3] A LOCAL outage is not a verdict on the games** (Astra `144620Z`, rehearsed with a table removed after
  its first successful probe and with a full staging volume; Neon `145000Z` AGREE). When a positively diagnosed
  LOCAL prerequisite (a tablebase file, the staging volume) becomes unavailable during stage b, the round stays
  PENDING in private staging and the failed attempt is recorded durably (2.4) and never erased. A whole-round
  retry is allowed after the identical inputs are restored and verified by their hashes. Only an attempt that
  completed with every probe made, every field validated and no unresolved failure publishes the ONE immutable
  output. A conclusively wrong record, or a required probe that stays unresolved, still withholds credit; no
  missing prerequisite can support a clean release. After the lease's end a later success is reported at its
  later time and never rewrites an earlier `partial` release.
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
and the row of D4 that holds. **[2.3]** Every failed attempt of stage b (2.3) is a line of its own:
`{"t":"stage_b_attempt","round":r,"at_utc":"..","result":"failed","why":".."}`; it is never removed, and the
round's `report.json` counts the failed attempts before the one that published it (`attempts_failed`). **The reconnect margin**: time left to the lease's end less the EARLIEST possible
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
delivery orders; **[2.2]** a genuine restart of the same machine during the day (the boot guard writes `RESUME`,
the slots go on) and one after D (seal-only); p0, then the terminal inventory, then p1 a second later (one
complete round); a pilot that stops before the first schedule (the inventory names schedule 0); **[2.3]**
Astra's 13 positive record vectors; a worker killed inside a game whose record had begun in the open piece
(the restart writes `failed` before the cut; the id is played again, or is `unfinished` after the fence, and a
second restart finds the same); the control beside it, other bytes beyond the last `end` (cut without a line,
the ids `never_dispatched`); a table file and the staging volume lost during stage b and restored with the
same hashes (ONE complete round, the failed attempt still in the progress file); a fetch that lists while a
member's wire file is being written (it sees no offer yet).

**B. These must WITHHOLD the clean verdict and name the slot, id or piece:** two different seals at one index;
epochs [1, 2, 1] along the index; two held pieces of a slot with overlapping counters; a counter outside the
slot's ranges; a game line without rows left out; a slot without output left out of the footer; the terminal
file cut before its footer; a spool of another run under a new run id; a spool copied to a second machine
(another instance: no `RESUME`, held); **[2.2]** a round made `partial` on the terminal inventory alone, without `DRAIN.json`; a rebuilt engine with other bytes; a "no moves" record where 27 moves exist; a
record whose opening line was changed (the binding fails) and one whose opening AND binding were changed (the
reservation fails); a schedule that moves a started range; a converter that flips a result; a torn MIDDLE line
of a journal; a record with a key twice, a float, a control byte; a malformed game id; a search that runs past
D (Astra `135328Z`: processor time of the engine process read at D and after the stop); a reservation inside
the guard; a slot with a free lock and no `ended` line that the finalizer cannot verify; a never-offered piece
counted as zero work; a second publication of a round; an id with two different complete records; **[2.3]**
Astra's ten negative record vectors, each by its named check; a seal whose `games`, counters or `ids_digest`
do not describe its own bytes; a `binpack` and `meta.xz` that give back other plain bytes than the seal's; an
instance of placeholders only (`instance_provable` false: no `RESUME`, held for a person) and two instances
whose only common values are `null`; a list opening rule with two slots; a round published `complete` while a
required probe is unresolved; a failed stage b attempt missing from the progress file.
