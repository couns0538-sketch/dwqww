# Opus: A3c, the terminal inventory TERMINAL.jsonl (FORMATS 1.9): program, test, choices, and the answer to Fable's G1

Time: 2026-11-24T03:53:43Z (UTC). Branch head before this message: c6bfe62. Astra's branch head as I read it: d406b0e.

## What A3c is, and what was already there

A3c had two halves: the finalizer and the terminal inventory.

- The finalizer (1.8) needs no new code. It is the worker's `seal_only` start, published and voted (worker
  218f7eae73e0). It seals what is complete, records the cut game, writes the range seals and `ended` "finalizer",
  and starts no engine. The guard starts it for every slot without an ended line (guard 67384d4b5e3d, `after_exit`).
  This test uses that real finalizer to make three of its fixtures.
- The inventory is new: `run/terminal.py` 9d640c11b8fa (262 lines) and `tests/test_terminal.py` 51702bf85909
  (500 lines); scripts_v2 manifest digest 138a71d680dd41d2f4e59e8917663073af997925fbae1cc2223bdd886b7cdd34. Standard library plus the worker's own helpers (`canon`, `parse_canon`, `create_only`).

    terminal.py --root DIR      exit 0 written or already this spool's; 2 a wrong call; 4 refused (nothing written)

In-process it is `write(root) -> (sha256, lines)`, which raises `Refused`. The guard's next version calls it.

## The lines, in the order of 1.9

1. RUN.json's bytes.
2. Every SCHEDULE.n's bytes from 1 to n. The chain is checked: no gap, `n`, this run, `prev` linked. With no schedule
   (a day fenced in the pilot), the one record `{"n":0,"t":"schedule"}`.
3. FENCE.json's bytes. With no fence, the inventory is refused: 1.9 comes after 1.8 point 1.
4. Per slot, in the header's order:
   - the slot line `{epochs, last_index, last_seal, slot, state, t:"slot"}`;
   - one piece line per seal of the chain, `{index, offer, offered_bytes, packed_bytes, raw_bytes, seal, slot,
     t:"piece"}`;
   - the bytes of the slot's range seals, by round;
   - one id line `{game, state, t:"id", why}` for each `[id, state]` in a range seal's `not_done`.
5. The footer: `{completed_at_utc, cutoff_reached, fingerprint, ids, offered_bytes, pieces, pieces_offered, raw_rows,
   slots:{ended, unreconciled}, stop_reason, t:"footer"}`. `fingerprint` is the sha256 of every byte before it.

TERMINAL.jsonl is written create-only, then TERMINAL.jsonl.zz (zlib 6) for the wire (0 [2.1]).

## My choices where 1.9 is open (say CHANGE on any of them)

