#!/usr/bin/env python3
"""test_cli.py - Opus R14-B item 1: exit-code tests of the loader tools with missing or wrong arguments and damaged
inputs (bug hunt #16, own code, stdlib only): fl_equal.py, fl_dataset_equal.py, fl_distribution.py, fl_abba.py.

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

    def case(name, want, argv, env=None):
        nonlocal fails, total
        d = os.path.join(scratch, name)
        os.makedirs(d)
        p = subprocess.run([PY, "-I", "-B"] + argv, cwd=d, capture_output=True, text=True, errors="replace",
                           env=dict(os.environ, **env) if env else None)
        left = sorted(os.listdir(d))
        problems = [f"exit {p.returncode}, wanted {want}"] if p.returncode != want else []
        problems += ["Python traceback"] if "Traceback" in p.stderr + p.stdout else []
        problems += [f"left {left}"] if left else []
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
