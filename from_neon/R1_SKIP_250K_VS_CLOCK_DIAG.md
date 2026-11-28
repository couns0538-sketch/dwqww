# R1-skip vs r0067: 250k vs 6+0.06 Clock Diagnostic & `same_search`
- **Generated:** 2026-11-28 15:51:33 PC
- **`base_r15dsg.exe` SHA-256:** `5e6f333b95b7ceda01a599a713d6bad536633b235dc73b409e1f12c1bb809011`
- **Loop PGO `forge.exe` SHA-256:** `cef2f21589102392fdd7e3cbde74bfd01baa94f9677a2be33365f68e4bceb03d`
- **Config UCI option diffs (250k vs 6+0.06):** `{}` (ZERO differences).

## 1. `same_search` Between `base_r15dsg.exe` and Loop PGO `forge.exe` (300 UHO pos, depth 9, exact live UCI opts)
| Net | Diffs / 300 | `base_r15dsg` Nodes | Loop PGO Nodes | `base_r15dsg` kNPS | Loop PGO kNPS | PGO Speed Ratio |
|---|---:|---:|---:|---:|---:|---:|
| `r0067` | **0** | 2,271,371 | 2,271,371 | 2,557.0 | 2,669.2 | 1.044x |
| `R1_skip` | **0** | 2,251,493 | 2,251,493 | 2,488.9 | 2,757.7 | 1.108x |

**Verdict on Hypothesis (c):** **RULED OUT.** `base_r15dsg.exe` and `runs/forge/engines/v3-r15dsg-sp-clang/forge.exe` are **bit-exact identical** in search on all 300 UHO positions for BOTH `r0067` and `R1-skip` (`0/300` diffs).

## 2. Raw PGN Game Lengths (Note: `pgn.min = true` omitted move comments)
- `OPUS_R1_skip_vs_r0067_1000g_250k` (`games_20261128_073659.pgn`, `sha256=30ae708664923186...`): `1000` games, median `141.0` plies/game (mean `148.62`, p10..p90 `83..222`).
- `OPUS_R1_skip_vs_r0067_2000g_6p006` (`games_20261128_140455.pgn`, `sha256=765d5b189b2c2737...`): `2000` games, median `146.0` plies/game (mean `154.57`, p10..p90 `85..232`).
- *Actionable note:* Future diagnostic matches should pass `-pgnout ...` without `min=true` (or keep `track_nodes`/`track_timeleft`) if we want per-move depth/time from PGNs.

## 3. Direct 40-Position UHO Probe on Loop PGO `forge.exe` (`250k` vs `6+0.06` Clock Limits)
| Net | Limit | Median Depth | Mean Depth | Median Nodes | Mean Nodes | Median Time | Mean Time | Mean |cp| |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `r0067` | `nodes_250k` | 18.0 | 17.60 | 202,936 | 198,157 | 83.6 ms | 83.2 ms | 79.4 |
| `r0067` | `clock_6000_inc60` | 20.0 | 20.48 | 541,651 | 664,506 | 181.9 ms | 221.5 ms | 76.2 |
| `r0067` | `clock_2500_inc60` | 19.0 | 18.62 | 270,475 | 345,020 | 92.0 ms | 114.6 ms | 76.3 |
| `R1_skip` | `nodes_250k` | 18.0 | 17.80 | 215,886 | 207,425 | 83.1 ms | 82.9 ms | 84.7 |
| `R1_skip` | `clock_6000_inc60` | 21.0 | 20.62 | 635,440 | 829,135 | 217.9 ms | 280.2 ms | 77.2 |
| `R1_skip` | `clock_2500_inc60` | 19.0 | 18.88 | 317,436 | 415,046 | 105.2 ms | 137.9 ms | 80.5 |
