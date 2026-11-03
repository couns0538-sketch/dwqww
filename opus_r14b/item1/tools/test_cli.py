#!/usr/bin/env python3
"""test_cli.py - Opus R14-B item 1: exit-code tests of the loader tools with missing or wrong arguments and damaged
inputs (bug hunt #16, own code, stdlib only): fl_equal.py, fl_dataset_equal.py, fl_distribution.py, fl_abba.py,
fl_fuzz.py (since the Code Review fixes of 2026-11-03, with in-process checks of fl_abba's 0-speed stop and fl_fuzz's
outcome / identity / disk-floor rules).

usage: python -I -B test_cli.py SCRATCH_DIR      (SCRATCH_DIR must not exist)
No DLL, binpack or torch is loaded: every case stops at an argument, file or output check (stand-in files take the
place of the DLL and the data where a case needs them to exist). Checks per case: the exit code, no Python traceback,
nothing left behind, existing files unchanged; plus the compare commands on small valid dumps (exit 0 / 1).
One PASS / FAIL line per case; exit 0 = all PASS.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
D24 = "0" * 24  # one tensor digest of a fl_dataset_equal.py dump row


def ds_dump(rows, batches, val_batches):
    return "".join(f"train\t{k}\t{D24}\t{D24}\n" for k in range(rows)) + \
        f"# loader=old workers=1 torch=x batches={batches} val_batches={val_batches}\n"


def eq_dump(rows, settings="# settings batch=16384 window=1048576"):
    return f"{settings}\n" + "".join(f"{k}\t100\tabc{k}\n" for k in range(rows)) + "# batches=1 hashed=True\n"


def abba_zero_speed(work, dll, data) -> str:
    """fl_abba.main() in this process with subprocess.run replaced by a stub whose dump says kept_per_s=0 (as a timed
    window of no batch did): '' when fl_abba stops with exit 1 before any ratio, else what went wrong (CR fix 2)."""
    import contextlib
    import importlib.util
    import io
    import types

    spec = importlib.util.spec_from_file_location("fl_abba_under_test", os.path.join(HERE, "fl_abba.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def stub_run(cmd, **_):
        with open(cmd[cmd.index("--out") + 1], "x", encoding="utf-8", newline="\n") as fh:
            fh.write("0\t1024\n# batches=1 seconds_total=0.100 warmup=0 seconds_timed=0.000 kept_per_s=0\n")

    mod.subprocess = types.SimpleNamespace(run=stub_run, DEVNULL=subprocess.DEVNULL,
                                           CalledProcessError=subprocess.CalledProcessError)
    os.makedirs(work)
    arm = f"fast:{dll}:1"
    argv, err = sys.argv, io.StringIO()
    sys.argv = ["fl_abba.py", "--out", os.path.join(work, "o"), "--pairs", "2", "--a", arm, "--b", arm, "--data", data,
                "--batches", "2", "--warmup", "1"]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            rc = mod.main()
    except Exception as e:  # noqa: BLE001 - the defect this test looks for is an exception
        return f"{type(e).__name__}: {e}"
    finally:
        sys.argv = argv
    if rc != 1 or "no speed figures" not in err.getvalue():
        return f"exit {rc}, stderr {err.getvalue().strip()[:120]!r}"
    return ""


def fuzz_rules() -> str:
    """fl_fuzz.py's rules, in-process (CR fix 4): exit 0 with no batch is 'empty' - a failure except where a case
    expects it -, the identity verdicts against the default loader, the disk-floor arithmetic. '' when all hold."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("fl_fuzz_under_test", os.path.join(HERE, "fl_fuzz.py"))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        checks = [
            ("exit 0 + 0 batches = empty", mod.classify("fast", 0, 0, [])[0] == "empty"),
            ("exit 0 + 3 batches = ok", mod.classify("fast", 0, 3, [])[0] == "ok"),
            ("exit 0 without a dump = OTHER", mod.classify("fast", 0, None, [])[0] == "OTHER"),
            ("fast exit 1 with its message = error", mod.classify("fast", 1, None, ["fast loader: x"])[0] == "error"),
            ("fast exit 1 without its message = OTHER", mod.classify("fast", 1, None, ["Traceback"])[0] == "OTHER"),
            ("old exit 1 = error", mod.classify("old", 1, None, ["RuntimeError: x"])[0] == "error"),
            ("Windows exception code = CRASH", mod.classify("old", 0xC0000005, None, [])[0] == "CRASH"),
            ("empty fails 'any'", not mod.acceptable("any", "empty")),
            ("empty fails 'ok'", not mod.acceptable("ok", "empty")),
            ("empty passes 'empty'", mod.acceptable("empty", "empty")),
            ("ok fails 'empty'", not mod.acceptable("empty", "ok")),
            ("ok / error pass 'any'", mod.acceptable("any", "ok") and mod.acceptable("any", "error")),
            ("HANG / CRASH / OTHER never pass", not any(mod.acceptable(e, o) for e in ("any", "ok", "error", "empty")
                                                        for o in ("HANG", "CRASH", "OTHER"))),
            ("identity same", mod.identity("ok", "ok", 0) == "same"),
            ("identity DIFF", mod.identity("ok", "ok", 1) == "DIFF"),
            ("identity compare refused", mod.identity("ok", "ok", 2) == "incomparable"),
            ("identity both empty", mod.identity("empty", "empty", None) == "same-empty"),
            ("identity old failed", mod.identity("ok", "error", None) == "old-error"),
            ("identity old empty", mod.identity("ok", "empty", None) == "old-empty"),
            ("only same / same-empty are good", [mod.identity_ok(v) for v in ("same", "same-empty", "DIFF", "old-error",
                                                                              "incomparable")] == [1, 1, 0, 0, 0]),
            ("disk floor: more than the free space is short", bool(mod.disk_short(HERE, 10 ** 18, 0))),
            ("disk floor: nothing needed above floor 0 is fine", not mod.disk_short(HERE, 0, 0)),
        ]
    except Exception as e:  # noqa: BLE001 - a missing rule shows up as an exception
        return f"{type(e).__name__}: {e}"
    return "; ".join(name for name, ok in checks if not ok)


