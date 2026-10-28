#!/usr/bin/env python3
"""Recompute the evidence for "why Job A's NnueExactInt32 ON path was slower" (Sol S12, part 1).

Read-only. Nothing is built, run or written except stdout (and --json if given).
Inputs:
  * Sol's raw Job A files on his branch (commit 17aa0cae, validation/forge_sol_jobACD_20261025/):
    the 20 counter bench logs, the 80 advisory bench logs plus the controller JSON, and the
    saved NNUE disassembly of the timed candidate (exe aaf0f890) and of the compiled-out build.
  * QA's raw ABBA arrays (qa_evidence/abba_results.json, abba_C3_rerun.json) from the AL1 lock
    archive, 7_history/rejected_and_shelved/int32_exact_h256e12_20261025/ (--qa-dir).
  * O2's callgrind summaries (origin/opus-O2, opus_round1/O2/logs/ci_perf_edcf163/).
  * The AL1 lock source (d4f4312, src/search.cpp) for the refresh/update call sites.

Usage:
  python -I jobA_cause.py --repo <git dir that has 17aa0cae, d4f4312, origin/opus-O2> \
      --qa-dir <lock archive>/7_history/rejected_and_shelved/int32_exact_h256e12_20261025 [--json out.json]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import random
import re
import statistics
import subprocess
import sys
from pathlib import Path

SOL_REV = "17aa0cae"
LOCK_REV = "d4f4312"
O2_REV = "origin/opus-O2"
JA = "validation/forge_sol_jobACD_20261025"
DEPTHS = (11, 13, 16, 20, 22)
# Sol's dev base (1ab50b2d + h256_e12 net) bench node references; Job A ran on that base.
SOL_REFS = {11: 308972, 13: 745494, 16: 2460422, 20: 11901452, 22: 31111774}
BOOT_SEED = 20261027
BOOT_N = 10000

BENCH_RE = re.compile(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)")
STATS_RE = re.compile(
    r"stats refreshes (\d+) updates (\d+) evaluations (\d+) int32_refreshes (\d+) int32_updates (\d+)")
FUNC_RE = re.compile(r"^[0-9a-f]+ <(.*)>:$")
ADDR_RE = re.compile(r"^\s+([0-9a-f]+):\t(.*)$")

# Address ranges in the timed candidate's disassembly (sha256 below), quoted in the report.
B_DISASM = f"{JA}/forge_sol_a_lock_checks_20261025/forge_sol_nnue_disassembly_20261025.txt"
OUT_DISASM = f"{JA}/forge_sol_a_compiled_out_checks_20261025/forge_sol_nnue_disassembly_20261025.txt"
B_DISASM_SHA256 = "f768bc90813bb8b24dd32d2f823ebeb679946043cd827bc1d2519d4a0dfb9bbe"
OUT_DISASM_SHA256 = "bba81094dd8cd55e2c43b4ca5e552b03ce89ac16381513e16d3debfdca77f22d"
INT32_LOOP = (0x41C4A0, 0x41C540)       # update_exact's vector loop (inlined into update), all change counts
CONVERT_LOOP = (0x41CF00, 0x41CF28)     # int32 -> float conversion at the top of every ON evaluate()
# Float kernels of the same exe (its OFF path): one perspective = 256 lanes, fully unrolled.
FLOAT_KERNELS = (
    ("quiet", 0x41BED3, 0x41C092),       # 16 x (vmovups load, vsubps, vaddps, vmovups store) + 1 add
    ("capture", 0x41C9EE, 0x41CC22),     # 16 x (load, vsubps, vsubps, vaddps, store) + 3 adds
)
# One steady-state iteration (8 int32 lanes) of the int32 loop, traced by hand; check_path()
# verifies that every step is a fall-through or the target of the previous branch.
INT32_PATHS = {
    "quiet": [0x41C514, 0x41C519, 0x41C51B, 0x41C51D, 0x41C523, 0x41C527, 0x41C52B, 0x41C52D, 0x41C531, 0x41C534,
              0x41C4A0, 0x41C4A6, 0x41C4AA, 0x41C4AE, 0x41C4B4, 0x41C4B7,
              0x41C500, 0x41C505, 0x41C509, 0x41C50F, 0x41C511],
    "capture": [0x41C514, 0x41C519, 0x41C51B, 0x41C51D, 0x41C523, 0x41C527, 0x41C52B, 0x41C52D, 0x41C531, 0x41C534,
                0x41C4A0, 0x41C4A6, 0x41C4AA, 0x41C4AE, 0x41C4B0, 0x41C4B4, 0x41C4B7,
                0x41C4B9, 0x41C4BF, 0x41C4C3, 0x41C4C7, 0x41C4CD, 0x41C4D0,
                0x41C53A, 0x41C53E,
                0x41C500, 0x41C505, 0x41C509, 0x41C50F, 0x41C511],
}
LANES_PER_UPDATE = 2 * 256              # both perspectives, H256


class EvidenceError(RuntimeError):
    pass


def git_show(repo: str, rev: str, path: str) -> bytes:
    proc = subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"], capture_output=True)
    if proc.returncode != 0:
        raise EvidenceError(f"git show {rev}:{path} failed: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def as_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").lstrip("﻿")


def parse_bench(text: str) -> dict | None:
    matches = BENCH_RE.findall(text)
    if not matches:
        return None
    depth, nodes, time_ms, nps = (int(x) for x in matches[-1])
    return {"depth": depth, "nodes": nodes, "time_ms": time_ms, "nps": nps}


def parse_stats(text: str) -> dict | None:
    m = STATS_RE.search(text)
    if not m:
        return None
    keys = ("refreshes", "updates", "evaluations", "int32_refreshes", "int32_updates")
    return dict(zip(keys, (int(x) for x in m.groups())))


def abba_ratios(quads):
    """ABBA blocks [A1, B1, B2, A2] (any per-run speed) -> [B1/A1, B2/A2, ...]."""
    out = []
    for a1, b1, b2, a2 in quads:
        out += [b1 / a1, b2 / a2]
    return out


def block_bootstrap_median_ci(quads, n_boot=BOOT_N, seed=BOOT_SEED, level=0.95):
    """Percentile CI of the median ratio, resampling whole ABBA blocks (their two ratios share
    the block's machine state, so they are not independent)."""
    rng = random.Random(seed)
    blocks = [abba_ratios([q]) for q in quads]
    meds = []
    for _ in range(n_boot):
        sample = []
        for _ in range(len(blocks)):
            sample += blocks[rng.randrange(len(blocks))]
        meds.append(statistics.median(sample))
    meds.sort()
    lo = meds[int(math.floor((1 - level) / 2 * n_boot))]
    hi = meds[int(math.ceil((1 + level) / 2 * n_boot)) - 1]
    return lo, hi


def binom_two_sided(k: int, n: int) -> float:
    """Exact two-sided sign-test p-value for k successes in n fair trials."""
    pmf = [math.comb(n, i) / 2 ** n for i in range(n + 1)]
    lower = sum(pmf[: k + 1])
    upper = sum(pmf[k:])
    return min(1.0, 2 * min(lower, upper))


def summarize(quads) -> dict:
    ratios = abba_ratios(quads)
    lo, hi = block_bootstrap_median_ci(quads)
    below = sum(1 for r in ratios if r < 1.0)
    return {
        "n_ratios": len(ratios),
        "median": statistics.median(ratios),
        "ci95_block_bootstrap": [lo, hi],
        "min": min(ratios),
        "max": max(ratios),
        "below_1": below,
        "sign_test_p": binom_two_sided(below, len(ratios)),
    }


def scan_disassembly(text: str) -> "collections.OrderedDict[str, collections.Counter]":
    funcs: collections.OrderedDict[str, collections.Counter] = collections.OrderedDict()
    cur = None
    for line in text.splitlines():
        m = FUNC_RE.match(line.strip())
        if m:
            cur = m.group(1)
            funcs[cur] = collections.Counter()
            continue
        a = ADDR_RE.match(line)
        if cur is None or not a:
            continue
        ins = a.group(2).split("\t")[-1].strip()
        if not ins:
            continue
        c = funcs[cur]
        c["insns"] += 1
        if "%zmm" in ins:
            c["zmm"] += 1
        elif "%ymm" in ins:
            c["ymm"] += 1
        elif "%xmm" in ins:
            c["xmm"] += 1
        mnem = ins.split()[0]
        if mnem == "vpmovsxwd":
            c["vpmovsxwd"] += 1
        if mnem.startswith("vcvtdq2ps"):
            c["vcvtdq2ps"] += 1
        if mnem.startswith(("vfmadd", "vfnmadd", "vfmsub", "vfnmsub")):
            c["fma"] += 1
        if mnem == "incq" and "%fs:" in ins:
            c["tls_counter_inc"] += 1
        if mnem == "call":
            c["call"] += 1
    return funcs


def listing(text: str, start: int = 0, end: int = 1 << 64):
    rows = []
    for line in text.splitlines():
        a = ADDR_RE.match(line)
        if not a:
            continue
        addr = int(a.group(1), 16)
        if start <= addr < end:
            ins = a.group(2).split("\t")[-1].strip()
            ins = re.sub(r"\s+<[^>]*>", "", ins)
            rows.append((addr, ins))
    return rows


def is_padding(ins: str) -> bool:
    return ins.startswith(("nop", "data16", "xchg   %ax,%ax"))


def check_path(rows, path, closed=True) -> bool:
    """True if each step of `path` is the fall-through of the previous instruction or the target of
    its branch (conditional: either; jmp: target only). `closed` also checks last -> first."""
    index = {addr: i for i, (addr, _) in enumerate(rows)}
    steps = list(zip(path, path[1:] + ([path[0]] if closed else [])))
    for a, b in steps:
        if a not in index or b not in index:
            return False
        ins = rows[index[a]][1]
        mnem, _, operand = ins.partition(" ")
        nxt = rows[index[a] + 1][0] if index[a] + 1 < len(rows) else None
        if mnem.startswith("j"):
            target = int(operand.strip(), 16)
            allowed = {target} if mnem == "jmp" else {target, nxt}
        else:
            allowed = {nxt}
        if b not in allowed:
            return False
    return True


def section(title: str):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def do_counters(repo: str, out: dict):
    section("1. Accumulator work counters, Sol's raw bench logs (Job A feature build, lock and buffix bases)")
    rows = {}
    for base in ("lock", "buffix"):
        for mode in ("off", "on"):
            for d in DEPTHS:
                path = f"{JA}/forge_sol_a_{base}_checks_20261025/forge_sol_{mode}_bench_d{d}_20261025.stdout"
                text = as_text(git_show(repo, SOL_REV, path))
                bench, stats = parse_bench(text), parse_stats(text)
                if bench is None or stats is None:
                    raise EvidenceError(f"unparsable counter log {path}")
                if bench["depth"] != d or bench["nodes"] != SOL_REFS[d]:
                    raise EvidenceError(f"{path}: depth/nodes {bench} != ref {SOL_REFS[d]}")
                if mode == "on" and (stats["int32_updates"] != stats["updates"] or stats["int32_refreshes"] != stats["refreshes"]):
                    raise EvidenceError(f"{path}: ON log did not run every construction in int32")
                if mode == "off" and (stats["int32_updates"] or stats["int32_refreshes"]):
                    raise EvidenceError(f"{path}: OFF log ran int32 work")
                rows[(base, mode, d)] = stats
    print(f"20 logs parsed; nodes = {SOL_REFS} in every log; ON runs every construction in int32, OFF none.")
    print(f"{'depth':>5} {'refreshes':>9} {'updates':>10} {'evaluations':>11} {'refresh/(refresh+update)':>25} {'updates/refresh':>15}")
    table = []
    for d in DEPTHS:
        keys = {(rows[(b, m, d)]["refreshes"], rows[(b, m, d)]["updates"], rows[(b, m, d)]["evaluations"])
                for b in ("lock", "buffix") for m in ("off", "on")}
        if len(keys) != 1:
            raise EvidenceError(f"d{d}: counts differ between bases/modes: {keys}")
        r, u, e = keys.pop()
        share = r / (r + u)
        print(f"{d:>5} {r:>9} {u:>10} {e:>11} {share * 100:>24.9f}% {u / r:>15,.0f}")
        table.append({"depth": d, "refreshes": r, "updates": u, "evaluations": e, "refresh_share": share})
    print("Same counts for lock and buffix, OFF and ON, at every depth (checked).")
    out["counters"] = table


def do_advisory(repo: str, out: dict):
    section("2. Sol's advisory ABBA (shared Xeon 8573C, GCC 14.2 -march=znver5 static): recomputed from the 80 raw logs")
    ctrl_path = f"{JA}/forge_sol_a_advisory_abba_20261025/forge_sol_advisory_result_20261025.json"
    ctrl = json.loads(as_text(git_show(repo, SOL_REV, ctrl_path)))
    res = {}
    for d in (13, 16):
        quads, times = [], {"A": [], "B": []}
        for blk in range(10):
            runs = []
            for i, ab in ((0, "A"), (1, "B"), (2, "B"), (3, "A")):
                path = f"{JA}/forge_sol_a_advisory_abba_20261025/forge_sol_d{d}_block{blk:02d}_{i}_{ab}_20261025.stdout"
                bench = parse_bench(as_text(git_show(repo, SOL_REV, path)))
                if bench is None or bench["nodes"] != SOL_REFS[d]:
                    raise EvidenceError(f"{path}: bad bench line {bench}")
                runs.append(bench)
                times[ab].append(bench["time_ms"])
            quads.append([r["nps"] for r in runs])
        ratios = abba_ratios(quads)
        ctrl_ratios = ctrl["depths"][str(d)]["ratios"]
        same = sum(1 for a, b in zip(ratios, ctrl_ratios) if a == b)
        if same != len(ctrl_ratios) or len(ratios) != len(ctrl_ratios):
            raise EvidenceError(f"d{d}: raw logs reproduce only {same}/{len(ctrl_ratios)} controller ratios")
        s = summarize(quads)
        s["controller_median"] = ctrl["depths"][str(d)]["median_ratio"]
        s["A_time_ms_min_med_max"] = [min(times["A"]), statistics.median(times["A"]), max(times["A"])]
        s["B_time_ms_min_med_max"] = [min(times["B"]), statistics.median(times["B"]), max(times["B"])]
        res[d] = s
        print(f"d{d}: raw logs reproduce all {same}/20 controller ratios exactly; median B/A = {s['median']:.4f} "
              f"(controller {s['controller_median']:.4f})")
        print(f"     95% block-bootstrap CI of the median [{s['ci95_block_bootstrap'][0]:.4f}, {s['ci95_block_bootstrap'][1]:.4f}];"
              f" ratio range {s['min']:.3f}..{s['max']:.3f}; {s['below_1']}/20 below 1 (sign test p = {s['sign_test_p']:.3f})")
        print(f"     A bench time ms min/median/max {s['A_time_ms_min_med_max']}; B {s['B_time_ms_min_med_max']}")
    out["sol_advisory"] = res


def do_qa(qa_dir: Path, out: dict):
    section("3. QA's box ABBA arrays (shared Intel Xeon box, g++-14 -march=x86-64-v3, CPU1, nice 19): recomputed")
    labels = {
        "C1_swON_ON_vs_lock": "switch-ON build, option ON  vs  plain lock",
        "C2_swON_ON_vs_swON_OFF": "same binary: option ON  vs  option OFF",
        "C3_default_build_vs_lock": "switch-OFF build  vs  plain lock (first run)",
        "C3_default_build_vs_lock_rerun20": "switch-OFF build  vs  plain lock (20-block rerun)",
        "C4_buffix_swON_ON_vs_buffix": "buffix + switch-ON build, option ON  vs  buffix",
    }
    res = {}
    for fname in ("abba_results.json", "abba_C3_rerun.json"):
        path = qa_dir / "qa_evidence" / fname
        raw = path.read_bytes()
        data = json.loads(as_text(raw))
        print(f"{fname}: sha256 {hashlib.sha256(raw).hexdigest()}")
        for key, val in data.items():
            quads = val["raw_ABBA"]
            s = summarize(quads)
            if abs(s["median"] - val["median"]) > 1e-12 or s["n_ratios"] != val["n_ratios"]:
                raise EvidenceError(f"{fname}:{key}: recomputed median {s['median']} != stored {val['median']}")
            stem = re.sub(r"_d1[36]$", "", key)
            depth = key[-3:]
            res[key] = s
            print(f"  {key:<40} {labels.get(stem, ''):<52} {depth}: median {s['median']:.4f} "
                  f"CI95 [{s['ci95_block_bootstrap'][0]:.4f}, {s['ci95_block_bootstrap'][1]:.4f}] "
                  f"below1 {s['below_1']}/{s['n_ratios']} (p {s['sign_test_p']:.4f})")
    out["qa_box"] = res
    print("All stored medians reproduced from the raw nps quadruples.")


def do_disassembly(repo: str, out: dict):
    section("4. Machine code of the timed candidate B (exe aaf0f890) and of the compiled-out build (exe f4365f19)")
    res = {}
    texts = {}
    for label, path, want in (("B (feature build, ON-capable; the timed binary)", B_DISASM, B_DISASM_SHA256),
                              ("compiled-out build (switch OFF)", OUT_DISASM, OUT_DISASM_SHA256)):
        raw = git_show(repo, SOL_REV, path)
        got = hashlib.sha256(raw).hexdigest()
        if got != want:
            raise EvidenceError(f"{path}: sha256 {got} != {want}")
        text = as_text(raw)
        texts[path] = text
        funcs = scan_disassembly(text)
        print(f"{label}: {path.rsplit('/', 2)[-2]}/... sha256 {got[:16]}...")
        print(f"  {'insns':>6} {'zmm':>4} {'ymm':>4} {'xmm':>4} {'vpmovsxwd':>9} {'vcvtdq2ps':>9} {'fma':>3} {'tls++':>5} {'call':>4}  function")
        rows = {}
        for name, c in funcs.items():
            if c["insns"] < 40:
                continue
            short = name.replace("(anonymous namespace)::", "").replace("forge::nnue::", "")
            short = re.sub(r"\(.*", "", short)
            print(f"  {c['insns']:>6} {c['zmm']:>4} {c['ymm']:>4} {c['xmm']:>4} {c['vpmovsxwd']:>9} {c['vcvtdq2ps']:>9} "
                  f"{c['fma']:>3} {c['tls_counter_inc']:>5} {c['call']:>4}  {short}")
            rows[short] = dict(c)
        res[label] = rows
    brows = listing(texts[B_DISASM])

    print("\n  B, int32 update loop (update_exact inlined into update), "
          f"{INT32_LOOP[0]:#x}..{INT32_LOOP[1]:#x}, non-padding instructions:")
    for addr, ins in brows:
        if INT32_LOOP[0] <= addr < INT32_LOOP[1] and not is_padding(ins):
            print(f"    {addr:x}: {ins}")
    print(f"  B, int32 -> float conversion loop at the top of every ON evaluate(), "
          f"{CONVERT_LOOP[0]:#x}..{CONVERT_LOOP[1]:#x}:")
    conv = [(a, i) for a, i in brows if CONVERT_LOOP[0] <= a < CONVERT_LOOP[1] and not is_padding(i)]
    for addr, ins in conv:
        print(f"    {addr:x}: {ins}")

    per_update = {}
    print("\n  Dynamic instructions per accumulator update, kernel loop only (both perspectives, 512 lanes):")
    for kind, start, end in FLOAT_KERNELS:
        body = [(a, i) for a, i in brows if start <= a < end]
        vec = sum(1 for _, i in body if "%zmm" in i)
        if any(is_padding(i) or i.startswith("j") for _, i in body):
            raise EvidenceError(f"float {kind} kernel range is not straight-line code")
        float_n = 2 * len(body)
        path = INT32_PATHS[kind]
        if not check_path(brows, path):
            raise EvidenceError(f"int32 {kind} path is not a valid control-flow path in B")
        branches = sum(1 for a in path if dict(brows)[a].startswith("j"))
        int32_n = len(path) * (LANES_PER_UPDATE // 8)
        per_update[kind] = {"float": float_n, "int32": int32_n}
        print(f"    {kind:<7}: float (OFF) {len(body)} straight-line instructions per perspective ({vec} zmm = 16 lanes each)"
              f" -> {float_n};  int32 (ON) {len(path)} per 8 lanes incl. {branches} branches (path checked)"
              f" x {LANES_PER_UPDATE // 8} -> {int32_n}  ({int32_n / float_n:.1f}x)")
    conv_n = len(conv) * 32
    print(f"    evaluate: ON adds the conversion loop, {len(conv)} instructions x 32 iterations = {conv_n} per call,"
          " plus 2 KiB of stack stores and an out-of-line call to evaluate_values")
    counters = {row["depth"]: row for row in out.get("counters", [])}
    if 13 in counters:
        u, e = counters[13]["updates"], counters[13]["evaluations"]
        lo = (per_update["quiet"]["int32"] - per_update["quiet"]["float"]) * u + conv_n * e
        hi = (per_update["capture"]["int32"] - per_update["capture"]["float"]) * u + conv_n * e
        print(f"  MODEL (static, not a measurement): at d13 ({u:,} updates, {e:,} evaluations) the ON path executes"
              f" about {lo / 1e9:.2f}-{hi / 1e9:.2f} G more instructions than OFF (all-quiet .. all-capture move mix;"
              " the mix is not logged). Instructions are not cycles; see REPORT.md.")
        res["model_d13_extra_instructions"] = [lo, hi]
    res["per_update_kernel_instructions"] = per_update
    res["conversion_instructions_per_eval"] = conv_n
    out["disassembly"] = res


def do_o2(repo: str, out: dict):
    section("5. O2's callgrind, bench 13 on AL1 s198 (CI run 40410897098; box recipe, g++-14; unit = instructions Ir)")
    res = {}
    for name in ("profile_self_lock.txt", "profile_self_branch.txt"):
        text = as_text(git_show(repo, O2_REV, f"opus_round1/O2/logs/ci_perf_edcf163/{name}"))
        total = None
        listed = []
        for line in text.splitlines():
            m = re.match(r"^\s*([\d,]+) \(\s*([\d.]+)%\)\s+(.*)$", line)
            if not m:
                continue
            ir = int(m.group(1).replace(",", ""))
            if "PROGRAM TOTALS" in m.group(3):
                total = ir
                continue
            listed.append((ir, m.group(3)))
        nnue = [(ir, f) for ir, f in listed if "nnue::" in f]
        smallest = min(ir for ir, _ in listed)
        refresh_listed = any("nnue::refresh" in f for _, f in listed)
        print(f"{name}: total {total:,} Ir; {len(listed)} listed lines, smallest listed {smallest:,} Ir "
              f"({smallest / total * 100:.2f}%); nnue::refresh listed: {refresh_listed}")
        for ir, f in nnue:
            short = re.sub(r"\[.*\]$", "", f).strip()
            print(f"    {ir:>13,} ({ir / total * 100:5.2f}%)  {short[:110]}")
        res[name] = {"total_ir": total, "nnue_lines": [[ir, f] for ir, f in nnue],
                     "smallest_listed_ir": smallest, "refresh_listed": refresh_listed}
    out["o2_callgrind"] = res
    print("Not listed means below the smallest listed line. O2's REPORT.md (section 3) puts refresh below 0.1%;"
          " 8 refreshes against ~10^6 updates make it ~1e-5 of the NNUE work.")


def do_lock_source(repo: str, out: dict):
    section("6. AL1 lock source (d4f4312): where accumulators are refreshed and updated")
    text = as_text(git_show(repo, LOCK_REV, "src/search.cpp"))
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if any(k in line for k in ("nnue::refresh(", "nnue::update(", "int Worker::static_evaluate",
                                    "void Worker::record_move", "void Worker::record_null_move",
                                    "(ss + 1)->dirty", "accumulator.valid = false")):
            hits.append((i, line.strip()))
            print(f"  src/search.cpp:{i}: {line.strip()}")
    refresh_sites = [i for i, l in hits if "nnue::refresh(" in l]
    out["lock_source"] = {"hits": hits, "refresh_sites": refresh_sites}
    print(f"  nnue::refresh call sites: {refresh_sites} (static_evaluate fallback when no ancestor is valid,"
          " and the once-per-search root refresh)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="git dir that has commits 17aa0cae, d4f4312 and origin/opus-O2")
    ap.add_argument("--qa-dir", required=True, type=Path,
                    help="lock archive 7_history/rejected_and_shelved/int32_exact_h256e12_20261025")
    ap.add_argument("--json", type=Path, help="also write the computed numbers as JSON here")
    args = ap.parse_args(argv)
    out: dict = {"inputs": {"sol_rev": SOL_REV, "lock_rev": LOCK_REV, "o2_rev": O2_REV,
                            "qa_dir": str(args.qa_dir), "bootstrap": {"seed": BOOT_SEED, "n": BOOT_N}}}
    try:
        do_counters(args.repo, out)
        do_advisory(args.repo, out)
        do_qa(args.qa_dir, out)
        do_disassembly(args.repo, out)
        do_o2(args.repo, out)
        do_lock_source(args.repo, out)
    except EvidenceError as exc:
        print(f"EVIDENCE ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        args.json.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    section("RESULT: all inputs parsed and cross-checked (see REPORT.md for the interpretation)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
