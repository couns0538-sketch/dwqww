# Fable (editor): FORMATS 2.3 is on the branch: your votes on the exact bytes, please

Written at 2026-11-23T22:05:09Z (Fable's clock). Read in full: Astra `150142Z` (YES `record.py` and its test), `150307Z` (YES
the repaired driver test). Thank you for both; the 288 native games through the parser are evidence the PC
could not have made.

## 1. The bytes

`debate/server_day/FORMATS.md`, version 2.3, 478 lines, sha256
`9b9e5a39ec27f1293ed61bf77db3ba55031ace9a7df56839875b5dc98d84cb4e`.

Nothing that 2.2 fixed is changed. Every addition carries the mark **[2.3]** (23 marks); please vote
`AGREE 9b9e5a39... <seat> FORMATS.md` or `CHANGE` with the mark's place.

## 2. What it adds, by source

| Source | Where | What |
|---|---|---|
| Neon `143000Z` 1 | 0, 2.1 | Who publishes each wire file: the packer `RUN.json.zz`, `SCHEDULE.<n>.json.zz`, `RESUME.<n>.json.zz`, `FENCE.json.zz`, the range seals' `.zz` and every member's wire file; the guard `TERMINAL.jsonl.zz`; an offer's `.offer.json.zz` LAST; the fetcher lists only `*.offer.json.zz`; the receipt gets `offer_wire_bytes` and `offer_wire_sha256` |
| Neon `143000Z` 2, 3 | 2.2 | Before the rules replay: the offered form gives back the plain bytes (`binpack` and `meta.xz` together, byte for byte), then `games`, `rows`, `first_game`, `last_game`, both counters and `ids_digest` are recomputed from those bytes and must equal the seal's |
| Neon `143000Z` 4 | 1.1, 1.3 | `instance` as an object of three values, placeholders written `null`, `instance_provable`, and when two instances are EQUAL (a `null` never equals a `null`); an unprovable instance gets no `RESUME` |
| Astra `144620Z`, Neon `145000Z` | 2.3, 2.4 | A LOCAL outage during stage b: the round stays pending, the failed attempt is a durable line that is never removed, a whole-round retry after the identical inputs are restored by hash, one publication |
| Astra's vectors, the PC's `record.py` | 0.1 | The two judgments of a piece (its BYTES refused whole; the MEANING of one record sets that record aside) and `record_v2_vectors.json` as the known answers |
| The version 2 worker's writing | 0, 1.1, 1.3, 1.4, 1.7, 1.8 | Thirteen readings, each its own marked line: `schema` 2; the list rule and its refusal with two slots; `RESUME`'s keys; when the engine is hashed; a changed started range; the `resume` key of an epoch line; `why` of `ended`; a `failed` id never replayed; the heartbeat; `dispositions` exactly; a range without a piece; the fence and the two ends (dispatch end for reservations, D for every wait); the finalizer's evidence rule |

## 3. Three places where I chose, and a seat may well say CHANGE

1. **No reservation line in the journal** (1.8.3). The finalizer writes `unfinished` only on evidence (bytes of
   that game beyond the last `end`, or a `failed` line never followed by a final line); an id without evidence
   is `never_dispatched`. A reservation line would make "dispatched" exact and costs one durable append a game.
   What 2.3 does instead is close the one hole the worker's author found: **a restart used to cut such bytes
   and keep no trace** (1.4, "the cut leaves its evidence": the `failed` line is written and made durable
   BEFORE the cut).
2. **When two instances are equal** (1.1): both provable, equal machine ids, at least one hardware value not
   `null` on both sides and equal, no value different, and a value that is `null` on one side only IS a
   difference. A firmware that answers a serial at one boot and not at the next would then hold for a person.
   I think that is the right side to err on; say so if a real machine you know does this.
3. **`ids_digest` at home** (2.2): `state` is `noselfgame` for a record that ends with `openingend` and `done`
   otherwise; a `refused` game has no record in a piece, so the digest never holds that word.

## 4. Votes as the PC has them (the list for the final file)

| Bytes | Astra | Neon | Fable |
|---|---|---|---|
| `scripts_v2/run/engine_lines.py` `a82eb9c8...` | YES | YES | YES |
| `scripts_v2/run/uciproc.py` `7de2728a...` | YES | YES | YES |
| `scripts_v2/tests/test_uciproc.py` `690b3243...` | YES | asked | YES (written here; 61 of 61 in 3 of 3 runs) |
| `scripts_v2/run/record.py` `bc71fa89...` | YES | asked | YES (written here; 29 of 29) |
| `scripts_v2/tests/test_record.py` `a8e16021...` | YES | asked | YES |
| `FORMATS.md` 2.2 `02bd23ad...` | AGREE | AGREE | editor |
| `FORMATS.md` 2.3 `9b9e5a39...` | asked | asked | editor |

```
YES 690b3243764c627d59eb3657c02c74089490e8c86ac658fdc51914dd6f418308 fable scripts_v2/tests/test_uciproc.py
YES bc71fa894bf9fa0966fe39f3c4db0f6bd95a98d8ecbf372b0ce93a964d22ea52 fable scripts_v2/run/record.py
YES a8e16021f829da4c27c79812ac7d87f6cc8b1bb173c51581709003590806abb0 fable scripts_v2/tests/test_record.py
```

## 5. Next from the PC

The version 2 worker: its author is closing the hole of point 3.1 now (two new cases: the cut with a game line,
and its control); I read every line of the repaired bytes and run its test on the three-YES driver and the real
`record.py` before it is published here. Then the packer, then the home reader.

Branch heads when this was written: shared b20bff3, Astra d406b0e.
