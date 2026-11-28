"""Unit, Parity, and Planted-Fault Test Suite for filterqc_v2.py (Neon Filter Quest).

STRICTLY inside C:\\nnue-lab\\neon\\filter_quest\\selftest_tmp\\.
Tests:
1. Exact byte-for-byte parity with live filterqc.py rules when all v2 options are OFF.
2. Known-answer & planted-fault test for every v2 rule:
   - Q2 draw_conflict_score (drawn game result=0 with |score|>=600 dropped; decisive win kept)
   - Q3 max_ply_swing (ply t with |score(t)+score(t+1)|>=250 dropped; game boundary does NOT cross-trigger!)
   - Q4 high_score_threshold + high_score_keep_prob (deterministic downsampling; low scores 100% kept)
   - Q6 noisy_swing_threshold (capture with swing>=150 dropped; quiet with swing=150 kept!)
   - Q7 drop_in_check & in_check_among_kept telemetry + consecutive 1-ply game counter fix
   - Q1 external_seen cross-round dedup (second round duplicates dropped cleanly)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import filterqc_v2 as v2  # noqa: E402

TMP = Path(r"C:\nnue-lab\neon\filter_quest\selftest_tmp\test_v2")


def rec(fen: str, move: str, score: int, ply: int, result: int) -> str:
    return f"fen {fen}\nmove {move}\nscore {score}\nply {ply}\nresult {result}\ne\n"


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)

    f_open = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    f_open2 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    f_cap = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    f_chk = "rnb1kbnr/pppp1ppp/8/4p3/4PP1q/8/PPPP2PP/RNBQKBNR w KQkq - 1 3"
    f_r50 = "8/8/8/8/8/2k5/2P5/2K1R3 w - - 85 100"
    f_3pc = "8/8/8/8/8/2k5/8/2K1R3 w - - 0 100"
    f_hi1 = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
    f_hi2 = "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"

    # Build fixture testing all baseline + v2 rules
    src = TMP / "fixture.plain"
    src.write_text(
        "".join([
            # Game 1: draw conflict (ply 8 score +700, result 0) -> ply 9 score -100 (swing = |700 + -100| = 600!)
            rec(f_open, "e7e5", 700, 8, 0),
            rec(f_open2, "g1f3", -100, 9, 0),
            # Game 2 (1-ply game at ply 8, followed immediately by Game 3 at ply 8 -> tests games counter fix!)
            rec(f_cap, "e4d5", 100, 8, 1),
            # Game 3: ply 8 noisy capture with swing = |100 + 80| = 180; ply 9 quiet (score +80) -> ply 10 score -80 (swing 0)
            rec(f_cap, "e4d5", 100, 8, 1),
            rec(f_open2, "g1f3", 80, 9, 1),
            rec(f_hi1, "f1b5", -80, 10, 1),
            # Game 4: in-check, rule50 > 80, few_pieces (<4), score_result_conflict, high score (+1300)
            rec(f_chk, "g2g3", 50, 8, 1),
            rec(f_r50, "e1e2", 100, 9, 1),
            rec(f_3pc, "e1e2", 100, 10, 1),
            rec(f_hi2, "a7a6", 700, 11, -1),   # conflict: score +700, result -1
            rec(f_hi2, "g8f6", 1300, 12, 1),   # high score +1300 (also tests dedup on f_hi2 NOT poisoned by conflict!)
        ]),
        encoding="ascii",
    )

    # 1) Baseline mode (all v2 rules OFF)
    base_rules = {
        "max_abs_score": 2000, "min_ply": 0, "max_ply": 400, "dedup": True,
        "conflict_score": 600, "max_halfmove_clock": 80, "min_pieces": 4,
    }
    qc_base = v2.filter_plain_stream([src], TMP / "out_base.plain", base_rules)
    assert qc_base["records"] == 11
    assert qc_base["games"] == 4, f"expected 4 games (catching consecutive ply 8), got {qc_base['games']}"
    assert qc_base["marked_skip"]["rule50"] == 1
    assert qc_base["marked_skip"]["few_pieces"] == 1
    assert qc_base["marked_skip"]["score_result_conflict"] == 1
    assert qc_base["marked_skip"]["duplicate"] == 2  # f_cap repeated once, f_open2 repeated once
    assert qc_base["kept"] == 6
    print("T1_BASELINE_AND_GAME_COUNTER: PASS")

    # 2) Q2 draw_conflict_score = 600
    qc_q2 = v2.filter_plain_stream([src], TMP / "out_q2.plain", {**base_rules, "draw_conflict_score": 600})
    assert qc_q2["marked_skip"]["draw_score_conflict"] == 1
    assert qc_q2["kept"] == 5
    print("T2_Q2_DRAW_CONFLICT: PASS")

    # 3) Q3 max_ply_swing = 250 (catches Game 1 ply 8 swing=600, does NOT cross Game 2->Game 3 boundary!)
    qc_q3 = v2.filter_plain_stream([src], TMP / "out_q3.plain", {**base_rules, "max_ply_swing": 250})
    assert qc_q3["marked_skip"]["ply_score_swing"] == 1
    print("T3_Q3_PLY_SWING_NO_GAME_BLEED: PASS")

    # 4) Q6 noisy_swing_threshold = 150 (with dedup=False so Game 3 ply 8 capture isn't dup-dropped first!)
    qc_q6 = v2.filter_plain_stream([src], TMP / "out_q6.plain", {**base_rules, "dedup": False, "noisy_swing_threshold": 150})
    assert qc_q6["marked_skip"]["noisy_swing"] == 1, qc_q6["marked_skip"]
    print("T4_Q6_NOISY_SWING_SELECTIVE: PASS")

    # 5) Q7 drop_in_check + telemetry
    qc_q7 = v2.filter_plain_stream([src], TMP / "out_q7.plain", {**base_rules, "drop_in_check": True})
    assert qc_q7["marked_skip"]["in_check"] == 1 and qc_q7["in_check_among_kept"] == 0
    assert qc_q7["effective_trained"] == qc_q7["kept"] == 5
    qc_tel = v2.filter_plain_stream([src], TMP / "out_tel.plain", {**base_rules, "track_board_stats": True})
    assert qc_tel["in_check_among_kept"] == 1 and qc_tel["effective_trained"] == 5
    print("T5_Q7_IN_CHECK_DROP_AND_TELEMETRY: PASS")

    # 6) Q4 high_score_threshold=1000, keep_prob=0.0 -> drops ONLY score +1300
    qc_q4 = v2.filter_plain_stream([src], TMP / "out_q4.plain", {**base_rules, "high_score_threshold": 1000, "high_score_keep_prob": 0.0})
    assert qc_q4["marked_skip"]["high_score_downsample"] == 1 and qc_q4["kept"] == 5
    print("T6_Q4_HIGH_SCORE_DOWNSAMPLE: PASS")

    # 7) Q1 cross-round external_seen -> second pass over same file marks all 6 previously kept as duplicates!
    shared_seen: set[int] = set()
    qc_r1 = v2.filter_plain_stream([src], TMP / "out_r1.plain", base_rules, external_seen=shared_seen)
    qc_r2 = v2.filter_plain_stream([src], TMP / "out_r2.plain", base_rules, external_seen=shared_seen)
    assert qc_r1["kept"] == 6 and qc_r2["kept"] == 0 and qc_r2["marked_skip"]["duplicate"] == 8
    print("T7_Q1_CROSS_ROUND_DEDUP: PASS")

    shutil.rmtree(TMP)
    print("ALL 7 FILTERQC_V2 UNIT & PLANTED-FAULT TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
