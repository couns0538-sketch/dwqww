# Neon Memory (Server Day Debate)

Updated: 2026-11-23T15:22:00Z (UTC). Stop time: 18:35Z (~3h 13m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable's last authored message was `220730Z` (`15:07:30Z` UTC, ~14.5 min ago; reading 1,050 lines of `worker.py` + waiting for PC gate); Fable's PC carry-over bot ran at `15:21Z`.
- On `FABLE OUT` (or 15 min silence without activity): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Plan & Formats State
- **`SETUP_PLAN.md` v2.3** (`cff7c298d7a3552f88bf13493e285940a5e556d5a4e6ef0efc9ae01c72412197`): **AGREE** from Astra (`150955Z`) and Neon (`151130Z`), editor Fable (`220730Z`). Minor alignment follow-up agreed by Astra (`151735Z`) & Neon (`152200Z`) for Section 2 (`RECEIVED` vs `C1`) and Section 6.2 (piece vs record vs local-outage retry).
- **`FORMATS.md` v2.3** (`9b9e5a39...`): **CHANGE** agreed by both Astra (`150955Z`, `151303Z`) and Neon (`151130Z`) for v2.4:
  1. §1.3 `RESUME.<n>.json` same-boot worker restart anchor check (first post-boot epoch matches `RESUME.<n>.slots[K]`, later same-boot restarts verify that anchor + chain and continue from current head with `"resume": null`).
  2. §1.8.1 pilot `FENCE.json` before `SCHEDULE.1` copies `RUN.json`'s `hard_cutoff_utc`.
  3. §1.8.3 `dispatch_unknown` for the single next in-flight candidate without disk evidence (later unreachable counters / unentered ranges stay `never_dispatched`).
  4. §1.1 `instance` wording: `null`/`null` in one hardware field contributes neither identity evidence nor a difference; both hardware fields `null` fails `instance_provable`; one-sided `null` is a difference.
- **Additional agreed controls for forthcoming v2 scripts (`151513Z`, `151916Z`, `152200Z`):**
  - Missing child Syzygy table (`KQPvKQ` present, `KPvK`/`KQvKP` missing) must never collapse into WDL `0` — log missing dependency and keep staged round pending.
  - Closing-inventory disk & inode budget per committed schedule (2.41 GB for 16.384M unplayed IDs vs 18.8 MB for 128k IDs) + rolling schedule horizon under §1.2.
- **Independent references (`ref/astra/`, `ref/neon/`):** outside paid package. Both tested & verified on Linux.

## Approval Ledger State (`scripts_v2/`) — ALL 5 PUBLISHED FILES 3/3 `YES`!
- **Package 1 (`scripts/`, 17 files):** `0` effective `YES` (frozen baseline).
- **`scripts_v2/` (manifest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`):**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c85f28f25792a98930b39fc4a4b26ad03639c4fc6ae303adffd32167f1`): **3/3 `YES`**.
  2. `scripts_v2/run/uciproc.py` (`7de2728aef77b686e759b73afedca5fee1f4d7ec68515e3176732690f0aa87a4`): **3/3 `YES`**.
  3. `scripts_v2/tests/test_uciproc.py` (`690b3243764c627d59eb3657c02c74089490e8c86ac658fdc51914dd6f418308`): **3/3 `YES`**.
  4. `scripts_v2/run/record.py` (`bc71fa894bf9fa0966fe39f3c4db0f6bd95a98d8ecbf372b0ce93a964d22ea52`): **3/3 `YES`**.
  5. `scripts_v2/tests/test_record.py` (`a8e16021f829da4c27c79812ac7d87f6cc8b1bb173c51581709003590806abb0`): **3/3 `YES`**.

## Next actions
1. Commit & push `152200Z` concurrence + memory update.
2. Poll both branches (`AwaitShell`) for Fable's `FORMATS.md` 2.4, `scripts_v2/run/worker.py`, `packer.py`, `tools/budget.py`, `home/`, `linux/`, guards (or hand-over signal).
3. Audit every line & live-test on Linux against `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`); keep updating memory ~every 10 minutes until `18:35Z` UTC.
