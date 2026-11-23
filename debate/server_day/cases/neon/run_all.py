"""Neon 2026-11-23: ten runnable failing cases (N1 to N10) against debate/server_day/scripts/ (v1, MANIFEST digest
9705a787bf51f71f8adee7b155d5fccd73f8616a520f39beaaad45c55a91c864).

    python3 -I -B debate/server_day/cases/neon/run_all.py <scripts_dir> <NEW work_dir> [--source DIR] [--net FILE] [only=N1,N2,...]

Exit 0: all selected cases satisfy v2 expectations (none should pass on v1).
Exit 1: one or more cases fail (on v1, all 10 cases FAIL with diagnostics).
Exit 2: wrong call or missing prerequisite.
"""
import argparse
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent.parent


def run_cmd(cmd, env=None, timeout=60):
    t0 = time.monotonic()
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=env, timeout=timeout)
    return p.returncode, p.stdout, p.stderr, time.monotonic() - t0


def case_n1(sd: Path, work: Path, _src: Path, _net: Path):
    """linux/cpu_check.sh line 25: missing flags line aborts with rc=1 silent instead of rc=2 with message."""
    rc, out, err, _ = run_cmd(["bash", sd / "linux" / "cpu_check.sh", "avx2_pext", HERE / "noflags.cpuinfo"])
    ok = rc == 2 and ("no flags" in (out + err).lower() or "flags" in (out + err).lower())
    return ok, f"rc={rc} stdout={out.strip()!r} stderr={err.strip()!r} (want rc=2 with diagnostic)"


def case_n2(sd: Path, work: Path, src: Path, net: Path):
    """linux/build_forge.sh lines 78/89/94/125: unquoted $extra word-splits $WORK containing spaces."""
    if not src.is_dir() or not net.is_file():
        return False, f"prerequisite missing: source={src} net={net}"
    space_work = work / "dir with space"
    arg_log = work / "cxx_argv.txt"
    fake_cxx = work / "fake_cxx.sh"
    fake_cxx.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "${1:-}" = "--version" ]; then echo "g++ (fake) 13.3.0"; exit 0; fi\n'
        f'printf "%s\\n" "$@" >> "{arg_log}"\n'
        "exit 1\n",
        encoding="ascii",
    )
    fake_cxx.chmod(fake_cxx.stat().st_mode | stat.S_IXUSR)
    env = dict(os.environ, CXX=str(fake_cxx), JOBS="1", LTO="full")
    run_cmd(["bash", sd / "linux" / "build_forge.sh", "avx2_pext", src, net, sd / "workloads", sd / "known", space_work], env=env)
    args = arg_log.read_text(encoding="utf-8").splitlines() if arg_log.exists() else []
    want = f"-fprofile-generate={space_work}/prof"
    has_intact = want in args
    has_split = "with" in args or "space/prof" in args
    ok = has_intact and not has_split
    return ok, f"intact_flag={has_intact} word_split={has_split} sample_args={[a for a in args if 'prof' in a or a in ('with', 'space/prof')][:6]}"


def case_n3(sd: Path, work: Path, _src: Path, _net: Path):
    """run/uciproc.py lines 62-74: read_until(..., 0.3, ...) hangs past deadline while 20 ms lines arrive."""
    helper = (
        f"import sys, time; sys.path.insert(0, {str(sd / 'run')!r}); import uciproc\n"
        f"e = uciproc.Engine({str(HERE / 'spam_engine.py')!r})\n"
        "try:\n"
        "    e.send('uci'); e.read_until(lambda s: s == 'uciok', 2.0, 'uci')\n"
        "    t0 = time.monotonic(); e.send('go depth 1')\n"
        "    try:\n"
        "        e.read_until(lambda s: s.startswith('bestmove'), 0.3, 'go')\n"
        "        print(f'RETURNED_OK {time.monotonic() - t0:.3f}')\n"
        "    except uciproc.EngineError as ex:\n"
        "        print(f'TIMED_OUT {time.monotonic() - t0:.3f} {ex}')\n"
        "finally:\n"
        "    e.kill()\n"
    )
    rc, out, err, _ = run_cmd([sys.executable, "-I", "-B", "-c", helper])
    line = out.strip().splitlines()[-1] if out.strip() else ""
    parts = line.split()
    ok = rc == 0 and len(parts) >= 2 and parts[0] == "TIMED_OUT" and float(parts[1]) <= 0.8
    return ok, f"rc={rc} out={line!r} err={err.strip()[:200]!r} (want TIMED_OUT <= 0.8s)"


