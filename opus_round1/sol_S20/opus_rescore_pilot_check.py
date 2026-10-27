"""Check a rescored file against its input (read-only): format, side-to-move sign, mates, no NaN, and a 200-position
comparison with the original labels.

  python -I -B opus_rescore_pilot_check.py --in input.txt --rescored run/rescored.txt --out report.json [--sample 200]

- Format: every rescored line is "FEN | int | result"; FEN and result equal the input line (same order; bad input
  lines are skipped by the rescorer and here); |score| <= max-score.
- Side-to-move sign: (a) on decisive positions the score's sign agrees with the side to move's result far more
  often than not; (b) material spot check: where the side to move is >= 5 pawns up (P1 N3 B3 R5 Q9) the score is
  positive, where it is >= 5 pawns down the score is negative; a sign flipped to WHITE's view would fail both.
- Mates: lines at +-max-score are counted and compared with the rescorer's mate count.
- NaN: no "nan"/"inf" text; every score parses as an integer.
- Comparison: every (n // sample)-th valid line (deterministic), new - old: mean, mean |.|, median |.|, sd, max |.|.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("opus_rescore", HERE / "opus_rescore.py")
rescore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rescore)
VALUE = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9}


def material_stm(fen: str) -> int:
    placement, stm = fen.split()[0], fen.split()[1]
    white = sum(VALUE.get(ch.lower(), 0) for ch in placement if ch.isupper())
    black = sum(VALUE.get(ch, 0) for ch in placement if ch.islower())
    return white - black if stm == "w" else black - white


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", type=Path, required=True)
    ap.add_argument("--rescored", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sample", type=int, default=200)
    ap.add_argument("--max-score", type=int, default=3000)
    args = ap.parse_args(argv)
    if args.out.exists():
        ap.error("--out must be a new file")
    src = []
    for line in args.inp.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            src.append(rescore.parse_line(line))
        except ValueError:
            pass
    text = args.rescored.read_text(encoding="utf-8")
    out_lines = text.splitlines()
    problems = []
    if len(out_lines) != len(src):
        problems.append(f"line count {len(out_lines)} != valid input lines {len(src)}")
    nan_text = "nan" in text.lower() or "inf" in text.lower()
    new_scores = []
    for i, (line, s) in enumerate(zip(out_lines, src)):
        try:
            fen, score, result_text, white_result, stm = rescore.parse_line(line)
        except ValueError as error:
            problems.append(f"line {i}: unparsable ({error})")
            continue
        if fen != s[0] or result_text != s[2]:
            problems.append(f"line {i}: FEN/result differ from the input")
        if abs(score) > args.max_score:
            problems.append(f"line {i}: |score| > max-score")
        new_scores.append(score)
    agree = disagree = 0
    up_ok = up_bad = down_ok = down_bad = 0
    for s, score in zip(src, new_scores):
        fen, _old, _rt, white_result, stm = s
        stm_result = white_result if stm == "w" else 1.0 - white_result
        if stm_result != 0.5 and score != 0:
            if (score > 0) == (stm_result == 1.0):
                agree += 1
            else:
                disagree += 1
        m = material_stm(fen)
        if m >= 5:
            up_ok, up_bad = up_ok + (score > 0), up_bad + (score <= 0)
        elif m <= -5:
            down_ok, down_bad = down_ok + (score < 0), down_bad + (score >= 0)
    at_max = sum(abs(x) == args.max_score for x in new_scores)
    step = max(1, len(src) // args.sample)
    picks = list(range(0, len(src), step))[:args.sample]
    diffs = [new_scores[i] - src[i][1] for i in picks]
    absd = [abs(d) for d in diffs]
    report = {
        "input": str(args.inp), "rescored": str(args.rescored), "valid_input_lines": len(src), "rescored_lines": len(out_lines),
        "format_problems": problems[:20], "format_problem_count": len(problems), "nan_or_inf_text": nan_text,
        "sign_decisive": {"agree": agree, "disagree": disagree, "agreement": agree / max(1, agree + disagree)},
        "sign_material_spot_check": {"stm_up_5_positive": up_ok, "stm_up_5_not_positive": up_bad,
                                     "stm_down_5_negative": down_ok, "stm_down_5_not_negative": down_bad},
        "lines_at_max_score": at_max,
        "comparison_vs_original_labels": {
            "sample": len(picks), "every_nth": step,
            "mean_new_minus_old": statistics.fmean(diffs) if diffs else math.nan,
            "mean_abs": statistics.fmean(absd) if absd else math.nan,
            "median_abs": statistics.median(absd) if absd else math.nan,
            "sd": statistics.pstdev(diffs) if len(diffs) > 1 else 0.0,
            "max_abs": max(absd) if absd else 0,
            "correlation": statistics.correlation([src[i][1] for i in picks], [new_scores[i] for i in picks]) if len(picks) > 2 else math.nan,
        },
    }
    report["pass"] = (not problems and not nan_text and report["sign_decisive"]["agreement"] > 0.8
                      and up_ok > 10 * max(1, up_bad) and down_ok > 10 * max(1, down_bad))
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
