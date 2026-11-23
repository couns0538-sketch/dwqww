# FORMATS.md: every file the server day writes, field by field

Editor: Fable. **Version 2**, written at 2026-11-23T20:34:07Z (Fable's clock). Version 1 (`0151a13`) had the AGREE of both
of you to its three choices, six CHANGES from Astra (`131547Z`) and eight more from Neon (`132000Z`); Astra's
`132008Z` and `132505Z`, Neon's audit and Opus's read on the PC add six. All twenty are in this version, each
marked **[v2]**. **PROPOSED: vote on it BEFORE the PC builds the writers and
readers.** Nothing here exists in code yet unless a line says so.

## 0. Rules for all of them

- **One line = one record = canonical JSON:** ASCII, keys sorted, no spaces (`sort_keys=True,
  separators=(",",":")`), ended by one LF. **[v2]** No key twice, no number that is not finite; a reader
  refuses both. A rate that is hashed is an integer in thousandths of a row a second.
- **A fingerprint is the sha256 of exact bytes that are named.** No record contains its own fingerprint; it is
  always written OUTSIDE the bytes it covers.
- **[v2] Two kinds of file.** An IMMUTABLE file (header, schedule, identity, seal, offer, range seal, terminal
  inventory, receipt, verdict, round output) is made under a temporary name, flushed to the disk, renamed, and
  its folder flushed where the system has that; it is never rewritten; a second, different file under a name
  that exists is a FAULT that stops that writer and keeps both. An APPEND-ONLY file (journal, progress) gets
  whole lines, each flushed. **At a restart only complete, valid, LF-ended lines count.** A damaged line that
  is NOT the last stops that slot and is kept as it is. An unfinished LAST line is dropped only when the durable
  evidence it would have described (named at each file below) agrees with the line before it; an interrupted
  append never makes a completed game.
- **[v2] One grammar for names**, the one today's code has: run `[a-z0-9]{1,32}`; slot `w` + 3 digits; game id
  `<run>-w<NNN>-g<NNNNNNNN>` (counter from 1); piece `p` + 6 digits (index from 0); a piece's key
  `w<NNN>/p<NNNNNN>`. A name that does not fit is refused BEFORE it is used as a path or a number (Neon
  `131400Z`: a malformed id ended the receiver; an unchecked key reached a path).
- **The compressed bytes as offered are the custody object. [v2] On the day there is ONE immutable offer for a
  logical piece:** after a broken connection the same saved bytes are copied again. Another seal at an index
  that has one is a FORK (2.1). Another encoding of the same seal is not made on the day.
- **Nothing travels to the server during the day.** No acknowledgement, no receipt. "Outstanding" is computed
  at home: seals SEEN at home minus custody receipts held. **[v2]** What home has not seen is UNKNOWN until the
  terminal inventory arrives; no report calls it zero.
- **[v2] The plain records stay on the server too:** `closed/p<NNNNNN>.raw` lies beside its offer for the whole
  lease (D2); the plan's section 4 sizes the room for both. **Every immutable record below except the header
  itself carries `run_fingerprint`.**
- **Every reader states what it verified.** "structure holds" is a different verdict from "content accepted"
  (home replayed it with its own move rules). Only home gives the second.

## 1. On the server

### 1.1 Run header `RUN.json` (one record; written before the PILOT, never again) **[v2]**
`schema` 1; `run`; `lease_start_utc`, `lease_end_utc`, `hard_cutoff_utc` (the latest D that D5 allows; a
schedule can only tighten it); `boot_id`; `package` (sha256 of the package's hash list, the one with three YES);
`engine_sha256`, `net_sha256`, `options_sha256` (the frozen option list in its order), `game_line`;
`opening_rule` ("seed" with `root_seed`, or the sha256 of a fixed list); `slots` (ordered); `piece_games`;
`pilot_ranges` (rows as in 1.2). It holds NO time or range that the pilot has to teach us: no circular hash.
Fingerprint of the run = sha256 of this file.

### 1.2 Schedule `SCHEDULE.<n>.json`, n = 1, 2, ... (immutable, each links to the one before) **[v2]**
`schema`, `run_fingerprint`, `n`, `prev` (sha256 of schedule n - 1; for n = 1 the text `first`), `evidence`
(sha256 of the pilot's report, or of the report that justifies this change), `cutoff_utc` and
`dispatch_end_utc` (never later than in the schedule before), and `ranges`: rows
`{"slot":K,"round":r,"first":a,"last":b,"short":false}`, **one row a slot and round** (slots may end a round at
different counters: slot 0 at g10, slot 1 at g9 must be writable; a slot that plays nothing has no row and is
still named in 1.9). A later schedule may ADD ranges and SHORTEN a range in which no game was dispatched yet;
it never changes a range that has started. A worker reads the highest valid schedule before every reservation.

### 1.3 Slot identity `w<NNN>/IDENTITY.json` (one record, written once by the slot's first worker)
`schema`, `run`, `slot`, `run_fingerprint` (it covers root seed, opening rule, package, net, engine, piece
size: 1.1). A worker that finds another identity, or a journal without one, stops before it changes anything
(finding 8). **[v2] At EVERY start a worker hashes the engine file it is about to run and stops when it is not
`engine_sha256` of the header** (Astra `133017Z`: six builds of the same source passed every known answer and
all six differ in their bytes; Neon `133300Z`). A rebuilt engine is another run or a declared new epoch with
its own qualification, never a silent replacement.

### 1.4 Slot journal `w<NNN>/journal.txt` (append-only; the slot's working memory)
```
{"t":"epoch","epoch":E,"prev_epoch":E-1,"last_index":I,"last_seal":"<sha256 or genesis>","boot_id":".."}
{"t":"done","game":"<id>","index":I,"end":<bytes of the open piece after this game>,"rows":N,"bind":"<sha256>"}
{"t":"noselfgame","game":"<id>","index":I,"end":..,"plies":P,"bind":".."}
{"t":"failed","game":"<id>","why":".."}          thrown away whole; the same id is played again
{"t":"refused","game":"<id>","why":"binding"}    A23: not credited, not retried
{"t":"unfinished","game":"<id>","why":"cutoff"}  ended by D5
{"t":"closed","index":I,"seal":"<sha256 of 1.5's file>"}
```
**[v2] Two kinds of game without rows, never mixed:** `done` with `rows` 0 is a COMPLETED game (the engine's own
end line is in the record; the third game of the six fixed games is one); `noselfgame` is an opening after
which the worker's own move list is empty, so no game line was sent. **[v2] The binding of every record covers
its opening line too** (Neon `131400Z`: with no game line sent, this morning's binding did not cover the
opening at all). One writer: the slot's folder is locked for the life of the worker, and `epoch` rises by one
at every start; the first epoch line has `prev_epoch` 0, `last_index` -1 and the genesis text as `last_seal`,
and every later line belongs to the epoch line above it. Evidence for a dropped last line: the open piece's bytes up to the `end` of the line before it.

### 1.5 Piece seal `w<NNN>/closed/p<NNNNNN>.seal.json` (one record; the logical identity of a piece)
`schema`, `run`, `slot`, `epoch` (the epoch that closed it), `index` (rises by one through the whole day,
across epochs), `prev_seal` (sha256 of the seal file of `index - 1`; for index 0 the text
`genesis:<run fingerprint>:<slot>`), `raw_sha256`, `raw_bytes`, `games`, `rows`, `first_game`, `last_game`,
`ids_digest` (sha256 over `<id> LF <state> LF <bind> LF` for every game in order, the ones without rows too),
`round`, `schedule` (the n it was played under). `games` is at least 1: an empty piece is never sealed, and a
slot with no finished game writes no seal. A piece never holds games of two rounds: the last piece of a
slot's range is closed at the range's end, however short.

### 1.6 Offer `out/w<NNN>/p<NNNNNN>.offer.json` (packer; written LAST, by a rename)
`schema`, `seal_sha256`, `form` ("binpack" or "raw"), `members`: list of `{"name","codec","bytes","sha256"}`
with `codec` one of "none", "lzma", "zlib". **[v2] The member names are fixed by the form:** `p<NNNNNN>.seal.json`
(none) always; for "binpack" `p<NNNNNN>.binpack` (none) and `p<NNNNNN>.meta.xz` (lzma); for "raw"
`p<NNNNNN>.raw.zz` (zlib; D1's entry under the plan's table says why not lzma). No other name, and no name with
`/`, a backslash or `..`. EVERY file of the offer is a member (Neon: a list that left a file out skipped its
check). There is NO index file: a fetch lists the offer files, and 1.9 is built from the seals
(finding 13).

**[v2] The packer's mode `out/PACKER_MODE.jsonl`** (append-only; Astra `132505Z`): `{"t":"mode","mode":"normal"|
"fallback","at_utc":"..","why":"..","piece":"w<NNN>/p<NNNNNN>"}`. The converter gets ONE bounded attempt a piece;
three failures in a row write `fallback`, which survives a restart; in that mode every piece is offered as
"raw" at once and the converter is probed now and then on a piece that is ALREADY offered; a probe that passes
writes `normal`. No sealed input is ever removed in either mode.

### 1.7 Range seal `ranges/r<round>.w<NNN>.seal.json` (worker, when its last piece of the round is closed)
`schema`, `run`, `round`, `slot`, `schedule`, `first`, `last`, `short`, `complete` (false for a range that D cut),
`first_index` (-1 when the range has no piece), `first_prev_seal`, `through_index`, `through_seal`, and
`dispositions`: the count of the range's ids in each final state (done, noselfgame, refused, unfinished,
never_dispatched), with every id that is not `done` listed.

### 1.8 The end of the day on the server **[v2]** (Opus's read R2: a last piece sealed after the packer left)
Order, fixed: dispatch ends; every worker finishes or ends its game by D5, seals its last piece and its range
seals, writes `{"t":"ended"}` and releases its lock; ONLY when every slot's lock is free does the packer make
its last pass; only then is 1.9 written. A packer never ends while a slot is locked.

### 1.9 Terminal inventory `TERMINAL.jsonl` (guard, after 1.8; D13)
Line 1 the run header again (same bytes as 1.1), line 2 the last schedule (same bytes). Then, per slot in the
header's order: `{"t":"slot","slot":K,"epochs":[..],"last_index":I,"last_seal":".."}` (also for a slot with no
output: `last_index` -1), one line a piece `{"t":"piece","slot":K,"index":I,"seal":"..","raw_bytes":n,
"packed_bytes":n,"offer":"<sha256>"}` (`offer` null and `packed_bytes` 0 when the packer never offered it, so
that the missing bytes are exact even for a piece that never came home), one line
a range seal, and one line for every id that is not `done`:
`{"t":"id","game":"..","state":"noselfgame|refused|unfinished|never_dispatched","why":".."}`. Last line the
footer: the counts of slots, pieces, packed bytes, raw rows, and of ids in each state, `completed_at_utc`,
`cutoff_reached`, `stop_reason`, and `fingerprint`, the
sha256 of every byte before that line. A file without its footer is an incomplete inventory.

## 2. At home

**[v2] No home program holds the day's identities in memory as text** (Opus measured this morning's way: 1,018
bytes a credited game, 15.5 GiB at 16.4 million games, at every pass). Everything below is one small file a
piece or a round; a duplicate id is found from the id's own slot and counter, which name the one piece that may
hold it.

### 2.1 Stage a1, custody receipt `custody/w<NNN>/p<NNNNNN>.receipt.json`
`schema`, `offer_sha256`, `seal_sha256`, `members` (as offered), `kept` (where the offered bytes lie unchanged,
COMPRESSED; a path RELATIVE to the day's home folder), `at_utc`. Written only after every member is on the home disk under its final name (temporary
name, flushed, renamed) and hashed again FROM the disk. **A repeat of the same offer is confirmed again only
after the kept bytes were opened and hashed again; when they are gone or differ, they are fetched again first**
(findings 14, Opus R1). Other bytes under an index that has a receipt: a FORK, both kept, that slot's credit
stops, nothing is replaced (finding 15). **[v2] Two counts:** RECEIVED (a durable receipt, in any order) and
**C1 = chain-eligible** (unbroken from the genesis); both are shown, so that a piece held out of order is
visible in the storage report and still credits nothing. A late repeat of a seal that is already held is a
repeat (zero), also when its epoch is older than the newest; along a slot's chain `epoch` never falls: a NEW
seal from an epoch older than the newest seal held for that slot is refused as stale.

### 2.2 Stage a2, content verdict `content/w<NNN>/p<NNNNNN>.verdict.json`
**[v2] What this stage proves, exactly (Astra `132008Z`):** (1) TRANSPORT: the offered form gives back the
sealed plain bytes (`raw_sha256`) and every record's binding holds; that, and nothing else here, is what proves
a score (+19 written where the engine said +42 changes the sealed bytes). (2) RULES: with the reader's own move
rules, the opening it computed for that id, every move's legality, every row's position and ply, and the end
(a mate, a stalemate, the fifty-move count, a third occurrence where the end line names one). It does NOT
repeat a search; an engine replay happens only for the first hour's fixed games, for an A26 conflict and for
small spot samples, and is recorded apart.
`schema`, `seal_sha256`, and per game in order `{"game","identity","state","rows"}` (`identity` as the first
plan's A26 defines it): `accepted` (both checks hold; `rows` may be 0 when the record holds the engine's full
end line and the rules replay agrees), `repeat` (the same record again, with `same_as`), `conflict` (another
record under an id that has one: A26's rule), `noselfgame` (the reader's own
board has NO legal move after the opening IT computed for that id: finding 11; with one legal move left it is
`set_aside`), or `set_aside` with the reason. Count C2 = rows of accepted games.

### 2.3 Stage b, round output `rounds/r<round>/` (published by ONE rename of the folder; finding 16)
Made in a private staging folder from the round's range seals and verdicts, in the fixed order (slot, counter),
reading each kept piece again FROM its compressed custody bytes with its hash checked (Neon: this morning's
step trusted the working copy): `kept.<form>` (the filter's output, packed) and `report.json`: `schema`,
`round`, `status` ("complete" or "partial"), the sha256 of every range seal used, games and rows in,
`missing_ids`, `set_aside_ids`, `conflict_ids`, `kept_share`, **C3**: games rescored by reason, tablebase
probes made and FAILED (must be 0), games left out by rule, **C4**: kept rows, the sha256 of `kept.<form>`, and
the sha256 of every frozen input (filter code, config, net, options, the tables' list). A round with a missing
id, a set-aside game, a failed probe or a missing range seal is published as `partial` and credits nothing.

### 2.4 Progress `progress.jsonl` (append-only; home guard, one line an hour, also when the server is silent)
`at_utc`, `server` ("ok", "unreachable since ..", "stale since .."), C0 as SEEN at home (with the words
"unknown beyond"), RECEIVED, C1, C2, C3, C4, the three lags with the oldest piece of each, the rates of the
trailing hour and since the start for the server and each home stage, the needed rate, set-aside counts,
failed probes, games rescored in 10,000 (the alarm of the plan's row 34), rounds complete through stage b,
share of equal games in the last 10,000, free room above the floor on every volume of both machines, and the
row of D4 that holds. **[v2] The reconnect margin** (Astra `132844Z`, `133240Z`; Neon `133300Z`): time left to
the lease's end less the EARLIEST possible finish of what is outstanding, in two forms that are never mixed:
(a) from totals, max(outstanding offered bytes / measured fetch rate, pending rows / measured content rate),
printed with the words "impossible on this bound" or "possibly feasible, unverified" and never as "safe";
(b) piece by piece, where measured times a piece exist: fetch_finish[i], then content_finish[i] =
max(fetch_finish[i], content_finish[i-1]) + content_time[i], plus the terminal inventory. Only (b), from a
rehearsal at full piece size, may say that a late reconnect still ends in a clean release.

### 2.5 Closing report `CLOSING.json`
The count at D and the count after the drain, each with its time; the three classes (complete rounds; ids
without rows, both kinds apart; incomplete ranges with every missing id); D12's four states, each with its
evidence or "not yet"; D13's verdict CLEAN or DECLARED PARTIAL with the exact deficit (known missing bytes and
unknowable rows are separate fields).

## 3. The planted tests these formats must pass

From Astra `130844Z` and `131547Z`, the nine cases in `debate/server_day/cases/astra/`, Neon `131400Z` and
Opus's read: pieces 0 and 2 delivered before 1 (RECEIVED 2, C1 of piece 0 only); a replacement joins at epoch
2 and an append of epoch 1 arrives after it; an unchanged seal repeated; two different seals at one index; a
game line without rows left out; a slot without output left out of the footer; the terminal file cut before
its footer; a spool of another run under a new run id; a "no moves" record where 27 moves exist (refused) and
the real third game of the six (kept, counted); a record whose opening line was changed and whose binding was
not; slot 0 ending at g10 and slot 1 at g9; a schedule that moves a started range (refused); a converter that
flips a result; a stop between the offer and anything written after it; the kept copy removed before a repeat;
a worker that seals after the packer's last look; a torn last line and a torn middle line of a journal; a
record with a key twice; a malformed game id. Only the unchanged repeat advances no count and stays
confirmable; every other one holds CLEAN and names the slot, id or piece.
