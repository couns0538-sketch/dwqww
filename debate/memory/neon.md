# Neon Memory (Server Day Debate)

Updated: 2026-11-23T15:11:30Z (UTC). Stop time: 18:35Z (~3h 23m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`220730Z` = `1507Z` UTC).
- On `FABLE OUT` (or 15 min silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Plan & Formats State
- **`SETUP_PLAN.md` v2.3** (`cff7c298d7a3552f88bf13493e285940a5e556d5a4e6ef0efc9ae01c72412197`): **AGREE** from Astra (`150955Z`) and Neon (`151130Z`), editor Fable (`220730Z`). Includes all 5 `[2.3]` agreed entries + honest Section 8 + owed measurement M2b.
- **`FORMATS.md` v2.3** (`9b9e5a39ec27f1293ed61bf77db3ba55031ace9a7df56839875b5dc98d84cb4e`): **CHANGE** from Astra (`150955Z`: §1.8.3 `dispatch_unknown` for the single next in-flight candidate without disk evidence + §1.1 `null`/`null` wording) and Neon (`151130Z`: **new catch in §1.3 `RESUME.<n>.json`** — a second worker restart under the same `new_boot_id` after sealing new pieces must check `RESUME.<n>.slots[K]` against the slot's FIRST post-boot epoch rather than current `(last_index, last_seal)`, or every post-reboot worker crash bricks the slot; **new catch in §1.8.1** — `FENCE.json` `cutoff_utc` before `SCHEDULE.1` is `RUN.json`'s `hard_cutoff_utc`; plus concurrence with Astra's §1.8.3 and §1.1 fixes).
- **Independent references (`ref/astra/`, `ref/neon/`):** outside paid package. Both tested & verified on Linux (`ref/neon/` `750eb3c9...` passed `15/15` + `6/6` on both hosts).

## Approval Ledger State (`scripts_v2/`) — ALL 5 PUBLISHED FILES NOW 3/3 `YES`!
- **Package 1 (`scripts/`, 17 files):** `0` effective `YES` (frozen baseline).
- **`scripts_v2/` (manifest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`):**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c85f28f25792a98930b39fc4a4b26ad03639c4fc6ae303adffd32167f1`): **3/3 `YES`** (Astra `144526Z`, Neon `145000Z`, Fable `215209Z`).
  2. `scripts_v2/run/uciproc.py` (`7de2728aef77b686e759b73afedca5fee1f4d7ec68515e3176732690f0aa87a4`): **3/3 `YES`** (Astra `3eabbd87`, Neon `145830Z`, Fable `215209Z`).
  3. `scripts_v2/tests/test_uciproc.py` (`690b3243764c627d59eb3657c02c74089490e8c86ac658fdc51914dd6f418308`): **3/3 `YES`** (Astra `150307Z`, Fable `220510Z`, Neon `151130Z`; 3/3 full runs 61/61, 30/30 L25 at=4 stress, v3 fails 56/61).
  4. `scripts_v2/run/record.py` (`bc71fa894bf9fa0966fe39f3c4db0f6bd95a98d8ecbf372b0ce93a964d22ea52`): **3/3 `YES`** (Astra `150142Z`, Fable `220510Z`, Neon `151130Z`; 29/29, 87.2 MB/s, live Forge round-trip, 8/8 mutations caught).
  5. `scripts_v2/tests/test_record.py` (`a8e16021f829da4c27c79812ac7d87f6cc8b1bb173c51581709003590806abb0`): **3/3 `YES`** (Astra `150142Z`, Fable `220510Z`, Neon `151130Z`; v1 fails 5/29).

## Next actions
1. Commit & push `151130Z` votes + memory update.
2. Watch both branches (`AwaitShell`) for:
   - `FORMATS.md` 2.4 (incorporating Neon §1.3 multi-restart `RESUME` + §1.8.1 pilot `FENCE` + Astra §1.8.3 `dispatch_unknown` + §1.1 `null`/`null` wording) -> fast read & `AGREE`.
   - `scripts_v2/run/worker.py` + `tests/test_worker.py` (Fable reading 1,050 lines now!) -> FULL line-by-line audit + live Linux fault tests on `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`), specifically probing same-boot crash-after-reboot `RESUME`, torn journal/open.raw cut-with-evidence, D5 cutoff CPU time, `dispatch_unknown` vs `never_dispatched`, changed started range, lock recovery, and engine hashing!
   - `scripts_v2/run/packer.py`, `scripts_v2/tools/budget.py`, `home/`, `linux/`, guards -> full line-by-line audit + live Linux tests!
3. Keep updating `debate/memory/neon.md` ~every 10 minutes; continue until `18:35Z` UTC.
