"""Neon 2026-11-23, server-day plan (SETUP_PLAN.md D10, N16, section 7 row 5):
Linux multi-variant C++ build, strict known-answer verification, and D10/N16 plain-vs-profiled comparator.
Standard library only (`python3 -I -B`).

Addresses every finding against v1 `linux/build_forge.sh`:
- Pure Python argv execution (zero shell word-splitting on spaced paths);
- Pre-flight ISA/affinity verification via sibling `machine_check.py` (every affinity CPU checked);
- Strict symlink-refusing `SOURCE.sha256` tree verification before any compile;
- Supports both `g++` (GCC PGO + `-flto=auto`) and `clang++` (`-flto=thin` + optional LLVM PGO);
- Builds plain comparator AND profiled variants in clean isolated directories (`plain_o3`, `plain_o3_lto`,
  `pgo_nolto`, `pgo_lto`);
- Drives `profile.uci`, `verify.uci`, `startup.uci`, AND `n12_batch.uci` (all 6 fixed games) with a steady
  per-line timeout, printable-ASCII enforcement, strict 4-form `info string` allow-list, and exact comparison
  against `known/{profile,verify,startup,n12_batch}.json`;
- Requires every compiled unit to produce a non-empty `.gcda` file (not merely >= 1 file), compiles pass 2
  with `-Werror=missing-profile -Werror=coverage-mismatch`, and refuses any profile/coverage compiler warning;
- Optional interleaved multi-worker self-play benchmark (never `bench`) verifying bit-identical game digests
  across every built binary and classifying the D10/N16 three-way outcome;
- Planted failure modes (`bad_source_hash`, `profile_error`, `missing_profile`, `other_source`);
- Writes canonical ASCII JSON (`build_report.json`, no floats) inside a NEW `--work-dir`; sets `TMPDIR`
  inside `--work-dir` and writes nothing outside it.

Exit codes: 0 = built & verified, 1 = build/check failed (or planted fault caught/uncaught), 2 = bad arguments.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import machine_check  # noqa: E402

COMMON_FLAGS = [
    "-std=c++20", "-O3", "-DNDEBUG",
    "-DFORGE_NNUE_HIDDEN=256", "-DFORGE_EXPOSE_TUNABLES=1",
    "-DFORGE_SPD_TT_NOTLS=1", "-DFORGE_SPD_NO_ZERO_MOVELISTS=2",
    "-DFORGE_SEARCH_SPEED2=1", "-DFORGE_SPD_PREFETCH_EARLY=1",
    "-DFORGE_MATE_ALPHA_GUARD=1", "-DFORGE_NNUE_V3=1",
    "-ffp-contract=off", "-fno-fast-math", "-pthread",
]

ARCH_FLAGS = {
    "v4": ["-march=x86-64-v4", "-DFORGE_SPD_SLIDER_PEXT=1", "-DFORGE_SPD_NNUE_ZMM=1"],
    "avx2_pext": ["-march=x86-64-v3", "-DFORGE_SPD_SLIDER_PEXT=1", "-DFORGE_SPD_NNUE_ZMM=0"],
    "avx2_nobmi2": ["-march=x86-64-v2", "-mavx2", "-mno-bmi2", "-DFORGE_SPD_SLIDER_PEXT=0", "-DFORGE_SPD_NNUE_ZMM=0"],
    "scalar_verify": ["-march=x86-64", "-DFORGE_SPD_SLIDER_PEXT=0", "-DFORGE_SPD_NNUE_ZMM=0", "-DFORGE_NNUE_V3_VERIFY=1"],
}

VALID_MODES = ("plain_o3", "plain_o3_lto", "pgo_nolto", "pgo_lto")
VALID_PLANTS = ("none", "bad_source_hash", "profile_error", "missing_profile", "other_source")
COMPARED_KEYS = ("bench", "perft", "eval", "net", "search", "games", "totals", "refusals", "drive")
MAX_LINE = 65536

# Strict whole-line allow-list matching loop/source/src/{uci,nnue_v3}.cpp
_INFO_ALLOWED_RES = (
    re.compile(r"^NNUE v3 (loaded|active): v3 .+ hidden \d+ king_buckets \d+ .*checksum [0-9a-f]+ .*kernel \S+$"),
    re.compile(r"^eval hce -?\d+ nnue -?\d+ total -?\d+(?: incheck 1)?$"),
    re.compile(r"^bench depth \d+ nodes \d+ time \d+ nps \d+$"),
)
_OTHER_ALLOWED_RE = re.compile(
    r"^(?:"
    r"sg \d+ -?\d+ [a-h][1-8][a-h][1-8][qrbn]? \S+ [wb] \S+ \S+ \d+ \d+"
    r"|sgend result (?:-1|0|1) reason \S+ plies \d+ .+"
    r"|info depth \d+ .+"
    r"|bestmove [a-h][1-8][a-h][1-8][qrbn]?(?: ponder [a-h][1-8][a-h][1-8][qrbn]?)?"
    r"|readyok|uciok"
    r"|id (?:name|author) .+"
    r"|option name .+ type (?:check|spin|string|button|combo).*"
    r"|[a-h][1-8][a-h][1-8][qrbn]?: \d+"
    r"|nodes \d+"
    r"|)$"
)


def why_line_bad(line: str) -> str:
    if any(ord(c) < 0x20 or ord(c) > 0x7e for c in line):
        return f"non-printable or non-ASCII character: {line[:120]!r}"
    if line.startswith("info string "):
        rest = line[12:]
        if any(rx.fullmatch(rest) for rx in _INFO_ALLOWED_RES):
            return ""
        return f"unexpected info string: {line[:200]}"
    if line.startswith("sgerror"):
        return f"engine sgerror: {line[:200]}"
    if _OTHER_ALLOWED_RE.fullmatch(line):
        return ""
    return f"unexpected engine line: {line[:200]}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_tree_strict(root: Path, subdirs: list) -> str:
    """Hash regular files under subdirs, refusing symlinks, dangling links, special files, and duplicates."""
    seen = set()
    files = []
    for sub in subdirs:
        base = root / sub
        if os.path.islink(str(base)):
            raise ValueError(f"symlink refused in tree: {base}")
        if not base.is_dir():
            raise ValueError(f"missing directory in tree: {base}")
        for dirpath, dirnames, filenames in os.walk(str(base), followlinks=False):
            dp = Path(dirpath)
            for d in list(dirnames):
                fp = dp / d
                if os.path.islink(str(fp)):
                    raise ValueError(f"symlink directory refused: {fp}")
            for fn in filenames:
                fp = dp / fn
                if os.path.islink(str(fp)):
                    raise ValueError(f"symlink file refused: {fp}")
                st = os.lstat(str(fp))
                if not os.path.isfile(str(fp)) or (st.st_mode & 0o170000) != 0o100000:
                    raise ValueError(f"non-regular file refused: {fp}")
                rel = fp.relative_to(root).as_posix()
                if rel in seen:
                    raise ValueError(f"duplicate path in tree: {rel}")
                seen.add(rel)
                files.append((rel, fp))
    files.sort(key=lambda x: x[0])
    rows = [f"{sha256_file(fp)}  {rel}" for rel, fp in files]
    body = ("\n".join(rows) + "\n").encode("ascii")
    rows.append("digest " + hashlib.sha256(body).hexdigest())
    return "\n".join(rows) + "\n"


def copy_tree_strict(src: Path, dst: Path, subdirs: list) -> None:
    """Copy regular files only (no symlinks) preserving directory layout."""
    for sub in subdirs:
        base = src / sub
        if os.path.islink(str(base)) or not base.is_dir():
            raise ValueError(f"source subdir invalid or symlink: {base}")
        for dirpath, dirnames, filenames in os.walk(str(base), followlinks=False):
            dp = Path(dirpath)
            rel_dir = dp.relative_to(src)
            (dst / rel_dir).mkdir(parents=True, exist_ok=True)
            for d in dirnames:
                if os.path.islink(str(dp / d)):
                    raise ValueError(f"symlink dir in source: {dp / d}")
            for fn in filenames:
                fp = dp / fn
                if os.path.islink(str(fp)):
                    raise ValueError(f"symlink file in source: {fp}")
                shutil.copy2(str(fp), str(dst / rel_dir / fn))


def run_uci_workload(exe: Path, commands: list, step_s: float, work_tmp: Path, transcript: Path,
                     run_cwd: Path = None) -> tuple:
    """Run UCI commands against exe with steady per-line timeout and strict printable-ASCII + allow-list checks."""
    env = dict(os.environ)
    env["TMPDIR"] = str(work_tmp)
    p = subprocess.Popen(
        [str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, cwd=str(run_cwd or work_tmp), env=env,
    )
    q: "queue.Queue" = queue.Queue(maxsize=200000)
    stop_flag = False

    def reader():
        try:
            while not stop_flag:
                raw = p.stdout.readline(MAX_LINE + 1)
                if not raw:
                    break
                if len(raw) > MAX_LINE and not raw.endswith(b"\n"):
                    q.put(("ERR", f"line longer than {MAX_LINE} bytes"))
                    break
                if not raw.endswith(b"\n"):
                    q.put(("ERR", f"unterminated line at EOF: {raw[:80]!r}"))
                    break
                body = raw[:-1]
                if body.endswith(b"\r"):
                    body = body[:-1]
                if any(b < 0x20 or b > 0x7e for b in body):
                    q.put(("ERR", f"non-printable/non-ASCII byte in line: {body[:120]!r}"))
                    break
                q.put(("LINE", body.decode("ascii")))
        except (OSError, ValueError) as e:
            q.put(("ERR", f"reader error: {e}"))
        finally:
            q.put(("EOF", ""))

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    out_lines = []
    segs = []
    refusals = []
    drive_err = ""
    engine_rc = None

    def send_cmd(cmd: str) -> None:
        if any(ord(c) < 0x20 or ord(c) > 0x7e for c in cmd):
            raise RuntimeError(f"invalid command characters: {cmd[:80]!r}")
        out_lines.append(">>> " + cmd)
        p.stdin.write((cmd + "\n").encode("ascii"))
        p.stdin.flush()

    def read_until(done_fn, what: str) -> list:
        deadline = time.monotonic() + step_s
        got = []
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise RuntimeError(f"timeout ({step_s}s) waiting for {what}")
            try:
                kind, val = q.get(timeout=left)
            except queue.Empty:
                raise RuntimeError(f"timeout ({step_s}s) waiting for {what}") from None
            if kind == "ERR":
                raise RuntimeError(f"{what}: {val}")
            if kind == "EOF":
                raise RuntimeError(f"{what}: engine closed stdout unexpectedly")
            out_lines.append(val)
            got.append(val)
            bad = why_line_bad(val)
            if bad:
                refusals.append(val[:200])
                if val.startswith("sgerror"):
                    raise RuntimeError(f"{what}: {bad}")
            if done_fn(val):
                return got

    try:
        for raw_cmd in commands:
            cmd = raw_cmd.strip()
            if not cmd or cmd.startswith("#"):
                continue
            head = cmd.split()[0]
            if head == "quit":
                send_cmd("quit")
                break
            send_cmd(cmd)
            if head == "uci":
                got = read_until(lambda s: s == "uciok", "uci")
            elif head == "isready":
                got = read_until(lambda s: s == "readyok", "isready")
            elif head == "go" and len(cmd.split()) >= 2 and cmd.split()[1] == "perft":
                send_cmd("isready")
                got = read_until(lambda s: s == "readyok", cmd)[:-1]
            elif head == "go":
                got = read_until(lambda s: s.startswith("bestmove"), cmd)
            elif head == "selfgame":
                got = read_until(lambda s: s.startswith("sgend "), cmd)
            else:
                send_cmd("isready")
                got = read_until(lambda s: s == "readyok", cmd)[:-1]
            segs.append((cmd, got))
        try:
            p.stdin.close()
        except OSError:
            pass
        engine_rc = p.wait(timeout=min(30.0, step_s))
    except Exception as e:  # noqa: BLE001
        drive_err = str(e)
        if p.poll() is None:
            try:
                p.kill()
            except OSError:
                pass
        try:
            engine_rc = p.wait(timeout=10.0)
        except subprocess.TimeoutExpired:
            engine_rc = "timeout"
    finally:
        stop_flag = True
        try:
            if p.stdin and not p.stdin.closed:
                p.stdin.close()
        except OSError:
            pass
        t.join(timeout=5.0)
        if not t.is_alive():
            try:
                if p.stdout and not p.stdout.closed:
                    p.stdout.close()
            except OSError:
                pass

    drive_rc = 0 if (not drive_err and not refusals and engine_rc == 0) else 1
    tail = f"### drive.py: exit {drive_rc}; engine exit code {engine_rc}; err={drive_err}"
    out_lines.append(tail)
    transcript.write_bytes(("\n".join(out_lines) + "\n").encode("ascii", errors="replace"))

    summary = summarize_segs(segs, refusals, drive_rc, str(engine_rc))
    return drive_rc == 0, summary, drive_err


def summarize_segs(segs: list, refusals: list, drive_rc: int, engine_rc_str: str) -> dict:
    s = {
        "bench": [], "perft": [], "eval": [], "net": [], "net_kernel": [],
        "search": [], "games": [], "refusals": list(refusals), "commands": len(segs),
    }
    all_sg = hashlib.sha256()
    rows = searches = nodes = 0
    position = ""
    for cmd, lines in segs:
        if cmd.startswith("position "):
            position = cmd
        for ln in lines:
            m = re.match(r"info string bench depth (\d+) nodes (\d+)", ln)
            if m:
                s["bench"].append([int(m[1]), int(m[2])])
            m = re.match(r"info string eval hce (-?\d+) nnue (-?\d+) total (-?\d+)", ln)
            if m:
                s["eval"].append([int(m[1]), int(m[2]), int(m[3])])
            if ln.startswith("info string NNUE v3 active:"):
                m = re.search(r" hidden (\d+) king_buckets (\d+).* checksum ([0-9a-f]+) ", ln)
                k = re.search(r" kernel (\S+)", ln)
                s["net"].append([int(m[1]), int(m[2]), m[3]] if m else ["unreadable", ln[:120]])
                s["net_kernel"].append(k[1] if k else "")
        head = cmd.split()[0]
        if cmd.startswith("go perft "):
            got = [int(ln.split()[1]) for ln in lines if re.fullmatch(r"nodes \d+", ln)]
            s["perft"].append([position, int(cmd.split()[2]), got[-1] if got else None])
        elif head == "go":
            last, best = None, None
            for ln in lines:
                if ln.startswith("info ") and " depth " in ln and " nodes " in ln and " hashfull " in ln:
                    t = ln.split()
                    last = [int(t[t.index("depth") + 1]), int(t[t.index("nodes") + 1]), int(t[t.index("hashfull") + 1])]
                if ln.startswith("bestmove"):
                    best = ln.split()[1] if len(ln.split()) > 1 else ""
            s["search"].append([*(last or [None, None, None]), best])
        elif head == "selfgame":
            sg = [ln for ln in lines if ln.startswith("sg ")]
            end = [ln for ln in lines if ln.startswith("sgend ")]
            for ln in sg + end:
                all_sg.update((ln + "\n").encode("ascii"))
            if len(end) != 1:
                s["games"].append([len(sg), "NO sgend LINE" if not end else "MORE THAN ONE sgend LINE", ""])
                continue
            t = end[0].split()
            res_tok = t[t.index("result") + 1]
            h = hashlib.sha256()
            for ln in sg:
                h.update((ln + " " + res_tok + "\n").encode("ascii"))
            s["games"].append([len(sg), end[0], h.hexdigest()])
            rows += len(sg)
            searches += int(t[t.index("searches") + 1])
            nodes += int(t[t.index("nodes") + 1])
    s["totals"] = {
        "games": len(s["games"]), "rows": rows, "searches": searches, "nodes": nodes,
        "sg_sha256": all_sg.hexdigest() if s["games"] else "",
    }
    s["drive"] = [drive_rc, engine_rc_str]
    return s


def compare_known(summary: dict, known_path: Path) -> list:
    known = json.loads(known_path.read_text(encoding="ascii"))
    diffs = []
    if summary["drive"] != [0, "0"]:
        diffs.append(f"drive={summary['drive']}")
    if summary["refusals"]:
        diffs.append(f"refusals={summary['refusals'][:3]}")
    for k in COMPARED_KEYS:
        if summary[k] != known[k]:
            diffs.append(f"{k} mismatch")
    return diffs


def check_workload(exe: Path, wl_file: Path, known_file: Path, net: Path, step_s: float,
                   work_tmp: Path, transcript: Path, extra_cmd: str = "", run_cwd: Path = None) -> tuple:
    cmds = [ln.replace("@@NET@@", str(net)) for ln in wl_file.read_text(encoding="utf-8").splitlines()]
    if extra_cmd:
        cmds.insert(1, extra_cmd)
    ok, summ, err = run_uci_workload(exe, cmds, step_s, work_tmp, transcript, run_cwd=run_cwd)
    diffs = compare_known(summ, known_file)
    if err:
        diffs.insert(0, f"driver: {err}")
    return (ok and not diffs), diffs, summ


def compile_units(cxx: str, flags: list, mdir: Path, units: list, pass_name: str, jobs: int) -> tuple:
    env = dict(os.environ)
    env["TMPDIR"] = "tmp"
    obj_dir = mdir / "obj"
    log_dir = mdir / "logs"
    for f in obj_dir.glob("*.o"):
        f.unlink()

    def one(u: str) -> tuple:
        cmd = [cxx, *flags, "-Isource/include", "-c", f"source/src/{u}.cpp", "-o", f"obj/{u}.o"]
        p = subprocess.run(cmd, cwd=str(mdir), capture_output=True, text=True, env=env, check=False)
        log = (p.stdout or "") + (p.stderr or "")
        (log_dir / f"{pass_name}_{u}.log").write_text(log, encoding="utf-8", errors="replace")
        return u, p.returncode, log

    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        for u, rc, log in pool.map(one, units):
            if rc != 0:
                first = next((ln for ln in log.splitlines() if "error" in ln.lower()), log[:200])
                errors.append(f"{u}.cpp rc={rc}: {first[:200]}")
    return len(errors) == 0, errors


def link_binary(cxx: str, flags: list, mdir: Path, units: list, out_rel: str, log_file: Path) -> tuple:
    env = dict(os.environ)
    env["TMPDIR"] = "tmp"
    objs = [f"obj/{u}.o" for u in units]
    cmd = [cxx, *flags, *objs, "-o", out_rel]
    p = subprocess.run(cmd, cwd=str(mdir), capture_output=True, text=True, env=env, check=False)
    log = (p.stdout or "") + (p.stderr or "")
    log_file.write_text(log, encoding="utf-8", errors="replace")
    return p.returncode == 0, log[:300]


def generate_openings(exe: Path, net: Path, wl_dir: Path, seed: str, workers: int,
                      games_per_worker: int, plies: int, tmp_dir: Path) -> list:
    """Generate deterministic per-(worker,game) 8-ply openings matching worker.py's sha256 rule."""
    opts = [ln.replace("@@NET@@", str(net)).strip()
            for ln in (wl_dir / "options.uci").read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")]
    env = dict(os.environ)
    env["TMPDIR"] = str(tmp_dir)
    p = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, cwd=str(tmp_dir), env=env)
    per_worker = [[] for _ in range(workers)]

    def ask(cmd: str) -> list:
        p.stdin.write((cmd + "\nisready\n").encode("ascii"))
        p.stdin.flush()
        out = []
        while True:
            raw = p.stdout.readline()
            if not raw:
                raise RuntimeError("engine exited while generating benchmark openings")
            ln = raw.decode("ascii").rstrip("\r\n")
            if ln == "readyok":
                return out
            out.append(ln)

    try:
        for opt in opts:
            ask(opt)
        for w in range(workers):
            for g in range(1, games_per_worker + 1):
                gid = f"d10-w{w:03d}-g{g:08d}"
                moves = []
                for ply in range(plies):
                    pos = "position startpos" if not moves else "position startpos moves " + " ".join(moves)
                    ask(pos)
                    lines = ask("go perft 1")
                    legal = sorted(ln.split(":")[0] for ln in lines if ": " in ln)
                    if not legal:
                        break
                    idx = int.from_bytes(hashlib.sha256(f"{seed}|{gid}|{ply}".encode("ascii")).digest()[:8], "big") % len(legal)
                    moves.append(legal[idx])
                per_worker[w].append((gid, moves))
        p.stdin.write(b"quit\n")
        p.stdin.flush()
        p.wait(timeout=15)
    finally:
        if p.poll() is None:
            p.kill()
            p.wait(timeout=10)
    return per_worker


