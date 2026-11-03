#!/usr/bin/env python3
"""test_helpers.py - Opus R14-B item 2: exit-code tests of the helpers around relabel2.py with broken input (bug hunts
#14 / #15, own code, stdlib only): sort_normalized.py, label_stats.py, probe_bench.py (requests / run / compare /
abba), fn_diff.py, and measure_rates.sh / bridge_check.sh / prove_resume.sh with wrong arguments (through bash).

usage: python -I -B test_helpers.py SCRATCH_DIR      (SCRATCH_DIR must not exist)
Every case runs in its own new folder with tiny own fixtures; no probe or engine is started (probe_bench `run` is only
called where it must refuse before starting anything, and `abba` is driven with a stand-in run_probe). Checks per case:
the exit code, no Python traceback, which files the case left behind (nothing on a refusal) and that existing files
were not changed. One PASS / FAIL line per case; exit 0 = all PASS.
"""

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
BASH = shutil.which("bash")  # Git's bash on this PC (for the shell scripts' cases)
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BLACK = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
LH = "row_id\tgame_id\tsplit\tfen\tscore_stm\told_score_stm\tresult\tdepth\tnodes\n"  # relabel2's LABELS_HEADER
RH = "row_id\tgame_id\tsplit\tfen\told_score_stm\tresult\tsource\tsource_row\n"  # relabel2's ROWS_HEADER


def norm(src, row):
    return json.dumps({"source": src, "source_row": row, "source_kind": "selfplay", "fen": START, "score": 10,
                       "result": 1.0}) + "\n"


GOOD_LABELS = LH + f"0\t0\ttrain\t{START}\t25\t30\t1\t9\t20001\n1\t0\ttrain\t{BLACK}\t-12\t-5\t1\t10\t20003\n" \
    f"2\t1\tval\t{START}\t3\t0\t0.5\t8\t20000\n"
ANSWERS = [{"id": i, "ok": True, "score_cp": 10 * i, "depth": 9, "nodes": 20000 + i, "elapsed_ns": 99 + i}
           for i in range(3)]
FIXTURES = {
    "good.jsonl": norm("b.txt", 2) + norm("a.txt", 7) + norm("a.txt", 1),
    "broken.jsonl": norm("a.txt", 1) + '{"source": "a.txt", "source_row": \n',
    "empty.jsonl": "",
    "blank.jsonl": "\n  \n",
    "badutf8.jsonl": norm("a.txt", 1).encode() + b'{"source": "\xff\xfe.txt", "source_row": 5}\n',
    "nondict.jsonl": "[1, 2]\n",
    "floatrow.jsonl": norm("a.txt", 1.5),
    "strrow.jsonl": norm("a.txt", "7"),
    "boolrow.jsonl": norm("a.txt", True),
    "intsource.jsonl": norm(10, 1) + norm(9, 1),
    "crlf.jsonl": (norm("a.txt", 2) + norm("a.txt", 1)).replace("\n", "\r\n"),
    "labels_good.tsv": GOOD_LABELS,
    "labels_empty.tsv": "",
    "labels_header.tsv": LH,
    "labels_rows.tsv": RH + f"0\t0\ttrain\t{START}\t30\t1\t0\t5\n",
    "labels_trunc.tsv": LH + f"0\t0\ttrain\t{START}\t25\n",
    "labels_nonint.tsv": LH + f"0\t0\ttrain\t{START}\tabc\t30\t1\t9\t20001\n",
    "labels_crlf.tsv": GOOD_LABELS.replace("\n", "\r\n"),
    "labels_const.tsv": LH + f"0\t0\ttrain\t{START}\t25\t30\t1\t9\t20001\n1\t0\ttrain\t{START}\t25\t31\t1\t9\t20001\n",
    "labels_badutf8.tsv": LH.encode() + b"0\t0\ttrain\t\xff\xfe\t25\t30\t1\t9\t20001\n",
    "ans_a.jsonl": "".join(json.dumps(a) + "\n" for a in ANSWERS),
    "ans_retimed.jsonl": "".join(json.dumps(dict(a, elapsed_ns=7)) + "\n" for a in ANSWERS),
    "ans_prefix.jsonl": "".join(json.dumps(a) + "\n" for a in ANSWERS[:2]),
    "ans_changed.jsonl": "".join(json.dumps(dict(a, score_cp=a["score_cp"] + (a["id"] == 1))) + "\n" for a in ANSWERS),
    "ans_broken.jsonl": json.dumps(ANSWERS[0]) + "\n" + '{"id": 1, "ok": tr\n',
    "ans_empty.jsonl": "",
    "ans_nondict.jsonl": "[1]\n",
    "ans_failed.jsonl": '{"id": 0, "ok": false, "error": "bad fen"}\n',
    "rows_good.tsv": RH + f"0\t0\ttrain\t{START}\t30\t1\t0\t5\n1\t0\ttrain\t{BLACK}\t-5\t1\t0\t6\n",
    "rows_empty.tsv": "",
    "rows_trunc.tsv": RH + "0\t0\n",
    "rows_badutf8.tsv": (RH + f"0\t0\ttrain\t{START}\t30\t1\t0\t5\n").encode() + b"1\t0\ttrain\t\xff\xfe\t-5\t1\t0\t6\n",
    "keep.txt": "KEEP THIS LINE\n",
    "req.tsv": f"0\tanalyze\t{START}\n",
    "broken.py": "def f(:\n",
    "stand_in_probe.exe": "stand-in: never started\n",
}