def case_n4(sd: Path, work: Path, _src: Path, _net: Path):
    """tools/drive.py lines 62-76: step limit 0.3 s is ignored while 20 ms info lines arrive."""
    uci = work / "spam.uci"
    uci.write_text("uci\ngo depth 1\nquit\n", encoding="ascii")
    out_file = work / "spam.transcript"
    rc, out, err, dt = run_cmd([sys.executable, "-I", "-B", sd / "tools" / "drive.py",
                                HERE / "spam_engine.py", uci, "-", out_file, "0.3"])
    ok = rc == 3 and dt <= 1.2
    return ok, f"rc={rc} elapsed={dt:.2f}s stdout={out.strip()!r} (want rc=3 timeout <= 1.2s)"


def case_n5(sd: Path, work: Path, _src: Path, _net: Path):
    """tools/drive.py line 43: missing engine exe crashes with FileNotFoundError (rc=1) instead of exit 2."""
    uci = work / "q.uci"
    uci.write_text("quit\n", encoding="ascii")
    rc, out, err, _ = run_cmd([sys.executable, "-I", "-B", sd / "tools" / "drive.py",
                               work / "no_such_engine", uci, "-", work / "missing.transcript"])
    ok = rc == 2 and "Traceback" not in err
    return ok, f"rc={rc} has_traceback={'Traceback' in err} out={out.strip()[:160]!r} (want rc=2, no traceback)"


def case_n6(sd: Path, work: Path, _src: Path, _net: Path):
    """run/record.py lines 44-48 & 108-112: bind() omits opening; mutating openingend line 1 passes faults()."""
    helper = (
        f"import sys; sys.path.insert(0, {str(sd / 'run')!r}); import record\n"
        "orig = record.text('r-w001-g00000001', ['f2f3','e7e5','g2g4','d8h4'], 'none', [], 'openingend plies 4 reason nomoves')\n"
        "mut = orig.replace('f2f3 e7e5 g2g4 d8h4', 'a2a3 a7a6 b2b3 b7b6', 1)\n"
        "parsed = record.parse(mut.encode('ascii'))\n"
        "print(record.faults(parsed[0], reserved=None))\n"
    )
    rc, out, err, _ = run_cmd([sys.executable, "-I", "-B", "-c", helper])
    ok = rc == 0 and out.strip() != "[]" and out.strip() != ""
    return ok, f"rc={rc} faults={out.strip()!r} err={err.strip()[:160]!r} (want non-empty bind fault)"


def case_n7(sd: Path, work: Path, _src: Path, _net: Path):
    """run/packer.py lines 114 & 199-203: 0-byte .sha256 crashes with uncaught IndexError (rc=1) instead of rc=3."""
    sp = work / "n7_spool"
    (sp / "w001" / "closed").mkdir(parents=True)
    (sp / "w001" / "closed" / "p000000.raw").write_bytes(b"")
    (sp / "w001" / "closed" / "p000000.sha256").write_bytes(b"")
    out_dir = work / "n7_out"
    rc, out, err, _ = run_cmd([sys.executable, "-I", "-B", sd / "run" / "packer.py",
                               "--spool", sp, "--out", out_dir, "--converter", HERE / "spam_engine.py", "--once"])
    ok = rc == 3 and "Traceback" not in err
    return ok, f"rc={rc} has_traceback={'Traceback' in err} tail={(out + err).strip().splitlines()[-1:]!r} (want rc=3, no traceback)"


def case_n8(sd: Path, work: Path, _src: Path, _net: Path):
    """tools/check_run.py line 31: unanchored ERROR false-positives on path; ^sgerror  misses bare sgerror."""
    rc, out, err, _ = run_cmd([sys.executable, "-I", "-B", sd / "tools" / "check_run.py",
                               HERE / "error_path_and_bare_sgerror.transcript", "show"])
    if rc != 0:
        return False, f"rc={rc} err={err.strip()[:160]!r}"
    s = json.loads(out)
    refs = s.get("refusals", [])
    false_pos = any("NNUE v3 active" in r for r in refs)
    caught_bare = any(r.strip() == "sgerror" for r in refs)
    ok = (not false_pos) and caught_bare
    return ok, f"refusals={refs!r} (want bare 'sgerror' caught and clean NNUE path NOT flagged)"


