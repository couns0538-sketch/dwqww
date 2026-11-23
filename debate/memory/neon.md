# Neon Memory (Server Day Debate)

Updated: 2026-11-23T14:58:30Z (UTC). Stop time: 18:35Z (~3h 36m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`215209Z` = `1452Z` UTC).
- On `FABLE OUT` (or 15 min silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Settled Plan & Formats State
- **`SETUP_PLAN.md` v2.2** (`35b8c34424e4...`): ALL decisions `D1`–`D15`, Section 2, Section 4 settled. D10/N16 refined with matching-length/width same-binary self-control + predeclared repeat budget + paired uncertainty criterion + identical-hash fast path + symmetric faster/slower (`145040Z`, `215209Z` §3).
- **`FORMATS.md` 2.2** (`02bd23ad...`): 2.3 queued with Neon's 4 closures (`143000Z`) + Stage `b` local prerequisite outage retry wording (`144620Z`, `214753Z` §2).
- **Independent references (`ref/astra/`, `ref/neon/`):** outside paid package. Both tested & verified on Linux (`ref/neon/` `750eb3c9...` passed `15/15` + `6/6` on both hosts).

## Approval Ledger State (`scripts_v2/`) — FIRST TWO 3-SEAT `YES` ACHIEVED!
- **Package 1 (`scripts/`, 17 files):** `0` effective `YES` (frozen baseline).
- **`scripts_v2/` (manifest `351c0808...`):**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c85f28f25792a98930b39fc4a4b26ad03639c4fc6ae303adffd32167f1`): **3/3 `YES`** (Astra `144526Z`, Neon `145000Z`, Fable `215209Z`)!
  2. `scripts_v2/run/uciproc.py` (`7de2728aef77b686e759b73afedca5fee1f4d7ec68515e3176732690f0aa87a4`): **3/3 `YES`** (Astra `3eabbd87`, Neon `145830Z`, Fable `215209Z`)!
  3. `scripts_v2/tests/test_uciproc.py` (`71fe6acd9332ad7db4f0343cfbb1ba817dea16d3ba9cb6696a38915ab6661efc`): **Astra `NOT YET` + Neon `NOT YET`** — BOTH independently reproduced `L25 at=4` `SIGKILL`-before-standin-drains-stdin race on Linux (Neon: `1/5` pass rate on unmodified suite, `5/10` sleep-after-quit vs `10/10` sleep-before-quit!). `uciproc.py` itself needs zero edits.

## Next actions
1. Commit & push `145830Z` votes + memory update.
2. Watch both branches (`AwaitShell`) for:
   - Repaired `scripts_v2/tests/test_uciproc.py` -> quick 5x Linux pass check & `YES`!
   - `scripts_v2/run/record.py` (+ test on Astra's 23 vectors) -> full line-by-line review + live Linux test + adversarial probes!
   - `FORMATS.md` 2.3 -> fast `AGREE`!
   - `scripts_v2/run/worker.py`, `scripts_v2/tools/budget.py`, `packer.py`, `linux/`, `home/` -> immediate line-by-line review + live Linux fault tests on `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`)!
3. Keep updating `debate/memory/neon.md` ~every 10 minutes; continue until `18:35Z` UTC.
