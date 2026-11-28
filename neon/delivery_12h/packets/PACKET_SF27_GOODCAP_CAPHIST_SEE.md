# Opus Placement Packet: `SF27_goodcap_caphist_see_threshold` (Capture-History GoodCaptures SEE Threshold)

> **Status:** Built, Master-Gated (`hard_pass=True`, `git apply --check RC=0`, `B4 bench 13 +7.0%`), queued for 600g @ 50k screen (`SF27_goodcap_caphist_see_threshold_600g_50k`).
> **Patch:** `C:\nnue-lab\neon\forge_fixes\patches\SF27_goodcap_caphist_see_threshold.patch` (`51` lines)
> **Target File:** `src/search.cpp` (`MovePicker::GoodCaptures` + `move_score_threshold`)
> **Source Citation:** Clean-room re-implementation of Stockfish `src/movepick.cpp` GoodCaptures capture-history-adjusted SEE threshold, replacing Forge's existing placeholder stub `move_score_threshold(Move) { return 0; }` (`search.cpp:946`), zero verbatim GPL code copied.

---

## 1. Exact Mechanism & Soundness Proof
- Replaces `static int move_score_threshold(Move) { return 0; }` with:
  ```cpp
  int move_score_threshold(Move move) const {
      if (!move.is_capture()) return 0;
      const int cap_h = searcher_.capture_history_value(board_, move);
      return std::clamp(cap_h / 128, -40, 80);
  }
  ```
- `see_thr = -move_score_threshold(move)` lies in `[-80, +40]`: captures with strong positive capture history are allowed into `GoodCaptures` even at slight negative SEE (e.g. tactical sacrifices up to `-80` cp), while captures with poor capture history require `SEE >= +40` cp.
- **Downstream Soundness (`last_move_see_nonnegative()`):** Tracks explicit `bool last_see_nonneg_ = (see_thr >= 0);` and returns `stage_ == GoodCaptures && last_see_nonneg_;` so downstream check extensions (`search.cpp:2370`) and SEE pruning (`search.cpp:2318`) NEVER falsely assume `SEE >= 0` when `see_thr < 0`!

## 2. Verification & Gates
- `git -C C:\nnue-lab\forge\r15dsg apply --check C:\nnue-lab\neon\forge_fixes\patches\SF27_goodcap_caphist_see_threshold.patch` -> `RC=0`.
- `builds/SF27_goodcap_caphist_see_threshold_gate.json`: `hard_pass = True`, `perft 5 = 4,865,609`.
- Fail-before / pass-after test: `C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\test_sf15_and_sf27.py --only sf27`.
- Playing strength decided strictly by declared `fastchess` matches.