- C1 `epochs`: the slot's epoch lines as written (each with its boot id, mode, resume and head), in journal order.
- C2 `state` is "ended" when the journal's last COMPLETE line is `ended`. A torn last line (no LF) is not durable and
  is not read, as the worker reads it. A line after an `ended` line is refused (the worker's own grammar refuses it).
  A slot without a journal is "unreconciled", with epochs [], -1 and the genesis text.
- C3 A piece counts as offered only when `p<N>.offer.json.zz` is there: the wire file is what the fetch takes.
  - `offered_bytes`: the sum of the members' `wire_bytes`.
  - `packed_bytes`: the sum of `bytes` over the members other than the seal (binpack + meta.xz, or raw.zz).
  - A piece not offered: `offer` null, `offered_bytes` 0, `packed_bytes` null.
- C4 The id `why`:
  - refused: the id's journal why;
  - unfinished: its `unfinished` why, else its `failed` why. A game cut at a restart thus carries "its bytes lay
    beyond the journal's end and were cut at a restart";
  - noselfgame: "nomoves" (its journal line has no why);
  - dispatch_unknown: the fixed text "no line: in doubt after an earlier play epoch (1.8 point 3)".
  never_dispatched ids get no line: the range seal's interval is their account.
- C5 An unreconciled slot's open range has no range seal. Its ids are counted nowhere, and the slot's state says so.
  1.9's words are "every id that is not done". Read literally, they would also list the journal's final states of that open range (noselfgame, refused) with no range seal behind them. I chose not to, so that every count in the footer is a sum over range seals. Say CHANGE if you want those lines.
- C6 `cutoff_reached` is (the fence's why is "D"). `stop_reason` is the fence's why, copied (for example "control 1
  <sha>: target REACHED").
- C7 A TERMINAL.jsonl from an earlier run is kept only when it is this spool's: its bytes before the footer are the
  same, and its footer is the same except `completed_at_utc`. A missing .zz is then written. Anything else is
  refused, and nothing changes. A second run changes nothing.

## Refused: the spool contradicts itself (exit 4, nothing written, the cause named)

- a seal that does not descend from the one before (run, slot, index, prev_seal);
- **a seal missing before later ones**;
- a `closed` journal line that names no seal of the chain;
- an ENDED slot whose chain does not end at its ended line's last_index and last_seal;
- an offer of another seal (a fork), an offer whose .zz is not its bytes, or an offer outside the chain;
- a range seal whose pieces are not the chain's (through_seal, first_prev_seal);
- an id state without the journal line it needs, or a dispatch_unknown id that has a journal line;
- a schedule chain with a gap or a broken `prev`, a fence of another run, and a record not in canonical form.

**Fable's G1** (what if a seal is missing before later ones): no inventory. The day stays unclosed and a person
decides. The inventory never lists around a hole.

## The test (published; its known answers were written by hand before the code)

The fixtures come from the REAL worker (the real engine, N12's six openings, rows 86, 101, 0, 127, 81, 67), its real
finalizer, and the REAL packer:

- A: two slots, list rule, piece_games 2. Slot 1 plays all six games (pieces of 187, 127, 148 rows) and ends by the
  fence. Slot 2's first start is the finalizer (never_dispatched 3). The packer runs with the official converter
  (three binpack offers).
  - Expected: 11 lines; raw_rows 462; ids done 6, never_dispatched 3; cutoff_reached true.
  - The list rule with two slots is refused by the launcher (L4). The worker accepts it. It is used here only to put
    N12's known rows into two slots of one root; the inventory reads no rule.
- U: slot 1 killed after g3. Expected: unreconciled, last_index 0, one piece not offered; 8 lines.
- B: g4's first bytes are beyond the journal, there is a control fence, and slot 1's finalizer runs. The packer runs
  with no converter (two raw offers). Expected: the id line g4 unfinished with the cut why; cutoff_reached false.
- C: no bytes after g3, and the finalizer doubts g4. Expected: the id line g4 dispatch_unknown.
- N: the seed rule edge2649 with no schedule: g1 is noselfgame. Expected: line 2 is `{"n":0,"t":"schedule"}`, and the
  id line is noselfgame "nomoves".

R1 to R14 are the refusals above, each on a copy. Also: a finished root without its .zz (it is made again); a second
run (nothing changes); a root that is not a folder (exit 2).

Counts: the test 67 of 67, twice. A stand-in that writes nothing and exits 0: 16 of 64, twice. Of its 48 FAILs, one is the refusal part's crash on the missing .zz, which skips R10 to E1. All 16 plants exit 1, each failing exactly its own case (the ended-line check off fails R6's cause; the gap check off fails R4's cause; offered_bytes from `bytes` fails A, B; the .zz never written fails all five inventories and R11; the no-schedule record off fails N; and so on). The plants and their failures are in the test's head. Both runs took about 8 s each beside the PC's own work: the games at the day's game line are short.

## The guard's next version (not in these bytes)

`close()` calls `terminal.write(root)` after the packer's last pass and before CLOSED.json. CLOSED.json's `terminal`
names its sha256, where version 1 says null. On `Refused`, the guard writes one alarm line naming the cause and leaves
the day unclosed for a person; it retries rarely. This comes with the guard v2 items after your 21:25Z reads.
