#!/usr/bin/env python3
"""
Job 35 — Reusable Step 0 / KB0 / Part C fresh-process verifier.
Prints every PASS / FAIL line with the two compared values side by side.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, "/tmp/carbon2_job28")
from sp_tools import NET768, PC20_OPTIONS, get_root_sets, run_60_game_hash16


def sha256_file(path: str | pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def run_fresh_bench(exe: str, depth: int, extra_uci: str = "") -> int:
    stdin = f"uci\n{extra_uci}isready\nbench {depth}\nisready\nquit\n"
    res = subprocess.run([exe], input=stdin, text=True, capture_output=True, check=True)
    if res.stderr:
        raise RuntimeError(f"Non-empty stderr from {exe}:\n{res.stderr}")
    prefix = f"info string bench depth {depth} nodes "
    for ln in res.stdout.splitlines():
        if ln.startswith(prefix):
            return int(ln[len(prefix) :].split()[0])
    raise RuntimeError(f"Did not find '{prefix}' in stdout of {exe}:\n{res.stdout}")


def run_fresh_perft5(exe: str) -> int:
    stdin = "uci\nisready\nposition startpos\ngo perft 5\nisready\nquit\n"
    res = subprocess.run([exe], input=stdin, text=True, capture_output=True, check=True)
    if res.stderr:
        raise RuntimeError(f"Non-empty stderr from {exe}:\n{res.stderr}")
    for ln in reversed(res.stdout.splitlines()):
        if ln.startswith("nodes "):
            return int(ln.split()[1])
    raise RuntimeError(f"Did not find 'nodes <N>' in perft stdout of {exe}:\n{res.stdout}")


def fmt_cmp(label: str, got: object, exp: object) -> tuple[bool, str]:
    ok = got == exp
    status = "PASS" if ok else "FAIL"
    op = "==" if ok else "!="
    return ok, f"  {label:<36s}: {status} ({got} {op} {exp})"


def verify_exe(
    label: str,
    exe_path: str,
    expected_sha256: str | None = None,
    profdata_path: str | None = None,
    expected_prof_sha256: str | None = None,
    with_job20: bool = False,
) -> tuple[bool, list[str]]:
    pc20_str = "".join(f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS)
    pc20_net768_str = (
        pc20_str
        + f"setoption name NNUEArchFile value {NET768}\n"
        + "setoption name NNUEArch value true\n"
    )

    lines: list[str] = [f"[{label}] exe={exe_path} (len={len(exe_path)})"]
    all_ok = True

    got_sha = sha256_file(exe_path)
    if expected_sha256 is not None:
        ok, s = fmt_cmp("exe_sha256 vs recorded", got_sha, expected_sha256)
        all_ok = all_ok and ok
        lines.append(s)
    else:
        lines.append(f"  {'exe_sha256':<36s}: {got_sha}")

    if profdata_path is not None and pathlib.Path(profdata_path).exists():
        got_psha = sha256_file(profdata_path)
        if expected_prof_sha256 is not None:
            ok, s = fmt_cmp("profdata_sha256 vs recorded", got_psha, expected_prof_sha256)
            all_ok = all_ok and ok
            lines.append(s)
        else:
            lines.append(f"  {'profdata_sha256':<36s}: {got_psha}")

    # Seven fresh-process checks (one fresh process per check)
    checks_7 = [
        ("no-option bench 11 (fresh proc)", run_fresh_bench(exe_path, 11, ""), 312866),
        ("no-option bench 13 (fresh proc)", run_fresh_bench(exe_path, 13, ""), 862329),
        ("no-option perft 5 (fresh proc)", run_fresh_perft5(exe_path), 4865609),
        ("PC20 bench 11 (fresh proc)", run_fresh_bench(exe_path, 11, pc20_str), 278024),
        ("PC20 bench 13 (fresh proc)", run_fresh_bench(exe_path, 13, pc20_str), 587276),
        ("PC20+net768 bench 11 (fresh proc)", run_fresh_bench(exe_path, 11, pc20_net768_str), 882074),
        ("PC20+net768 bench 13 (fresh proc)", run_fresh_bench(exe_path, 13, pc20_net768_str), 4275906),
    ]
    for name, got, exp in checks_7:
        ok, s = fmt_cmp(name, got, exp)
        all_ok = all_ok and ok
        lines.append(s)

    if with_job20:
        j20_roots, _, _ = get_root_sets()
        j20 = run_60_game_hash16(exe_path, NET768, j20_roots)
        for name, got, exp in [
            ("Job 20 searches (fresh proc)", j20["searches"], 7670),
            ("Job 20 nodes (fresh proc)", j20["nodes"], 25641316),
            ("Job 20 trace (fresh proc)", j20["trace_fnv1a64"], "ee465caeff9c0fcf"),
        ]:
            ok, s = fmt_cmp(name, got, exp)
            all_ok = all_ok and ok
            lines.append(s)

    return all_ok, lines


def run_step0(out_path: pathlib.Path) -> None:
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    header = [
        f"UTC: {utc}",
        "=== JOB 35 STEP 0: Plain r15d and kF Verification (7 Fresh Processes Each) ===",
        "Reusing recorded SP-PGO executables from earlier jobs (verified by recorded sha256):",
        "  - plain r15d: /tmp/carbon2_job11/bld_sp_r15d_1/forge (recorded in job31/builds.txt & job33/builds.txt)",
        "  - plain kF:   /tmp/carbon2_job17/bld_sp_tidy_1/forge (recorded in job28/builds.txt, job30/builds.txt & job31/builds.txt)",
        "",
    ]
    ok_d, lines_d = verify_exe(
        "plain_r15d (reused bld_sp_r15d_1)",
        "/tmp/carbon2_job11/bld_sp_r15d_1/forge",
        expected_sha256="31489d73bb8f3fa8af14c020bb1f419ded39dc835b0dd3e0b2fee9cddf6faf03",
        profdata_path="/tmp/carbon2_job11/bld_sp_r15d_1/forge.profdata",
        expected_prof_sha256="7ec91d0bbf8dc50ba53817a4eea858e242403ded7096ba7bf41a96eba834c77f",
        with_job20=False,
    )
    ok_f, lines_f = verify_exe(
        "plain_kF (reused bld_sp_tidy_1)",
        "/tmp/carbon2_job17/bld_sp_tidy_1/forge",
        expected_sha256="c16daacc5987a820801c792ec4ffbb5f997f2c8d97af4399aa365c5edc473b4e",
        profdata_path="/tmp/carbon2_job17/bld_sp_tidy_1/forge.profdata",
        expected_prof_sha256="43849e2eea568ce8b74364357e3f90e076e45d8fe1e35cd1d280b287d355658f",
        with_job20=False,
    )
    both_ok = ok_d and ok_f
    footer = [
        "",
        f"STEP 0 OVERALL: {'PASS' if both_ok else 'FAIL'} (passed_exes: {int(ok_d) + int(ok_f)} == 2)",
    ]
    txt = "\n".join(header + lines_d + [""] + lines_f + footer) + "\n"
    out_path.write_text(txt)
    print(txt, flush=True)
    if not both_ok:
        raise SystemExit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step0-out", type=pathlib.Path, default=None)
    ap.add_argument("--exe", type=str, default=None)
    ap.add_argument("--label", type=str, default="exe")
    ap.add_argument("--profdata", type=str, default=None)
    ap.add_argument("--with-job20", action="store_true")
    ap.add_argument("--out", type=pathlib.Path, default=None)
    args = ap.parse_args()

    if args.step0_out is not None:
        run_step0(args.step0_out)
        return

    assert args.exe is not None
    ok, lines = verify_exe(args.label, args.exe, profdata_path=args.profdata, with_job20=args.with_job20)
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    txt = f"UTC: {utc}\n" + "\n".join(lines) + f"\nOVERALL: {'PASS' if ok else 'FAIL'} ({int(ok)} == 1)\n"
    if args.out is not None:
        args.out.write_text(txt)
    print(txt, flush=True)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