def case_n9(sd: Path, work: Path, _src: Path, _net: Path):
    """tools/hash_tree.py lines 17-26: dangling symlink silently ignored AND overlapping subs emit duplicate entries."""
    root = work / "n9_tree"
    (root / "sub").mkdir(parents=True)
    (root / "sub" / "a.txt").write_text("hello\n", encoding="ascii")
    os.symlink("/nonexistent/neon_dangling_target", root / "sub" / "dangling")
    out_list = work / "n9_list.sha256"
    rc_sym, out_sym, err_sym, _ = run_cmd([sys.executable, "-I", "-B", sd / "tools" / "hash_tree.py",
                                           root, out_list, "sub"])
    (root / "sub" / "dangling").unlink()
    out_dup = work / "n9_dup.sha256"
    rc_dup, out_dup_s, err_dup_s, _ = run_cmd([sys.executable, "-I", "-B", sd / "tools" / "hash_tree.py",
                                               root, out_dup, "sub", "sub/a.txt"])
    dup_lines = [ln for ln in out_dup.read_text(encoding="utf-8").splitlines() if "sub/a.txt" in ln] if out_dup.exists() else []
    ok = (rc_sym != 0) and (rc_dup != 0 or len(dup_lines) == 1)
    return ok, f"dangling_symlink_rc={rc_sym} (want !=0); overlap_rc={rc_dup} sub/a.txt_entries={len(dup_lines)} (want <=1 or !=0)"


def case_n10(sd: Path, work: Path, _src: Path, _net: Path):
    """tools/make_workloads.py line 65: missing arg-count check crashes with ValueError (rc=1) instead of exit 2."""
    helper = (
        "import importlib.util, sys, types\n"
        "if 'chess' not in sys.modules:\n"
        "    try:\n"
        "        import chess\n"
        "    except ImportError:\n"
        "        sys.modules['chess'] = types.ModuleType('chess')\n"
        f"spec = importlib.util.spec_from_file_location('mw', {str(sd / 'tools' / 'make_workloads.py')!r})\n"
        "mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\n"
        "sys.argv = ['make_workloads.py']\n"
        "rc = mod.main()\n"
        "sys.exit(0 if rc is None else rc)\n"
    )
    rc, out, err, _ = run_cmd([sys.executable, "-I", "-B", "-c", helper])
    ok = rc == 2 and "Traceback" not in err
    return ok, f"rc={rc} has_traceback={'Traceback' in err} tail={(out + err).strip().splitlines()[-1:]!r} (want rc=2, no traceback)"


CASES = [
    ("N1", "linux/cpu_check.sh line 25 missing flags line", case_n1),
    ("N2", "linux/build_forge.sh unquoted $extra with space in $WORK", case_n2),
    ("N3", "run/uciproc.py line 66 deadline hang under 20 ms output", case_n3),
    ("N4", "tools/drive.py line 66 step-limit hang under 20 ms output", case_n4),
    ("N5", "tools/drive.py line 43 missing exe FileNotFoundError", case_n5),
    ("N6", "run/record.py lines 44-48 bind omits opening on openingend", case_n6),
    ("N7", "run/packer.py line 114 empty .sha256 uncaught IndexError", case_n7),
    ("N8", "tools/check_run.py line 31 ERROR path false positive & bare sgerror miss", case_n8),
    ("N9", "tools/hash_tree.py lines 17-26 dangling symlink & duplicate subs", case_n9),
    ("N10", "tools/make_workloads.py line 65 missing argc check ValueError", case_n10),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scripts_dir")
    ap.add_argument("work_dir")
    ap.add_argument("--source", default=str(REPO / "loop" / "source"))
    ap.add_argument("--net", default=str(REPO / "loop" / "forge65_r0067.fnn3"))
    ap.add_argument("extra", nargs="*")
    a = ap.parse_args()
    only = set()
    for ex in a.extra:
        if not ex.startswith("only="):
            print(f"STOP: not understood: {ex}")
            return 2
        only |= set(ex[5:].split(","))
    sd, work = Path(a.scripts_dir).resolve(), Path(a.work_dir).resolve()
    if not sd.is_dir() or work.exists():
        print("STOP: scripts_dir must exist and work_dir must be a NEW folder")
        return 2
    work.mkdir(parents=True)
    src, net = Path(a.source).resolve(), Path(a.net).resolve()
    passed = failed = 0
    for cid, desc, fn in CASES:
        if only and cid not in only:
            continue
        ok, detail = fn(sd, work, src, net)
        print(f"{'PASS' if ok else 'FAIL'} {cid} ({desc}): {detail}", flush=True)
        passed += int(ok)
        failed += int(not ok)
    print(f"SUMMARY: {passed} PASS, {failed} FAIL (expected on v1: 0 PASS, {passed + failed} FAIL)")
    return 0 if failed == 0 and passed > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
