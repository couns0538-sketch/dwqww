# Patch Note & Placement Declaration: `SF4b1_v3_endgame_scale.patch`

## 1. Summary & Source Citation (Owner 19:02 PC Stockfish-Style Rule)
- **Patch file:** `C:\nnue-lab\neon\forge_fixes\patches\SF4b1_v3_endgame_scale.patch` (`61` lines; sha256 `acf5062fae7d...`)
- **Purpose:** Stand-alone FORGENN3 (`v3`) nets bypass `Evaluator::evaluate()`, losing drawish endgame scaling (`scale_factor` in `src/eval.cpp`). This patch adds `scale_v3_eval(board, stm_eval)` called on the return of `Worker::static_evaluate_v3()` for:
  1. Pawnless stronger-side endings with `strong_np - weak_np <= Bishop`: returns `0` when `strong_np < Rook` (dead draws such as `KB-K`, `KN-K`, `KB-KN`, `KB-KB`, `KN-KN`, `KN-KP` for the knight side) and scales by `12 / 64` when `strong_np >= Rook` (e.g., `KRB-KR`, `KRN-KR` fortresses).
  2. Opposite-coloured bishops damping (`min(64, 32 + 4 * strong_pawns) / 64` for pure OCB; `min(64, 48 + 2 * strong_pawns) / 64` with other pieces).
- **Primary Source & License Compliance:** Re-implemented cleanly in Forge from classic Stockfish endgame scale-factor logic (`Stockfish` classic `src/material.cpp` & `src/evaluate.cpp` `scale_factor()`, and Forge's own existing `src/eval.cpp` HCE endgame scaling); NOT copied verbatim.

## 2. Responses to Opus Second-Reading Remarks (`OPUS-2711-SF4B1-SECOND-READ-YES-WITH-REMARKS`, 19:03 PC)
- **R1 (12/64 vs 4/64 or 14/64):** Uniform `12/64` kept for simplicity and minimal branching; source cited above.
- **R2 (`KNN-K`):** Intentionally left to the NNUE weights via `anchors/dead_draws_20k.fqs.z` (`20,000/20,000` Syzygy `wdl == 0`) so raw `net_sanity` `S5` passes inside the net itself.
- **R3 (stronger side's pawns only):** Matches classic Stockfish & Forge HCE.
- **R4 (feeds TT, correction history, self-play labels; raw `uci eval` unchanged):** Verified (`v3_parity` `200/200` `0 differ`).

## 3. Verified Gates (Recounted by Opus `gates_exe.py` & Teamwork Stream 1)
- `perft 5`: `4865609` (identical to live `forge.exe` and `base_r15dsg.exe`)
- Built-in net `bench 11 / 13`: `312866 / 862329` (identical to live `forge.exe` and `base_r15dsg.exe`)
- `r0067 + B4/BigTune` `bench 11 / 13`: `176165 / 656345` (vs base `187930 / 632195`)
- Standalone failing-on-old / passing-on-new test: `neon/forge_fixes/teamwork_trial/test_sf4b.py` (`EXIT=0`)
- Initial 600g @ 50k screen: `+15.06 Elo [-0.35, +30.54]` (`154-128-318`, `z = +1.915`, `LOS = 97.2%`)

## 4. Formal Placement Declaration (Declared Before First Game)
1. **Fixed-Node Proof:** `fastchess` SPRT `elo0 = 0`, `elo1 = 5`, `alpha = 0.05`, `beta = 0.05`, `model = normalized`, `nodes = 50000`, `max_games = 4000`, `UHO_Lichess_4852_v1.epd`, `r0067` + live `v3_uci_options` on both sides (`SF4b1_v3_endgame_scale.exe` vs `base_r15dsg.exe`).
2. **Equal-Time Clock Check (GPU IDLE, `neon/CLOCK_MATCH_RUNNING` set):** `fastchess` `400` games at `10+0.1` (`concurrency = 8`, `timemargin = 100`), `SF4b1_v3_endgame_scale.exe` vs `base_r15dsg.exe`; acceptance requires 95% lower Elo bound `> -10` and `0` time losses.
