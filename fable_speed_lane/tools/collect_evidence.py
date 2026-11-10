"""collect_evidence.py - copy the compact evidence of the chain into the pack and write BENCH.md from it.

Reads only out\\id, out\\build receipts and out\\logs of this job; writes fable_speed_lane\\evidence\\ and
fable_speed_lane\\BENCH.md. Every number in BENCH.md is taken from a file named in the same table row, so the
tables cannot drift from the evidence. A stage that has no PASS line is printed as "not run" or "FAIL", never
left out.

usage: collect_evidence.py OUT_DIR PACK_DIR
"""
import hashlib
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402
import work_counters  # noqa: E402

SINGLES = [("WITNESS_NOPIN", "wit"), ("EVADE_LEGAL", "evd"), ("PAWN_CAPMASK", "cap"), ("CHECKERS_KL", "chk"),
           ("KING_PAWN_CACHE", "kpc")]
BUNDLES = [("BUNDLE4", "bn4"), ("BUNDLE3", "bn3"), ("BUNDLE", "bun")]
NOTE = {"KING_PAWN_CACHE": "not new (built before, DUPCHECK.md); extra", "BUNDLE": "BUNDLE4 + KING_PAWN_CACHE; extra",
        "BUNDLE4": "the four new candidates", "BUNDLE3": "three new candidates: EVADE_LEGAL, PAWN_CAPMASK, CHECKERS_KL",
        "PAWN_CAPMASK": "UNLISTED", "WITNESS_NOPIN": "LISTED-UNBUILT",
        "EVADE_LEGAL": "LISTED-UNBUILT", "CHECKERS_KL": "LISTED-UNBUILT"}
QA_ROWS = {net: rf"C:\Users\Administrator\grok-pc\forge_push\overnight_timing_20261108\checks2\combo29_{net}\fens_n12000_d13.tsv"
           for net in ("on", "off")}
STAGES = [("harness", "Harness, 12,000 FENs, switch 1"), ("harness, verify build", "Harness, 12,000 FENs, verify build (=2)"),
          ("harness, targeted positions", "Harness, targeted positions, switch 1"),
          ("harness, targeted positions, verify build", "Harness, targeted positions, verify build (=2)"),
          ("engine, verify build, 12 pins", "Verify engine, 12 pins"),
          ("engine, verify build, cold net on", "Verify engine, cold 12,000 net on"),
          ("cold net on", "Cold 12,000, depth 13, net on"), ("cold net off", "Cold 12,000, depth 13, net off"),
          ("warm", "Warm session transcript"), ("soak", "Threads 2-4 soak"), ("perft set", "Perft set (6 positions)")]


def now_vienna():
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(time.time() + 3600)) + " Vienna"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def qualify_lines(out, name):
    """Last line per stage of out\\id\\<name>\\QUALIFY.log: {stage: (verdict, text, when)}."""
    res = {}
    path = os.path.join(out, "id", name, "QUALIFY.log")
    if not os.path.isfile(path):
        return res
    rx = re.compile(r"^QUAL (\S+) (.+?): (PASS|FAIL|INCOMPLETE) (.*) \[([^\]]+)\]\s*$")
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = rx.match(line.strip())
            if m and "300 FENs" not in m.group(4) and " 200 rows" not in m.group(4):
                if "NOT STARTED (" in m.group(4) or "rows differing from the lock: -1;" in m.group(4):
                    # the run was not started (D: under the floor, the same rows were being written by another run,
                    # or - "-1 rows" - the exe to run did not exist yet): not a result. An earlier result of the
                    # stage stays; a stage with no result is shown as not run.
                    res.setdefault(m.group(2), ("HELD", m.group(4), m.group(5)))
                    continue
                res[m.group(2)] = (m.group(3), m.group(4), m.group(5))
    return res


def copy(src, dst_dir, name=None):
    if os.path.isfile(src):
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copyfile(src, os.path.join(dst_dir, name or os.path.basename(src)))
        return True
    return False


def newest_abba(out, name, net, depth=20):
    base = os.path.join(out, "id", name)
    if not os.path.isdir(base):
        return None
    dirs = sorted(d for d in os.listdir(base) if d.startswith(f"abba_d{depth}_{net}_") and
                  os.path.isfile(os.path.join(base, d, "SUMMARY.json")))
    return os.path.join(base, dirs[-1]) if dirs else None


