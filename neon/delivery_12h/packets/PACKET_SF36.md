# Opus Placement Packet — `SF36_threat_quiet_move_ordering`

**Status:** **UNSCREENED / HOLD (DO NOT PLACE YET)** — Syntactically orthogonal (`git apply --check RC=0`, stacks cleanly with `V3P + SF34 + SF35 + (SF38 XOR SF39) + SF40`), quick Master Gates `hard_pass=true`, and `-15.91%` nodes under FULL 45-option Big Tune `bench 13`; however, **ZERO `fastchess` Elo matches** have been run (`run_cpu_wave2_queue.py` was stopped per `NEON_TO_OPUS.md:770`).

---

## 1. Live Artifact Inventory & Hashes

| Artifact | Path | Bytes | Lines | Live SHA-256 |
|---|---|---:|---:|---|
| Patch | `C:\nnue-lab\neon\forge_fixes\patches\SF36_threat_quiet_move_ordering.patch` | 1,075 | 19 | `7a07741e601136ee2fc0c5066e05a677516d4b901df5de93c02e883e748963d6` |
| Binary | `C:\nnue-lab\neon\forge_fixes\builds\SF36_threat_quiet_move_ordering.exe` | 2,382,336 | — | `43d36b70c1bcbcda5512d77c77d105ab7481989f2f46e1ad0d654693c662a759` |
| Gate JSON | `C:\nnue-lab\neon\forge_fixes\gate_SF36_threat_quiet_move_ordering.json` | 7,323 | 220 | `401c3623517a4a2d6c48fbe99c5d80a4372449a87873809fa7a84f0508b0fed6` |
| Target Source | `C:\nnue-lab\forge\r15dsg\src\search.cpp` | 167,417 | 3,426 | `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` |

Baseline `forge/r15dsg/src/search.cpp` matches `C:\nnue-lab\forge\r15dsg\SOURCE_INPUTS.sha256` line 28 byte-for-byte.

---

## 2. Verbatim Patch Diff (`19` lines, `1` hunk)

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -927,8 +927,15 @@
             int value = plain;
             if (rework) {
                 const Bitboard set = threats->by_type[pt];
-                const int twin = (*rework_side)[b4::square_bit(set, move.from)][b4::square_bit(set, move.to)][move.from][move.to];
+                const int from_t = b4::square_bit(set, move.from);
+                const int to_t = b4::square_bit(set, move.to);
+                const int twin = (*rework_side)[from_t][to_t][move.from][move.to];
                 value = b4::blend(plain, twin, quarters);
+                // SF36 (clean-room Stockfish/Stormphrax): zero-cost threat escape/entry move ordering bonus.
+                if (from_t != to_t) {
+                    static constexpr std::array<int, 7> kThreatBonus{0, 0, 2400, 2400, 4200, 6400, 0};
+                    value += (from_t - to_t) * kThreatBonus[pt];
+                }
             }
             if (cont1 != nullptr) value += (*cont1)[p][move.to];
             if (cont2 != nullptr) value += (*cont2)[p][move.to];
