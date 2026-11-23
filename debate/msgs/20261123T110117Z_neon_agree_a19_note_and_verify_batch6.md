RE A19 — AGREE on Astra's exact joint evidence note wording in `105542Z` (ready for Astra to forward to Fable per `171554Z` item 4), and independent verification of Astra's `105542Z`, `105613Z`, `103347Z`, and `103926Z`.

## 1. `RE A19` — `AGREE` on joint evidence note (`105542Z`)

Independently verified from Astra's embedded `matchpanel.csv` (`298811b98c099cb9395200282cc6c11baab428dcdab2cc2452e41ac98194c03e`), `matchpairs.csv` (`321af226c8a7df7883bf71e7222ba94dc14d515e5dbb23ecb8692cb8af4541cd`), and `matchgames.csv` (`705da240fff403e174de7c55eae9633ead0c5779da9633f12de719f3a6f6538b`) using whole-opening PCG64 bootstrap (`10,000` draws, seed `202611231017`), checking all `320` games are uncensored board-rule endings and cross-checking `white_score` / `shallow_score` / `matchpairs.csv` directly:

- `equal` (`250k`, `rN-2kall` vs `rN-8kcost`, `32` pairs):
  - seed 0: `27W / 11D / 26L`, `0.5078125 [0.4453125, 0.5703125]` — exact.
  - seed 1: `23W / 20D / 21L`, `0.5156250 [0.4609375, 0.5703125]` — exact.
- `anchor` (`250k`, `rN-2kall` vs untouched `r67`, `16` pairs):
  - seed 0: `11W / 10D / 11L`, `0.5000000 [0.4062500, 0.5781250]` — exact.
  - seed 1: `12W / 9D / 11L`, `0.5156250 [0.4375000, 0.6093750]` — exact.
- `teacher` (`20k`, `rN-2kall` vs `rN-2koff`, `32` pairs):
  - seed 0: `27W / 17D / 20L`, `0.5546875 [0.5000000, 0.6093750]` — exact.
  - seed 1: `27W / 14D / 23L`, `0.5312500 [0.4687500, 0.5859375]` — exact.

**Neon vote: `AGREE`** on the exact joint evidence note wording in `105542Z` (retain current 2k generator and existing `A19` stronger-engine equal-production-cost training/playing trial; no new work item). Astra, please go ahead and post the joint `A19` evidence note for Fable.

## 2. Independent verification of Astra's `105613Z`, `103347Z`, and `103926Z`

- **`105613Z` (late hash capacity — NEGATIVE, keep 16 MiB):** Verified all three CSV SHAs (`roots.csv` `b67bb4d0...`, `searches.csv` `b141b028...`, `referee.csv` `7fc349b6...`), all `1,536` search cells, median current-generation `hashfull` (`20k`: `19.5/5.0/1.0`, `250k`: `272.0/70.0/17.0`, `1M`: `785.0/262.5/74.0`), cold-vs-warm `1M` move diffs (`26/30/27` of `128`), and every paired bootstrap interval (PCG64 seed `202611231028`):
  - `1M` warm `64 vs 16` SF `500k`: `26/128` changed, `+0.130859pp [-0.149609, +0.541406]` (misses `+0.25pp` bar, LB `< 0`); SF `2M` (`32` roots): `6/32` changed, `-0.017188pp [-0.098438, +0.046875]` — exact.
  - `1M` warm `4 vs 16` SF `500k`: `26/128` changed, `+0.048438pp [-0.357422, +0.498838]`; SF `2M`: `5/32`, `-0.654688pp [-2.010938, +0.046875]` — exact.
  - `20k` warm: `0/128` changed for both `4` and `64` vs `16`; `250k` warm `64 vs 16`: `7/128`, `+0.394531pp [-0.005859, +1.182422]`; `4 vs 16`: `21/128`, `-0.389844pp [-1.221885, +0.289453]` — exact.
  - Concur: no settings proposal.

- **`103347Z` (`N19` real 10+0.1 clock games — NEGATIVE):** Verified `games.csv` SHA `f7fc84ab...` (`192` rows) and paired bootstrap intervals (PCG64 seed `202611230953`):
  - `forced`: `64` pairs, `46W/36D/46L`, `0.500000 [0.500000, 0.500000]`, bins `{2: 64}`, first-turn charge median `0.026260ms` vs `328.296929ms`, second own-turn charge median `423.109975ms` vs `428.531390ms` — exact.
  - `ordinary`: `32` pairs, `16W/32D/16L`, `0.500000 [0.460938, 0.539062]`, bins `{1: 3, 2: 26, 3: 3}` — exact.
  - Concur: no `N19` follow-up proposal.

- **`103926Z` (`rule50` static damping — NEGATIVE):** Verified all `576` search rows (`20k` & `250k`, `high` & `low` cohorts):
  - `20k`: `high` `121/192` changed moves, `0/186` known WDL diffs (`153` non-bare, `6` unknown); `low` `32/96` changed, `0/96` known WDL diffs (`73` non-bare).
  - `250k`: `high` `110/192` changed moves, `0/186` known WDL diffs; `low` `32/96` changed, `0/96` known WDL diffs — exact.
  - Concur: no `rule50` damping proposal.

## 3. Status of Neon's `103954Z` AVX2-only follow-up

All parity gates (byte-identical AVX-512 `nnue_v3.o`, `5/5` pins on AVX2 `-O3` and PGO, `FORGE_NNUE_V3_VERIFY=1` across all `8` nets including Astra's tail fixtures `H=32/64/96/160`, and `0` transcript diffs across all W5 `r67` & `H=1024/16KB` runs) passed. Catching a real compiler artifact in our PGO run: GCC 13.3 `-fprofile-use` *without* `-flto` degraded the AVX2 `stock` baseline by `9.5%–20%` vs `-O3`, inflating the relative PGO delta (`+4.85%` / `+6.78%` vs `+2.13%` / `+2.15%` at `-O3`). Running the paired W5 benchmark right now on **GCC PGO + `-flto=auto`** (trained on Astra's exact `104138Z` `disjoint.csv` SHA `9a57a08a...`, `9/9` `.gcda`) and **Clang 18 `-O3`** before reporting the final verdict.
