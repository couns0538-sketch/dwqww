# Opus: A3d part 1, stage a1 at home: custody (FORMATS 2.1 and 2.4): program, test, choices

Time: 2026-11-24T04:21:27Z (UTC). Branch head before this message: 0086238.

## What a1 is

`home/custody.py` d46817f23f72 (the new home folder of scripts_v2) and `tests/test_custody.py` a42965f17d50; scripts_v2
manifest digest 225fe4600da5d6ee4ab067512970ed94ae4b6d4a2002d75eb0eb154caae9617b. Standard library plus the package's
own helpers (the packer's key lists and forms; the worker's `canon`, `parse_canon`, `create_only`, `sha256_bytes`).

    custody.py --home DIR --fingerprint HEX64 [--confirm w<NNN>/p<NNNNNN> ...]
    exit 0 a pass; 2 a wrong call; 3 the home run header cannot be trusted; 4 a file cannot be read or written;
    5 a confirmation failed

One call is one pass. It writes receipts and fork records, create-only, and nothing else. Its last line:
`custody: RECEIVED <p> pieces <r> rows; C1 <p> pieces <r> rows; new receipts <n>; not received <n>; waits <n>;
conflicts <n>; forks <n>`.

## My choices where 2.1 and 2.4 are open (say CHANGE on any of them)

- C1 The home folder. `wire/` holds what the fetch brought, under the server's own relative paths and names, whole
  files only: `RUN.json.zz`, `SCHEDULE.<n>.json.zz`, `FENCE.json.zz`, `TERMINAL.jsonl.zz`, `ranges/*.seal.json.zz`,
  and per slot `out/w<NNN>/p<N>.offer.json.zz` with the member files each offer names by `wire_name`. a1 never writes
  in `wire/`. It writes `custody/w<NNN>/p<NNNNNN>.receipt.json` and `custody/w<NNN>/p<NNNNNN>.fork.json`.
- C2 `--fingerprint` is home's own pin of the run, taken when the pilot started. `wire/RUN.json.zz` must decode to
  canonical bytes with that sha256; otherwise exit 3 and nothing is written. No `RUN.json.zz` yet: exit 0, nothing
  to do.
- C3 A receipt only when all of this holds: the offer's wire file decodes to canonical bytes with the keys of 1.6,
  schema 2, this run's fingerprint, the slot and index of its own name, and a form of 1.6 (its members' names,
  codecs and wire names); every member file is there with the offer's `wire_bytes` and `wire_sha256`, and its
  decoded data has the offer's `bytes` and `sha256`; the seal member's sha256 is the offer's `seal_sha256`; the seal
  is canonical, schema 2, this run, this slot and index. A member not there yet: `WAITS` (no receipt, not a fault).
  Anything else: `NOT RECEIVED` with the reason, and no receipt; the next pass looks again, so right bytes that
  arrive later are received then.
- C4 The receipt has the keys of 2.1: `members` = the offer's members; `kept` = `wire/out/w<NNN>` (relative, forward
  slashes); `epoch`, `first_counter` and `last_counter` from the seal; `offer_sha256` of the PLAIN offer bytes,
  `offer_wire_bytes` and `offer_wire_sha256` of its `.zz`; `at_utc` the time of writing. A receipt is written once;
  a later pass leaves it as it is.
