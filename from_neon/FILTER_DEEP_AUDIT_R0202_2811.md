# FILTER_DEEP_AUDIT_R0202_2811 — Live Round `r0202` Deep Filter Pathology Audit

- **Source:** `C:\nnue-lab\runs\forge\r0202\data\filtered.plain` (strictly read-only full scan of `16,005,733` records in `78.82s`; raw JSON in `FILTER_DEEP_AUDIT_R0202_2811.json`)
- **Totals:** `kept = 15,156,682`, `marked_skip = 849,051`, `quiet_kept = 12,338,956`, `noisy_kept = 2,817,726` (`18.591%`), `games = 121,783`, **`avg_kept_per_game = 124.46`**, **`avg_quiet_per_game = 101.32`**

## 1. Extreme Within-Game Correlation & Horizon Swings (Quiet Adjacent Plies)
- **Adjacent quiet pairs:** `10,650,131` | **Lag-1 score correlation `corr(s_t, -s_{t+1})`:** **`0.99697`** | **Mean `|s_t + s_{t+1}|`:** `22.78 cp`
- **Adjacent exact-zero runs (`s_t == 0 && s_{t+1} == 0`):** **`232,370`** (`63.7%` of all quiet `score == 0` rows!)
- **Quiet ply-to-ply swings:** `>=200`: `81,728` (`0.767%`), `>=300`: `30,143` (`0.283%`), `>=400`: `14,274` (`0.134%`), `>=600`: `4,475` (`0.042%`)
- **Implication for Server Day `2.0B`:** Forge keeps **100% of consecutive plies (`101.32` quiet pos/game)** with `0.997` lag-1 correlation, whereas Stockfish `nnue-pytorch` uses random per-ply skipping to decorrelate positions within a game.

## 2. Massive White Eval & Outcome Bias by Ply Band (Fixed Even `random_move_count = 8`)
| Ply Band | Quiet Rows | Share % | Mean White Eval (cp) | White Score % |
|---|---:|---:|---:|---:|
| `0..7` | `0` | `0.000%` | — | — |
| `8..15` | `779,900` | `6.321%` | **`+100.62`** | **`61.33%`** |
| `16..31` | `1,494,671` | `12.113%` | **`+111.46`** | **`62.45%`** |
| `32..79` | `4,168,476` | `33.783%` | **`+145.74`** | **`62.56%`** |
| `80+` | `5,895,909` | **`47.783%`** | **`+181.80`** | **`59.85%`** |

- **Critical Note:** Nearly HALF (`47.78%`) of all quiet positions are at `ply >= 80` (`23.69%` at `ply >= 120`), carrying **`+181.80 cp`** mean White eval bias! Meanwhile `ply 0..7` is `0.0%` (so dropping `ply < 16` on existing `r0178..r0202` without opening anchors would remove all opening positions!).

## 3. Exact `score == 0` Flood & `|score|` Saturation Tail (Quiet Kept)
- **Total `score == 0` quiet:** **`364,905` (`2.957%`)** (`res == 0`: `331,658`, `res != 0`: `33,247`, `halfmove >= 30`: `10,846`, `<= 10 pcs`: `124,834`).
- **Extreme blowout tail (`|score| >= 800`):** **`14.629%`** (`1,805,099` quiet rows/round), including **`6.843%` (`844,346` rows/round = `~21.1M` per 25r window)** with **`|score| >= 1200`** where sigmoid gradient `p(1-p)` collapses `> 3,466x`!

| `|score|` Band (Quiet) | Count | Share % |
|---|---:|---:|
| `==0` | `364,905` | `2.957%` |
| `1..49` | `2,177,812` | `17.650%` |
| `50..99` | `1,753,391` | `14.210%` |
| `100..299` | `3,335,524` | `27.032%` |
| `300..599` | `2,145,821` | `17.391%` |
| `600..799` | `756,404` | `6.130%` |
| `800..1199` | `960,753` | `7.786%` |
| `1200..1599` | `510,320` | `4.136%` |
| `1600..2000` | `334,026` | `2.707%` |

## 4. Score-Result Conflicts Missed by `filterqc.py` (Quiet Kept)
- **Drawn-game (`res == 0`) conflicts (`filterqc.py` skips `res == 0`):**
  - `|s| >= 300`: `168,748` (`1.368%`)
  - `|s| >= 400`: **`64,679` (`0.524%`)**
  - `|s| >= 600`: `13,366` (`0.108%`)
- **Decisive (`res != 0`) opposite-sign conflicts (`filterqc.py` only drops `<= -600`):**
  - `s * res <= -200`: `22,843` (`0.185%`)
  - `s * res <= -300`: **`6,319` (`0.051%`)**
  - `s * res <= -400`: `1,783` (`0.015%`)

## 5. Output-Bucket Skew (Quiet Kept)
- **`OB0` (`<= 4` pcs, `min_pieces = 4` drops `2–3` pcs):** **`2.095%`** (`258,541`) — **9.5x starved** vs **`OB1` (`19.851%`)** and **8.6x starved** vs **`OB2` (`18.040%`)**!
- Full distribution: `OB0 2.095%`, `OB1 19.851%`, `OB2 18.040%`, `OB3 13.682%`, `OB4 11.062%`, `OB5 10.193%`, `OB6 11.041%`, `OB7 14.035%`.
- Note: Verified `config.forge.toml:313-314` sets `tablebase_path` ONLY for self-play adjudication; `SyzygyPath` is NOT set in `v3_uci_options` for search/matches, so `OB0` starvation (`KNN-K = +97..+114 cp`) directly impacts live play.

## 6. Composite Filter Drop Rates & Next `250k` Proof (`F_FIX_25R_v2`)
- **Rule A (`draw>=600 | dec>=400 | swing>=400`):** `30,834` (`0.250%` of quiet rows)
- **Rule B (`draw>=400 | dec>=300 | swing>=300 | (score==0 & hm>=30)`):** `115,093` (`0.933%` of quiet rows)
- **Immediate Monday Bar 3 `250k` GPU Test (`F_FIX_25R_v2` vs `R1-skip` on `r0178..r0202`, same recipe/seed=1):** Drops `F-03` (`res == 0 & |score| >= 400`), tightened decisive conflicts (`res != 0 & score*res <= -300`), and `F-08` extreme dead-gradient blowouts (`|score| > 1200`) -> removes **`~7.42%`** pure noise/dead-gradient rows while keeping `92.6%` volume and `100%` of openings. Declared in `F_FIX_25R_V2_DECLARATION.json` before training!