def benchmark_variants(built: dict, net: Path, wl_dir: Path, work_dir: Path,
                       workers: int, games_per_worker: int, reps: int, seed: str, step_s: float) -> dict:
    """D10/N16 interleaved multi-worker self-play benchmark verifying bit-identical game digests."""
    names = list(built.keys())
    tmp_dir = work_dir / "bench_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    first_exe = Path(built[names[0]]["binary"])
    per_worker_openings = generate_openings(first_exe, net, wl_dir, seed, workers, games_per_worker, 8, tmp_dir)

    opts = [ln.replace("@@NET@@", str(net)).strip()
            for ln in (wl_dir / "options.uci").read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")]
    sg_line = (wl_dir / "selfgame_line.txt").read_text(encoding="utf-8").strip()

    worker_scripts = []
    for w in range(workers):
        cmds = list(opts)
        for _gid, moves in per_worker_openings[w]:
            cmds.append("ucinewgame")
            cmds.append("position startpos" if not moves else "position startpos moves " + " ".join(moves))
            cmds.append(sg_line)
        cmds.append("quit")
        worker_scripts.append(cmds)

    rep_results = {n: [] for n in names}
    digests = {}
    for rep in range(reps):
        order = names[rep % len(names):] + names[:rep % len(names)]
        for name in order:
            exe = Path(built[name]["binary"])

            def run_one_worker(w_idx: int) -> tuple:
                tr = tmp_dir / f"rep{rep}_{name}_w{w_idx}.txt"
                ok, summ, err = run_uci_workload(exe, worker_scripts[w_idx], step_s, tmp_dir, tr)
                if not ok:
                    raise RuntimeError(f"bench {name} rep {rep} w{w_idx} failed: {err} {summ['refusals'][:2]}")
                return summ["totals"]["rows"], summ["totals"]["sg_sha256"]

            t0 = time.monotonic_ns()
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                outs = list(pool.map(run_one_worker, range(workers)))
            dt_ns = max(1, time.monotonic_ns() - t0)
            tot_rows = sum(r for r, _ in outs)
            comb_digest = hashlib.sha256("\n".join(d for _, d in outs).encode("ascii")).hexdigest()
            if name not in digests:
                digests[name] = comb_digest
            elif digests[name] != comb_digest:
                raise RuntimeError(f"non-deterministic self-play digest inside {name} on rep {rep}")
            rps_milli = (tot_rows * 1_000_000_000_000) // dt_ns
            rep_results[name].append({"rep": rep, "rows": tot_rows, "elapsed_ms": dt_ns // 1_000_000,
                                      "rows_per_sec_milli": rps_milli})

    unique_digests = set(digests.values())
    if len(unique_digests) != 1:
        raise RuntimeError(f"variants produced different self-play digests: {digests}")

    totals = {}
    for name in names:
        tot_r = sum(x["rows"] for x in rep_results[name])
        tot_ms = max(1, sum(x["elapsed_ms"] for x in rep_results[name]))
        totals[name] = {
            "rows": tot_r,
            "elapsed_ms": tot_ms,
            "rows_per_sec_milli": (tot_r * 1_000_000) // tot_ms,
            "reps": rep_results[name],
        }

    # D10/N16 three-way classification when both plain_o3_lto and pgo_lto (or plain_o3 and pgo_*) exist
    verdict = "single_family"
    plain_key = "plain_o3_lto" if "plain_o3_lto" in totals else ("plain_o3" if "plain_o3" in totals else None)
    pgo_key = "pgo_lto" if "pgo_lto" in totals else ("pgo_nolto" if "pgo_nolto" in totals else None)
    if plain_key and pgo_key:
        wins = sum(1 for a, b in zip(rep_results[pgo_key], rep_results[plain_key])
                   if a["rows_per_sec_milli"] > b["rows_per_sec_milli"])
        losses = sum(1 for a, b in zip(rep_results[pgo_key], rep_results[plain_key])
                     if a["rows_per_sec_milli"] < b["rows_per_sec_milli"])
        if wins == reps and totals[pgo_key]["rows_per_sec_milli"] > totals[plain_key]["rows_per_sec_milli"]:
            verdict = "pgo_faster"
        elif losses == reps and totals[pgo_key]["rows_per_sec_milli"] < totals[plain_key]["rows_per_sec_milli"]:
            verdict = "pgo_slower_use_plain"
        else:
            verdict = "inconclusive_gain_not_shown"

    return {
        "workers": workers,
        "games_per_worker": games_per_worker,
        "reps": reps,
        "seed": seed,
        "common_sg_digest": next(iter(unique_digests)),
        "variants": totals,
        "d10_n16_verdict": verdict,
        "plain_ref": plain_key,
        "pgo_ref": pgo_key,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="D10/N16 Linux Forge build and comparator (Neon reference)")
    p.add_argument("--variant", required=True, choices=sorted(ARCH_FLAGS))
    p.add_argument("--source", required=True, help="Directory containing src/ and include/")
    p.add_argument("--net", required=True, help="Frozen .fnn3 net file")
    p.add_argument("--workloads", required=True, help="Directory with profile/verify/startup/n12_batch .uci")
    p.add_argument("--known", required=True, help="Directory with SOURCE.sha256 and known *.json")
    p.add_argument("--work-dir", required=True, help="NEW work directory")
    p.add_argument("--compiler", default="g++", help="C++ compiler (g++ or clang++)")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--modes", default="plain_o3_lto,pgo_lto",
                   help="Comma-separated subset of plain_o3,plain_o3_lto,pgo_nolto,pgo_lto")
    p.add_argument("--step-s", type=float, default=1800.0)
    p.add_argument("--plant", default="none", choices=VALID_PLANTS)
    p.add_argument("--bench-workers", type=int, default=0)
    p.add_argument("--bench-games", type=int, default=0)
    p.add_argument("--bench-reps", type=int, default=0)
    p.add_argument("--bench-seed", default="d10cmp")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 2

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    if not modes or any(m not in VALID_MODES for m in modes) or len(set(modes)) != len(modes):
        print(f"STOP: invalid --modes {args.modes!r} (allowed: {VALID_MODES})", file=sys.stderr)
        return 2
    if args.jobs < 1 or args.step_s <= 0:
        print("STOP: --jobs >= 1 and --step-s > 0 required", file=sys.stderr)
        return 2

    work = Path(args.work_dir).resolve()
    if work.exists():
        print(f"STOP: work dir already exists: {work}", file=sys.stderr)
        return 2

    src_in = Path(args.source).resolve()
    net = Path(args.net).resolve()
    wl = Path(args.workloads).resolve()
    kn = Path(args.known).resolve()
    for req in (src_in / "src", src_in / "include", net,
                wl / "profile.uci", wl / "verify.uci", wl / "startup.uci", wl / "n12_batch.uci",
                kn / "SOURCE.sha256", kn / "profile.json", kn / "verify.json",
                kn / "startup.json", kn / "n12_batch.json"):
        if not req.exists():
            print(f"STOP: missing required input: {req}", file=sys.stderr)
            return 2

    cxx = shutil.which(args.compiler)
    if not cxx:
        print(f"STOP: compiler not found: {args.compiler}", file=sys.stderr)
        return 2
    ver_p = subprocess.run([cxx, "--version"], capture_output=True, text=True, timeout=10, check=False)
    cxx_ver = (ver_p.stdout.splitlines() or ver_p.stderr.splitlines() or [""])[0].strip()
    is_clang = "clang" in cxx_ver.lower()

    work.mkdir(parents=True, exist_ok=False)
    tmp_dir = work / "tmp"
    tmp_dir.mkdir()

    # Step 1: Preflight ISA + hardlink + exec mount via sibling machine_check
    mc_args = machine_check.build_parser().parse_args([
        "--work-dir", str(work / "machine_check"),
        "--variant", args.variant,
        "--min-threads", "1",
        "--min-ram-bytes", "0",
        "--compiler", args.compiler,
        "--volume", f"build:{work}:0:0:1",
    ])
    (work / "machine_check").mkdir()
    mc_ok, mc_rep = machine_check.run_check(mc_args)
    machine_check.write_immutable(work / "machine_check" / "machine_check.json",
                                  machine_check.canonical_json_bytes(mc_rep))
    if not mc_ok:
        print("STOP: machine_check refused host: " + " | ".join(mc_rep["failures"]), file=sys.stderr)
        return 1

    # Step 2: Copy source and strictly verify SOURCE.sha256
    src_copy = work / "source"
    src_copy.mkdir()
    try:
        copy_tree_strict(src_in, src_copy, ["src", "include"])
    except ValueError as e:
        print(f"STOP: source copy failed: {e}", file=sys.stderr)
        return 1

    if args.plant == "bad_source_hash":
        sp = src_copy / "src" / "search.cpp"
        sp.write_bytes(b"// planted source tamper\n" + sp.read_bytes())

    try:
        got_manifest = hash_tree_strict(src_copy, ["src", "include"])
    except ValueError as e:
        print(f"STOP: source hash failed: {e}", file=sys.stderr)
        return 1
    want_manifest = (kn / "SOURCE.sha256").read_text(encoding="ascii")
    if got_manifest != want_manifest:
        print("STOP: SOURCE.sha256 mismatch (source does not match frozen tree)", file=sys.stderr)
        return 1
    machine_check.write_immutable(work / "SOURCE.sha256", got_manifest.encode("ascii"))
    source_digest = got_manifest.strip().splitlines()[-1].split()[-1]

    units = sorted(p.stem for p in (src_copy / "src").glob("*.cpp"))
    if not units:
        print("STOP: no .cpp units found in source/src", file=sys.stderr)
        return 1

    # Step 3..6: Build and verify every requested mode in its own clean isolated subdir
    built = {}
    for mode in modes:
        mdir = work / "modes" / mode
        obj_dir = mdir / "obj"
        prof_dir = mdir / "prof"
        bin_dir = mdir / "bin"
        log_dir = mdir / "logs"
        m_src = mdir / "source"
        m_tmp = mdir / "tmp"
        for d in (obj_dir, prof_dir, bin_dir, log_dir, m_src, m_tmp):
            d.mkdir(parents=True)
        copy_tree_strict(src_copy, m_src, ["src", "include"])

        use_lto = mode in ("plain_o3_lto", "pgo_lto")
        use_pgo = mode in ("pgo_nolto", "pgo_lto")
        lto_flags = (["-flto=thin"] if is_clang else ["-flto=auto"]) if use_lto else []
        base_flags = list(COMMON_FLAGS) + list(ARCH_FLAGS[args.variant]) + lto_flags

        profile_digest = ""
        gcda_count = 0

        if use_pgo:
            if is_clang:
                profdata_bin = shutil.which("llvm-profdata") or shutil.which("llvm-profdata-18")
                if not profdata_bin:
                    print(f"STOP: Clang PGO requested for {mode} but llvm-profdata not found", file=sys.stderr)
                    return 1
                gen_flags = base_flags + ["-fprofile-instr-generate=prof/default_%m.profraw"]
            else:
                gen_flags = base_flags + ["-fprofile-generate=prof", "-fprofile-update=atomic"]

            ok, errs = compile_units(cxx, gen_flags, mdir, units, "gen", args.jobs)
            if not ok:
                print(f"STOP: {mode} pass 1 compile failed: {errs[:3]}", file=sys.stderr)
                return 1
            gen_bin = bin_dir / "forge_gen"
            ok, lerr = link_binary(cxx, gen_flags, mdir, units, "bin/forge_gen", log_dir / "gen_link.log")
            if not ok:
                print(f"STOP: {mode} pass 1 link failed: {lerr}", file=sys.stderr)
                return 1

            # Profile workload runs with cwd=mdir so relative prof/ receives .gcda/.profraw cleanly
            extra_plant = "setoption name NoSuchThing value 1" if args.plant == "profile_error" else ""
            ok, diffs, _ = check_workload(gen_bin, wl / "profile.uci", kn / "profile.json", net,
                                          args.step_s, m_tmp, mdir / "profile_run.txt",
                                          extra_cmd=extra_plant, run_cwd=mdir)
            if not ok:
                print(f"STOP: {mode} profile run failed: {diffs[:4]}", file=sys.stderr)
                return 1

            if is_clang:
                raws = sorted(prof_dir.glob("*.profraw"))
                if not raws or any(r.stat().st_size == 0 for r in raws):
                    print(f"STOP: {mode} no non-empty .profraw files produced", file=sys.stderr)
                    return 1
                merged = prof_dir / "merged.profdata"
                mp = subprocess.run([profdata_bin, "merge", "-output", str(merged), *(str(r) for r in raws)],
                                    capture_output=True, text=True, check=False)
                if mp.returncode != 0:
                    print(f"STOP: {mode} llvm-profdata merge failed: {mp.stderr[:200]}", file=sys.stderr)
                    return 1
                gcda_count = len(raws)
                profile_digest = sha256_file(merged)
                if args.plant == "missing_profile":
                    merged.unlink()
                elif args.plant == "other_source":
                    sp = m_src / "src" / "search.cpp"
                    sp.write_bytes(b"// planted other source\n" + sp.read_bytes())
                use_flags = base_flags + ["-fprofile-instr-use=prof/merged.profdata",
                                          "-Werror=profile-instr-unprofiled", "-Werror=profile-instr-out-of-date"]
            else:
                gcdas = sorted(prof_dir.rglob("*.gcda"))
                empty = [g for g in gcdas if g.stat().st_size == 0]
                if len(gcdas) != len(units) or empty:
                    print(f"STOP: {mode} expected {len(units)} non-empty .gcda files, got {len(gcdas)} ({len(empty)} empty)",
                          file=sys.stderr)
                    return 1
                gcda_count = len(gcdas)
                prof_manifest = hash_tree_strict(mdir, ["prof"])
                machine_check.write_immutable(mdir / "PROFILE.sha256", prof_manifest.encode("ascii"))
                profile_digest = prof_manifest.strip().splitlines()[-1].split()[-1]

                if args.plant == "missing_profile":
                    victims = [g for g in gcdas if "search" in g.name]
                    if not victims:
                        print("STOP: plant missing_profile could not find search.gcda", file=sys.stderr)
                        return 1
                    victims[0].unlink()
                elif args.plant == "other_source":
                    sp = m_src / "src" / "search.cpp"
                    sp.write_bytes(b"// planted other source\n" + sp.read_bytes())

                use_flags = base_flags + ["-fprofile-use=prof",
                                          "-Werror=missing-profile", "-Werror=coverage-mismatch"]

            ok, errs = compile_units(cxx, use_flags, mdir, units, "use", args.jobs)
            if not ok:
                print(f"STOP: {mode} pass 2 compile failed: {errs[:3]}", file=sys.stderr)
                return 1
            final_bin = bin_dir / "forge"
            ok, lerr = link_binary(cxx, use_flags, mdir, units, "bin/forge", log_dir / "use_link.log")
            if not ok:
                print(f"STOP: {mode} pass 2 link failed: {lerr}", file=sys.stderr)
                return 1
            for lf in sorted(log_dir.glob("use_*.log")):
                if re.search(r"warning:.*(?:profile|coverage)", lf.read_text(encoding="utf-8", errors="replace")):
                    print(f"STOP: {mode} profile/coverage warning in {lf.name}", file=sys.stderr)
                    return 1
        else:
            ok, errs = compile_units(cxx, base_flags, mdir, units, "plain", args.jobs)
            if not ok:
                print(f"STOP: {mode} compile failed: {errs[:3]}", file=sys.stderr)
                return 1
            final_bin = bin_dir / "forge"
            ok, lerr = link_binary(cxx, base_flags, mdir, units, "bin/forge", log_dir / "plain_link.log")
            if not ok:
                print(f"STOP: {mode} link failed: {lerr}", file=sys.stderr)
                return 1

        if args.plant != "none":
            print(f"STOP: planted fault {args.plant} was NOT caught by mode {mode}", file=sys.stderr)
            return 1

        # Verify finished binary against verify.json, startup.json, AND n12_batch.json
        checks_ok = {}
        for wname in ("verify", "startup", "n12_batch"):
            ok, diffs, summ = check_workload(final_bin, wl / f"{wname}.uci", kn / f"{wname}.json",
                                             net, args.step_s, tmp_dir, mdir / f"{wname}_run.txt")
            if not ok:
                print(f"STOP: {mode} failed {wname}.json check: {diffs[:4]}", file=sys.stderr)
                return 1
            checks_ok[wname] = {
                "equal": True,
                "net_kernels": sorted(set(summ["net_kernel"])),
                "games": summ["totals"]["games"],
                "rows": summ["totals"]["rows"],
            }

        built[mode] = {
            "binary": str(final_bin),
            "sha256": sha256_file(final_bin),
            "bytes": final_bin.stat().st_size,
            "lto": use_lto,
            "pgo": use_pgo,
            "gcda_count": gcda_count,
            "profile_digest": profile_digest,
            "checks": checks_ok,
        }

    bench_report = None
    if args.bench_workers > 0 and args.bench_games > 0 and args.bench_reps > 0 and len(built) >= 2:
        try:
            bench_report = benchmark_variants(
                built, net, wl, work, args.bench_workers, args.bench_games,
                args.bench_reps, args.bench_seed, args.step_s,
            )
        except Exception as e:  # noqa: BLE001
            print(f"STOP: D10 benchmark failed: {e}", file=sys.stderr)
            return 1

    report = {
        "schema": 1,
        "variant": args.variant,
        "compiler_path": cxx,
        "compiler_version": cxx_ver,
        "source_digest": source_digest,
        "net_sha256": sha256_file(net),
        "units": units,
        "modes": built,
        "benchmark": bench_report,
        "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    rep_path = work / "build_report.json"
    machine_check.write_immutable(rep_path, machine_check.canonical_json_bytes(report))
    summary_bits = [f"{m}={built[m]['sha256'][:12]}" for m in modes]
    if bench_report:
        summary_bits.append(f"d10={bench_report['d10_n16_verdict']}")
    print("BUILT " + " ".join(summary_bits) + f" report={rep_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