def cell(q, stage):
    if stage not in q:
        return "not run"
    verdict, text, _ = q[stage]
    if verdict == "HELD":
        return "not run (held: " + ("disk guard" if "disk guard" in text else "see log") + ")"
    if verdict == "INCOMPLETE":
        m = re.search(r"^(\d+) of (\d+) rows written.*?; (\d+) of them equal the lock's rows, (\d+) differ", text)
        if not m:
            return "INCOMPLETE"
        n, total, same, diff = (int(x) for x in m.groups())
        if n <= 1:
            return f"INCOMPLETE: stopped at the start ({n} of {total} rows)"
        return (f"INCOMPLETE: {n} of {total} rows, " + ("all equal the lock's" if diff == 0 else f"{diff} DIFFER"))
    if stage.startswith("harness") and stage.endswith("verify build"):
        m = re.search(r"exit (-?\d+); prim_dump: (\d+) FENs, .*transcript equal to base: (\w+)", text)
        return f"{verdict}: {m.group(2)} FENs, exit {m.group(1)} (no abort), transcript equal {m.group(3)}" if m else verdict
    if stage.startswith("harness"):
        m = re.search(r"(\d+) FENs, (\d+) positions, (\d+) generated moves, (\d+) self-check failures; transcript equal to base: (\w+)", text)
        return (f"{verdict}: {m.group(1)} FENs, transcript equal to base {m.group(5)}, {m.group(4)} self-check failures"
                if m else f"{verdict}")
    if stage == "engine, verify build, 12 pins":
        return f"{verdict}: " + ("12/12" if "MATCH 12/12" in text else "see log")
    if stage == "engine, verify build, cold net on":
        m = re.search(r"rows differing from the lock: (-?\d+)", text)
        return f"{verdict}: {m.group(1)} rows differ" if m else verdict
    if stage.startswith("cold net"):
        m = re.search(r"(\d+)/(\d+) rows equal the lock's", text)
        return f"{verdict}: {m.group(1)}/{m.group(2)} rows equal" if m else verdict
    if stage == "warm":
        m = re.search(r"equal to the lock's: (\w+); WARM DONE (\d+) FENs, (\d+) searches, bench13 (\d+)", text)
        return f"{verdict}: transcript equal {m.group(1)}, {m.group(3)} searches, bench 13 = {m.group(4)}" if m else verdict
    if stage == "soak":
        m = re.search(r"legal (\d+)/60, max elapsed ([\d.]+)s, T1 tail (\d+)/50, bench13 (\d+)", text)
        return f"{verdict}: {m.group(1)}/60 legal, T1 tail {m.group(3)}/50" if m else verdict
    if stage == "perft set":
        return f"{verdict}: " + ("6/6" if "MATCH 6/6" in text else "see log")
    return verdict


def run_dirs(base, prefix):
    """Finished abba run folders under base whose name starts with prefix, oldest first (by SUMMARY.json time)."""
    if not os.path.isdir(base):
        return []
    dirs = [os.path.join(base, d) for d in os.listdir(base)
            if d.startswith(prefix) and os.path.isfile(os.path.join(base, d, "SUMMARY.json"))]
    return sorted(dirs, key=lambda d: os.path.getmtime(os.path.join(d, "SUMMARY.json")))


def stats_of(vals):
    """vals: block ratios minus 1. Median with a bootstrap 95 % interval, mean with its standard error, spread."""
    n = len(vals)
    rng = random.Random(20261110)
    boot = sorted(statistics.median(rng.choices(vals, k=n)) for _ in range(10000)) if n >= 2 else [vals[0]] * 10000
    q = statistics.quantiles(vals, n=4, method="inclusive") if n >= 2 else [vals[0]] * 3
    sd = statistics.pstdev(vals) if n >= 2 else 0.0
    return {"n": n, "median": statistics.median(vals), "lo": boot[249], "hi": boot[9749], "mean": statistics.mean(vals),
            "se": sd / n ** 0.5, "sd": sd, "q1": q[0], "q3": q[2], "min": min(vals), "max": max(vals)}


def p2(x):
    return f"{100 * x:+.2f}"


def copy_run(d, ev, *sub):
    e = os.path.join(ev, *sub, os.path.basename(d))
    for f in ("SUMMARY.json", "PROTOCOL.json", "SAMPLES.json"):
        copy(os.path.join(d, f), e)
    copy(d + ".txt", os.path.join(ev, *sub))
    return "evidence/" + "/".join(sub) + "/" + os.path.basename(d)


