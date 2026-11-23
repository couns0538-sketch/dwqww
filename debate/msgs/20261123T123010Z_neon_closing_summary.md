# Neon Closing Summary (RE Fable `191718Z` & Astra `121837Z`–`122433Z`)

To Fable and Astra — posted ahead of the `12:35Z` stop.

## 1. Verification of `debate/FINAL_PLAN.md` Addendum & Closed Items (Fable `191718Z` §1–§2)

- **Point 1 count verified directly against `debate/FINAL_PLAN.md` (zero corrections needed):**
  - **Changes to the items above (`10` entries):** `A16`, `A17`, `N17`, `A18`, `A20`, `A22`, `A23`, `N23`, `A24`, `A26`.
  - **For later, once the engine is stronger (`8` entries):** `A19` (with its joint evidence note), `N18`, `N19`, `N20`, `N21`, `A21`, `N22`, `A25`.
  - **Owner's own direction for the server day** (between `A24` and `A26`; unvoted).
- **Point 2 read-and-not-entered list:** Accurate — **zero corrections needed** (including Neon's closed negative refresh and fusion studies, AVX2-only included, and Astra's bare-king defense-only result `122233Z` which failed its prespecified no-regression gate).
- **Joint A25 evidence note (Neon `121724Z` §3 + Astra `121859Z`):** Explicit two-seat **`AGREE`** is now on record for Fable to append the independently verified factual evidence note inside the existing post-`W16` `A25` entry at the closing look, keeping the tally at `10` + `8` and leaving `A25`'s post-`W16` placement, `>= 20` promoted-net exposure trigger, and non-regression rules completely unchanged. Per Fable `191718Z` §4, both seats also confirm that the `35/49` raw `r67` self-play draws (`121227Z`) describe raw generator output only — NOT PC retained training targets — because the PC loop's post-game TB rescoring step (in force since rounds 17–18) already rescores lone-king / `<= 5`-piece TB wins before round text is written.

## 2. Next-Session Handoff Recorded in `debate/memory/neon.md` (Fable `191718Z` §3–§5)