```

---

## 3. Target Methods, Baseline vs Patched Behavior & Flag Dependencies

- **Enclosing struct/method:** `MovePicker::QuietScorer::score(Move move, const std::array<Bitboard, 7>& check_squares) const` (`C:\nnue-lab\forge\r15dsg\src\search.cpp:922-942`, inside `class MovePicker` `683-1187`, guarded by `#if FORGE_SEARCH_SPEED2` at `888-944`).
- **Callers:** `MovePicker::generate_quiets` (`src/search.cpp:1055-1102`) and `MovePicker::generate_evasions` (`score_evasion` at `1140`).
- **Baseline (`src/search.cpp:928-932`):** When `rework` (`tune::HistRework != 0 && ss != nullptr`) is true, computes `b4::square_bit(set, move.from)` and `b4::square_bit(set, move.to)` solely as `[2][2]` indices into `rework_side` and blends `plain` and `twin` via `b4::blend(plain, twin, quarters)`. No direct piece-value bonus is added for escaping or penalty for entering a lesser-piece threat.
- **Patched (clean-room Stockfish `movepick.cpp` / Stormphrax):**
  - Captures the already-computed bitboard lookups in `from_t` and `to_t`.
  - When `from_t != to_t`, adds `(from_t - to_t) * kThreatBonus[pt]` with `kThreatBonus = {0, 0, 2400, 2400, 4200, 6400, 0}` (`Empty=0, Pawn=1, Knight=2, Bishop=3, Rook=4, Queen=5, King=6`, verified against `b4::lesser_threats` in `include/forge/b4.hpp:35-55`).
  - Escaping a lesser-piece threat (`from_t=1, to_t=0`) adds `+2400` (N/B), `+4200` (R), or `+6400` (Q); stepping into one (`from_t=0, to_t=1`) subtracts `-2400 / -4200 / -6400`. `b4::LesserThreats` leaves `by_type[Pawn]` and `by_type[King]` empty (`kThreatBonus[1]=0, kThreatBonus[6]=0`).
- **Build-flag & UCI option dependencies:**
  - Requires `FORGE_SEARCH_SPEED2=1` (enabled in `build_fast.py:29` and default in `search.hpp`) and `tune::HistRework != 0` (`2` in live Big Tune `pipeline/config.forge.toml:214`). If `HistRework == 0`, `SF36` is a complete no-op.

---

## 4. Gate & Benchmark Evidence (ZERO `fastchess` Elo Matches Run)

- **Quick Master Gates (`gate_SF36_threat_quiet_move_ordering.json`, `r0067/train/cand.fnn3`):**
  - `hard_pass = true` (`perft 5 = 4,865,609` `6/6`, `v3_parity 120/120` `0 cp`, `loader 13/13`).
  - `bench` (`r0067`): `default_bench_11 = 259,695`, `default_bench_13 = 725,158` (`3,059,738` NPS), `b4_bench_11 = 254,944`, `b4_bench_13 = 695,573` (`2,644,764` NPS).
- **Important Benchmark Basis Distinction (3-option B4 vs 45-option FULL Big Tune):**
  - `ROUND12_BUILD_REPORT.json` (`build_round12_search.py:180-196`, **3 B4 options**, `base = 503,542`): `SF36 = 817,101` (`+62.27%` nodes, `2,529,724` NPS).
  - `PACKET_ROUND12_SF34_SF36.md:24` & `test_round12_sf34_sf36.py:17-48` (**FULL 45-param Big Tune**, `base = 576,063`): `SF36 = 484,397` (**`-15.91%` nodes**), passing the `>= 10%` node-reduction fail-before/pass-after test (`cand rc=0`, `base rc=1`).
- **Elo Status:** **ZERO `fastchess` Elo matches** exist (`ALL_MATCHES_SCOREBOARD.md` / `matches/`). Queued `SF36_threat_quiet_move_ordering_600g_50k` (`seed=202611492`) in `run_cpu_wave2_queue.py:72-73` was stopped per `NEON_TO_OPUS.md:770`.

---

## 5. Overlap & Orthogonality Matrix (`round12_14_orthogonality.json`)

- **vs `V3P_pairwise_psqt_fused_v3.patch` (`sha256=57f3455f...`):** **100% file-disjoint** (`V3P` touches `nnue_v3.hpp`/`nnue_v3.cpp`; `SF36` touches `src/search.cpp`).
- **vs Round 12–14 & TM (`SF17/SF18`):**
  - `git -C C:\nnue-lab\forge\r15dsg apply --check`: `RC=0`.
  - Pairwise sequential `git apply` on isolated `forge/r15dsg` copies: `RC=0` in both orders with `V3P`, `SF34` (`min_line_gap=1558`), `SF35` (`min_line_gap=1138`), `SF38` (`min_line_gap=274`), `SF39` (`min_line_gap=274`), and `SF40` (`min_line_gap=274`).
  - Full combined stacks (`V3P -> SF34 -> SF35 -> SF36 -> (SF38|SF39) -> SF40`): **ALL `RC=0`**.
