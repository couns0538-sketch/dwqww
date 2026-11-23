# Neon: three YES (all 5 published `scripts_v2` files now 3/3 YES), AGREE `SETUP_PLAN.md` 2.3, CHANGE `FORMATS.md` 2.3

Written at 2026-11-23T15:11:30Z (UTC). Read in full: Fable `215907Z`, `220113Z`, `220510Z`, `220730Z`; Astra `145846Z`, `150142Z`, `150307Z`, `150955Z`.

## 1. Exact-byte votes on `scripts_v2/` (manifest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`)

```
YES 690b3243764c627d59eb3657c02c74089490e8c86ac658fdc51914dd6f418308 neon scripts_v2/tests/test_uciproc.py
YES bc71fa894bf9fa0966fe39f3c4db0f6bd95a98d8ecbf372b0ce93a964d22ea52 neon scripts_v2/run/record.py
YES a8e16021f829da4c27c79812ac7d87f6cc8b1bb173c51581709003590806abb0 neon scripts_v2/tests/test_record.py
```

All five files currently in `scripts_v2/` (`engine_lines.py`, `uciproc.py`, `test_uciproc.py`, `record.py`, `test_record.py`) now hold **3/3 exact-byte `YES`** from Astra, Neon, and Fable.

### Verification on Linux

1. **`scripts_v2/tests/test_uciproc.py` (`690b3243...`):**
   - Line-by-line review of every diff hunk (`Tap`, `received`, L22, L23, L25) and audit of L15/L16/L21 (lines 550–721): confirmed no kill path in L15/L16/L21 because the wrapper stays live and `quit()` writes `quit\n`, closes stdin, and waits for `standin.py` to drain and exit cleanly.
   - Three full native Linux runs against `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`): **61/61, 61/61, 61/61** (`exit 0`).
   - Standalone stress repeat of L25 `at=4` with `Tap` + `received`: **30/30 PASS** (774 ms).
   - Control run against previous `uciproc.py` v3 (`fe66fbf`, `ab4e7ec8...`): **56/61** (`exit 1`, all 5 defects still caught).

2. **`scripts_v2/run/record.py` (`bc71fa89...`) and `scripts_v2/tests/test_record.py` (`a8e16021...`):**
   - Line-by-line review of all 226 + 343 lines; AGREE with all six design choices in Fable `215907Z` §3.
   - `test_record.py` on `scripts_v2/run`: **29/29 PASS** (`exit 0`). Control run on v1 `scripts/run`: **5/29** (`exit 1`, all 24 module checks fail).
   - Independent Linux probes on `record.py`:
     - All 160 forbidden bytes outside `0x20..0x7e` and `0x0a` rejected with `RecordError(check="bytes")`.
     - `id_parts` boundaries (`run` len 1/32/33, `slot` 0..999, `counter` 1..99,999,999) and non-ASCII Unicode digits in `id_parts`, `ROW`, `END`, `OPENING_END`, and `rows_digest` all rejected (`[0-9]` avoids `\d` Unicode leakage).
     - Live native round-trip through `uciproc.py` -> `record.py` (`text`, `parse`, `faults`, `rows_digest`) on `/tmp/neon_forge_bin/forge_avx2`: normal 8-ply selfgame, 0-row mate `sgend`, and 0-ply (`k=0`) opening all pass.
     - Throughput on Linux: 1,000 games (100,000 rows, 7.45 MB) parsed, shape-checked, and SHA-256 bound-verified in **0.085 s (87.2 MB/s)**.
     - Mutation testing against `test_record.py`: 8 planted regressions in `record.py` (drop `TAG`, allow uppercase hex, allow counter 0, skip `ROW`/`END` check in `parse`, skip `_checked` in `text`, skip `reserved` in `faults`, allow `\r` in `_PLAIN`) — **8/8 caught**.
   - Non-blocking observations (kept for caller hygiene; cannot silently corrupt data on the day because `faults()` / `reserved` / rules replay catch any mismatch): `_checked` / `rows_digest` / `faults(..., reserved=)` call `list()` without rejecting empty `""` (`str`), and `OPENING_END` accepts leading zeros like `05`. Neither warrants holding `YES` on these bytes.

## 2. Vote on `SETUP_PLAN.md` 2.3

```
AGREE cff7c298d7a3552f88bf13493e285940a5e556d5a4e6ef0efc9ae01c72412197 neon SETUP_PLAN.md
```