def main(scratch) -> int:
    if os.path.exists(scratch):
        print(f"refusing existing {scratch}", file=sys.stderr)
        return 2
    fx_dir = os.path.join(scratch, "fixtures")
    os.makedirs(fx_dir)
    for name, data in FIXTURES.items():
        with open(os.path.join(fx_dir, name), "wb") as fh:
            fh.write(data if isinstance(data, bytes) else data.encode())

    def fx(name):
        return os.path.join(fx_dir, name)

    def digest():
        return {n: hashlib.sha256(open(fx(n), "rb").read()).hexdigest() for n in sorted(os.listdir(fx_dir))}

    before = digest()
    fails = total = 0

    def report(name, ok, detail):
        nonlocal fails, total
        fails += not ok
        total += 1
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")

    def case(name, want, argv, leaves=(), check=None, setup=None, env=None, shell=False):
        """Run one helper; PASS = exit `want`, no traceback, exactly the files `leaves` new in the case folder."""
        d = os.path.join(scratch, name)
        os.makedirs(d)
        if setup:
            setup(d)
        pre = set(os.listdir(d))
        cmd = [BASH] + argv if shell else [PY, "-I", "-B"] + argv
        p = subprocess.run(cmd, cwd=d, capture_output=True, text=True, errors="replace",
                           env=dict(os.environ, **env) if env else None)
        left = sorted(set(os.listdir(d)) - pre)
        problems = []
        if p.returncode != want:
            problems.append(f"exit {p.returncode}, wanted {want}")
        if "Traceback" in p.stderr + p.stdout:
            problems.append("Python traceback")
        if left != sorted(leaves):
            problems.append(f"left {left}, wanted {sorted(leaves)}")
        if check and not problems:
            problems += check(d, p)
        msg = (p.stderr.strip().splitlines() or p.stdout.strip().splitlines() or [""])[-1]
        report(name, not problems, "; ".join(problems) or f"exit {p.returncode}: {msg.replace(fx_dir + os.sep, '')[:110]}")

    def stale_part(d):
        open(os.path.join(d, "out.jsonl.part"), "w").write("left by a killed run\n")

    def keep_copy(d):
        open(os.path.join(d, "out.jsonl"), "w").write("KEEP THIS LINE\n")

    def unchanged(file_name, text):
        return lambda d, p: [] if open(os.path.join(d, file_name)).read() == text else [f"{file_name} was changed"]

    def sorted_rows(d, p):
        keys = [(r["source"], r["source_row"]) for r in map(json.loads, open(os.path.join(d, "out.jsonl")))]
        return [] if keys == [("a.txt", 1), ("a.txt", 7), ("b.txt", 2)] else [f"order {keys}"]

    def lf_only(d, p):
        return [] if b"\r" not in open(os.path.join(d, "out.jsonl"), "rb").read() else ["CR left in the output"]

    def no_stats(d, p):
        return [] if not p.stdout.strip() else ["statistics printed for a damaged input"]

    sort_py, stats_py, bench_py = (os.path.join(HERE, n) for n in ("sort_normalized.py", "label_stats.py",
                                                                    "probe_bench.py"))
    s = [sort_py, "out.jsonl"]
    case("sort_good", 0, s + [fx("good.jsonl")], ["out.jsonl"], sorted_rows)
    case("sort_ram_floor_equals_form", 0, [sort_py, "--min-free-ram-gb=0", "out.jsonl", fx("good.jsonl")], ["out.jsonl"])
    case("sort_crlf_input_gives_lf", 0, s + [fx("crlf.jsonl")], ["out.jsonl"], lf_only)
    for name, fixture in (("broken_json", "broken.jsonl"), ("empty_input", "empty.jsonl"),
                          ("blank_input", "blank.jsonl"), ("invalid_utf8", "badutf8.jsonl"),
                          ("non_object_line", "nondict.jsonl"), ("float_source_row", "floatrow.jsonl"),
                          ("string_source_row", "strrow.jsonl"), ("bool_source_row", "boolrow.jsonl"),
                          ("integer_source", "intsource.jsonl")):
        case(f"sort_{name}", 2, s + [fx(fixture)])
    case("sort_same_input_twice", 2, s + [fx("good.jsonl"), fx("good.jsonl")])
    case("sort_folder_as_input", 2, s + [fx_dir])
    case("sort_missing_input", 2, s + [fx("nope.jsonl")])
    case("sort_ram_floor_impossible", 2, [sort_py, "--min-free-ram-gb", "100000", "out.jsonl", fx("good.jsonl")])
    case("sort_ram_floor_nan", 2, [sort_py, "--min-free-ram-gb", "nan", "out.jsonl", fx("good.jsonl")])
    case("sort_ram_floor_negative", 2, [sort_py, "--min-free-ram-gb", "-1", "out.jsonl", fx("good.jsonl")])
    case("sort_misspelt_option", 2, [sort_py, "--min-free-ram=8", fx("good.jsonl"), fx("crlf.jsonl")])
    case("sort_option_after_out", 2, s + [fx("good.jsonl"), "--min-free-ram-gb", "8"])
    case("sort_out_folder_missing", 2, [sort_py, "nodir/out.jsonl", fx("good.jsonl")])
    case("sort_stale_part_kept", 2, s + [fx("good.jsonl")], setup=stale_part,
         check=unchanged("out.jsonl.part", "left by a killed run\n"))
    case("sort_out_exists_kept", 2, s + [fx("good.jsonl")], setup=keep_copy, check=unchanged("out.jsonl", "KEEP THIS LINE\n"))
    case("sort_help", 2, [sort_py, "--help"])
    case("stats_good", 0, [stats_py, fx("labels_good.tsv")])
    case("stats_crlf", 0, [stats_py, fx("labels_crlf.tsv")])
    case("stats_constant_new_score", 0, [stats_py, fx("labels_const.tsv")])
    case("stats_header_only", 1, [stats_py, fx("labels_header.tsv")])
    for name, fixture in (("empty_file", "labels_empty.tsv"), ("rows_tsv_given", "labels_rows.tsv"),
                          ("truncated_row", "labels_trunc.tsv"), ("non_integer_score", "labels_nonint.tsv"),
                          ("missing_file", "nope.tsv")):
        case(f"stats_{name}", 2, [stats_py, fx(fixture)], check=no_stats)
    case("stats_invalid_utf8_line_named", 2, [stats_py, fx("labels_badutf8.tsv")],
         check=lambda d, p: no_stats(d, p) + ([] if "labels_badutf8.tsv:2: not UTF-8" in p.stderr else ["no line 2"]))
    case("stats_good_then_damaged", 2, [stats_py, fx("labels_good.tsv"), fx("labels_trunc.tsv")], check=no_stats)
    case("stats_folder", 2, [stats_py, fx_dir], check=no_stats)
    case("stats_help", 2, [stats_py, "--help"])
    c = [bench_py, "compare"]
    case("compare_same", 0, c + [fx("ans_a.jsonl"), fx("ans_a.jsonl")])
    case("compare_timing_ignored", 0, c + [fx("ans_a.jsonl"), fx("ans_retimed.jsonl")])
    case("compare_one_label_changed", 1, c + [fx("ans_a.jsonl"), fx("ans_changed.jsonl")])
    case("compare_b_shorter", 1, c + [fx("ans_a.jsonl"), fx("ans_prefix.jsonl")])
    case("compare_failed_answers", 1, c + [fx("ans_failed.jsonl"), fx("ans_failed.jsonl")])
    case("compare_both_empty", 2, c + [fx("ans_empty.jsonl"), fx("ans_empty.jsonl")])
    case("compare_broken_json", 2, c + [fx("ans_a.jsonl"), fx("ans_broken.jsonl")])
    case("compare_non_object_line", 2, c + [fx("ans_nondict.jsonl"), fx("ans_nondict.jsonl")])
    case("compare_missing_file", 2, c + [fx("ans_a.jsonl"), fx("nope.jsonl")])
    case("compare_one_argument", 2, c + [fx("ans_a.jsonl")])
    r = [bench_py, "requests", "--out", "req.tsv", "--rows"]
    case("requests_good", 0, r + [fx("rows_good.tsv")], ["req.tsv"],
         check=lambda d, p: [] if open(os.path.join(d, "req.tsv")).read() == f"0\tanalyze\t{START}\n1\tanalyze\t{BLACK}\n"
         else ["wrong request lines"])
    case("requests_from_labels_tsv", 0, r + [fx("labels_good.tsv")], ["req.tsv"])
    case("requests_empty_file", 2, r + [fx("rows_empty.tsv")])
    case("requests_truncated_row", 2, r + [fx("rows_trunc.tsv")])
    case("requests_invalid_utf8_line_named", 2, r + [fx("rows_badutf8.tsv")],
         check=lambda d, p: [] if "rows_badutf8.tsv:3: not UTF-8" in p.stderr else ["no line 3"])
    case("requests_start_past_end", 2, r + [fx("rows_good.tsv"), "--start", "9"])
    case("requests_count_zero", 2, r + [fx("rows_good.tsv"), "--count", "0"])
    case("requests_missing_rows", 2, r + [fx("nope.tsv")])
    case("requests_wrong_file", 2, r + [fx("good.jsonl")])
    case("requests_out_exists_kept", 2, [bench_py, "requests", "--rows", fx("rows_good.tsv"), "--out", fx("keep.txt")])
    case("run_out_exists_kept", 2, [bench_py, "run", "--exe", "C:/Windows/System32/findstr.exe", "--req", fx("req.tsv"),
                                    "--out", "out.jsonl"], setup=keep_copy, check=unchanged("out.jsonl", "KEEP THIS LINE\n"))
    case("run_missing_exe", 2, [bench_py, "run", "--exe", "nope.exe", "--req", fx("req.tsv"), "--out", "out.jsonl"])
    case("run_missing_requests", 2, [bench_py, "run", "--exe", PY, "--req", fx("nope.tsv"), "--out", "out.jsonl"])
    case("run_out_folder_missing", 2, [bench_py, "run", "--exe", PY, "--req", fx("req.tsv"), "--out", "nodir/o.jsonl"])

    # bug hunt #15: fn_diff.py and the shell scripts refuse wrong arguments before any work (no probe is started:
    # every case below stops at an argument or file check; the stand-in probe is a text file)
    fd = [os.path.join(HERE, "fn_diff.py")]
    relabel = os.path.join(HERE, "relabel2.py")
    case("fn_diff_no_arguments", 2, fd)
    case("fn_diff_missing_file", 2, fd + [fx("nope.py"), relabel])
    case("fn_diff_broken_python", 2, fd + [fx("broken.py"), relabel])
    case("fn_diff_unknown_function", 2, fd + [relabel, relabel, "no_such_function"])
    case("fn_diff_same_file", 0, fd + [relabel, relabel, "label_shard"])
    if BASH:
        mr, stand_in = [os.path.join(HERE, "measure_rates.sh")], {"PROBE": fx("stand_in_probe.exe")}

        def short_input(d):
            os.makedirs(os.path.join(d, "mr"))
            open(os.path.join(d, "mr", "in220k.txt"), "w").write("".join(f"{START} | 0 | 0.5\n" for _ in range(10)))

        def stale_input_part(d):
            os.makedirs(os.path.join(d, "mr"))
            open(os.path.join(d, "mr", "in220k.txt.part"), "w").write("left by a killed run\n")

        def mr_untouched(*names):
            return lambda d, p: [] if sorted(os.listdir(os.path.join(d, "mr"))) == sorted(names) else ["mr changed"]

        case("measure_rates_unknown_step", 2, mr + ["bogus", "mr"], shell=True)
        case("measure_rates_missing_probe", 2, mr + ["workers", "mr"], shell=True, env={"PROBE": fx("nope.exe")})
        case("measure_rates_short_input", 2, mr + ["workers", "mr"], shell=True, env=stand_in, setup=short_input,
             check=mr_untouched("in220k.txt"))
        case("measure_rates_stale_input_part", 2, mr + ["nodes", "mr"], shell=True, env=stand_in,
             setup=stale_input_part, check=mr_untouched("in220k.txt.part"))
        case("bridge_check_wrong_proof_dir", 2, [os.path.join(HERE, "bridge_check.sh"), fx("no_proof"), "out"],
             shell=True)
        case("prove_resume_unknown_step", 2, [os.path.join(HERE, "prove_resume.sh"), "bogus", "base"], shell=True)
    else:
        report("shell_scripts", False, "no bash on PATH: the measure_rates / bridge_check / prove_resume cases did not run")

    # abba with a stand-in run_probe (no process): answers that change stop it with exit 1 and no speed figures
    sys.path.insert(0, HERE)
    import probe_bench
    calls = []

    def fake(exe, req, out, mask, nodes, differ_at=None):
        calls.append(out)
        open(out, "x").write("{}\n")
        score = 11 if len(calls) == differ_at else 10
        return 1.0 + 0.01 * len(calls), [{"id": 0, "ok": True, "score_cp": score, "elapsed_ns": len(calls)}]

    stand_ins = [os.path.join(scratch, n) for n in ("A.exe", "B.exe", "abba_req.tsv")]
    for path in stand_ins:
        open(path, "x").write("stand-in\n")
    for name, pairs, differ_at, want in (("abba_complete", 2, None, 0), ("abba_answers_differ", 3, 3, 1),
                                         ("abba_one_pair", 1, None, 2), ("abba_zero_pairs", 0, None, 2)):
        calls.clear()
        probe_bench.run_probe = lambda *args, _d=differ_at: fake(*args, differ_at=_d)
        out = os.path.join(scratch, name)
        ns = argparse.Namespace(a=stand_ins[0], b=stand_ins[1], req=stand_ins[2], pairs=pairs, out=out, mask="0x4",
                                nodes=20000)
        buf = io.StringIO()
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = probe_bench.cmd_abba(ns)
        except SystemExit as e:
            rc = e.code
        summary = open(os.path.join(out, "summary.txt")).read() if os.path.exists(os.path.join(out, "summary.txt")) else ""
        has_ci = "95% CI" in summary
        ok = rc == want and has_ci == (want == 0) and (want != 2 or not os.path.exists(out))
        report(name, ok, f"exit {rc} (wanted {want}), {len(calls)} runs, CI line {'yes' if has_ci else 'no'}")
    report("fixtures_unchanged", digest() == before, "every fixture file has its first sha256")
    print(f"{total - fails} PASS / {fails} FAIL")
    return 0 if not fails else 1


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