FIXTURES = {
    "stand_in.dll": "stand-in, never loaded\n",
    "stand_in.binpack": "stand-in, never read\n",
    "keep.txt": "KEEP\n",
    "junk.txt": "not a dump\n",
    "ds_ok_a.tsv": ds_dump(3, 2, 1),
    "ds_ok_b.tsv": ds_dump(3, 2, 1),
    "ds_short.tsv": ds_dump(2, 2, 1),
    "ds_nofooter.tsv": ds_dump(3, 2, 1).split("# loader")[0],
    "ds_empty.tsv": "# loader=old workers=1 torch=x batches=0 val_batches=0\n",
    "eq_ok_a.tsv": eq_dump(3),
    "eq_ok_b.tsv": eq_dump(3),
    "eq_diff.tsv": eq_dump(3).replace("abc1", "xyz1"),
    "eq_none_a.tsv": eq_dump(0),
    "eq_none_b.tsv": eq_dump(0),
    "dist_bad.json": "[1, 2]\n",
}


def main(scratch) -> int:
    if os.path.exists(scratch):
        print(f"refusing existing {scratch}", file=sys.stderr)
        return 2
    fx_dir = os.path.join(scratch, "fixtures")
    os.makedirs(fx_dir)
    for name, text in FIXTURES.items():
        with open(os.path.join(fx_dir, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def fx(name):
        return os.path.join(fx_dir, name)

    def snapshot():
        return {n: open(fx(n), "rb").read() for n in sorted(os.listdir(fx_dir))}

    before = snapshot()
    fails = total = 0

    def case(name, want, argv, env=None, text=None):  # text: a reason the output must give (not just any exit 2)
        nonlocal fails, total
        d = os.path.join(scratch, name)
        os.makedirs(d)
        p = subprocess.run([PY, "-I", "-B"] + argv, cwd=d, capture_output=True, text=True, errors="replace",
                           env=dict(os.environ, **env) if env else None)
        left = sorted(os.listdir(d))
        problems = [f"exit {p.returncode}, wanted {want}"] if p.returncode != want else []
        problems += ["Python traceback"] if "Traceback" in p.stderr + p.stdout else []
        problems += [f"left {left}"] if left else []
        problems += [f"no '{text}' in the output"] if text and text not in p.stderr + p.stdout else []
        total += 1
        fails += bool(problems)
        msg = (p.stderr.strip().splitlines() or p.stdout.strip().splitlines() or [""])[-1]
        print(f"{'FAIL' if problems else 'PASS'} {name}: {'; '.join(problems) or msg.replace(fx_dir + os.sep, '')[:110]}")

    eq, ds, di, ab = (os.path.join(HERE, n) for n in ("fl_equal.py", "fl_dataset_equal.py", "fl_distribution.py",
                                                      "fl_abba.py"))
    dump = [eq, "dump", "--loader", "fast", "--dll", fx("stand_in.dll"), "--data", fx("stand_in.binpack")]
    case("equal_no_arguments", 2, [eq])
    case("equal_dump_out_exists", 2, dump + ["--out", fx("keep.txt")])
    case("equal_dump_out_folder_missing", 2, dump + ["--out", "nodir/x.tsv"])
    case("equal_dump_missing_dll", 2, [eq, "dump", "--loader", "fast", "--dll", fx("nope.dll"), "--data",
                                       fx("stand_in.binpack"), "--out", fx("new1.tsv")])
    case("equal_dump_missing_data", 2, [eq, "dump", "--loader", "fast", "--dll", fx("stand_in.dll"), "--data",
                                        fx("nope.binpack"), "--out", fx("new2.tsv")])
    case("equal_dump_bad_mask", 2, dump + ["--out", fx("new3.tsv"), "--mask", "xyz"])
    case("equal_dump_zero_mask", 2, dump + ["--out", fx("new4.tsv"), "--mask", "0x0"])
    case("equal_compare_identical", 0, [eq, "compare", fx("eq_ok_a.tsv"), fx("eq_ok_b.tsv")])
    case("equal_compare_one_batch_differs", 1, [eq, "compare", fx("eq_ok_a.tsv"), fx("eq_diff.tsv")])
    case("equal_compare_no_batches", 2, [eq, "compare", fx("eq_none_a.tsv"), fx("eq_none_b.tsv")])
    case("equal_compare_junk", 2, [eq, "compare", fx("junk.txt"), fx("junk.txt")])
    case("equal_compare_missing", 2, [eq, "compare", fx("eq_ok_a.tsv"), fx("nope.tsv")])
    case("dataset_no_arguments", 2, [ds])
    case("dataset_dump_out_exists", 2, [ds, "--loader", "old", "--out", fx("keep.txt")])
    case("dataset_dump_fast_without_dir", 2, [ds, "--loader", "fast", "--out", fx("new5.tsv")],
         env={"FORGE_FAST_LOADER_DIR": ""})
    case("dataset_compare_identical", 0, [ds, "--compare", fx("ds_ok_a.tsv"), fx("ds_ok_b.tsv")])
    case("dataset_compare_junk", 2, [ds, "--compare", fx("junk.txt"), fx("junk.txt")])
    case("dataset_compare_no_footer", 2, [ds, "--compare", fx("ds_nofooter.tsv"), fx("ds_nofooter.tsv")])
    case("dataset_compare_short_dump", 2, [ds, "--compare", fx("ds_short.tsv"), fx("ds_short.tsv")])
    case("dataset_compare_no_batches", 2, [ds, "--compare", fx("ds_empty.tsv"), fx("ds_empty.tsv")])
    case("dataset_compare_missing", 2, [ds, "--compare", fx("ds_ok_a.tsv"), fx("nope.tsv")])
    case("distribution_no_arguments", 2, [di])
    case("distribution_stats_out_exists", 2, [di, "stats", "--loader", "fast", "--dll", fx("stand_in.dll"),
                                              "--workers", "1", "--data", fx("stand_in.binpack"), "--out", fx("keep.txt")])
    case("distribution_compare_not_stats", 2, [di, "compare", fx("dist_bad.json"), fx("dist_bad.json")])
    case("distribution_compare_junk", 2, [di, "compare", fx("junk.txt"), fx("junk.txt")])
    case("distribution_compare_missing", 2, [di, "compare", fx("nope1.json"), fx("nope2.json")])
    arm = f"fast:{fx('stand_in.dll')}:1"
    abba = [ab, "--data", fx("stand_in.binpack"), "--a", arm, "--b", arm]
    case("abba_no_arguments", 2, [ab])
    case("abba_zero_pairs", 2, abba + ["--out", "o", "--pairs", "0"])
    case("abba_one_pair", 2, abba + ["--out", "o", "--pairs", "1"])
    case("abba_malformed_arm", 2, [ab, "--data", fx("stand_in.binpack"), "--a", "fast", "--b", arm, "--out", "o"])
    case("abba_missing_dll", 2, [ab, "--data", fx("stand_in.binpack"), "--a", f"fast:{fx('nope.dll')}:1", "--b", arm,
                                 "--out", "o"])
    case("abba_bad_mask", 2, abba + ["--out", "o", "--mask", "xyz"])
    case("abba_out_exists", 2, abba + ["--out", fx_dir])
    # CR fix 2 (2026-11-03): a warm-up that is not below the batch count timed nothing - a 0 kept/s "speed" and then a
    # ZeroDivisionError in the ratios; refused before the output folder is made (and by fl_equal.py dump itself)
    case("abba_warmup_equals_batches", 2, abba + ["--out", "o", "--batches", "20", "--warmup", "20"])
    case("abba_warmup_above_batches", 2, abba + ["--out", "o", "--batches", "20", "--warmup", "30"])
    case("abba_negative_warmup", 2, abba + ["--out", "o", "--warmup", "-1"])
    case("abba_zero_batches", 2, abba + ["--out", "o", "--batches", "0", "--warmup", "0"])
    case("equal_dump_warmup_not_below_batches", 2, dump + ["--out", fx("new6.tsv"), "--batches", "5", "--warmup", "5"])
    case("equal_dump_negative_warmup", 2, dump + ["--out", fx("new7.tsv"), "--warmup", "-1"])
    case("equal_dump_zero_batches", 2, dump + ["--out", fx("new8.tsv"), "--batches", "0"])
    problem = abba_zero_speed(os.path.join(scratch, "abba_zero_speed"), fx("stand_in.dll"), fx("stand_in.binpack"))
    total += 1
    fails += bool(problem)
    print(f"{'FAIL' if problem else 'PASS'} abba_zero_speed_stops: {problem or 'a 0 kept/s run ends fl_abba with exit 1'}")
    # CR fix 4 (2026-11-03): fl_fuzz.py's arguments are checked before it reads, pins or writes anything
    fz = os.path.join(HERE, "fl_fuzz.py")
    fuzz = [fz, "--dll", fx("stand_in.dll"), "--old-dll", fx("stand_in.dll"), "--binpack", fx("stand_in.binpack")]
    case("fuzz_flips_over_cap", 2, fuzz + ["--out", "o", "--flips", "1001"], text="--flips 1001: must be 0..1000")
    case("fuzz_negative_flips", 2, fuzz + ["--out", "o", "--flips", "-1"], text="--flips -1: must be 0..1000")
    case("fuzz_without_old_dll", 2, [fz, "--dll", fx("stand_in.dll"), "--binpack", fx("stand_in.binpack"), "--out", "o"],
         text="--old-dll")
    case("fuzz_old_dll_missing", 2, [fz, "--dll", fx("stand_in.dll"), "--old-dll", fx("nope.dll"), "--binpack",
                                     fx("stand_in.binpack"), "--out", "o"], text="nope.dll: file not found")
    case("fuzz_bad_mask", 2, fuzz + ["--out", "o", "--mask", "xyz"], text="is not a hexadecimal CPU mask")
    case("fuzz_zero_timeout", 2, fuzz + ["--out", "o", "--timeout", "0"], text="--timeout must be at least 1")
    case("fuzz_disk_floor", 2, fuzz + ["--out", "o", "--min-free-gb", "1000000000"], text="disk floor")
    case("fuzz_out_exists", 2, fuzz + ["--out", fx_dir], text="exists or its folder is missing")
    problem = fuzz_rules()
    total += 1
    fails += bool(problem)
    print(f"{'FAIL' if problem else 'PASS'} fuzz_rules: {problem or 'outcome, identity and disk-floor rules hold'}")
    ok = snapshot() == before
    total += 1
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'} fixtures_unchanged: every fixture file still has its first bytes")
    print(f"{total - fails} PASS / {fails} FAIL")
    return 0 if not fails else 1


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
