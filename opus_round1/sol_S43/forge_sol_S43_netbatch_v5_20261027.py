#!/usr/bin/env python3
"""S43: S26 net-pack batch add-on for the PC (Opus 5.5 for Sol's S43, 2026-10-27).

Sol's S26 v4 kit (`forge_sol_S26_netbatch_v4_20261026.py`) is Linux-only (flock, nice, sched affinity, setsid, GCC 14
box recipe). This v5 is a new PC-native file with the S43 requirements; Sol's files are not edited:
  --base <dir>          any source tree (relative or absolute on the command line; resolved ONCE to an absolute real
                        path at start, so applying the tool to a new base needs no path edits)
  --bench-ref <FILE>    Sol's `forge-s26-bench-refs-v1` JSON (bench nodes per depth, keyed by net sha256), unchanged
  ABSOLUTE PATHS        every output, log, build product, junit file and subprocess argument that is a path is
                        absolute; every subprocess gets an explicit absolute cwd (a relative ctest path once aborted
                        ctest with exit 2: ctest resolves a relative --output-junit against the test dir, not the cwd)
Per net: private copy of the base under the NEW --out (the base is never modified), the net copied into
src/nnue_weights.inc, the PC lock recipe build (MSYS2 ucrt64 g++: -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256
-ffp-contract=off -fno-fast-math -march=znver5 -static -pthread), whole-binary FMA count (objdump), bench
d11/13/16/20/22 (one UCI process, Threads=1 Hash=16 OwnBook=false) against the reference file, optional perft 5 +
kiwipete, optional CMake+Ninja build and CTest with Sol's allowlist JSON (forge-s26-allowlist-v1).
Everything runs at Idle priority, one process at a time, single-threaded builds; free RAM is checked before each step.
Exit 0 only when every net builds, has FMA 0, matches every bench reference and (with --ctest) has no unexpected failure.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

DATE = "20261027"
TOOL = "forge_sol_S43_netbatch_v5_" + DATE
DEPTHS = (11, 13, 16, 20, 22)
RECIPE = ["-std=c++20", "-O3", "-DNDEBUG", "-DFORGE_NNUE_HIDDEN=256", "-ffp-contract=off", "-fno-fast-math",
          "-march=znver5", "-static", "-pthread", "-Iinclude"]
SRCS = ["src/bitboard.cpp", "src/board.cpp", "src/book.cpp", "src/eval.cpp", "src/eval_params.cpp", "src/nnue.cpp",
        "src/search.cpp", "src/uci.cpp"]
UCRT = r"C:\msys64\ucrt64\bin"
VSCM = r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake"
CMAKE_FLAGS = "-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
PERFT_REF = {"startpos": 4865609, "kiwipete": 193690690}
FMA_RE = re.compile(r"\bvfn?m(?:add|sub)")
IDLE = 0x40


class Fail(Exception):
    pass


def absolute(p):
    """Resolve once: relative paths are taken against the cwd at start; symlinks/junctions resolved."""
    return Path(os.path.realpath(os.path.abspath(str(p))))


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def free_gib():
    if os.name != "nt":
        try:
            for line in open("/proc/meminfo"):
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / (1 << 20)
        except OSError:
            return 1e9
    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong),
                    ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
    m = MS(); m.dwLength = ctypes.sizeof(MS); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys / (1 << 30)


def command(value, default):
    """A tool given as a path or as a JSON list (the tests use ["python", "-I", "-B", "fake.py"])."""
    v = value if value is not None else default
    if isinstance(v, str) and v.strip().startswith("["):
        lst = json.loads(v)
        return [str(absolute(lst[0])) if os.path.exists(lst[0]) else lst[0]] + \
               [str(absolute(x)) if (x.endswith(".py") and os.path.exists(x)) else x for x in lst[1:]]
    return [str(absolute(v))]


class Runner:
    def __init__(self, out, min_free, env_path, timeout):
        self.out, self.min_free, self.timeout = out, min_free, timeout
        self.env = dict(os.environ, PATH=os.pathsep.join(env_path + [os.environ.get("PATH", "")]))
        self.steps = []

    def run(self, argv, cwd, label, timeout=None, accept=(0,)):
        if free_gib() < self.min_free:
            raise Fail(f"free RAM {free_gib():.1f} GiB < {self.min_free} GiB before {label}")
        cwd = Path(cwd)
        assert cwd.is_absolute(), cwd
        so, se = self.out / "logs" / f"{label}.stdout.txt", self.out / "logs" / f"{label}.stderr.txt"
        kw = {"creationflags": IDLE} if os.name == "nt" else {"preexec_fn": lambda: os.nice(19)}
        t0 = time.monotonic()
        with open(so, "xb") as fo, open(se, "xb") as fe:
            p = subprocess.run(argv, cwd=str(cwd), env=self.env, stdout=fo, stderr=fe, timeout=timeout or self.timeout, **kw)
        rec = {"label": label, "argv": argv, "cwd": str(cwd), "returncode": p.returncode, "seconds": round(time.monotonic() - t0, 1),
               "stdout": str(so), "stderr": str(se)}
        self.steps.append(rec)
        if p.returncode not in accept:
            raise Fail(f"{label} failed with exit {p.returncode} (see {se})")
        return rec


SKIP_DIRS = {".git", "__pycache__", "artifacts", "build", "build_release", "build_debug", "cmake_build"}


def copy_tree(base, dst):
    """Copy the source tree minus VCS/build products. Exact, case-SENSITIVE names: shutil.ignore_patterns is
    case-insensitive on Windows, and a pattern like 'cmake*' would silently drop CMakeLists.txt."""
    def skip(directory, names):
        out = set()
        for n in names:
            full = os.path.join(directory, n)
            if os.path.isdir(full) and (n in SKIP_DIRS or n.startswith("build_") or n.startswith("cmake-build")):
                out.add(n)
            elif os.path.isfile(full) and n.endswith((".exe", ".o", ".obj")):
                out.add(n)
        return out
    shutil.copytree(base, dst, ignore=skip)
    if (Path(base) / "CMakeLists.txt").exists() and not (Path(dst) / "CMakeLists.txt").exists():
        raise Fail("private copy lost CMakeLists.txt")


def uci_session(cmd, cwd, depths, perft, timeout):
    """One engine process: bench at every depth, then optional perft. Waits for real output lines."""
    kw = {"creationflags": IDLE} if os.name == "nt" else {}
    p = subprocess.Popen(cmd, cwd=str(cwd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         text=True, bufsize=1, **kw)
    t0 = time.monotonic(); transcript = []

    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush(); transcript.append("> " + s)

    def wait(pat):
        rx = re.compile(pat)
        for line in p.stdout:
            transcript.append(line.rstrip("\n"))
            m = rx.search(line)
            if m:
                return m
            if time.monotonic() - t0 > timeout:
                break
        raise Fail(f"engine output ended before /{pat}/")

    try:
        send("uci"); wait(r"^uciok")
        for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
            send("setoption name " + o)
        send("isready"); wait(r"^readyok")
        bench = {}
        for d in depths:
            send(f"bench {d}"); bench[d] = int(wait(rf"bench depth {d} nodes (\d+)").group(1))
        perfts = {}
        if perft:
            for name, pos in (("startpos", "position startpos"), ("kiwipete", "position fen " + KIWI)):
                send(pos); send("go perft 5"); perfts[name] = int(wait(r"^nodes (\d+)").group(1))
        send("quit")
        p.wait(timeout=60)
    finally:
        if p.poll() is None:
            p.kill()  # only our own engine child, started above
    return bench, perfts, transcript


def load_refs(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "forge-s26-bench-refs-v1" or not isinstance(data.get("nets"), dict):
        raise Fail("bench-ref FILE must use Sol's forge-s26-bench-refs-v1 schema")
    return data


def check_ctest_output(text, junit, allow, tests_sha):
    """Sol's allowlist: only the allowed test may fail; each FAIL/KNOWN line must match a rule within its max counts."""
    failed = []
    if junit.exists():
        root = ET.parse(junit).getroot()
        for tc in root.iter("testcase"):
            if tc.find("failure") is not None or tc.get("status") == "fail":
                failed.append(tc.get("name"))
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith(("FAIL:", "KNOWN_FAILURE:"))]
    counts, unknown = {}, []
    for l in lines:
        for r in allow["rules"]:
            if re.fullmatch(r["pattern"], l) or re.match(r["pattern"], l):
                counts[r["pattern"]] = counts.get(r["pattern"], 0) + 1; break
        else:
            unknown.append(l)
    over = [p for p, c in counts.items() if c > next(r["max_count"] for r in allow["rules"] if r["pattern"] == p)]
    unexpected_tests = [t for t in failed if t != allow.get("allowed_test_failure")]
    status = "PASS" if not unknown and not over and not unexpected_tests and len(lines) <= allow.get("max_total", 0) else "FAIL"
    return {"status": status, "failed_tests": failed, "fail_lines": lines, "unknown_lines": unknown, "over_max": over,
            "unexpected_failed_tests": unexpected_tests, "tests_cpp_sha256": tests_sha,
            "tests_cpp_bound_in_allowlist": tests_sha in allow.get("test_source_sha256", [])}