- C5 C1 per slot: from index 0 up, a piece counts while it has a receipt, its kept seal (read and hashed again) is
  the receipt's, its `prev_seal` is the genesis text (index 0) or the seal sha256 of the piece before, its epoch is
  not below the epoch before, and no fork record names it. The walk stops at the first piece that fails; one line
  says why. RECEIVED counts every receipt. Both are counted in pieces and in rows (the seal's `rows`).
- C6 Intervals: two receipted pieces of a slot whose `[first_counter, last_counter]` overlap give a `CONFLICT` line
  (counted). A piece whose interval is not inside the range of its seal's round, in the schedule its seal names
  (0 = the header's `pilot_ranges`), gives `CONFLICT` when home holds that schedule and `WAITS` when it does not
  (a false conflict would be immutable). a1 finds and counts conflicts. The conflict RECORDS, with both bindings,
  need the records: they are stage a2's or b's.
- C7 Forks: when `wire/TERMINAL.jsonl.zz` is there and verifies (its footer fingerprint, its first line RUN.json's
  bytes), a piece line whose `seal`, or non-null `offer`, differs from that piece's receipt gives `p<N>.fork.json`,
  and C1 stops before that piece. An inventory that does not verify gives one line and no fork. a1 sees only whole
  files in `wire/`: a fork the FETCH meets (other bytes under a name already held) is the fetch's to land (A3f).
- C8 `--confirm KEY` opens the kept members its receipt names and hashes them again, wire and data. All equal:
  `CONFIRMED KEY`. Gone or other bytes: `CONFIRM FAILED KEY: <member> ...`, exit 5, nothing written. A key without
  a receipt: exit 2. A listing is never a confirmation.

## The test (its known answers were written by hand before the code)

The fixture comes from the REAL worker (the real engine, N12's six openings, rows 86, 101, 0, 127, 81, 67), the
REAL packer with the official converter, and the published `terminal.py`. The fetch is stood in by a byte copy:
the members first, the offer's `.zz` last.

Fixture H: run `cust`, slot 1, piece_games 2, the list rule, pilot range round 1 counters 1 to 4. The first worker
run plays g1 to g4 and ends by the STOP file after the range seal. SCHEDULE.1 adds round 2 (counters 5 and 6). The
second run (epoch 2) plays g5 and g6 and ends by the fence "D".

| piece | games | rows | epoch | counters | round | schedule |
|---|---|---|---|---|---|---|
| p0 | g1 g2 | 187 | 1 | 1..2 | 1 | 0 |
| p1 | g3 g4 | 127 | 1 | 3..4 | 1 | 0 |
| p2 | g5 g6 | 148 | 2 | 5..6 | 2 | 1 |

- H1 three receipts; RECEIVED 3/462; C1 3/462. H2 a second pass changes no byte.
- H3 (2.1's case A) p0 and p2 only: RECEIVED 2/335, C1 1/187; after p1 arrives, 3/462.
- H4 all six arrival orders: C1 follows the longest run from p0 that has arrived; the receipts at the end are equal.
- H5 epochs [1, 2, 1] in all six orders: C1 never passes p1 and ends at 2/314, naming "epoch 1 after epoch 2".
- H6 an inventory naming another offer for p1, its footer made right: a fork record, C1 1/187, forks 1. The same
  inventory with its footer NOT made right: no fork, the line "does not verify".
- R1 to R12, each on a copy: a member byte flipped; a member missing (WAITS); another data sha256 in the offer;
  another run; p1's own offer with index 2; an offer not canonical; another `--fingerprint` (exit 3) and no
  RUN.json.zz (exit 0); a seal wire compressed again at another level; p0's seal forged to overlap p1 (one
  CONFLICT); p2's seal forged past its range (one CONFLICT, and a WAITS instead when SCHEDULE.1 is not at home);
  `--confirm` (exit 0, 5, 5, 2); p1's `prev_seal` forged (C1 1/187, "prev_seal does not link").

Counts: the test 49 of 49, twice. A stand-in that writes nothing: 2 of 40, twice. All 16 plants exit 1. The plants
are: the wire sha256 not compared; the data sha256 not compared; the offer's fingerprint not compared; the offer's
index not compared with its name; the epoch test off; `prev_seal` not compared; C1 printed as RECEIVED; a receipt
written again on every pass; the fork test off; the overlap test off; the outside test off; a missing schedule
judged as outside; `--confirm` without hashing; the RUN.json fingerprint not compared; `kept` written as an
absolute path; the inventory's footer not verified. FAIL lines per plant: 1, 1, 1, 1, 6, 1, 22, 12, 2 (one of them
the H6 case crashing on the fork record that was never written), 1, 1, 1, 1, 1, 11, 1.

Corrections to the known answers, each made before any run: R9 (my first version also lay outside round 2's range
and would have given two conflicts); R12 added, because no case isolated `prev_seal`; R5 made exact (p1's own offer
with index 2, so that the member names do not refuse it first); and no forged home holds the inventory (the real
inventory names the real seals and would make every forged piece a fork).

## What a1 does not do (named so that nothing falls between)

- the fetch, and a fork the fetch meets: A3f;
- the content (transport, the rules replay, the ids, the equal-games index): a2, which comes next;
- the conflict records with both bindings, and credit: a2 and b;
- the home guard: after a2 and b.

## The guard's parts C and P once more on Linux (the result owed from my last message)

Ubuntu 24.04 under the PC's virtual machine, its own python3: 68 of 79. All 11 FAILs lie in two cases, PA (10) and
PD (1). In both, the guard's own alarm line stands 7 hours away from the lines around it ("the guard's clocks are in
a HOLD (UTC alone ahead)"): that virtual machine's clock stepped forward and back during the case. The guard HELD, as
it is meant to (UTC moved and the monotonic clock did not), so PA never fenced or closed and PD never started its
slot. Every other case of C and P passed, PF among them (PF met the same kind of step in the first Linux run). This
is not a fault of the guard. A clean Linux run of PA and PD needs a machine whose clock does not step: the server's
machine check (A3g) and the guard's first start there.
