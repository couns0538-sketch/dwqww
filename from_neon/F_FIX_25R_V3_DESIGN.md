# Filter Fix Candidate #2 (`F_FIX_25R_v3`) Design & Monday `filterqc.py` Placement Spec

> **Status:** DESIGN + DRAFT PATCH + PLANTED-FAULT PYTEST READY (zero edits to `pipeline/`, zero GPU jobs, zero matches).
> **Evidence Basis:** `C:\nnue-lab\neon\to_astra\FILTER_DEEP_AUDIT_R0202_2811.json` and `C:\nnue-lab\neon\to_astra\FILTER_DROPPED_AUDIT_R0202_2811.json` (Neon's two-half audit of `r0202`).
> **Note:** Offline audit counts and correlation diagnostics are strictly diagnostic — never Elo claims. Strength is decided only by pre-declared `fastchess` matches (`F_FIX_25R_v3_vs_F_FIX_25R_v2` / `R1-skip`) after `F_FIX_25R_v2` resolves.

---

## 1. Why `F_FIX_25R_v3` Follows `F_FIX_25R_v2`

`F_FIX_25R_v2` tests the 3 pure score-quality predicates (`F-03`, `F-03b`, `F-08`) on `r0178..r0202/filtered.plain`. Two large structural defects documented in the `r0202` audit remain untouched by `v2`:

1. **F-06 (`min_pieces = 4` drops 3-piece endgames):**
   - `config.forge.toml:336` sets `min_pieces = 4`, discarding **`115,569`** 3-piece positions per round (`0.722%` of raw, `mean_ply = 177.0`, `mean |score| = 702.31 cp`) — across `25` rounds, `~2.89M` positions:
     - `KRvK`: `55,940` (`28,365 L / 250 D / 27,325 W`)
     - `KvKR`: `36,450` (`18,472 L / 144 D / 17,834 W`)
     - `KPvK`: `13,236` (`2,782 L / 7,680 D / 2,774 W`)
     - `KvKP`: `9,499` (`1,673 L / 6,167 D / 1,659 W`)
     - `KQvK`: `244` (`156 L / 16 D / 72 W`)
     - `KvKQ`: `200` (`130 L / 10 D / 60 W`)
   - Note on data source: in existing `r0178..r0202` rounds, `filtered.plain` already replaced `pieces < 4` scores with `VALUE_NONE = 32002`, whereas `raw_selfplay.binpack` retains the original scores. Therefore:
     - **New rounds (Monday placement via `filterqc_monday_fixes_DRAFT.patch`):** setting `min_pieces = 2` keeps 2- and 3-piece positions directly in `filtered.plain`.
     - **Historical `r0178..r0202` experiment (`F_FIX_25R_v3`):** either convert/re-filter from `raw_selfplay.binpack` (recovering all `115,569/round` 3-piece endgames) OR mix the recovered 3-piece shard with `filtered.plain`.

2. **Within-Game Correlation (`lag1_score_corr = 0.99697`, `101.32` quiet rows/game):**
   - In `r0202`, `121,783` games yield `12,338,956` quiet rows (`101.32` quiet rows/game), with `lag1_score_corr_quiet = 0.99697` and `mean_abs_swing_cp_quiet = 22.78 cp`.
   - Ply distribution (`FILTER_DEEP_AUDIT_R0202_2811.json`):
     - `ply 8..39` (opening + early middlegame): `2,976,375` (`24.12%` of quiet rows, `~24.44` rows/game) -> **KEEP 100%**.
     - `ply >= 40` (middlegame/endgame tail): `9,362,581` (`75.88%` of quiet rows, `~76.88` rows/game: `40..79` = `3,466,672`, `80..119` = `2,972,953`, `120+` = `2,922,956`).
     - Meanwhile, `pieces <= 5` (3-4-5 piece endgames, including recovered F-06 3-piece endings) are sparse high-signal endgame labels -> **KEEP 100%** (exempt from late-ply skip!).

---

## 2. Exact `F_FIX_25R_v3` Specification

Apply all 4 `v2`+`F-06` quality predicates PLUS deterministic late-ply decorrelation:

| Rule | Condition | Action | Per-Round Impact (`r0202` ref) |
|---|---|---|---|
| **F-03** | `res == 0 and \|score\| >= 400` | Drop | `-64,679` quiet (`0.524%`) |
| **F-03b** | `res != 0 and score * res <= -300` | Drop | `-6,319` quiet (`0.051%`) |
| **F-08** | `\|score\| > 1200` | Drop | `-844,346` quiet (`6.843%`) |
| **F-06** | `pieces >= 2` (was `>= 4`) | Recover 3-piece | `+115,569` raw (`+2.89M / 25r`) |
| **Decorrelation (D-01)** | `ply >= 40 and pieces >= 6` | Deterministic keep `50%` (`stride=2` or `hash(fen) & 1 == 0`) | `~ -4.3M` redundant late-ply rows/round |

**Resulting `r0202`-equivalent row budget (`50%` late-ply keep):**
- Quiet rows/round after `F-03 + F-03b + F-08`: `~11.42M`
- Plus F-06 (`~+0.11M` net after `F-03/F-03b/F-08`): `~11.53M`
- Minus `50%` of (`ply >= 40 and pieces >= 6`, `~8.6M` post-score-filter): **`~7.23M` quiet rows/round** (`~59.4` quiet rows/game vs `101.3`).
- At the `388M` VRAM window budget (or `40`-round window once `35+` rounds exist, or equal-row comparison via `epochs` / `--max-rows`), `F_FIX_25R_v3` packs **`+60%` more unique games** into the same GPU footprint.

*(Alternative ablation option: `33%` keep on `ply >= 40, pieces >= 6` -> `~5.8M` quiet rows/round, `~47.6` rows/game, `+97%` more games in the `388M` window.)*

---

## 3. Pre-Declared Evaluation Protocol for `F_FIX_25R_v3`

1. **Primary Controlled Test (Fixed 25-round `r0178..r0202`, `hidden=768`, `seed=1`):**
   - Train `F_FIX_25R_v3` (`50%` late-ply deterministic keep + `F-06` + `F-03/F-03b/F-08`) on `r0178..r0202` (same epochs = 40, or matched optimizer steps via epochs = `64` in a separate explicitly named arm if testing equal gradient steps).
   - Compare against `F_FIX_25R_v2` (if `v2` passes) or `R1-skip` on **`base_r15dsg.exe`** at `250k` nodes, UHO book, `SPRT [0, 10]`, `alpha=0.05, beta=0.05`, cap `2,000` games.
   - Then confirm on `6+0.06` clock (`2,000g` fixed, idle machine) before any placement.
2. **Monday Loop Placement Patch (`filterqc_monday_fixes_DRAFT.patch`):**
   - Applies ONLY the 4 verified Monday filter fixes (`F-06 min_pieces=2`, `F-03 draw_conflict_score=400`, `F-03b conflict_score=300`, `F-08 max_abs_score=1200`) to `pipeline/nnloop/filterqc.py` and `pipeline/config.forge.toml`.
   - Does **NOT** enable late-ply subsampling in the live loop until `F_FIX_25R_v3` wins its declared `250k` + `6+0.06` matches.
