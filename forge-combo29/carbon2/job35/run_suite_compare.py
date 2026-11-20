#!/usr/bin/env python3
"""
Job 35 — Suite Runner & Side-by-Side Comparator for Part A (r15d Ref vs r15d+v2 Loop)
and Part C (kF+v2 Ref & Loop vs r15d Known Answers).
Every PASS/FAIL line prints both compared values side by side.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import pathlib
import sys

sys.dont_write_bytecode = True
JOB35 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job35")
sys.path.insert(0, str(JOB35))

from loop_driver import run_loop
from ref_driver import AttemptRow, RunResult, RunSettings, run_ref, write_attempt_rows

NET768 = "/tmp/carbon2_work/net768.fnn3"

SUITES: dict[str, tuple[str, int, RunSettings, dict]] = {
    "A": (
        "carbon2-job33-a",
        200,
        RunSettings(),
        {
            "full_sha256": "d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2",
            "first10_sha256": "a61127c24d896515dd9594ff759a3dc87b6a0506ab36f1b915ac912c0a7dacf6",
            "records": 26741,
            "moves_finished": 28298,
            "searches": 26867,
            "final_nodes": 107124743,
            "finished": 200,
            "thrown_away": 0,
        },
    ),
    "B": (
        "carbon2-job33-b",
        100,
        RunSettings(N=50),
        {
            "full_sha256": "f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c",
            "first10_sha256": "aa4b3b00a749f6bee067450ef05e7130b9e097c5d6c7daf62faa17e172657be1",
            "records": 3857,
            "moves_finished": 4183,
            "searches": 5554,
            "final_nodes": 509980,
            "finished": 41,
            "thrown_away": 59,
            "thrown_searches": 1661,
            "thrown_nodes": 157341,
            "pc_b_spots": {
                1: (25, 2094),
                2: (15, 1653),
                3: (4, 444),
                6: (13, 1329),
                7: (4, 453),
                9: (17, 1556),
            },
        },
    ),
    "C": (
        "carbon2-job33-c",
        100,
        RunSettings(N=300, E=400, M=120, P=20, S=30, C=3),
        {
            "full_sha256": "4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf",
            "first10_sha256": "b18af256d7a872200f6c095296502093849f825fdb8adbaa9d6f3c7c51e17510",
            "records": 2904,
            "moves_finished": 3661,
            "searches": 2960,
            "final_nodes": 1433776,
            "finished": 100,
            "thrown_away": 0,
        },
    ),
    "n": (
        "carbon2-job33-n",
        100,
        RunSettings(net_path=NET768),
        {
            "full_sha256": "2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204",
            "first10_sha256": "1c1f4a183ffb62754bf640ff26c56b82d5a40fb4b9a5debbc67a10cb74b626f6",
            "records": 13736,
            "moves_finished": 14519,
            "searches": 13801,
            "final_nodes": 59241899,
            "finished": 100,
            "thrown_away": 0,
        },
    ),
}


def fmt_cmp(label: str, got: object, exp: object) -> tuple[bool, str]:
    ok = got == exp
    st = "PASS" if ok else "FAIL"
    op = "==" if ok else "!="
    return ok, f"  {label:<44s}: {st} ({got} {op} {exp})"


def find_first_record_diff(a_bytes: bytes, b_bytes: bytes) -> str:
    a_recs = [x for x in a_bytes.decode("ascii").split("e\n") if x]
    b_recs = [x for x in b_bytes.decode("ascii").split("e\n") if x]
    for idx, (ra, rb) in enumerate(zip(a_recs, b_recs), start=1):
        if ra != rb:
            return f"record #{idx} differs:\n    got={ra!r}\n    exp={rb!r}"
    return f"record count differs: got={len(a_recs)} vs exp={len(b_recs)}"


def _worker_task(kind: str, exe: str, set_name: str, rec_path: str) -> tuple[str, str, RunResult]:
    seed, attempts, settings, _ = SUITES[set_name]
    rp = pathlib.Path(rec_path)
    if kind == "Ref":
        res = run_ref(exe, seed, attempts, settings, out_records_path=rp)
    else:
        res = run_loop(exe, seed, attempts, settings, out_records_path=rp)
    return kind, set_name, res


def compare_pair(
    prefix: str,
    set_name: str,
    ref_res: RunResult,
    loop_res: RunResult,
    ref_rec_file: pathlib.Path,
    loop_rec_file: pathlib.Path,
    r15d_ref_rec_file: pathlib.Path | None = None,
) -> tuple[bool, list[str]]:
    seed, attempts, _, ka = SUITES[set_name]
    lines: list[str] = [f"--- Set {set_name} (seed={seed}, attempts={attempts}) ---"]
    all_ok = True

    for label, got, exp in [
        (f"Ref full_sha256 vs KA({set_name})", ref_res.full_sha256, ka["full_sha256"]),
        (f"Loop full_sha256 vs KA({set_name})", loop_res.full_sha256, ka["full_sha256"]),
        ("Loop full_sha256 vs Ref full_sha256", loop_res.full_sha256, ref_res.full_sha256),
        ("Loop first10_sha256 vs Ref first10_sha256", loop_res.first10_sha256, ref_res.first10_sha256),
        (f"Ref searches vs KA({set_name})", ref_res.searches, ka["searches"]),
        ("Loop searches vs Ref searches", loop_res.searches, ref_res.searches),
        (f"Ref nodes vs KA({set_name})", ref_res.final_nodes, ka["final_nodes"]),
        ("Loop nodes vs Ref nodes", loop_res.final_nodes, ref_res.final_nodes),
        ("Loop records vs Ref records", loop_res.records, ref_res.records),
        ("Loop moves_finished vs Ref moves_finished", loop_res.moves_finished, ref_res.moves_finished),
        ("Loop finished vs Ref finished", loop_res.finished, ref_res.finished),
        ("Loop thrown_away vs Ref thrown_away", loop_res.thrown_away, ref_res.thrown_away),
    ]:
        ok, s = fmt_cmp(label, got, exp)
        all_ok = all_ok and ok
        lines.append(s)

    ref_bytes = ref_rec_file.read_bytes()
    loop_bytes = loop_rec_file.read_bytes()
    ok_b, sb = fmt_cmp("Loop record bytes == Ref record bytes", len(loop_bytes) if loop_bytes == ref_bytes else -1, len(ref_bytes))
    all_ok = all_ok and ok_b
    lines.append(sb)
    if loop_bytes != ref_bytes:
        lines.append("  FIRST RECORD DIFF (Loop vs Ref): " + find_first_record_diff(loop_bytes, ref_bytes))
    if r15d_ref_rec_file is not None and r15d_ref_rec_file.exists():
        base_bytes = r15d_ref_rec_file.read_bytes()
        if ref_bytes != base_bytes:
            lines.append("  FIRST RECORD DIFF (Ref vs r15d): " + find_first_record_diff(ref_bytes, base_bytes))
        if loop_bytes != base_bytes:
            lines.append("  FIRST RECORD DIFF (Loop vs r15d): " + find_first_record_diff(loop_bytes, base_bytes))

    # Per-attempt row comparison across ALL attempts (finished AND thrown)
    eq_all = 0
    first_row_diff = ""
    for rr, lr in zip(ref_res.rows, loop_res.rows):
        if rr == lr:
            eq_all += 1
        elif not first_row_diff:
            first_row_diff = f"attempt {rr.attempt}: Loop={lr} != Ref={rr}"
    ok_rows, s_rows = fmt_cmp("All attempts exact row match (Loop vs Ref)", eq_all, attempts)
    all_ok = all_ok and ok_rows
    lines.append(s_rows)
    if first_row_diff:
        lines.append(f"  FIRST ROW DIFF: {first_row_diff}")

    if set_name == "B":
        ref_thrown = [r for r in ref_res.rows if not r.finished]
        loop_thrown = [r for r in loop_res.rows if not r.finished]
        eq_thrown = sum(1 for rr, lr in zip(ref_thrown, loop_thrown) if rr == lr and len(ref_thrown) == len(loop_thrown))
        ok_th, s_th = fmt_cmp("B thrown attempts equal (Loop vs Ref)", eq_thrown, 59)
        all_ok = all_ok and ok_th
        lines.append(s_th)

        ref_th_s = sum(r.searches for r in ref_thrown)
        loop_th_s = sum(r.searches for r in loop_thrown)
        ref_th_n = sum(r.nodes for r in ref_thrown)
        loop_th_n = sum(r.nodes for r in loop_thrown)
        for label, got, exp in [
            ("B 59 thrown searches (Ref vs PC KA)", ref_th_s, ka["thrown_searches"]),
            ("B 59 thrown searches (Loop vs Ref)", loop_th_s, ref_th_s),
            ("B 59 thrown nodes (Ref vs PC KA)", ref_th_n, ka["thrown_nodes"]),
            ("B 59 thrown nodes (Loop vs Ref)", loop_th_n, ref_th_n),
        ]:
            ok, s = fmt_cmp(label, got, exp)
            all_ok = all_ok and ok
            lines.append(s)

        ref_by_att: dict[int, AttemptRow] = {r.attempt: r for r in ref_res.rows}
        loop_by_att: dict[int, AttemptRow] = {r.attempt: r for r in loop_res.rows}
        for att_i, exp_pair in ka["pc_b_spots"].items():
            rr = ref_by_att[att_i]
            lr = loop_by_att[att_i]
            ok1, s1 = fmt_cmp(f"B attempt {att_i} Ref (searches,nodes) vs PC", (rr.searches, rr.nodes), exp_pair)
            ok2, s2 = fmt_cmp(f"B attempt {att_i} Loop (searches,nodes) vs Ref", (lr.searches, lr.nodes), (rr.searches, rr.nodes))
            all_ok = all_ok and ok1 and ok2
            lines.append(s1)
            lines.append(s2)

    lines.append(
        f"  timing_info (unblocked): Ref wall={ref_res.wall_s:.3f}s (drv={ref_res.driver_cpu_s:.3f}s, eng={ref_res.engine_cpu_s:.3f}s) | "
        f"Loop wall={loop_res.wall_s:.3f}s (drv={loop_res.driver_cpu_s:.3f}s, eng={loop_res.engine_cpu_s:.3f}s)"
    )
    return all_ok, lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True, help="e.g. partA or partC")
    ap.add_argument("--ref-exe", required=True)
    ap.add_argument("--loop-exe", required=True)
    ap.add_argument("--summary-out", type=pathlib.Path, required=True)
    ap.add_argument("--tmp-dir", type=pathlib.Path, default=pathlib.Path("/tmp/carbon2_job35"))
    ap.add_argument("--r15d-rec-dir", type=pathlib.Path, default=None)
    args = ap.parse_args()

    args.tmp_dir.mkdir(parents=True, exist_ok=True)
    tasks = []
    for set_name in ("A", "B", "C", "n"):
        tasks.append(("Ref", args.ref_exe, set_name, str(args.tmp_dir / f"{args.prefix}_ref_{set_name}.txt")))
        tasks.append(("Loop", args.loop_exe, set_name, str(args.tmp_dir / f"{args.prefix}_loop_{set_name}.txt")))

    results: dict[tuple[str, str], RunResult] = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(_worker_task, *t) for t in tasks]
        for f in concurrent.futures.as_completed(futs):
            kind, set_name, res = f.result()
            results[(kind, set_name)] = res
            row_path = JOB35 / f"{args.prefix}_{kind}_{set_name}_rows.txt"
            write_attempt_rows(row_path, f"{args.prefix} {kind} Set {set_name}", res)
            print(f"Completed {args.prefix} {kind} Set {set_name}: sha256={res.full_sha256[:16]}... searches={res.searches} nodes={res.final_nodes}", flush=True)

    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    out_lines = [
        f"UTC: {utc}",
        f"=== JOB 35 {args.prefix.upper()} — Ref vs Loop Comparison Across Sets A, B, C, n ===",
        f"Ref exe:  {args.ref_exe}",
        f"Loop exe: {args.loop_exe}",
        "",
    ]
    overall_ok = True
    for set_name in ("A", "B", "C", "n"):
        r15d_rec = (args.r15d_rec_dir / f"partA_ref_{set_name}.txt") if args.r15d_rec_dir else None
        ok, blk = compare_pair(
            args.prefix,
            set_name,
            results[("Ref", set_name)],
            results[("Loop", set_name)],
            args.tmp_dir / f"{args.prefix}_ref_{set_name}.txt",
            args.tmp_dir / f"{args.prefix}_loop_{set_name}.txt",
            r15d_ref_rec_file=r15d_rec,
        )
        overall_ok = overall_ok and ok
        out_lines.extend(blk)
        out_lines.append("")

    out_lines.append(f"{args.prefix.upper()} OVERALL: {'PASS' if overall_ok else 'NOT MET / DIFFERENCE'} (sets_equal: {int(overall_ok)*4 if overall_ok else 'see above'} == 4)")
    txt = "\n".join(out_lines) + "\n"
    args.summary_out.write_text(txt)
    print("\n" + txt, flush=True)


if __name__ == "__main__":
    main()