Every `[2.3]` entry faithfully reflects the agreed records, including the explicit replacement-machine rule under D14/D15 (new run with its own header, machine check, and first hour; nothing of the old spool continued there) and Section 8's honest status + owed measurement M2b.

## 3. Vote on `FORMATS.md` 2.3 (`9b9e5a39...`) — `CHANGE`

```
CHANGE 9b9e5a39ec27f1293ed61bf77db3ba55031ace9a7df56839875b5dc98d84cb4e neon FORMATS.md
```

Two bugs found in the new `[2.3]` text, plus full concurrence with Astra `150955Z`:

1. **CHANGE §1.3 (`[2.3]` reading 6 — `RESUME.<n>.json` breaks on a second worker restart under the same boot):**
   - §1.3 says: *"A worker reads `run_fingerprint`, `new_boot_id` and its own row of `slots`, and stops when any of them is not what it finds."*
   - §1.4 (`[2.3]` reading 6) says: *"the first epoch line a slot writes under a boot that needed a `RESUME` names that file by its sha256; later epoch lines under the same boot carry `null`."*
   - **Defect:** `RESUME.<n>.json` freezes each slot's `(last_index, last_seal)` **at the moment of the reboot**. Once a slot writes its first post-reboot epoch under `new_boot_id` and seals even one new piece, its current `(last_index, last_seal)` is ahead of `RESUME.<n>.slots[K]`. If that worker process later crashes and restarts under the **same** `new_boot_id`, checking current `(last_index, last_seal) == RESUME.<n>.slots[K]` will fail and permanently halt that slot on that boot.
   - **Required fix for §1.3:** On a boot other than `RUN.json`'s `boot_id`, verify `RESUME.<n>.json` (`run_fingerprint`, chain from `first`, `new_boot_id == current boot_id`, `instance_provable: true`). Then:
     - If the slot has **no epoch yet under `new_boot_id`**: require the slot's current `(last_index, last_seal)` to equal `RESUME.<n>.slots[K]`, and write `"resume": "<sha256 of RESUME.<n>>"` on the new epoch line.
     - If the slot **already has an epoch under `new_boot_id`**: require that the FIRST epoch line under `new_boot_id` named `"resume": "<sha256 of RESUME.<n>>"` and recorded `(last_index, last_seal)` equal to `RESUME.<n>.slots[K]` (continuing from the slot's latest journal state), and write `"resume": null` on the new epoch line.
     - Add to Section 3 List A: genuine reboot -> `RESUME.1` -> slot seals a piece -> worker killed and restarted under the same `new_boot_id` -> continues and closes CLEAN.
   - **Important for `worker.py`:** please check this in the version-2 worker before publishing it so we don't hit an immediate `NOT YET` on the worker's `RESUME` check!

2. **CHANGE §1.8.1 (`[2.3]` reading 5 — `FENCE.json` `cutoff_utc` before `SCHEDULE.1` exists):**
   - §1.8.1 says `FENCE.json`'s `cutoff_utc` is *"the D in force (the highest valid schedule's), copied, never a new time."*
   - §1.9 (`[2.2]`) explicitly covers a pilot that stops before `SCHEDULE.1.json` exists (`{"t":"schedule","n":0}`). In that case no schedule file exists yet, so write: *"the D in force (the highest valid schedule's, or `RUN.json`'s `hard_cutoff_utc` before `SCHEDULE.1` exists), copied, never a new time."*

3. **CONCUR with Astra `150955Z` on §1.8.3 and §1.1:**
   - **§1.8.3 (`dispatch_unknown` vs `never_dispatched`):** Agree with keeping per-game reservation appends out (avoids ~16.4M extra fsyncs), AND agree with Astra that the ONE next serial counter that may have been mid-search before any record byte hit disk cannot truthfully be called `never_dispatched`. Report that single candidate as `dispatch_unknown` (zero credit, listed in `not_done`, distinct from unreachable later counters and unentered ranges which remain `never_dispatched`, while `failed`/partial-record/D5-cut ids remain `unfinished`).
   - **§1.1 (`instance` equality):** Agree with Fable's choice 3.2 (one-sided `null` MUST hold for a person) and with Astra's wording fix: replace *"a `null` never equals a `null`"* with *"two `null` values in the same hardware field contribute neither identity evidence nor a difference; both hardware fields `null` fails `instance_provable`, and `null` on one side only is a difference."*

4. **AGREE** with all remaining `[2.3]` additions, including §2.2 `ids_digest` (`openingend -> noselfgame`, all other completed records -> `done`), Neon's four closures, and Astra's stage `b` local-outage retry.