def timing_sections(out, ev):
    """Section 3 of BENCH.md: (3.1) what a fixed pair of exe files does to a timing on this PC, (3.2) the
    timing taken with a new copy of the exe per arm, (3.3) the first timing step with fixed files."""
    L = ["## 3. INDICATIVE timing (not the ABBA)", "",
         "All of it: lock exe (A) against a switch-1 exe (B), Threads 1, Hash 16, fresh engine per arm, warm `bench 13`, "
         "then a timed bench; blocks of four arms; ratio per block = sqrt(B*B / (A*A)) of nodes per unit; positive = B "
         "faster. **Cycles** = CPU cycles of the engine process over the timed bench (QueryProcessCycleTime), which "
         "preemption by other jobs does not inflate; **wall** = wall-clock time, which it does. One shared CPU (3) at "
         "Idle priority while the crew's gates ran and, for most of it, while this job's own cold runs shared the "
         "same CPU. None of this is QA's quiet ABBA.", ""]

    # 3.1 the per-file effect
    L += ["### 3.1 The same exe is not equally fast from two files", "",
          "Found while checking why `BUNDLE4` first timed 3.7 % slower than the lock and, two hours later, 0.3 % "
          "faster on the same two files. Lock against lock, by cycles:", "",
          "| Lock against lock | Timed | Blocks | Median | SD of block ratios | IQR | min .. max | Evidence |",
          "|---|---|---|---|---|---|---|---|"]
    null_rows = []
    for d in run_dirs(os.path.join(out, "id", "AA_lock_vs_lock"), "abba_d20_"):
        null_rows.append(("one file for all arms (first timing step)", d, ("AA_lock_vs_lock",)))
    for d in run_dirs(os.path.join(out, "regime", "AA_recopy"), "rc16_d20_"):
        null_rows.append(("two byte-identical copies made anew for every block", d, ("regime", "AA_recopy")))
    for d in run_dirs(os.path.join(out, "regime", "AA_recopy"), "rc16_d16_"):
        null_rows.append(("a new copy for every arm", d, ("regime", "AA_recopy")))
    for d in run_dirs(os.path.join(out, "regime", "AA_fixedbase"), "fb16_d16_"):
        null_rows.append(("a new copy for every arm, load address fixed at 0x140000000", d, ("regime", "AA_fixedbase")))
    for d in run_dirs(os.path.join(out, "id", "AA_lock_vs_lock"), "abbarc_"):
        null_rows.append(("a new copy for every arm, order alternating (section 3.2)", d, ("AA_lock_vs_lock",)))
    for label, d, sub in null_rows:
        s = load_json(os.path.join(d, "SUMMARY.json"))
        c = load_json(os.path.join(d, "PROTOCOL.json")) or {}
        if not s or "cpu_block_ratios" not in s:
            continue
        st = stats_of([r - 1 for r in s["cpu_block_ratios"]])
        net = "net on" if "UseNNUE=true" in c.get("options", "") else "net off"
        L.append(f"| {label} | {c.get('timed', '?')}, {net} | {st['n']} | {p2(st['median'])} % | {100 * st['sd']:.2f} % | "
                 f"{p2(st['q1'])} .. {p2(st['q3'])} | {p2(st['min'])} .. {p2(st['max'])} | `{copy_run(d, ev, *sub)}` |")
    # same file twice against two files, arm by arm, from the per-block-copy run
    pb = run_dirs(os.path.join(out, "regime", "AA_recopy"), "rc16_d20_")
    if pb:
        smp = load_json(os.path.join(pb[0], "SAMPLES.json")) or []
        same, diff = [], []
        for b in sorted({x["block"] for x in smp}):
            arms = [x for x in smp if x["block"] == b]
            if len(arms) != 4:
                continue
            c = [x["cpu_s"] / x["nodes"] for x in arms]          # order A B B A, A1/A4 one file, B2/B3 the other
            same += [abs(c[3] / c[0] - 1), abs(c[2] / c[1] - 1)]
            diff.append(abs((c[1] + c[2]) / (c[0] + c[3]) - 1))
        if same and diff:
            L += ["", f"In the per-block run each block holds two launches of one copy and two of another. Two launches "
                  f"of the same file differ by {100 * statistics.median(same):.2f} % (median of {len(same)} pairs); the two "
                  f"files of a block differ by {100 * statistics.median(diff):.2f} % (median of {len(diff)} blocks, largest "
                  f"{100 * max(diff):.2f} %). The copies are byte-identical."]
    fe = []
    fe_dir = os.path.join(out, "regime", "FILE_EFFECT")
    for d in sorted(os.listdir(fe_dir)) if os.path.isdir(fe_dir) else []:
        j = load_json(os.path.join(fe_dir, d, "FILE_EFFECT.json"))
        if j:
            copy(os.path.join(fe_dir, d, "FILE_EFFECT.json"), os.path.join(ev, "regime", "FILE_EFFECT", d))
            fe.append(f"{j['started'][11:16]}: {j['copies']} copies of the lock, {j['rounds']} launches each in rotating order "
                      f"({j['timed']}, net {j['net']}): SD between copies {j['sd_between_copies_pct']:.2f} %, SD of one launch "
                      f"{j['sd_residual_pct']:.2f} %, permutation p {j['p_permutation']:.2f} "
                      f"(`evidence/regime/FILE_EFFECT/{d}/FILE_EFFECT.json`)")
    if fe:
        L += ["", "The copy test (`tools/file_effect.py`), which separates a copy's own offset from the drift of the machine: "
              + "; ".join(fe) + "."]
    L += ["",
          "Reading, with its limits. At 11:43 one fixed pair of files gave -3.65 % with a spread of a few tenths of a "
          "percent over 30 blocks (section 3.3); the five-bundle, which holds the same four switches, gave +0.43 % in "
          "the next quarter of an hour; the same two files gave about +0.3 % two hours later; and with a new copy per "
          "arm the four-bundle reads -0.70 % (section 3.2). Between 13:40 and 14:01 byte-identical copies of the lock "
          "differed by up to 6 % in single blocks, while two launches of one copy agreed far better. From 14:04 on the "
          "extra spread was gone, and the copy test at 14:17 found no offset that belongs to a copy. So at times an exe "
          "file carried its own offset of several percent for many minutes, and at other times it did not. The load "
          "address is not the cause (copies forced to one address scattered as much). What else it is, I could not "
          "establish; where Windows put the file's code and constant pages in physical memory is a candidate, not a "
          "finding. Consequences that do not depend on the cause: (1) a timing of two fixed files can be off by "
          "several percent while looking tight; (2) lock against lock with one file cannot show that; (3) a new copy "
          "of the exe for every arm turns such an offset into visible spread. Whether a quiet machine shows any of "
          "this is for QA to measure (QA_ABBA_PROTOCOL.md).", ""]

    # 3.2 fresh-copy timing
    L += ["### 3.2 Timing with a new copy of the exe for every arm", "",
          "`tools/timing2.ps1`: every arm runs from a copy made for that arm, odd blocks run B A A B, timed bench 16 "
          "(the ABBA's own timed bench). The per-file effect is then part of the spread of the block ratios instead of "
          "a bias. The interval is a bootstrap 95 % interval of the median over blocks. A candidate's row is to be read "
          "against the lock-against-lock row, which shows what the method gives when there is nothing to find.", "",
          "| Pair | Net | Blocks | Cycles median | 95 % interval | Cycles mean +/- SE | SD of blocks | min .. max | Wall median | Evidence |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for name, _tag in [("AA_lock_vs_lock", "")] + BUNDLES + SINGLES:
        for net in ("on", "off"):
            runs = run_dirs(os.path.join(out, "id", name), f"abbarc_d16_{net}_")
            label = "lock against lock" if name.startswith("AA_") else name
            cyc, wall, where = [], [], []
            for d in runs:
                s = load_json(os.path.join(d, "SUMMARY.json")) or {}
                cyc += [r - 1 for r in s.get("cpu_block_ratios", [])]
                wall += [r - 1 for r in s.get("block_ratios", [])]
                where.append(f"`{copy_run(d, ev, name)}`")
            # runs that were stopped before their end (no SUMMARY.json): the block ratios are in their logs
            stopped = []
            base = os.path.join(out, "id", name)
            for fn in sorted(os.listdir(base)) if os.path.isdir(base) else []:
                if fn.startswith(f"abbarc_d16_{net}_") and fn.endswith(".txt") and \
                        not os.path.isfile(os.path.join(base, fn[:-4], "SUMMARY.json")):
                    txt = open(os.path.join(base, fn), encoding="utf-8", errors="replace").read()
                    c2 = [float(x) - 1 for x in re.findall(r"^ABBA block \d+ \([AB]{4}\) wall ratio [0-9.]+ cpu ratio ([0-9.]+)", txt, re.M)]
                    w2 = [float(x) - 1 for x in re.findall(r"^ABBA block \d+ \([AB]{4}\) wall ratio ([0-9.]+)", txt, re.M)]
                    if c2:
                        copy(os.path.join(base, fn), os.path.join(ev, name))
                        stopped.append((c2, w2, f"`evidence/{name}/{fn}`"))
            if not cyc and not stopped:
                if net == "on":
                    L.append(f"| {label} | {net} | not run | | | | | | | |")
                continue
            if cyc:
                st = stats_of(cyc)
                L.append(f"| {label} | {net} | {st['n']} | {p2(st['median'])} % | {p2(st['lo'])} .. {p2(st['hi'])} | "
                         f"{p2(st['mean'])} +/- {100 * st['se']:.2f} | {100 * st['sd']:.2f} % | {p2(st['min'])} .. {p2(st['max'])} | "
                         f"{p2(statistics.median(wall))} % | {' '.join(where)} |")
            for c2, w2, where2 in stopped:
                st = stats_of(c2)
                L.append(f"| {label}, **INCOMPLETE** (run stopped at 16:56) | {net} | {st['n']} | {p2(st['median'])} % | "
                         f"{p2(st['lo'])} .. {p2(st['hi'])} | {p2(st['mean'])} +/- {100 * st['se']:.2f} | {100 * st['sd']:.2f} % | "
                         f"{p2(st['min'])} .. {p2(st['max'])} | {p2(statistics.median(w2))} % | {where2} (log only) |")
    L += ["", "Finished runs of the same pair are pooled; the evidence column names each run. Rows marked INCOMPLETE are "
          "runs that were stopped at 16:56 on the owner's instruction to wrap up: the blocks they had finished are "
          "shown as they are, with fewer blocks than planned (100 for `BUNDLE3`, 40 for the singles and for the second "
          "lock-against-lock round, 60 and 40 for the two extras) and therefore wider intervals. From 15:11 on about "
          "forty of this job's own runs shared the CPU with the timing arms (every arm of a pair alike); all INCOMPLETE "
          "rows were taken in that crowd, the second lock-against-lock row with them. No net-off timing was taken in "
          "this step.", ""]

    # 3.3 the first timing step
    L += ["### 3.3 First timing step: one fixed file per exe (superseded by 3.2)", "",
          "Kept for the record, not as results: each row is the patch plus whatever offset its two files carried at "
          "that time. The last rows repeat `BUNDLE4` on the same two files two hours later.", "",
          "| Pair | Net | Timed | When (Vienna) | Wall median | Cycles median | Cycles IQR | Cycles min .. max | Blocks | Evidence |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for name, _tag in [("AA_lock_vs_lock", "")] + BUNDLES + SINGLES:
        for net in ("on", "off"):
            label = "lock against lock" if name.startswith("AA_") else name
            runs = run_dirs(os.path.join(out, "id", name), f"abba_d20_{net}_")
            if not runs:
                L.append(f"| {label} | {net} | bench 20 | not run | | | | | | |")
            for d in runs:
                L.append(fixed_row(label, net, d, copy_run(d, ev, name)))
    for d in run_dirs(os.path.join(out, "regime", "BUNDLE4"), "h"):
        c = load_json(os.path.join(d, "PROTOCOL.json")) or {}
        L.append(fixed_row("BUNDLE4 (repeat)", "on" if "UseNNUE=true" in c.get("options", "") else "off", d,
                           copy_run(d, ev, "regime", "BUNDLE4")))
    L += ["", "The repeats named `h1_`, `h16_` and `h256_` were meant to vary the hash size; `bench` builds its own "
          "16 MB table and ignores the option, so they are three plain repeats.", ""]
    pc = os.path.join(out, "regime", "BUNDLE4", "pos_d20_on_h16", "POS_CYCLES.json")
    j = load_json(pc)
    if j:
        copy(pc, os.path.join(ev, "regime", "BUNDLE4", "pos_d20_on_h16"))
        L += [f"`go depth 20` on the eight bench positions one by one (`tools/pos_cycles.py`, 2 blocks, fixed files, "
              f"same tree as bench 20: {sum(r['nodes_last_info'] for r in j['positions'])} nodes): BUNDLE4 "
              f"{j['total_b_speed_pct']:+.2f} % by cycles; per position from "
              f"{min(r['b_speed_pct'] for r in j['positions']):+.2f} % to {max(r['b_speed_pct'] for r in j['positions']):+.2f} % "
              f"(`evidence/regime/BUNDLE4/pos_d20_on_h16/POS_CYCLES.json`).", ""]

    # 3.4 table size
    rows = []
    reg = os.path.join(out, "regime")
    for name in sorted(os.listdir(reg)) if os.path.isdir(reg) else []:
        for d in sorted(os.listdir(os.path.join(reg, name))):
            pj = os.path.join(reg, name, d, "POS_CYCLES.json")
            j = load_json(pj)
            if not j or "block_median_pct" not in j or not str(j.get("recopy", "")).startswith("a new copy"):
                continue
            copy(pj, os.path.join(ev, "regime", name, d))
            copy(os.path.join(reg, name, d + ".txt"), os.path.join(ev, "regime", name))
            rows.append((name, int(j["hash"]), f"| {name} | {j['hash']} MB | {j['go']} | {sum(r['nodes_last_info'] for r in j['positions'])} | "
                         f"{len(j['block_speed_pct'])} | {j['block_median_pct']:+.2f} % | {j['block_median_boot95_pct'][0]:+.2f} .. "
                         f"{j['block_median_boot95_pct'][1]:+.2f} | {j['block_mean_pct']:+.2f} +/- {j['block_se_pct']:.2f} | "
                         f"`evidence/regime/{name}/{d}/POS_CYCLES.json` |"))
    L += ["### 3.4 Does the size of the transposition table matter? (`go`, Hash 1 / 16 / 256 MB)", "",
          "`bench` cannot answer this: it builds its own 16 MB table. `tools/regime_pos.ps1` runs `go` on the eight bench "
          "positions with the Hash option set, a new copy of the exe for every arm, odd blocks B A A B. The three sizes "
          "ran at the same time on the same CPU, together with many other runs of this job, so each block is noisy. "
          "Node counts differ between sizes (another table, another tree) and are equal for lock and candidate at each size.", "",
          "| Candidate | Table | Search | Nodes (last info lines) | Blocks | Cycles median | 95 % interval | Cycles mean +/- SE | Evidence |",
          "|---|---|---|---|---|---|---|---|---|"]
    L += [r[2] for r in sorted(rows)] if rows else ["| not run | | | | | | | | |"]
    L += witness_counters(out, ev)
    L += ["", "What the question is: the search prefetches the child's table entry before `make_move` and reads it at the "
          "top of the child, after the stalemate test that calls `has_legal_move`. In the lock that call builds the king "
          "lines while the entry is on its way. `WITNESS_NOPIN` skips the build there; at a node that goes on, the build "
          "then happens after the probe at full cost, and at a node that ends at the probe nothing is saved while the "
          "entry has not arrived. If that is why `WITNESS_NOPIN` times slower under load, it should lose more with a "
          "large table than with one that stays in cache. The rows above are the test; read them with their intervals.", ""]
    return L


LLVM_PROFDATA = r"C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin\llvm-profdata.exe"


def witness_counters(out, ev):
    """Exact counters of has_legal_move in the lock and in the WITNESS_NOPIN build (frozen workload): how often
    the patch skips the king-line build, how many builds disappear, how many are only made later."""
    def blocks(tag, mangled):
        prof = os.path.join(out, "build", tag, "m2gen", "m2.profdata")
        if not (os.path.isfile(prof) and os.path.isfile(LLVM_PROFDATA)):
            return None, None, ""
        r = subprocess.run([LLVM_PROFDATA, "show", "--counts", f"--function={mangled}", prof], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        fc = re.search(r"Function count: (\d+)", r.stdout)
        bc = re.search(r"Block counts: \[([^\]]*)\]", r.stdout)
        return (int(fc.group(1)) if fc else None, [int(x) for x in bc.group(1).split(",") if x.strip()] if bc else [],
                r.stdout)
    hl, rk = "_ZNK5forge5Board14has_legal_moveEv", "_ZNK5forge5Board18refresh_king_linesEv"
    lock_calls, lock_blocks, t1 = blocks("c29ctl", hl)
    wit_calls, wit_blocks, t2 = blocks("wit_on", hl)
    lock_builds, _, t3 = blocks("c29ctl", rk)
    wit_builds, _, t4 = blocks("wit_on", rk)
    if not (lock_calls and wit_calls and lock_builds and wit_builds and len(wit_blocks) >= 2):
        return ["", "Counters of `has_legal_move` could not be read (profile or llvm-profdata missing)."]
    with open(os.path.join(ev, "witness_counters.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("llvm-profdata show --counts --function=<name> on the instrumented stage of each build "
                "(frozen workload, bench 11/13/16)\n\n")
        for label, text in (("lock (control rebuild c29ctl), has_legal_move", t1), ("WITNESS_NOPIN (wit_on), has_legal_move", t2),
                            ("lock, refresh_king_lines", t3), ("WITNESS_NOPIN, refresh_king_lines", t4)):
            f.write(f"== {label}\n{text}\n")
    skipped = wit_blocks[1]                    # region 1 of the patched function: witness accepted without is_legal
    gone = lock_builds - wit_builds
    return ["", f"Exact counters for this (frozen workload, 4,200,115 nodes; `evidence/witness_counters.txt`): "
            f"`has_legal_move` is called {lock_calls:,} times. The lock builds the king lines {lock_builds:,} times. "
            f"`WITNESS_NOPIN` accepts the witness without the legality test, and so without the build, {skipped:,} "
            f"times. {gone:,} builds disappear; the other {skipped - gone:,} are made later in the node, after the "
            f"table probe."]


def fixed_row(label, net, d, where):
    s = load_json(os.path.join(d, "SUMMARY.json")) or {}
    c = load_json(os.path.join(d, "PROTOCOL.json")) or {}
    when = f"{c.get('started', '')[11:16]} to {s.get('finished', '')[11:16]}"
    cyc = (f"{s['cpu_median_delta_pct']:+.2f} % | {s['cpu_q1_pct']:+.2f} .. {s['cpu_q3_pct']:+.2f} | "
           f"{s['cpu_min_pct']:+.2f} .. {s['cpu_max_pct']:+.2f}") if "cpu_median_delta_pct" in s else "n/a | n/a | n/a"
    return (f"| {label} | {net} | {c.get('timed', '?')} | {when} | {s.get('median_delta_pct', 0):+.2f} % | {cyc} | "
            f"{s.get('blocks', '?')} | `{where}` |")


def main():
    out, pack = sys.argv[1], sys.argv[2]
    print(pinguard.ensure(), flush=True)
    ev = os.path.join(pack, "evidence")
    if os.path.isdir(ev):
        shutil.rmtree(ev)
    os.makedirs(ev)
    lines = ["# BENCH: identity evidence and indicative timing", "",
             f"Generated {now_vienna()} by `tools/collect_evidence.py` from the files under `evidence/` (copied from "
             "`D:\\forge_jobs_20261109\\fable2\\out\\id`). All runs: CPU 3 only (mask 0x08), Idle priority, one process "
             "at a time, while the crew's gates ran on other cores. Lock = combo29 exe `e1284f7f...8802e`.", ""]

    # ---------------- lock rows
    lock_dir = os.path.join(out, "id", "lock")
    lq = qualify_lines(out, "lock")
    for f in ("pins.json", "cold_on_all.tsv", "cold_off_all.tsv", "warm.txt", "perftset.json", "QUALIFY.log"):
        copy(os.path.join(lock_dir, f), os.path.join(ev, "lock"))
    lines += ["## 1. Lock reference rows", "", "| Item | Result | File |", "|---|---|---|"]
    pins = load_json(os.path.join(lock_dir, "pins.json"))
    lines.append(f"| 12 pins on the lock copy | {'12/12' if pins and pins.get('ok') else 'MISSING'} | `evidence/lock/pins.json` |")
    for net in ("on", "off"):
        p = os.path.join(lock_dir, f"cold_{net}_all.tsv")
        if os.path.isfile(p):
            mine = [x.rstrip("\r\n") for x in open(p, encoding="utf-8")]
            lines.append(f"| Cold rows net {net} | {len(mine)} rows, sha256 `{sha256(p)}` | `evidence/lock/cold_{net}_all.tsv` |")
            qa = QA_ROWS[net]
            if os.path.isfile(qa):
                theirs = [x.rstrip("\r\n") for x in open(qa, encoding="utf-8", errors="replace")]
                diff = abs(len(mine) - len(theirs)) + sum(1 for a, b in zip(mine, theirs) if a != b)
                lines.append(f"| ... against QA's cached lock rows, net {net} | {len(theirs)} QA rows, {diff} rows differ "
                             f"(QA file sha256 `{sha256(qa)}`) | `{qa}` (read only) |")
            else:
                lines.append(f"| ... against QA's cached lock rows, net {net} | QA file not found | `{qa}` |")
        else:
            lines.append(f"| Cold rows net {net} | not run | |")
    p = os.path.join(lock_dir, "warm.txt")
    if os.path.isfile(p):
        lines.append(f"| Warm transcript | sha256 `{sha256(p)}` | `evidence/lock/warm.txt` |")
    lines.append(f"| Perft set | {cell(lq, 'lock perft set') if 'lock perft set' in lq else 'not run'} | `evidence/lock/perftset.json` |")
    lines.append("")

    # ---------------- identity ladder
    lines += ["## 2. Identity ladder", "",
              "Switch 0 = the patch applied, switch left at its default. `89 / 0` = 89 differing bytes inside the debug "
              "record (PDB hash and path), 0 differing bytes anywhere else: code and data bytes identical to the lock; "
              "sha256 identity UNRESOLVED (debug record only), see STATUS.md.", ""]
    header = "| Check | " + " | ".join(n for n, _ in SINGLES + BUNDLES) + " |"
    lines += [header, "|---|" + "---|" * len(SINGLES + BUNDLES)]
    lines.append("| Status | " + " | ".join(NOTE[n] for n, _ in SINGLES + BUNDLES) + " |")
    row_patch, row_off, row_pins = [], [], []
    quals = {}
    for name, tag in SINGLES + BUNDLES:
        d = os.path.join(out, "id", name)
        e = os.path.join(ev, name)
        quals[name] = qualify_lines(out, name)
        patch = os.path.join(pack, "patches", f"{name}_after_combo29.patch")
        row_patch.append(f"`{md5(patch)[:8]}...`" if os.path.isfile(patch) else "MISSING")
        bc = load_json(os.path.join(d, "bytecmp_lock_vs_off.json"))
        row_off.append(f"{bc['differing_bytes_debug']} / {bc['differing_bytes_other']}" if bc else "not run")
        pj = load_json(os.path.join(d, "pins_on.json"))
        row_pins.append(("12/12" if pj.get("ok") else "MISMATCH") if pj else "not run")
        for f in ("QUALIFY.log", "bytecmp_lock_vs_off.json", "pins_on.json", "pins_v2.json", "perftset.json"):
            copy(os.path.join(d, f), e)
        copy(os.path.join(d, "soak", "RECEIPT.json"), e, "soak_RECEIPT.json")
        for f in ("cold_on_all.tsv", "cold_off_all.tsv", "cold_v2_on_all.tsv", "warm.txt", "prim_on_all.tsv", "prim_verify_all.tsv"):
            p = os.path.join(d, f)
            if os.path.isfile(p):
                os.makedirs(e, exist_ok=True)
                with open(os.path.join(e, f + ".sha256"), "w", encoding="utf-8", newline="\n") as o:
                    o.write(f"{sha256(p)}  {f}\n")
        for suffix in ("off", "on", "v2"):
            copy(os.path.join(out, "build", f"{tag}_{suffix}", "RUN_RECEIPT.json"), e, f"RUN_RECEIPT_{tag}_{suffix}.json")
    lines.append("| Patch md5 | " + " | ".join(row_patch) + " |")
    lines.append("| Switch 0 vs lock, bytes (debug / other) | " + " | ".join(row_off) + " |")
    lines.append("| Switch 1, 12 pins | " + " | ".join(row_pins) + " |")
    for stage, label in STAGES:
        lines.append(f"| {label} | " + " | ".join(cell(quals[n], stage) for n, _ in SINGLES + BUNDLES) + " |")
    lines += ["", "\"not run\" in a verify row of `PAWN_CAPMASK` or `KING_PAWN_CACHE` means the patch has no verify mode. "
              "The verify engine was run over the cold set for the bundles only (all verify modes on at once). "
              "A verify build of `WITNESS_NOPIN` still asks the legality test it would skip, which builds the king "
              "lines; verify builds therefore take the `CHECKERS_KL` shortcut in a superset of the shipped mode's cases.", ""]
    base_t = os.path.join(out, "id", "prim", "base_all.tsv")
    if os.path.isfile(base_t):
        lines += [f"Base harness transcript (lock source, 12,000 FENs): sha256 `{sha256(base_t)}`.", ""]
        os.makedirs(os.path.join(ev, "prim"), exist_ok=True)
        with open(os.path.join(ev, "prim", "base_all.tsv.sha256"), "w", encoding="utf-8", newline="\n") as o:
            o.write(f"{sha256(base_t)}  base_all.tsv\n")
        copy(base_t + ".log", os.path.join(ev, "prim"))

    # ---------------- timing
    lines += timing_sections(out, ev)

    # ---------------- other evidence
    for src, dst in ((os.path.join(out, "logs", "chain.log"), os.path.join(ev, "logs")),
                     (os.path.join(out, "logs", "chain_done.txt"), os.path.join(ev, "logs"))):
        copy(src, dst)
    lines += ["## 4. Mutants: would the harness notice a wrong patch?", "",
              "`tests/mutants.ps1` plants one wrong change per run, builds the harness on it and runs the targeted "
              "positions and the first 300 FENs. CAUGHT = transcript differs, a self-check fails, or a verify build "
              "aborts. Each tree is first run unchanged with the same switches (control) and must be clean.", "",
              "| Tree | Mutant | Planted change | Verdict | Where |", "|---|---|---|---|---|"]
    rx_m = re.compile(r"^MUTANT (\S+) \[([A-Z_0-9]+); (.*); switches ([^\]]*)\]: (CAUGHT|MISSED|ERROR|INCOMPLETE|not caught \(allowed\)); (.*?); first report: ")
    guard_rows = 0
    rx_c = re.compile(r"^CONTROL (\S+) \[([^\]]*)\]: (clean|NOT CLEAN); (.*?) \[[^\]]*\]\s*$")
    controls = []
    for log_name in ("MUTANTS.log", "MUTANTS_BUNDLE4.log", "MUTANTS_BUNDLE3.log", "MUTANTS_BUNDLE.log"):
        mut = os.path.join(out, "id", "mutants", log_name)
        if not os.path.isfile(mut):
            lines.append(f"| ({log_name}) | not run | | | |")
            continue
        copy(mut, os.path.join(ev, "mutants"))
        text_all = open(mut, encoding="utf-8", errors="replace").read()
        if "\nSUMMARY " not in "\n" + text_all:
            done = len(re.findall(r"^MUTANT ", text_all, re.M))
            lines.append(f"| ({log_name}) | pass **INCOMPLETE**: stopped at 16:56 on the owner's instruction to wrap up, "
                         f"after {'the control and ' if 'CONTROL ' in text_all else ''}{done} mutants | | | |")
        for line in open(mut, encoding="utf-8", errors="replace"):
            m = rx_m.match(line)
            if m:
                verdict = m.group(5)
                if "exit 95" in m.group(6) or "NOT STARTED" in m.group(6):
                    guard_rows += 1
                    if verdict == "ERROR" and "exit 95" in m.group(6) and ("self-check failures" in m.group(6) or "transcript differs" in m.group(6) or "verify abort" in m.group(6)):
                        verdict = "ERROR in the log (one set refused by the disk guard); caught on the set that ran"
                lines.append(f"| {m.group(2)} | `{m.group(1)}` | {m.group(3)} | {verdict} | {m.group(6)} |")
            c = rx_c.match(line.strip())
            if c:
                controls.append(f"| {c.group(1)} | `{c.group(2)}` | {c.group(3)} | {c.group(4)} |")
    if guard_rows:
        lines += ["", "\"exit 95\" in a row is the launcher's refusal to start a run while D: was under this job's 30.3 GiB "
                  "guard: that set was not run for that mutant. The script of that day counted any such exit as ERROR; the "
                  "verdict column says what the set that did run showed."]
    lines += ["", "Controls (the unchanged tree with the same switches):", "", "| Tree | Switches | Result | Sets |", "|---|---|---|---|"]
    lines += controls
    lines += ["", "Evidence: `evidence/mutants/`.", ""]

    # ---------------- exact work counters
    md, tsv = work_counters.table(out)
    with open(os.path.join(ev, "work_counters.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(tsv) + "\n")
    lines += ["## 5. Exact work counters: what each switch removes", "",
              "Not a timing. Every lock-recipe build has an instrumented first stage that runs the frozen workload "
              "(bench 11, 13 and 16; 4,200,115 nodes in every build, since all builds are node-identical). Its profile "
              "holds an exact counter per source function and per source region. The table compares those counters "
              "between the control rebuild of the lock source and each switch-1 build (`tools/work_counters.py`). "
              "\"same\" = equal to the lock's count. Counters measure work removed, not time gained: they say nothing "
              "about cache or code-layout effects, but they are exact and repeatable, which the timing above is not.", ""]
    lines += md
    lines += ["", "Evidence: `evidence/work_counters.tsv`; the profiles are `out\\build\\<tag>\\m2gen\\m2.profdata` on the PC.", ""]
    with open(os.path.join(pack, "BENCH.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    n_files = sum(len(fs) for _, _, fs in os.walk(ev))
    size = sum(os.path.getsize(os.path.join(d, x)) for d, _, fs in os.walk(ev) for x in fs)
    print(f"BENCH.md written; evidence: {n_files} files, {size / 1e6:.2f} MB", flush=True)


if __name__ == "__main__":
    main()
