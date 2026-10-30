"""R11 check stage: build the Forge exe + parity tool from a pinned commit, export a checkpoint, and check a K32H3^
.nnue against Forge's HalfKA loader.

  build   `git archive <commit>` (src + include) -> box-recipe build with -march=x86-64-v3 appended (AVX2 only,
          QA rule: never the znver5 build, never exe 9b7e2fcd); FMA count must be 0 and no zmm (AVX-512) instruction;
          halfka_tool from the same export with the same flags. Cached by commit + march.
  export  (optional) the trainer's serialize.py <ckpt> <net> --features=K32H3^ --l1=N on the CPU.
  parity  halfka_tool eval (Forge kernels, SIMD vs scalar) against parity_nnue_pytorch.py (the trainer's reader,
          feature extractor and fake-quantized forward in float64): fens_12k must be 12000/12000 exact.
  off     the lock's uci_check.py --full on the exe (OFF bench 312866 at d11 ... ALL OK). Cached per exe.
  on      EvalFileHalfKA=<net>: load message, bench 11/13/16/20/22 (Threads 1, Hash 16, OwnBook false), d11 twice
          (stable), a reload gives the same d11.
  wac     the lock's WAC 300 harness at 200 ms, ON (and OFF once per exe for reference). Score reported.
Writes <out>/check.json with one PASS/FAIL per item and the overall verdict, and logs to <root>/logs/pipeline.log.
Usage: r11_check.py --config <cfg.json> --net <net.nnue> [--ckpt <ckpt> --l1 1024] --out <dir>
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r11_common as C  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BASH = r"C:\Program Files\Git\bin\bash.exe"
OBJDUMP = "C:/msys64/ucrt64/bin/objdump.exe"
LOCK_BENCH = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
BAD_EXE_SHA_PREFIXES = ("9b7e2fcd",)  # QA: never use the R10 gate exe forge_r10_c


def _run(cmd, log: C.Log, what: str, env=None, cwd=None, timeout=None) -> subprocess.CompletedProcess:
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd, timeout=timeout)
    log.info(f"{what}: exit {r.returncode} in {time.time() - t0:.1f} s")
    return r


# ----------------------------------------------------------------------------------------------------------------
# build
# ----------------------------------------------------------------------------------------------------------------
def export_tree(commit: str, dest: str, log: C.Log) -> str:
    done = os.path.join(dest, ".export_done")
    if os.path.isfile(done):
        return dest
    os.makedirs(dest, exist_ok=True)
    r = subprocess.run(["git", "-C", REPO, "archive", "--format=tar", commit, "src", "include"], capture_output=True)
    if r.returncode != 0:
        raise C.StageFailed(f"git archive {commit} failed: {r.stderr.decode(errors='replace')[:300]}")
    with tarfile.open(fileobj=io.BytesIO(r.stdout), mode="r:") as tf:
        tf.extractall(dest, filter="data")
    full = subprocess.run(["git", "-C", REPO, "rev-parse", commit], capture_output=True, text=True).stdout.strip()
    with open(done, "w", encoding="utf-8", newline="\n") as f:
        f.write(full + "\n")
    log.info(f"exported {commit} ({full}) src + include to {dest}")
    return dest


def _count(pattern: str, exe: str) -> int:
    r = subprocess.run([OBJDUMP, "-d", exe], capture_output=True, text=True)
    return len(re.findall(pattern, r.stdout))


def build_engine(cfg: dict, log: C.Log) -> dict:
    e = cfg["engine"]
    commit, march = e["commit"], e.get("march", "x86-64-v3")
    bdir = os.path.join(cfg["root"], "build")
    tag = f"{commit[:8]}_{march}"
    meta_path = os.path.join(bdir, f"forge_{tag}.json")
    meta = C.read_json(meta_path)
    if meta and os.path.isfile(meta["exe"]) and C.sha256_file(meta["exe"]) == meta["exe_sha256"] \
            and os.path.isfile(meta["tool"]) and C.sha256_file(meta["tool"]) == meta["tool_sha256"]:
        return meta
    src = export_tree(commit, os.path.join(bdir, f"src_{commit[:8]}"), log)
    exe = os.path.join(bdir, f"forge_{tag}.exe")
    tool = os.path.join(bdir, f"halfka_tool_{tag}.exe")
    for p in (exe, tool):
        if os.path.exists(p):
            raise C.StageFailed(f"{p} exists without a matching build record; not overwriting")
    env = dict(os.environ)
    env["FORGE_EXTRA_SRCS"] = " ".join(e.get("extra_srcs", ["src/nnue_halfka.cpp"]))
    r = _run([BASH, e.get("build_script", "D:/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh"),
              C.winpath(src), C.winpath(exe), f"-march={march}"], log, f"build engine {tag}", env=env)
    text = r.stdout + r.stderr
    if r.returncode != 0 or not os.path.isfile(exe):
        raise C.StageFailed(f"engine build failed: {text[-800:]}")
    warnings = text.lower().count("warning")
    tool_src = os.path.join(REPO, "opus_r10", "tools", "halfka_tool.cpp")
    r2 = _run([sys.executable, "-I", "-B", os.path.join(REPO, "opus_r10", "tools", "build_tool.py"), C.winpath(src),
               tool_src, C.winpath(tool), f"-march={march}"], log, f"build halfka_tool {tag}")
    if r2.returncode != 0 or not os.path.isfile(tool):
        raise C.StageFailed(f"halfka_tool build failed: {(r2.stdout + r2.stderr)[-800:]}")
    meta = {"commit": commit, "commit_full": open(os.path.join(src, ".export_done")).read().strip(), "march": march,
            "exe": C.winpath(exe), "exe_sha256": C.sha256_file(exe), "tool": C.winpath(tool),
            "tool_sha256": C.sha256_file(tool), "fma_count_exe": _count(r"\bvfn?m(add|sub)", exe),
            "zmm_count_exe": _count(r"%zmm", exe), "fma_count_tool": _count(r"\bvfn?m(add|sub)", tool),
            "zmm_count_tool": _count(r"%zmm", tool), "engine_warnings": warnings,
            "flags": "box recipe (build_pc.sh: -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off "
                     f"-fno-fast-math -march=znver5 -static -pthread) + -march={march} (the later -march wins)",
            "built": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if meta["exe_sha256"].startswith(BAD_EXE_SHA_PREFIXES):
        raise C.StageFailed(f"built exe has a forbidden sha256 {meta['exe_sha256']}")
    if meta["fma_count_exe"] or meta["fma_count_tool"]:
        raise C.StageFailed(f"FMA instructions in the build: {meta}")
    if march.startswith("x86-64") and (meta["zmm_count_exe"] or meta["zmm_count_tool"]):
        raise C.StageFailed(f"AVX-512 (zmm) instructions in an {march} build: {meta}")
    C.write_json(meta_path, meta)
    log.ok(f"build {tag}: exe {meta['exe_sha256'][:12]} tool {meta['tool_sha256'][:12]} FMA 0 zmm 0 "
           f"warnings {warnings}")
    return meta


# ----------------------------------------------------------------------------------------------------------------
# export
# ----------------------------------------------------------------------------------------------------------------
def trainer_env(cfg: dict) -> dict:
    t = cfg["trainer"]
    env = dict(os.environ)
    tmp = os.path.join(cfg["root"], "tmp")
    os.makedirs(tmp, exist_ok=True)
    env.update({"NNUE_REPO": t["clone"], "PYTHONPATH": t["clone"], "NNUE_DATA_LOADER_LIB": t["loader_lib"],
                "NNUE_FT_BACKEND": "torch", "TORCHDYNAMO_DISABLE": "1", "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "TMP": tmp, "TEMP": tmp,
                "CUDA_VISIBLE_DEVICES": "", "HIP_VISIBLE_DEVICES": ""})
    return env


def export_net(cfg: dict, ckpt: str, out_net: str, l1: int, log: C.Log, gov: C.Governor) -> str:
    C.assert_writable_path(out_net)
    if os.path.isfile(out_net):
        return out_net
    need = max(2.0, 2.5 * os.path.getsize(ckpt) / 2**30)
    gov.wait_ok(f"export {os.path.basename(ckpt)}", need_ram_gb=need)
    tmp = out_net + ".part.nnue"
    if os.path.exists(tmp):
        raise C.StageFailed(f"leftover {tmp}; not overwriting")
    t = cfg["trainer"]
    r = _run([t["python"], "-B", os.path.join(t["clone"], "serialize.py"), ckpt, tmp, "--features=K32H3^", f"--l1={l1}"],
             log, f"export {ckpt}", env=trainer_env(cfg), cwd=t["clone"], timeout=3600)
    with open(out_net + ".export.log", "w", encoding="utf-8", newline="\n") as f:
        f.write(r.stdout[-20000:] + "\n--- stderr ---\n" + r.stderr[-20000:])
    if r.returncode != 0 or not os.path.isfile(tmp):
        raise C.StageFailed(f"serialize.py failed ({r.returncode}): {r.stderr[-600:]}")
    os.replace(tmp, out_net)
    log.info(f"exported {ckpt} -> {out_net} ({os.path.getsize(out_net)} bytes)")
    return out_net


# ----------------------------------------------------------------------------------------------------------------
# checks
# ----------------------------------------------------------------------------------------------------------------
def parity(cfg: dict, build: dict, net: str, l1: int, out: str, log: C.Log, gov: C.Governor) -> dict:
    fens = cfg["check"]["fens"]
    n_fens = sum(1 for ln in open(fens, encoding="ascii") if ln.strip())
    forge_raw = os.path.join(out, "forge_raw.txt")
    r = _run([build["tool"], "eval", net, fens, forge_raw], log, "parity: halfka_tool eval")
    m = re.search(r"eval: (\d+) positions, (\d+) bad FENs, SIMD \((\S+)\) vs scalar mismatches (\d+)", r.stdout)
    if r.returncode != 0 or not m:
        raise C.StageFailed(f"halfka_tool eval failed: {r.stdout[-400:]} {r.stderr[-400:]}")
    positions, bad, simd, simd_mism = int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(4))
    ref_raw = os.path.join(out, "ref_raw_float64.txt")
    if not os.path.isfile(ref_raw):
        gov.wait_ok("parity reference", need_ram_gb=3.0 if l1 >= 1024 else 1.5)
        tmp = ref_raw + ".part"
        t = cfg["trainer"]
        rr = _run([t["python"], "-I", "-B", os.path.join(REPO, "opus_r10", "tools", "parity_nnue_pytorch.py"), net, fens,
                   tmp, "--l1", str(l1)], log, "parity: nnue-pytorch reference (float64)", env=trainer_env(cfg),
                  timeout=7200)
        if rr.returncode != 0 or not os.path.isfile(tmp):
            raise C.StageFailed(f"parity reference failed: {rr.stdout[-400:]} {rr.stderr[-600:]}")
        os.replace(tmp, ref_raw)
    ref = [ln.split() for ln in open(ref_raw, encoding="ascii")]
    got = [ln.split() for ln in open(forge_raw, encoding="ascii")]
    exact = sum(1 for a, b in zip(ref, got) if a and b and int(a[0]) == int(b[0])) if len(ref) == len(got) else 0
    maxdiff = max((abs(int(a[0]) - int(b[0])) for a, b in zip(ref, got)), default=0) if len(ref) == len(got) else -1
    res = {"fens": C.winpath(fens), "fens_count": n_fens, "positions": positions, "bad_fens": bad, "simd": simd,
           "simd_vs_scalar_mismatches": simd_mism, "exact": exact, "max_raw_diff": maxdiff,
           "forge_raw": C.winpath(forge_raw), "ref_raw": C.winpath(ref_raw)}
    res["ok"] = (positions == n_fens == len(ref) == exact and bad == 0 and simd_mism == 0)
    text = (f"parity {os.path.basename(net)} on {n_fens} FENs: {exact}/{n_fens} raw outputs exact vs nnue-pytorch "
            f"(float64), max |raw diff| {maxdiff}, bad FENs {bad}, SIMD ({simd}) vs scalar mismatches {simd_mism}")
    with open(os.path.join(out, "parity.log"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n" + r.stdout)
    (log.ok if res["ok"] else log.fail)(text)
    return res


def off_identity(cfg: dict, build: dict, out: str, log: C.Log) -> dict:
    cache = os.path.join(cfg["root"], "build", f"off_identity_{build['exe_sha256'][:16]}.json")
    res = C.read_json(cache)
    if not res:
        r = _run([cfg["check"]["python_chess"], "-I", "-B", cfg["check"]["uci_check"], build["exe"], "--full"], log,
                 "OFF identity uci_check --full", timeout=3600)
        text = r.stdout + r.stderr
        res = {"ok": r.returncode == 0 and "ALL OK" in text, "output_tail": text[-3000:]}
        # uci_check.py prints "bench d11 nodes 312866 ref 312866 OK"
        nodes = {int(d): int(n) for d, n in re.findall(r"^bench d(\d+) nodes (\d+) ref \d+", text, re.M)}
        res["bench_nodes"] = {str(d): n for d, n in sorted(nodes.items())}
        res["bench_d11"] = nodes.get(11)
        res["exe_sha256"] = build["exe_sha256"]
        C.write_json(cache, res)
    with open(os.path.join(out, "off_identity.log"), "w", encoding="utf-8", newline="\n") as f:
        f.write(res["output_tail"])
    res = dict(res)
    res["ok"] = res["ok"] and res.get("bench_d11") == LOCK_BENCH[11]
    (log.ok if res["ok"] else log.fail)(f"OFF identity (uci_check --full): {'ALL OK' if res['ok'] else 'FAILED'}, "
                                        f"bench d11 {res.get('bench_d11')} (lock {LOCK_BENCH[11]})")
    return res


class Uci:
    def __init__(self, exe: str):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1)
        self.lines: list[str] = []

    def send(self, s: str) -> None:
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def until(self, prefix: str) -> list[str]:
        out = []
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise C.StageFailed("engine exited unexpectedly: " + " | ".join(out[-5:]))
            line = line.rstrip("\r\n")
            out.append(line)
            self.lines.append(line)
            if line.startswith(prefix):
                return out

    def setopt(self, name: str, value: str) -> list[str]:
        self.send(f"setoption name {name} value {value}")
        self.send("isready")
        return [x for x in self.until("readyok") if x.startswith("info string")]

    def bench(self, depth: int) -> tuple[int, str]:
        self.send(f"bench {depth}")
        for line in self.until("info string bench"):
            m = re.search(r"bench depth \d+ nodes (\d+)", line)
            if m:
                return int(m.group(1)), line
        raise C.StageFailed("no bench line")

    def quit(self) -> None:
        try:
            self.send("quit")
            self.p.wait(timeout=60)
        except Exception:  # noqa: BLE001
            pass


def on_bench(cfg: dict, build: dict, net: str, out: str, log: C.Log) -> dict:
    depths = cfg["check"].get("on_bench_depths", [11, 13, 16, 20, 22])
    u = Uci(build["exe"])
    res = {"depths": depths, "lines": {}, "nodes": {}}
    try:
        u.send("uci")
        uci = u.until("uciok")
        res["option_advertised"] = any("option name EvalFileHalfKA" in x for x in uci)
        for o, v in (("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")):
            u.send(f"setoption name {o} value {v}")
        info = u.setopt("EvalFileHalfKA", net)
        res["load_info"] = info
        res["loaded"] = any("EvalFileHalfKA loaded" in x for x in info) and not any("ERROR" in x for x in info)
        if res["loaded"]:
            for d in depths:
                n, line = u.bench(d)
                res["nodes"][str(d)], res["lines"][str(d)] = n, line
                log.info(f"ON bench d{d}: {line}")
            res["d11_repeat"] = u.bench(11)[0]
            u.setopt("EvalFileHalfKA", "<empty>")
            res["off_after"] = u.bench(11)[0]
            u.setopt("EvalFileHalfKA", net)
            res["d11_reload"] = u.bench(11)[0]
    finally:
        u.quit()
    n11 = res["nodes"].get("11")
    res["ok"] = bool(res.get("loaded") and res.get("option_advertised") and len(res["nodes"]) == len(depths)
                     and all(v > 0 for v in res["nodes"].values()) and res.get("d11_repeat") == n11
                     and res.get("d11_reload") == n11 and res.get("off_after") == LOCK_BENCH[11] and n11 != LOCK_BENCH[11])
    with open(os.path.join(out, "on_bench.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"net {C.winpath(net)}\nexe {build['exe']} sha256 {build['exe_sha256']}\n")
        f.write("setoption Threads 1, Hash 16, OwnBook false, EvalFileHalfKA <net>\n")
        for x in res.get("load_info", []):
            f.write(x + "\n")
        for d in depths:
            f.write(res["lines"].get(str(d), f"bench {d}: missing") + "\n")
        f.write(f"d11 repeat {res.get('d11_repeat')}, after <empty> (OFF) {res.get('off_after')}, after reload "
                f"{res.get('d11_reload')}\n")
    (log.ok if res["ok"] else log.fail)(
        f"ON bench {os.path.basename(net)}: " + ", ".join(f"d{d} {res['nodes'].get(str(d))}" for d in depths)
        + f"; d11 stable {res.get('d11_repeat') == n11}, reload {res.get('d11_reload') == n11}, OFF after "
          f"{res.get('off_after')}")
    return res


def wac(cfg: dict, build: dict, net: str | None, out: str, log: C.Log) -> dict:
    c = cfg["check"]
    tag = "on" if net else "off"
    if net:
        js = os.path.join(out, "wac_on.json")
    else:
        js = os.path.join(cfg["root"], "build", f"wac_off_{build['exe_sha256'][:16]}.json")
    if not os.path.isfile(js):
        env = dict(os.environ)
        env["OPTS"] = f"EvalFileHalfKA={net}" if net else ""
        r = _run([c["python_chess"], "-I", "-B", os.path.join(REPO, "opus_r10", "tools", "wac_tactics.py"), build["exe"],
                  tag, c["wac_suite"], str(c.get("wac_movetime_ms", 200)), js + ".part"], log, f"WAC 300 {tag}",
                 env=env, timeout=7200)
        if r.returncode != 0 or not os.path.isfile(js + ".part"):
            raise C.StageFailed(f"WAC run failed: {r.stdout[-400:]} {r.stderr[-400:]}")
        os.replace(js + ".part", js)
    d = C.read_json(js)
    solved = sum(1 for v in d["results"].values() if v["solved"])
    res = {"solved": solved, "positions": len(d["results"]), "movetime_ms": d["movetime"], "json": C.winpath(js)}
    res["ok"] = res["positions"] == 300
    log.info(f"WAC 300 {tag}: {solved}/{res['positions']} at {d['movetime']} ms")
    return res


def run_check(cfg: dict, net: str, out: str, l1: int, log: C.Log, gov: C.Governor, ckpt: str | None = None) -> dict:
    C.assert_writable_path(out)
    os.makedirs(out, exist_ok=True)
    build = build_engine(cfg, log)
    if ckpt:
        net = export_net(cfg, ckpt, net, l1, log, gov)
    res = {"net": C.winpath(net), "net_sha256": C.sha256_file(net), "net_bytes": os.path.getsize(net), "l1": l1,
           "build": build, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    gov.wait_ok("parity", need_ram_gb=1.0)
    res["parity"] = parity(cfg, build, net, l1, out, log, gov)
    res["off"] = off_identity(cfg, build, out, log)
    res["on"] = on_bench(cfg, build, net, out, log)
    res["wac_on"] = wac(cfg, build, net, out, log)
    res["wac_off"] = wac(cfg, build, None, out, log)
    res["pass"] = all(res[k]["ok"] for k in ("parity", "off", "on", "wac_on"))
    res["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    C.write_json(os.path.join(out, "check.json"), res)
    msg = (f"check {os.path.basename(net)}: parity {res['parity']['exact']}/{res['parity']['fens_count']}, OFF d11 "
           f"{res['off'].get('bench_d11')}, ON d11 {res['on']['nodes'].get('11')}, WAC ON {res['wac_on']['solved']}/300 "
           f"(OFF {res['wac_off']['solved']}/300)")
    (log.ok if res["pass"] else log.fail)(msg)
    return res


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--ckpt")
    ap.add_argument("--l1", type=int, default=1024)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    cfg = C.read_json(a.config)
    C.set_below_normal()
    log = C.Log(os.path.join(cfg["root"], "logs", "pipeline.log"), "check")
    gov = C.Governor(cfg["root"], C.Limits(**cfg.get("limits", {})), log)
    try:
        res = run_check(cfg, a.net, a.out, a.l1, log, gov, a.ckpt)
        return 0 if res["pass"] else 1
    except C.StageFailed as e:
        log.fail(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
