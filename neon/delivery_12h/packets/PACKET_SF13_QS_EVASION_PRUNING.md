# Opus Placement Packet: `SF13_qs_evasion_pruning.patch` (Quiescence Losing-Evasion Pruning)

> **Status:** **SCREEN PASSED (`+20.87 [+4.86, +36.97] Elo`, `LOS = 99.47%`, `600g @ 50k`)** — awaiting independent unbiased `1,000g @ 50k` confirmation (`SF13_confirm_vs_base_1000g_50k`, fresh seed `202611499`, never pooled per R5) + equal-time confirmation before placement!
> **Patch:** `C:\nnue-lab\neon\forge_fixes\patches\SF13_qs_evasion_pruning.patch` (`28` lines, `git -C C:\nnue-lab\forge\r15dsg apply --check RC=0`, SHA-256 `63eb3288af4712a7d641035177e561448e6fc94041d8ee916776ab3fced6b6e4`)
> **Target File:** `src/search.cpp` (`Worker::qsearch`, 5 net lines added)
> **Clean-Room Provenance:** Clean-room re-implementation of **Stockfish's `qsearch` SEE pruning of check evasions once `bestValue` is not a loss** (`best_score > -MateInMaxPly`), written from scratch on Forge's `Worker::qsearch` + `board.see_ge(move, 0)`. More cautious than Stockfish on move filtering (`move_count > 2`, `!is_capture()`, `!is_promotion()`, `!gives_check()`, `!see_ge(move, 0)`).
> **Difference vs Stockfish (Disclosed per Opus Review `OPUS-2711-READINGS-ON-2100`):** Stockfish also requires `non_pawn_material(us)` (skipping this prune in pure pawn endings), whereas `SF13` does not check `has_non_pawn_material(us)` (low risk because `move_count > 2`, `best_score > -MateInMaxPly`, and `!gives_check` already guard pawn-ending evasions, and king evasions rarely fail `SEE >= 0`).
> **Opus Code Review Verdict (`21:01 PC`):** `YES WITH REMARKS` (`PLAN-2711-OPUS-SF13-FIRST-READ`). Playing strength remains candidate-only until independent fresh-seed `1,000g @ 50k` confirmation (`SF13_confirm_vs_base_1000g_50k`) decides!

---

## 1. Exact Mechanism & Safety Proof

In `forge/r15dsg/src/search.cpp` (`Worker::qsearch`), the pruning guard previously skipped the entire block whenever `in_check == true`, forcing quiescence search to expand every single legal check evasion (even quiet interpositions that immediately lose material on the landing square).

`SF13_qs_evasion_pruning.patch` adds a single `else if` branch inside `if (mate_moves_ == 0 && best_score > -MateInMaxPly)`:
```cpp
} else if (move_count > 2 && !move.is_capture() && !move.is_promotion() && !board.gives_check(move) &&
           !board.see_ge(move, 0)) {
    continue;
}
```

### Invariants Verified
1. **Zero false checkmate/stalemate:** Requires `move_count > 2` (at least 2 legal evasions already searched) AND `best_score > -MateInMaxPly` (a non-mated escape is already proven).
2. **Zero mate-finder interference:** Guarded by `mate_moves_ == 0`.
3. **Never prunes tactical/checking evasions:** Captures, promotions, counter-checks, and all `SEE >= 0` quiet evasions (including king moves that don't lose material) are always searched.
4. **Master Gates (`SF13_qs_evasion_pruning_gate.json`):** `perft 5 = 4,865,609`, `v3_parity = 0 cp`, `hard_pass = True`.

---

## 2. Empirical Evidence (Strict Non-Pooled R5 Accounting)

- **600g @ 50k Screen (`SF13_qs_evasion_pruning_600g_50k`):**
  - `W–D–L = 169–298–133` (`53.00%`), **`+20.87 [+4.86, +36.97] Elo`**, `z = +2.556`, **`LOS = 99.47%`**, `ptnml = [5, 60, 137, 90, 8]`, `0` TL/IL.
- **Independent 1,000g @ 50k Confirmation (`SF13_confirm_vs_base_1000g_50k`, seed `202611499`):** Queued #1 in `run_cpu_wave2_queue.py` (never pooled with the 600g screen!).
- **Stacked Compatibility:** Verified `git -C C:\nnue-lab\forge\r15dsg apply --check RC=0` standalone and orthogonal to `V3P_pairwise_psqt_fused_v3.patch`, `SF8_conthist_6ply.patch`, `SF20_killer_lmr_relief.patch`, and `LmrDeeperShallower=true`.

---

## 3. Fail-Before / Pass-After Verification Command
```powershell
# Passes on SF13 target exe (RC=0):
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\SF13_qs_evasion_pruning.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\test_sf13_qs_evasion_pruning.py

# Fails on baseline r15dsg exe (RC=1, proves test actually catches the change):
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\test_sf13_qs_evasion_pruning.py
```
