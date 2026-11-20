#!/usr/bin/env python3
"""
Job 44 Part L (`run_partL.py`): IS THE BUNDLE ALIVE AT 2,000 NODES?
Runs the O set (UHO book lines 1..200) on `/tmp/carbon2_job44/bld_bundle9/forge` with `ucinewgame` + `isready`
before every search, `go nodes 2000`, `Threads=1`, `Hash=16`, `PC20`, built-in evaluation (`IdeaB8_Fast=false`
everywhere):
  (a) `all_off_a`                  -> `L_all_off_a_O_n2000.rows.txt`
  (b) `all_off_b`                  -> `L_all_off_b_O_n2000.rows.txt` (must equal (a) on 200 of 200)
  (c) `bundle_B8b_HindsightDepth`  -> `L_bundle_B8b_HindsightDepth_O_n2000.rows.txt`
  (d) `only_IdeaB8b`               -> `L_only_IdeaB8b_O_n2000.rows.txt`
  (e) `only_HindsightDepth`        -> `L_only_HindsightDepth_O_n2000.rows.txt`
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j44_lib import (  # noqa: E402
    ALL_TEN_FALSE,
    JOB44,
    NINE_SWITCH_NAMES,
    O_FENS_PATH,
    UHO_BOOK,
    WORK44,
    diff_breakdown_with_samples,
    fmt_cmp,
    load_fens,
    pc20_option_lines,
    sha256_file,
    utc_now,
)


def run_o_nodes2000(
    exe_path: str,
    setting_tag: str,
    extra_opts: list[tuple[str, str]],
    fens: list[str],
    cpu_pin: int = 1,
) -> tuple[list[tuple[int, int, str, str]], list[int]]:
    opt_lines = pc20_option_lines(extra_opts)
    proc = subprocess.Popen(
        ["taskset", "-c", str(cpu_pin), exe_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None

    proc.stdin.write("uci\n")
    proc.stdin.flush()
    id_name = "id name <unknown>"
    while True:
        ln = proc.stdout.readline().rstrip("\r\n")
        if ln.startswith("id name "):
            id_name = ln
        elif ln == "uciok":
            break

    proc.stdin.write("".join(o + "\n" for o in opt_lines) + "isready\n")
    proc.stdin.flush()
    while proc.stdout.readline().rstrip("\r\n") != "readyok":
        pass

    rows: list[tuple[int, int, str, str]] = []
    fin_depths: list[int] = []
    for idx, fen in enumerate(fens, start=1):
        proc.stdin.write("ucinewgame\nisready\n")
        proc.stdin.flush()
        while proc.stdout.readline().rstrip("\r\n") != "readyok":
            pass
        proc.stdin.write(f"position fen {fen}\nisready\n")
        proc.stdin.flush()
        while proc.stdout.readline().rstrip("\r\n") != "readyok":
            pass

        last_nodes: int | None = None
        last_score = ""
        last_depth = 0
        bestmove: str | None = None
        proc.stdin.write("go nodes 2000\n")
        proc.stdin.flush()
        while True:
            ln = proc.stdout.readline()
            if not ln:
                raise RuntimeError(f"EOF at pos {idx}")
            ln_s = ln.rstrip("\r\n")
            if ln_s.startswith("bestmove "):
                bestmove = ln_s.split()[1]
                break
            if ln_s.startswith("info ") and " nodes " in ln_s and " depth " in ln_s:
                toks = ln_s.split()
                last_depth = int(toks[toks.index("depth") + 1])
                last_nodes = int(toks[toks.index("nodes") + 1])
                if "score" in toks:
                    si = toks.index("score")
                    last_score = f"{toks[si + 1]} {toks[si + 2]}"
        assert last_nodes is not None and bestmove is not None
        rows.append((idx, last_nodes, bestmove, last_score))
        fin_depths.append(last_depth)

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    stderr_txt = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()
    assert rc == 0 and not stderr_txt, f"rc={rc} stderr={stderr_txt!r}"

    node_sum = sum(r[1] for r in rows)
    rows_path = JOB44 / f"L_{setting_tag}_O_n2000.rows.txt"
    meta_path = JOB44 / f"L_{setting_tag}_O_n2000.rows.txt.meta"
    hdr = [
        f"# set=first200.fens positions={len(rows)} go=nodes_2000 setting={setting_tag} sum_nodes={node_sum}",
        "position\tnodes\tbestmove\tscore",
    ]
    rows_path.write_text(
        "\n".join(hdr + [f"{p}\t{nd}\t{bm}\t{sc}" for p, nd, bm, sc in rows]) + "\n",
        encoding="utf-8",
    )
    meta_path.write_text(
        "\n".join(
            [
                f"exe_path: {exe_path}",
                f"exe_sha256: {sha256_file(pathlib.Path(exe_path))}",
                f"id_name: {id_name}",
                "set_name: first200.fens (UHO_Lichess_4852_v1.epd lines 1..200)",
                f"set_sha256: {sha256_file(O_FENS_PATH)}",
                f"positions: {len(rows)}",
                "go_command: go nodes 2000",
                f"sum_nodes: {node_sum}",
                f"mean_finished_depth: {sum(fin_depths) / len(fin_depths):.3f} (min={min(fin_depths)}, max={max(fin_depths)})",
                "per_search_reset: ucinewgame + isready",
                "options_sent_begin:",
                *[f"  {o}" for o in opt_lines],
                "options_sent_end",
                f"utc_completed: {utc_now()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return rows, fin_depths


def main() -> int:
    b9_exe = str(WORK44 / "bld_bundle9/forge")
    b9_sha = sha256_file(pathlib.Path(b9_exe))
    fens = load_fens(O_FENS_PATH)

    # Verify O_FENS_PATH == UHO_BOOK lines 1..200
    uho_first200: list[str] = []
    with open(UHO_BOOK, "r", encoding="utf-8") as bf:
        for _ in range(200):
            uho_first200.append(bf.readline().strip())
    ok_book, s_book = fmt_cmp("O set FENs == UHO_BOOK lines 1..200", sum(1 for a, b in zip(fens, uho_first200) if a == b), 200)

    bundle_opts = [(o, "true" if o == "IdeaB8b" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "true")]
    b8b_opts = [(o, "true" if o == "IdeaB8b" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "false")]
    hd_opts = ALL_TEN_FALSE[:-1] + [("HindsightDepth", "true")]

    specs = [
        ("a", "all_off_a", ALL_TEN_FALSE),
        ("b", "all_off_b", ALL_TEN_FALSE),
        ("c", "bundle_B8b_HindsightDepth", bundle_opts),
        ("d", "only_IdeaB8b", b8b_opts),
        ("e", "only_HindsightDepth", hd_opts),
    ]

    out_lines = [
        "=== JOB 44 PART L: IS THE BUNDLE ALIVE AT 2,000 NODES? (O Set, 200 FENs, go nodes 2000, PC20, Built-in Eval) ===",
        f"start_utc: {utc_now()}",
        f"exe_path: {b9_exe}",
        f"exe_sha256({b9_exe}): {b9_sha}",
        s_book,
        "",
    ]
    all_ok = ok_book

    results: dict[str, tuple[list[tuple[int, int, str, str]], list[int]]] = {}
    for code, tag, opts in specs:
        results[code] = run_o_nodes2000(b9_exe, tag, opts, fens, cpu_pin=1)

    rows_a, _ = results["a"]
    rows_b, _ = results["b"]
    d_ab, _ = diff_breakdown_with_samples(rows_b, rows_a, "all_off_b", "all_off_a")
    ok_det1, s_det1 = fmt_cmp("Part L (b) all_off_b equal positions vs (a) all_off_a", d_ab["equal"], 200)
    ok_det2, s_det2 = fmt_cmp("Part L (b) all_off_b node_sum vs (a) all_off_a", sum(r[1] for r in rows_b), sum(r[1] for r in rows_a))
    all_ok = all_ok and ok_det1 and ok_det2
    out_lines.extend([s_det1, s_det2, ""])

    out_lines.extend(
        [
            "--- Summary Table vs (a) all_off_a ---",
            "  code | setting                   | sum_nodes | mean_d | any_diff | node_diff | bestmove_diff | score_diff | equal_pos",
            "  -----+---------------------------+-----------+--------+----------+-----------+---------------+------------+----------",
        ]
    )
    sample_blocks: list[str] = []
    for code, tag, _ in specs:
        r_cur, fdepths = results[code]
        d_cur, samples = diff_breakdown_with_samples(r_cur, rows_a, tag, "all_off_a")
        out_lines.append(
            f"  ({code})  | {tag:<25s} | {sum(r[1] for r in r_cur):>9d} | {sum(fdepths)/len(fdepths):>6.2f} | "
            f"{d_cur['any']:>8d} | {d_cur['nodes']:>9d} | {d_cur['bestmove']:>13d} | {d_cur['score']:>10d} | {d_cur['equal']:>9d}"
        )
        if samples:
            sample_blocks.append(f"  [{tag} vs all_off_a]:")
            sample_blocks.extend(samples)

    out_lines.append("")
    out_lines.extend(sample_blocks)

    d_c, _ = diff_breakdown_with_samples(results["c"][0], rows_a, "bundle_c", "all_off_a")
    out_lines.append("")
    out_lines.append(f"  PREDICTION (1) CHECK: bundle (c) node_diff vs (a) = {d_c['nodes']} / 200 (predicted 194, range [175, 200] -> {'TRUE' if 175 <= d_c['nodes'] <= 200 else 'FALSE'})")
    out_lines.append(f"  M9 GATE: bundle (c) differs from (a) on {d_c['any']} / 200 positions -> PLAY PART M9 = {d_c['any'] > 0}")
    ok_ov, s_ov = fmt_cmp("PART L OVERALL", 1 if all_ok else 0, 1)
    out_lines.append(s_ov)
    out_lines.append(f"done_utc: {utc_now()}")

    (JOB44 / "partL_summary.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