def one_net(a, run, refs, allow, idx, net):
    net_sha = sha256(net); job = a.out / f"net_{idx:02d}_{net_sha[:12]}"; job.mkdir()
    tree = job / "src_tree"; copy_tree(a.base, tree)
    shutil.copyfile(net, tree / "src" / "nnue_weights.inc")
    if sha256(tree / "src" / "nnue_weights.inc") != net_sha:
        raise Fail("net copy mismatch")
    row = {"net": str(net), "net_sha256": net_sha, "net_md5": md5(net), "job_dir": str(job), "private_tree": str(tree),
           "tests_cpp_sha256": sha256(tree / "tests" / "tests.cpp") if (tree / "tests" / "tests.cpp").exists() else None}
    exe = job / "forge.exe"
    run.run(a.gpp + RECIPE + list(a.extra_flag or []) + SRCS + ["-o", str(exe)], tree, f"net{idx:02d}_build", timeout=a.build_timeout)
    row["exe"] = str(exe); row["exe_sha256"] = sha256(exe)
    dump = run.run(a.objdump + ["-d", str(exe)], job, f"net{idx:02d}_objdump")
    with open(dump["stdout"], encoding="utf-8", errors="replace") as f:
        row["fma_count"] = sum(1 for line in f if FMA_RE.search(line))
    t0 = time.monotonic()
    bench, perfts, transcript = uci_session(a.launcher + [str(exe)], job, DEPTHS, a.perft, a.uci_timeout)
    (job / "uci_transcript.txt").write_text("\n".join(transcript) + "\n", encoding="utf-8")
    row["bench_seconds"] = round(time.monotonic() - t0, 1)
    ref = refs["nets"].get(net_sha)
    row["bench"] = {str(d): bench[d] for d in DEPTHS}
    if ref is None:
        row["bench_ref"] = None; row["bench_status"] = "NO_REFERENCE"
    else:
        exp = {str(d): int(ref["bench"][str(d)]) for d in DEPTHS}
        row["bench_ref"] = {"id": ref.get("id"), **exp}
        row["bench_cmp"] = {str(d): ("MATCH" if bench[d] == exp[str(d)] else f"MISMATCH ref {exp[str(d)]}") for d in DEPTHS}
        row["bench_status"] = "PASS" if all(v == "MATCH" for v in row["bench_cmp"].values()) else "PIN_MISMATCH"
    if a.perft:
        row["perft"] = perfts; row["perft_status"] = "PASS" if perfts == PERFT_REF else "MISMATCH"
    if a.ctest:
        bd = job / "cmake_build"; junit = job / "ctest_junit.xml"
        flags = ["-S", str(tree), "-B", str(bd), "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_CXX_COMPILER={a.gpp[0]}",
                 f"-DCMAKE_CXX_FLAGS={CMAKE_FLAGS}", "-DCMAKE_EXE_LINKER_FLAGS=-static"]
        if a.python3:
            flags.append(f"-DPython3_EXECUTABLE={a.python3}")
        run.run(a.cmake + flags, job, f"net{idx:02d}_cmake_configure", timeout=a.build_timeout)
        run.run(a.cmake + ["--build", str(bd), "-j", "1"], job, f"net{idx:02d}_cmake_build", timeout=a.build_timeout * 4)
        rec = run.run(a.ctest_cmd + ["--test-dir", str(bd), "--output-on-failure", "--no-tests=error", "--timeout", str(a.ctest_timeout),
                                 "--output-junit", str(junit)], job, f"net{idx:02d}_ctest", timeout=a.ctest_timeout * 4, accept=(0, 8))
        text = Path(rec["stdout"]).read_text(encoding="utf-8", errors="replace")
        row["ctest"] = check_ctest_output(text, junit, allow, row["tests_cpp_sha256"]) if allow else {"status": "NO_ALLOWLIST"}
        row["ctest"].update({"returncode": rec["returncode"], "junit": str(junit), "junit_exists": junit.exists()})
    ok = row["fma_count"] == 0 and row["bench_status"] == "PASS" and (not a.perft or row["perft_status"] == "PASS") \
        and (not a.ctest or row["ctest"]["status"] == "PASS")
    row["status"] = "PASS" if ok else "FAIL"
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True); ap.add_argument("--net", action="append", required=True)
    ap.add_argument("--bench-ref", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--allowlist"); ap.add_argument("--ctest", action="store_true"); ap.add_argument("--perft", action="store_true")
    ap.add_argument("--gpp"); ap.add_argument("--objdump"); ap.add_argument("--launcher", default="[]")
    ap.add_argument("--cmake"); ap.add_argument("--ctest-exe"); ap.add_argument("--python3")
    ap.add_argument("--extra-flag", action="append", help="extra g++ flag for the box build (e.g. -DFORGE_X=1)")
    ap.add_argument("--min-free-ram-gib", type=float, default=6.0); ap.add_argument("--build-timeout", type=float, default=3600)
    ap.add_argument("--uci-timeout", type=float, default=1800); ap.add_argument("--ctest-timeout", type=float, default=900)
    a = ap.parse_args(argv)
    cwd0 = os.getcwd(); given = {"base": a.base, "net": list(a.net), "bench_ref": a.bench_ref, "out": a.out, "allowlist": a.allowlist}
    a.base = absolute(a.base); a.net = [absolute(n) for n in a.net]; a.bench_ref = absolute(a.bench_ref); a.out = absolute(a.out)
    a.allowlist = absolute(a.allowlist) if a.allowlist else None
    a.gpp = command(a.gpp, os.path.join(UCRT, "g++.exe")); a.objdump = command(a.objdump, os.path.join(UCRT, "objdump.exe"))
    a.launcher = json.loads(a.launcher) if a.launcher.strip().startswith("[") else [a.launcher]
    a.launcher = [str(absolute(x)) if os.path.exists(x) else x for x in a.launcher]
    a.cmake = command(a.cmake, os.path.join(VSCM, "CMake", "bin", "cmake.exe")); a.ctest_cmd = command(a.ctest_exe, os.path.join(VSCM, "CMake", "bin", "ctest.exe"))
    a.python3 = str(absolute(a.python3)) if a.python3 else None
    try:
        if not (a.base / "src").is_dir() or not (a.base / "include").is_dir():
            raise Fail(f"--base {a.base} is not a Forge source tree (src/, include/)")
        for n in a.net:
            if not n.is_file():
                raise Fail(f"--net {n} not found")
        if a.out.exists() and any(a.out.iterdir()):
            raise Fail(f"--out {a.out} exists and is not empty (never overwritten)")
        for inp in [a.base] + [n.parent for n in a.net]:
            if str(a.out).lower().startswith(str(inp).lower().rstrip("\\/") + os.sep):
                raise Fail("--out may not lie inside an input directory")
        refs = load_refs(a.bench_ref)
        allow = json.loads(a.allowlist.read_text(encoding="utf-8")) if a.allowlist else None
        a.out.mkdir(parents=True, exist_ok=True); (a.out / "logs").mkdir()
        try:
            k = ctypes.windll.kernel32; k.SetPriorityClass(k.GetCurrentProcess(), IDLE)
        except Exception:
            pass
        base_hash_before = tree_hash(a.base)
        run = Runner(a.out, a.min_free_ram_gib, [UCRT, os.path.join(VSCM, "CMake", "bin"), os.path.join(VSCM, "Ninja")], a.build_timeout)
        rows = []
        for i, net in enumerate(a.net, start=1):
            try:
                rows.append(one_net(a, run, refs, allow, i, net))
            except Fail as exc:
                rows.append({"net": str(net), "status": "FAIL", "failure": str(exc)})
        base_unchanged = tree_hash(a.base) == base_hash_before
        res = {"tool": TOOL, "tool_sha256": sha256(__file__), "cwd_at_start": cwd0, "arguments_as_given": given,
               "arguments_resolved": {"base": str(a.base), "net": [str(n) for n in a.net], "bench_ref": str(a.bench_ref),
                                      "bench_ref_sha256": sha256(a.bench_ref), "out": str(a.out),
                                      "allowlist": str(a.allowlist) if a.allowlist else None, "gpp": a.gpp, "objdump": a.objdump},
               "recipe": RECIPE + SRCS, "base_tree_sha256": base_hash_before, "base_unchanged": base_unchanged,
               "nets": rows, "steps": run.steps, "python": sys.version.split()[0], "platform": platform.platform(),
               "status": "PASS" if rows and all(r["status"] == "PASS" for r in rows) and base_unchanged else "FAIL"}
        (a.out / "netbatch_result.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        md = ["| net | sha256 | exe sha256 | FMA | " + " | ".join(f"d{d}" for d in DEPTHS) + " | bench | ctest | status |",
              "|---|---|---|---|" + "---|" * len(DEPTHS) + "---|---|---|"]
        for r in rows:
            if "bench" not in r:
                md.append(f"| {Path(r['net']).name} | | | | " + " | " * len(DEPTHS) + f" | | {r['status']}: {r.get('failure', '')} |"); continue
            md.append(f"| {Path(r['net']).name} | {r['net_sha256'][:12]} | {r['exe_sha256'][:12]} | {r['fma_count']} | "
                      + " | ".join(f"{r['bench'][str(d)]}" + ("" if r.get('bench_cmp', {}).get(str(d), 'MATCH') == 'MATCH' else " (!)") for d in DEPTHS)
                      + f" | {r['bench_status']} | {r.get('ctest', {}).get('status', 'not run')} | {r['status']} |")
        (a.out / "netbatch_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(json.dumps({"status": res["status"], "out": str(a.out), "nets": [{k: r.get(k) for k in ("net_sha256", "bench", "bench_status", "fma_count", "status")} for r in rows]}, indent=1))
        return 0 if res["status"] == "PASS" else 1
    except Fail as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


def tree_hash(root):
    h = hashlib.sha256()
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            h.update(p.relative_to(root).as_posix().encode() + b"\0" + sha256(p).encode() + b"\n")
    return h.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
