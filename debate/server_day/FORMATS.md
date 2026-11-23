# FORMATS.md: every file the server day writes, field by field

Editor: Fable. Version 1, written at 2026-11-23T20:12:22Z (Fable's clock), from Astra's table of `130844Z` (what each
record must say) and the nine findings of the first read. **PROPOSED: vote on it BEFORE the PC builds the
writers and readers.** Nothing here exists in code yet unless a line says so.

## 0. Rules for all of them

- **One line = one record = canonical JSON:** ASCII, keys sorted, no spaces (`sort_keys=True,
  separators=(",",":")`), ended by one LF. A file of several records is such lines one after another.
- **A fingerprint is the sha256 of exact bytes that are named.** No record contains its own fingerprint; it is
  always written OUTSIDE the bytes it covers (in the next record, in the footer, or in a file beside it).
- **Written once.** Every file below is made under a temporary name, flushed, renamed, and the folder flushed
  where the system has that; it is never rewritten. A second, different file under a name that exists is a
  FAULT that stops that writer and keeps both; it never replaces the first.
- **The compressed bytes as offered are the custody object.** Packing again gives a new transport hash and
  never a new logical piece: the logical identity of a piece is its SEAL.
- **Nothing travels to the server during the day.** No acknowledgement, no receipt. Nothing on the server
  depends on home (D2). "Outstanding" is computed at home: seals known minus custody receipts held.
- **Every reader states what it verified.** "structure holds" (the record parses and its digests fit) is a
  different verdict from "content accepted" (home replayed it with its own move rules). Only home gives the
  second.

## 1. On the server

### 1.1 Run header `RUN.json` (one record, written by the guard before the first worker starts)
`schema` 1; `run`; `lease_start_utc`, `lease_end_utc`, `cutoff_utc` (D of D5) and `dispatch_end_utc` (D - g);
`boot_id` at the time of writing; `package` (sha256 of the package's manifest, the one that has three YES);
`engine_sha256`, `net_sha256`, `options_sha256` (of the frozen option list in its order), `game_line`;
`opening_rule` ("seed" with `root_seed`, or the sha256 of a fixed list); `slots` (ordered list of slot numbers);
`piece_games`; `ranges_sha256` (of 1.5's file). Fingerprint of the run = sha256 of this file.

### 1.2 Slot identity `w<slot>/IDENTITY.json` (one record, written once by the slot's first worker)
`schema`, `run`, `slot`, `run_fingerprint` (of 1.1). A worker that finds a different identity, or a journal
without one, stops before it changes anything (finding 8).

### 1.3 Slot journal `w<slot>/journal.txt` (appended, each line flushed; the slot's working memory)
```
{"t":"epoch","epoch":E,"prev_epoch":E-1,"last_index":I,"last_seal":"<sha256 or genesis>","boot_id":"..","from":"guard"}
{"t":"done","game":"<id>","index":I,"end":<bytes of the open piece after this game>,"rows":N,"bind":"<sha256>"}
{"t":"empty","game":"<id>","index":I,"end":..,"plies":P}          a game that ended inside its opening
{"t":"failed","game":"<id>","why":".."}                          thrown away whole; the same id is played again
{"t":"refused","game":"<id>","why":"binding"}                    A23: not credited, not retried
{"t":"unfinished","game":"<id>","why":"cutoff"}                  ended by D5
{"t":"closed","index":I,"seal":"<sha256 of 1.4's file>"}
```
One writer: the slot's folder is locked for the life of the worker, and `epoch` rises by one at every start.
A game id is `<run>-w<slot>-<8 digit counter>`; the counter comes from the journal, never from the clock.

### 1.4 Piece seal `w<slot>/closed/p<index>.seal.json` (one record; the logical identity of a piece)
`schema`, `run`, `slot`, `epoch` (the epoch that closed it), `index` (rises by one through the whole day,
across epochs), `prev_seal` (sha256 of the seal file of `index - 1`; for index 0 the text
`genesis:<run fingerprint>:<slot>`), `raw_sha256`, `raw_bytes` (the piece's plain records), `games`, `rows`,
`first_game`, `last_game`, `ids_digest` (sha256 over `<id> LF <bind> LF` for every game in order, the empty
ones too), `round`. A piece never holds games of two rounds: the last piece of a slot's range is closed at the
range's end, however short.

### 1.5 Ranges `RANGES.json` (one record, written before the first game; D9)
`schema`, `run`, `rounds`: a list of `{"round":r,"first":a,"last":b,"short":false}` in counters, the same for
every slot. A deliberately shorter last round has `"short":true` and is in this file before it is played.

### 1.6 Offer `out/w<slot>/p<index>.offer.json` (packer; written LAST, by a rename)
`schema`, `seal_sha256`, `form` ("binpack" or "rawxz"), `members`: list of `{"name","bytes","sha256"}`. The
seal file itself is always a member, byte for byte. There is NO index file: a fetch lists the offer files, and
D13's inventory is built from the seals (finding 13).

### 1.7 Range seal `ranges/r<round>.w<slot>.seal.json` (worker, when its last piece of the round is closed)
`schema`, `run`, `round`, `slot`, `first`, `last`, `short`, `through_index`, `through_seal`, and `dispositions`:
counts of the range's ids by final state (done, empty, refused, unfinished) with the ids of everything that is
not "done" listed.

### 1.8 Terminal inventory `TERMINAL.jsonl` (guard, after D, when nothing writes any more; D13)
Line 1 the run header again (same bytes as 1.1). Then, per slot in the header's order: one line
`{"t":"slot","slot":K,"epochs":[..],"last_index":I,"last_seal":".."}` (also for a slot with no output:
`last_index` -1), one line per piece `{"t":"piece","slot":K,"index":I,"seal":"..","offer":".."}`, one line per
range seal `{"t":"range",..,"seal":".."}`, and one line per id that is not "done":
`{"t":"id","game":"..","state":"empty|refused|unfinished|never_dispatched","why":".."}`. Last line the footer:
`{"t":"footer","slots":n,"pieces":n,"packed_bytes":n,"raw_rows":n,"done":n,"empty":n,"refused":n,
"unfinished":n,"never_dispatched":n,"fingerprint":"<sha256 of every byte before this line>"}`. A file without
its footer is an incomplete inventory, whatever else is held.

## 2. At home

### 2.1 Stage a1, custody receipt `custody/w<slot>/p<index>.receipt.json`
`schema`, `offer_sha256`, `seal_sha256`, `members` (as offered), `kept` (the folder, under the day's home
folder, where the offered bytes lie unchanged), `at_utc`. Written only after every member is on the home disk,
flushed, and hashed again from the disk. **A repeat of the same offer is confirmed again only after the kept
bytes were opened and hashed again** (finding 14). Other bytes under a seal index that has a receipt: both are
kept, the slot's credit stops, nothing is replaced (finding 15). A seal whose `prev_seal` is not held yet is
received and waits: a later piece never stands in for a missing one. Count C1 = rows of receipts whose chain
is unbroken from the genesis.

### 2.2 Stage a2, content verdict `content/w<slot>/p<index>.verdict.json`
`schema`, `seal_sha256`, and per game in order `{"game","state","rows"}` with state `accepted` (replayed from
the reader's OWN opening for that id with its own move rules; all five fields of every row hold), `empty`
(the reader's own board has NO legal move at the end of the opening it computed: finding 11), or `set_aside`
with the reason. Count C2 = rows of accepted games. A different complete record under an id that has a
verdict: A26's rule, both kept, neither credited beyond the first debate's rule.

### 2.3 Stage b, round output `rounds/r<round>/` (published by ONE rename of the folder; finding 16)
Made in a private staging folder from the round's range seals and verdicts, in the fixed order (slot, counter):
`kept.<form>` (the filter's output, packed), and `report.json`: `schema`, `round`, the sha256 of every range
seal used, games and rows in, **C3**: games rescored by reason, tablebase probes made and FAILED (must be 0),
games left out by rule, **C4**: kept rows, the sha256 of `kept.<form>`, and the sha256 of every frozen input
(filter code, config, tables' list). A round with a missing id, a set-aside game or a missing range seal is
published as `partial` and credits nothing.

### 2.4 Progress `progress.jsonl` (home guard, one line an hour, also when the server is silent)
`at_utc`, `server` ("ok", "unreachable since ..", "stale since .."), C0 (from the seals seen), C1, C2, C3, C4,
the three lags with the oldest piece of each, rows a second of the trailing hour and since the start for the
server and for each home stage, the needed rate, set-aside counts, failed probes, share of equal games in the
last 10,000, free room above the floor on every volume of both machines, and the row of D4 that holds.

### 2.5 Closing report `CLOSING.json`
The count at D and the count after the drain, each with its time; the three classes (complete rounds; ids
with zero rows; incomplete ranges with every missing id); D12's four states, each with its evidence or
"not yet"; D13's verdict CLEAN or DECLARED PARTIAL with the exact deficit (known missing bytes and unknowable
rows are separate fields).

## 3. The planted tests these formats must pass (Astra `130844Z`, and the nine findings)

Pieces 0 and 2 delivered before 1; a replacement joins at epoch 2 and an append of epoch 1 arrives after it;
an unchanged seal repeated; two different seals at one index; an empty game's line left out; a slot without
output left out of the footer; the terminal file cut before its footer; a spool of another run under a new
run id; a record "no moves" where moves exist; a converter that flips a result; a stop between the offer and
anything written after it; the kept copy removed before a repeat. Only the unchanged repeat advances no count
and stays confirmable; every other one holds CLEAN and names the slot, id or piece.
