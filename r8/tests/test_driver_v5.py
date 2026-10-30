"""R8 v5: tests of forge_selfplay_fast's review fixes with the fault-injection engine (no search: seconds per test).
usage: python -I -B test_driver_v5.py <driver.exe> <fake_engine.exe> <scratch dir> [--cpus 2-3] [--only name,name]
Every test works in its own new folder under <scratch dir>\\<run stamp>\\ (nothing is deleted or overwritten).
Prints PASS/FAIL per test and a summary; exit 1 if any test failed."""
import hashlib
import json
import os
import re
import sqlite3
import struct
import subprocess
import sys
import time

DRIVER, FAKE, SCRATCH = (os.path.abspath(p) for p in sys.argv[1:4])
CPUS = sys.argv[sys.argv.index("--cpus") + 1] if "--cpus" in sys.argv else "2-3"
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
HERE = os.path.dirname(os.path.abspath(__file__))
DEDUP_TOOL = os.path.join(os.path.dirname(HERE), "tools", "dedup_against_db.py")
ROOT = os.path.join(SCRATCH, time.strftime("run_%H%M%S"))
os.makedirs(ROOT)
PREFIX = "forge_selfplay_fast"
results = []


def folder(name):
    return os.path.join(ROOT, name)


def run(args, env_mode=None, timeout=180):
    env = dict(os.environ)
    env.pop("FORGE_FAKE_ENGINE", None)
    if env_mode:
        env["FORGE_FAKE_ENGINE"] = env_mode
    p = subprocess.run([DRIVER, "--engine", FAKE, "--cpus", CPUS, "--progress-seconds", "600"] + args,
                       capture_output=True, text=True, env=env, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def start(args, env_mode=None):
    env = dict(os.environ)
    env.pop("FORGE_FAKE_ENGINE", None)
    if env_mode:
        env["FORGE_FAKE_ENGINE"] = env_mode
    return subprocess.Popen([DRIVER, "--engine", FAKE, "--cpus", CPUS, "--progress-seconds", "600"] + args,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)


def check(name, cond, detail):
    results.append((name, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'} {name}: {detail}", flush=True)
    return bool(cond)


def shard(d, no, ext=".txt"):
    return os.path.join(d, f"{PREFIX}_{no:03d}{ext}")


def read_lines(path):
    with open(path, "rb") as f:
        return f.read().split(b"\n")[:-1]


CODE = {c: i + 1 for i, c in enumerate("PNBRQKpnbrqk")}


def fpos_record(line):
    fen, cp, res = (x.strip() for x in line.decode("ascii").split("|"))
    placement, side = fen.split()[:2]
    codes = [0] * 64
    r, f = 7, 0
    for ch in placement:
        if ch == "/":
            r, f = r - 1, 0
        elif ch.isdigit():
            f += int(ch)
        else:
            codes[r * 8 + f] = CODE[ch]
            f += 1
    board = bytes(codes[2 * i] | (codes[2 * i + 1] << 4) for i in range(32))
    return board, int(cp), (1 if side == "b" else 0) | ({"0.0": 0, "0.5": 1, "1.0": 2}[res] << 1)


def write_pos(path, lines):
    recs = [fpos_record(x) for x in lines]
    with open(path, "xb") as f:
        f.write(struct.pack("<4sIQ", b"FPOS", 1, len(recs)))
        f.write(b"".join(r[0] for r in recs))
        f.write(b"".join(struct.pack("<h", r[1]) for r in recs))
        f.write(bytes(r[2] for r in recs))


def pos_matches_text(pos_path, txt_path):
    data = open(pos_path, "rb").read()
    magic, ver, n = struct.unpack_from("<4sIQ", data, 0)
    lines = read_lines(txt_path)
    if magic != b"FPOS" or ver != 1 or n != len(lines) or len(data) != 16 + 35 * n:
        return False, f"header n={n} vs {len(lines)} lines, {len(data)} bytes"
    for i, line in enumerate(lines):
        board, cp, meta = fpos_record(line)
        if (data[16 + 32 * i:16 + 32 * i + 32] != board or struct.unpack_from("<h", data, 16 + 32 * n + 2 * i)[0] != cp
                or data[16 + 34 * n + i] != meta):
            return False, f"record {i} differs"
    return True, f"{n} records == text"


def key(line):
    fen = line.split(b"|", 1)[0].strip()
    return hashlib.blake2b(b" ".join(fen.split()[:4]), digest_size=16).digest()


def fake_engines_alive():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq fake_engine.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return out.count("fake_engine.exe")


def wanted(name):
    return ONLY is None or name in ONLY


# ---------------------------------------------------------------- tests
if wanted("refuse_out"):
    d = folder("refuse_out")
    os.makedirs(d)
    rc, out = run(["--out", d, "--no-global-dedup", "--games-per-worker", "1"])
    check("refuse_out", rc == 2 and "pass --resume" in out, f"rc={rc}; {out.strip().splitlines()[0] if out.strip() else ''}")

if wanted("seed"):
    texts, seeds = [], []
    for tag in ("s1", "s2"):
        rc, out = run(["--out", folder("seed_" + tag), "--no-global-dedup", "--games-per-worker", "3"])
        m = re.search(r"seed=(\d+) \(random_device \^ time \^ pid\)", out)
        seeds.append(m.group(1) if m else None)
        texts.append(open(shard(folder("seed_" + tag), 1), "rb").read() if rc == 0 else b"")
    check("seed_random", seeds[0] and seeds[1] and seeds[0] != seeds[1] and texts[0] != texts[1] and texts[0],
          f"seeds {seeds[0]} / {seeds[1]}, texts differ: {texts[0] != texts[1]}")
    fixed = []
    for tag in ("f1", "f2"):
        rc, out = run(["--out", folder("seed_" + tag), "--no-global-dedup", "--games-per-worker", "3", "--seed", "12345"])
        fixed.append((rc, "seed=12345 (--seed)" in out, open(shard(folder("seed_" + tag), 1), "rb").read() if rc == 0 else b""))
    check("seed_fixed", all(r == 0 and s for r, s, _ in fixed) and fixed[0][2] == fixed[1][2] and fixed[0][2],
          f"--seed 12345 twice: identical {len(fixed[0][2])} bytes: {fixed[0][2] == fixed[1][2]}")

if wanted("timeout"):
    d = folder("timeout")
    os.makedirs(d)
    t0 = time.time()
    rc, out = run(["--out", os.path.join(d, "out"), "--no-global-dedup", "--games-per-worker", "2", "--engine-timeout", "3"],
                  env_mode="hang:5:" + os.path.join(d, "flag"))
    done = re.search(r"DONE: .*games=(\d+) .*restarts=(\d+) timeouts=(\d+)", out)
    check("timeout_kill_restart", rc == 0 and "gave no answer for 3 s: killed" in out and "(restarted)" in out
          and done and done.groups() == ("2", "1", "1"),
          f"rc={rc}, games/restarts/timeouts={done.groups() if done else None}, {time.time() - t0:.1f} s")

if wanted("exit"):
    d = folder("exit")
    os.makedirs(d)
    rc, out = run(["--out", os.path.join(d, "out"), "--no-global-dedup", "--games-per-worker", "2"],
                  env_mode="exit:5:" + os.path.join(d, "flag"))
    done = re.search(r"DONE: .*games=(\d+) .*restarts=(\d+) timeouts=(\d+)", out)
    check("exit_restart", rc == 0 and "engine pipe closed" in out and done and done.groups() == ("2", "1", "0"),
          f"rc={rc}, games/restarts/timeouts={done.groups() if done else None}")

if wanted("all_dead"):
    rc, out = run(["--out", folder("all_dead"), "--no-global-dedup", "--workers", "2", "--max-restarts", "2"], env_mode="dead")
    check("all_dead_exit3", rc == 3 and out.count("gives up after 3 engine failures") == 2 and "every engine is dead" in out,
          f"rc={rc}, give-ups={out.count('gives up')}")

if wanted("stop_rotation"):
    d = folder("stop_rotation")
    p = start(["--out", d, "--no-global-dedup", "--pos", "--rotate-minutes", "0.05", "--flush-seconds", "1"])
    time.sleep(9)
    open(os.path.join(d, "STOP"), "x").close()
    out, _ = p.communicate(timeout=120)
    shards = sorted(f for f in os.listdir(d) if re.fullmatch(PREFIX + r"_\d{3}\.txt", f))
    parts = [f for f in os.listdir(d) if f.endswith(".part")]
    ok_pos = [pos_matches_text(os.path.join(d, s[:-4] + ".pos"), os.path.join(d, s)) for s in shards]
    infos = [open(os.path.join(d, s[:-4] + ".pos.info")).read() for s in shards]
    check("stop_rotation", p.returncode == 0 and "STOP file" in out and len(shards) >= 2 and not parts
          and all(ok for ok, _ in ok_pos) and all("global_dedup=OFF" in i for i in infos),
          f"rc={p.returncode}, shards={len(shards)}, parts={parts}, pos==text {[m for _, m in ok_pos]}")
    rc, out = run(["--out", d, "--resume", "--no-global-dedup"])
    check("stop_file_blocks_start", rc == 0 and "exists: not starting" in out, f"rc={rc}")

if wanted("hard_kill"):
    d = folder("hard_kill")
    rc, out = run(["--out", d, "--no-global-dedup", "--pos", "--flush-seconds", "1", "--rotate-minutes", "0",
                   "--test-exit-after-seconds", "6"])
    part = shard(d, 1, ".txt.part")
    raw = open(part, "rb").read() if os.path.exists(part) else b""
    complete = raw.count(b"\n")
    torn = len(raw) - (raw.rfind(b"\n") + 1)
    time.sleep(1)
    alive = fake_engines_alive()
    check("hard_kill_leaves_part", rc == 9 and complete > 0 and alive == 0,
          f"rc={rc}, {complete} complete lines + {torn} bytes in .txt.part, fake engines alive {alive}")
    rc, out = run(["--out", d, "--resume", "--no-global-dedup", "--pos", "--games-per-worker", "1"])
    txt = shard(d, 1)
    n = len(read_lines(txt)) if os.path.exists(txt) else -1
    ok, msg = pos_matches_text(shard(d, 1, ".pos"), txt) if os.path.exists(txt) else (False, "no .txt")
    check("resume_salvage", rc == 0 and f"{complete} complete lines kept" in out and n == complete and ok
          and os.path.exists(shard(d, 2)) and not os.path.exists(part),
          f"rc={rc}, salvaged {n} lines (expected {complete}), {msg}, next shard {os.path.exists(shard(d, 2))}")

if wanted("write_fail"):
    d = folder("write_fail")
    rc, out = run(["--out", d, "--no-global-dedup", "--flush-seconds", "0.3", "--games-per-worker", "400",
                   "--test-fail-write-after", "2"])
    check("write_error_exit4", rc == 4 and "output failed: write (test hook" in out and os.path.exists(shard(d, 1, ".txt.part")),
          f"rc={rc}")

if wanted("lock"):
    d = folder("lock")
    p = start(["--out", d, "--no-global-dedup", "--max-minutes", "1"])
    time.sleep(3)
    rc, out = run(["--out", d, "--resume", "--no-global-dedup", "--games-per-worker", "1"])
    open(os.path.join(d, "STOP"), "x").close()
    p.communicate(timeout=120)
    check("one_driver_per_folder", rc == 2 and "another driver writes into" in out, f"second driver rc={rc}")

if wanted("post_unit"):
    d = folder("post_unit")
    os.makedirs(d)
    src = read_lines(shard(folder("seed_f1"), 1)) if os.path.exists(shard(folder("seed_f1"), 1)) else []
    uniq, keys = [], set()
    for line in src:
        if key(line) not in keys:
            keys.add(key(line))
            uniq.append(line)
    L = uniq[:12]
    live = os.path.join(d, "live.sqlite3")
    con = sqlite3.connect(live)
    con.execute("CREATE TABLE hashes (hash BLOB PRIMARY KEY) WITHOUT ROWID")
    con.execute("INSERT INTO hashes VALUES (?)", (key(L[0]),))
    con.commit()
    con.close()
    own = os.path.join(d, "own.sqlite3")
    base = lambda n: os.path.join(d, f"x_{n:03d}")
    shards_in = {1: L[0:5], 2: L[2:8] + [L[5]], 3: L[8:10]}
    for n, lines in shards_in.items():
        open(base(n) + ".txt", "xb").write(b"".join(x + b"\n" for x in lines))
        write_pos(base(n) + ".pos", lines)
    py = sys.executable

    def tool(n):
        p = subprocess.run([py, "-I", "-B", DEDUP_TOOL, "--shard", base(n), "--live-db", live, "--own-db", own],
                           capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    rc1, o1 = tool(1)
    ok1 = rc1 == 0 and read_lines(base(1) + ".dedup.txt") == L[1:5] and pos_matches_text(base(1) + ".dedup.pos", base(1) + ".dedup.txt")[0]
    rc2, o2 = tool(2)
    ok2 = rc2 == 0 and read_lines(base(2) + ".dedup.txt") == L[5:8] and "own DB 3, inside 1" in o2
    rc1b, o1b = tool(1)
    con = sqlite3.connect(own)  # simulate an attempt killed after its commit: shard 3's keys are already in
    con.execute("INSERT OR IGNORE INTO shards(name) VALUES ('x_003')")
    sid = con.execute("SELECT id FROM shards WHERE name='x_003'").fetchone()[0]
    con.executemany("INSERT OR IGNORE INTO hashes VALUES (?, ?)", [(key(x), sid) for x in L[8:10]])
    con.commit()
    con.close()
    rc3, o3 = tool(3)
    ok3 = rc3 == 0 and read_lines(base(3) + ".dedup.txt") == L[8:10]
    open(base(4) + ".txt", "xb").write(L[10] + b"\n")
    open(base(4) + ".dedup.txt", "xb").write(b"")
    rc4, o4 = tool(4)
    check("post_step_unit", ok1 and ok2 and rc1b == 0 and "already done" in o1b and ok3 and rc4 == 4 and "REFUSED" in o4,
          f"A: {o1.strip()} | B: {o2.strip()} | A again rc={rc1b} | killed-attempt C: {o3.strip()} | stale rc={rc4}")

if wanted("post_driver"):
    d = folder("post_driver")
    os.makedirs(d)
    rc0, out0 = run(["--out", os.path.join(d, "ref"), "--no-global-dedup", "--seed", "777", "--games-per-worker", "3"])
    ref = read_lines(os.path.join(d, "ref", f"{PREFIX}_001.txt"))
    live = os.path.join(d, "live.sqlite3")
    con = sqlite3.connect(live)
    con.execute("CREATE TABLE hashes (hash BLOB PRIMARY KEY) WITHOUT ROWID")
    planted = {key(x) for x in ref[:10]}
    con.executemany("INSERT OR IGNORE INTO hashes VALUES (?)", [(k,) for k in planted])
    con.commit()
    con.close()
    out_dir = os.path.join(d, "run")
    rc, out = run(["--out", out_dir, "--seed", "777", "--games-per-worker", "3", "--pos", "--dedup-db", live,
                   "--post-script", DEDUP_TOOL, "--post-python", sys.executable])
    js = json.load(open(os.path.join(out_dir, f"{PREFIX}_001.dedup.json"))) if os.path.exists(os.path.join(out_dir, f"{PREFIX}_001.dedup.json")) else {}
    okp = pos_matches_text(os.path.join(out_dir, f"{PREFIX}_001.dedup.pos"), os.path.join(out_dir, f"{PREFIX}_001.dedup.txt")) if js else (False, "")
    check("post_step_driver", rc == 0 and js.get("dup_live") == len(planted) and js.get("read") == len(ref)
          and js.get("kept") == len(ref) - len(planted) and okp[0] and "global dedup" in out,
          f"rc={rc}, json {dict((k, js.get(k)) for k in ('read', 'kept', 'dup_live', 'dup_own', 'dup_self'))}, planted {len(planted)}, {okp[1]}")
    m = re.search(r"DONE: .*RSS driver ([\d.]+) MB \(peak ([\d.]+), private ([\d.]+)\), engines ([\d.]+) MB .*job peak commit ([\d.]+) MB", out)
    check("rss_reported", m is not None, f"DONE line: {m.group(0)[m.group(0).find('RSS'):] if m else out[-300:]}")

failed = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed" + (f"; FAILED: {failed}" if failed else ""), flush=True)
sys.exit(1 if failed else 0)