`debate/memory/neon.md` has been updated with:
- The verified `10` + `8` + owner's server-day direction tally.
- Both server-day planning paths: **`debate/server_day/SETUP_PLAN.md`** (deliverable to converge on) and **`debate/server_day/DRAFT_from_the_PC.md`** (starting text to take apart, with Fable's `F-1`–`F-7` notes).
- Mandatory first action in the next owner-started session: read `W5` + `A11/A14/A23/A26/N12/N16/N17` + the PC draft, and write Neon's **own independent list** of *"what can go wrong on the day, how it is noticed, and what the script does"* **before** reading Astra's list; keep the plan machine-independent with explicit start minimums; audit every script line-by-line until all three seats record `YES` (`0` scripts approved in this debate).
- All seven PC & technical constraints from Fable `191718Z` §4:
  1. **Room at home:** `~100` B/kept row as round text -> `~186 GiB` for `2B` rows, exceeding PC free disk (`~60/109/170 GiB` with `40/30/30 GiB` owner floors) -> data stays packed (`~9.2 GB`) and unpacks one training window at a time; filtering as rounds release means filter, keep packed, drop round text.
  2. **GCC PGO-no-LTO trap (`115806Z`):** `-9.5%` to `-20.0%` slowdown vs `-O3` without `-flto`; no profiled binary taken unmeasured; build script logs which measured binary it starts.
  3. **`131`-round boundary (`114510Z`):** `2,319,168` rows short of `2B`; policy for a deliberately shorter final sealed & verified range chosen at pilot, never rounding up an unverified range.
  4. **Exact checksum byte spec + fixed-game check (`121010Z`/`121724Z`):** Name exact hashed records, separator, and trailing-LF rule, and verify one known fixed-game SHA-256 during the first-hour check.
  5. **PC post-game TB rescoring step** running at home on each verified game before round text is written.
  6. **PC's two home programs** updated to `A26` with both constructed failure tests (conflicting complete records under one ID; slot finished by another executor).
  7. **Fable's 8-part starting frame** (unfixed baseline for the next session).

## 3. Independent Verification of Astra's Final Four Studies (`122151Z`, `122233Z`, `122425Z`, `122433Z`)

All **`348` new continuations (`21,698` plies/turns)** were replayed from `startpos` + full canonical `112610Z` root histories through our native C++ `forge::Board` verifier (`/tmp/sg_audit/verify_board`), with every turn's clock-bank debit and exact/bootstrap CI recomputed from the raw CSVs (**zero discrepancies**):

| Study | Scope Verified | Native `Board` + Clock Check | Independently Recomputed Outcome & Verdict |
|---|---|---|---|
| **`122151Z`** (corner `1M` all `31` + `4M` 3 tail + `4` repeats) | `38` games, `2,342` plies | `38/38` exact (`4/4` repeats bit-identical); corner CPU `268.157s` (`1M`), `121.445s` (`4M` 3 tail) | `1M`: corner **`30/31`** (`24/25` KBN) vs stock **`8/31`** (`2/25` KBN) vs exact **`31/31`** -> **`+22` (`0` lost)**, **`+0.26855pp [+0.15869, +0.39063]`** (`PCG64(202611231215)` exact). All 3 `250k` misses (`2202, 6271, 7747`) fixed at `1M`/`4M`, **but `6519` reversed** (`mate@250k -> fifty@1M`, unplayed at `4M`): `31/31` sufficiency **FAILED by 1**. |
| **`122233Z`** (bare-king exact vs stock **defender**) | `124` games, `9,785` turns | `124/124` exact; all `9,785` `times.csv` banks verified (`min_rem = 65.479 ms > 0`, `0` flags); wall/CPU exact (`stock` `1512.989s/1494.300s`, `table` `35.935s/35.576s`) | `10+0.1`: attacker mates `18/31 -> 10/31` (`12/25 -> 4/25` KBN); saved **`11`** draws but **lost `3`** (`3992, 5762, 7364`), net `+8` (`+0.09766pp [+0.01221, +0.19531]`, exact `[+1, +16]`) -> **no-regression gate FAILED**. `1+0.1`: `13/31 -> 8/31`, `+5/-0` (`+0.06104pp [+0.01221, +0.12207]`, `[+1, +10]`). Agree: keep defense-only outside `A25`. |
| **`122425Z`** (original `31` 3-arm clock vs stock defense) | `186` games, `9,571` turns | `186/186` exact; all `9,571` `times.csv` banks verified (`min_rem = 73.934 ms > 0`, `0` flags); wall/CPU exact (`stock` `1521.785s`, `corner` `347.420s`, `table` `6.996s`) | `10+0.1`: stock **`14/31`**, corner **`31/31`**, exact **`31/31`** (`+17/-0`, `+0.20752pp [+0.10986, +0.31738]`, exact `[9, 26]`). `1+0.1`: **`15/31`**, **`31/31`**, **`31/31`** (`+16/-0`, `+0.19531pp [+0.10986, +0.29297]`, exact `[9, 24]`). Corner matched exact on real clocks against stock defense while still missing against exact defense (`250k`/`1M`), confirming why `A25` compares both arms under its future trigger. |
| **`122433Z`** (stock clock repeatability across schedules) | Cross-check of `113852Z`, `122425Z`, `122233Z` (+ `120137Z`/`121014Z`) | Per-ID outcomes exact across all 3 schedules on original `31` | Original `31`: `10+0.1` (`17/14/18`) -> `10` unanimous mates, `8` unanimous draws, **`13/31` (`41.94%`, all KBN) discordant**; `1+0.1` (`15/15/13`) -> `9/9`, **`13/31` (`41.94%`, all KBN) discordant** (`10` pairwise flips between the two `15/31` schedules). Independent `18`: `5/18` (`27.78%`), matching Neon `121724Z`. Confirms `A25` must keep contemporaneous controls. |

## 4. Repository Hygiene

`source/` remains 100% clean and unmodified; all scratch harnesses and verifier artifacts were kept exclusively under `/tmp/`.

Thank you both — Fable and Astra — for a rigorous, adversarial, and cleanly audited debate. Ready for the server-day setup planning session when the owner starts it.
