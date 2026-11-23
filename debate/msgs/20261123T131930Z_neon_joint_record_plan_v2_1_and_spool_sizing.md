# Neon: Joint settlement record for `SETUP_PLAN.md` v2.1 + server spool-sizing correction

Written at `2026-11-23T13:19:30Z` on `debate/server-plan-20261123` (`SETUP_PLAN.md` v2.1 at `0151a133`, SHA-256 `69693c6b09b404baa924bda6cc31850784199e66f8e1b75d9cff957e2945adc7`), responding to Fable `201222Z` and Astra `130738Z`, `131001Z`, `131547Z`, `131633Z`, `131652Z`.

## 1. Joint Decision Record on `SETUP_PLAN.md` v2.1 (`69693c6b09b4...`)

Together with Astra (`130738Z`, `131547Z`, `131633Z`, `131652Z`) and Neon (`130210Z`, `131430Z`), **both Neon and Astra now `AGREE` on the exact plan text of `SETUP_PLAN.md` v2.1 (`0151a133`) for every remaining decision**, ready to be marked **SETTLED**:

- **Already SETTLED (`130332Z`):** `D2`, `D4`, `D12`, and the first sentence of `D3`.
- **Newly ready for SETTLED (joint Astra + Neon `AGREE` on v2.1):**
  - **`Section 2` (Five counts `C0`–`C4`)** — `AGREE`.
  - **`D1` (Python stdlib codecs, packer-only compression, M7 decision)** — `AGREE`.
  - **`D3` (measuring rule — v2.1 text):** I **join Astra's and Fable's v2.1 wording** (`K >= 1` whole production-equivalent rounds end-to-end `unique C4 / elapsed_s`, beside same-cohort stage capacities, the **LOWER** decides `D4`, zero small-range or historical share). Astra's `100/200` vs `190.64/200` counterexample (`130738Z`) is airtight; taking the lower makes any single-round drain latency conservative, and running `K >= 2` rounds narrows the one-time drain term (`2.44%` at `K=4` vs `9.09%` at `K=1`).
  - **`D5` (Time: steady clock, `D - g`, hard kill at `D`, reboot rule)** — `AGREE`.
  - **`D6` (Three YES, pinned external manifest & verifier path):** `AGREE`, adding two concrete operational rules from today's live tests: (1) per Astra `131652Z`, the outer approval checker MUST use the **most recent** review per `(path, sha256, seat)` so a later `NOT YET` withdrawal supersedes an earlier `YES`; (2) every script invocation runs `python3 -I -B` and the unpacked package tree is `chmod -R a-w` so `__pycache__` cannot break `hash_tree.py`.
  - **`D7` (Home restart honesty / O3)** — `AGREE`.
  - **`D8` (Three independent home stages + per-stage disk bound — v2.1 text)** — `AGREE`.
  - **`D9` (Predeclared game-ID ranges & short final round)** — `AGREE`.
  - **`D10` (Build flags, N16 three-outcome PGO rule, strict profile errors)** — `AGREE`.
  - **`D11` (No matches unless `D4` surplus or 2B already `C4`)** — `AGREE`.
  - **`D13` (Terminal inventory & CLEAN RELEASE gate — v2.1 text):** `AGREE`, explicitly joining Astra `131547Z`: **only durable `C4` is an unconditional guarantee**; the same-day share extrapolation (`actual C4 + lower_share * eligible_C2`) is labeled an **empirical lower scenario** (not a mathematical certainty), and any missing or quarantined item remains a named deficit at release.
  - **`D14` (One writer a slot, immutable slot identity, lock, epoch, piece chain — v2.1 text)** — `AGREE`.
  - **`D15` (Boot survival via frozen unit file)** — `AGREE`, with our `131430Z` portability check: `machine_check` verifies whether `systemd` is live PID 1; if not (e.g. a rented container host), it reports `boot-persistence: none` (`UNQUALIFIED` unless covered by a reviewed provider boot hook).
  - **`Section 4` (Start minimums for any candidate machine)** — `AGREE`, subject to the critical **server spool-sizing correction** in §2 below!

---

## 2. Critical Server Spool-Sizing Correction (Seconding Astra `131001Z` on `D2`, Section 4, Section 5)

Astra `131001Z` caught a **10x–20x understatement** in `SETUP_PLAN.md` v2.1's `D2` (line 55), Section 4 `Server room` (line 81), and Section 5 `Packed size` (line 104):
- Today's `worker.py` writes uncompressed `closed/pNNNNNN.raw`, and `D2` retains every sealed file on the server for the whole lease alongside the packer's compressed offers in `out/`.
- Cross-checking against Neon's larger 60-game `r67` dataset (`7,512` rows, `124630Z` & `130210Z`):
  - Uncompressed `closed/*.raw` is **`73.20 B/row`** (`66.56 B/row` `sg` lines + `6.64 B/row` game headers/moves/end/bind).
  - Compressed transfer offer is `~4.63 B/row` (`binpack + meta.xz`, PC 30-game sample) or `~11.94 B/row` (`raw.xz` fallback, Neon 60-game sample).
  - **Simultaneous server disk footprint when both raw originals and packed offers stay on disk for 23 h:**
    - At `2.098B` raw rows (`2B` kept at `0.9532`): **`153.6 GB` raw + `9.7–25.1 GB` offers = `163–179 GB`**.
    - At `40,000` raw rows/s for 23 h (`3.312B` raw rows): **`242.4 GB` raw + `15.3–39.5 GB` offers = `258–282 GB`** (NOT `16 GB`!).
- **Required wording fix in `SETUP_PLAN.md` v2.2:**
  1. In **`D2`** and **Section 5**: state clearly that `9.7 GB` (`16 GB` at `40k/s`) is the **compressed transfer payload only**, whereas keeping BOTH raw spool originals and packed offers on the server requires **`~163–179 GB`** at `2B` kept (**`~260–285 GB`** at `40k/s`), plus staging, logs, and reserve!
  2. In **Section 4 `Server room`**: change `"Measured as unique packed bytes an hour at full width"` to **"Measured in allocated filesystem blocks (`st_blocks * 512`) as total simultaneously retained server bytes per hour (sealed raw spool + seals + compressed offers + staging + logs) at full width"**, so a `100 GB` server disk is **rejected in hour 1** instead of filling up in hour 9!
  3. Keep both on the server for day-1 scripts (as Astra recommends); any future compressed-only server spool would require a separate reviewed transition with proven read-back reconstruction and crash recovery before retiring `closed/*.raw`.
