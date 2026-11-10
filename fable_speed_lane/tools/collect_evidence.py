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
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402

SINGLES = [("WITNESS_NOPIN", "wit"), ("EVADE_LEGAL", "evd"), ("PAWN_CAPMASK", "cap"), ("CHECKERS_KL", "chk"),
           ("KING_PAWN_CACHE", "kpc")]
BUNDLES = [("BUNDLE4", "bn4"), ("BUNDLE", "bun")]
NOTE = {"KING_PAWN_CACHE": "not new (built before, DUPCHECK.md); extra", "BUNDLE": "BUNDLE4 + KING_PAWN_CACHE; extra",
        "BUNDLE4": "the four new candidates", "PAWN_CAPMASK": "UNLISTED", "WITNESS_NOPIN": "LISTED-UNBUILT",
        "EVADE_LEGAL": "LISTED-UNBUILT", "CHECKERS_KL": "LISTED-UNBUILT"}
QA_ROWS = {net: rf"C:\Users\Administrator\grok-pc\forge_push\overnight_timing_20261108\checks2\combo29_{net}\fens_n12000_d13.tsv"
           for net in ("on", "off")}
STAGES = [("harness", "Harness, 12,000 FENs, switch 1"), ("harness, verify build", "Harness, 12,000 FENs, verify build (=2)"),
          ("harness, targeted positions", "Harness, 23 targeted positions, switch 1"),
          ("harness, targeted positions, verify build", "Harness, 23 targeted positions, verify build (=2)"),
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
    rx = re.compile(r"^QUAL (\S+) (.+?): (PASS|FAIL) (.*) \[([^\]]+)\]\s*$")
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = rx.match(line.strip())
            if m and "300 FENs" not in m.group(4) and " 200 rows" not in m.group(4):
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
    if stage.startswith("harness") and stage.endswith("verify build"):
        m = re.search(r"exit (-?\d+); .*transcript equal to base: (\w+)", text)
        return f"{verdict}: exit {m.group(1)} (no abort), transcript equal {m.group(2)}" if m else verdict
    if stage.startswith("harness"):
        m = re.search(r"(\d+) FENs, (\d+) positions, (\d+) generated moves, (\d+) self-check failures; transcript equal to base: (\w+)", text)
        return f"{verdict}: transcript equal to base {m.group(5)}, {m.group(4)} self-check failures" if m else f"{verdict}"
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
    lines += ["## 3. INDICATIVE timing (not the ABBA)", "",
              "Lock exe (A) against the switch-1 exe (B), Threads 1, Hash 16, fresh engine per arm, warm `bench 13`, timed "
              "`bench 20`, 10 ABBA blocks, ratio per block = sqrt(B1*B2 / (A1*A2)). **Wall** = nodes per wall second. "
              "**Cycles** = nodes per CPU cycle of the engine process (QueryProcessCycleTime), which preemption by other "
              "jobs does not inflate. Positive = B faster. These numbers come from one shared CPU at Idle priority; "
              "they cannot prove a gain under 1 % and they are not QA's quiet ABBA.", "",
              "| Pair | Net | Wall median | Wall IQR | Wall min .. max | Cycles median | Cycles IQR | Cycles min .. max | Blocks | Folder |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for name, _tag in [("AA_lock_vs_lock", "")] + BUNDLES + SINGLES:
        for net in ("on", "off"):
            d = newest_abba(out, name, net)
            label = "A/A (lock vs lock)" if name.startswith("AA_") else name
            if not d:
                lines.append(f"| {label} | {net} | not run | | | | | | | |")
                continue
            s = load_json(os.path.join(d, "SUMMARY.json"))
            e = os.path.join(ev, name, os.path.basename(d))
            for f in ("SUMMARY.json", "PROTOCOL.json", "SAMPLES.json"):
                copy(os.path.join(d, f), e)
            cyc = (f"{s['cpu_median_delta_pct']:+.2f} % | {s['cpu_q1_pct']:+.2f} .. {s['cpu_q3_pct']:+.2f} | "
                   f"{s['cpu_min_pct']:+.2f} .. {s['cpu_max_pct']:+.2f}") if "cpu_median_delta_pct" in s else "n/a | n/a | n/a"
            lines.append(f"| {label} | {net} | {s['median_delta_pct']:+.2f} % | {s['q1_pct']:+.2f} .. {s['q3_pct']:+.2f} | "
                         f"{s['min_pct']:+.2f} .. {s['max_pct']:+.2f} | {cyc} | {s['blocks']} | `evidence/{name}/{os.path.basename(d)}` |")
    lines.append("")

    # ---------------- other evidence
    for src, dst in ((os.path.join(out, "logs", "chain.log"), os.path.join(ev, "logs")),
                     (os.path.join(out, "logs", "chain_done.txt"), os.path.join(ev, "logs"))):
        copy(src, dst)
    lines += ["## 4. Mutants: would the harness notice a wrong patch?", "",
              "`tests/mutants.ps1` plants one wrong change per run, builds the harness on it and runs the targeted "
              "positions and the first 300 FENs. CAUGHT = transcript differs, a self-check fails, or a verify build "
              "aborts. Each tree is first run unchanged with the same switches (control) and must be clean.", "",
              "| Tree | Mutant | Planted change | Verdict | Where |", "|---|---|---|---|---|"]
    rx_m = re.compile(r"^MUTANT (\S+) \[([A-Z_0-9]+); (.*); switches ([^\]]*)\]: (CAUGHT|MISSED|ERROR|not caught \(allowed\)); (.*?); first report: ")
    rx_c = re.compile(r"^CONTROL (\S+) \[([^\]]*)\]: (clean|NOT CLEAN); (.*?) \[[^\]]*\]\s*$")
    controls = []
    for log_name in ("MUTANTS.log", "MUTANTS_BUNDLE4.log", "MUTANTS_BUNDLE.log"):
        mut = os.path.join(out, "id", "mutants", log_name)
        if not os.path.isfile(mut):
            lines.append(f"| ({log_name}) | not run | | | |")
            continue
        copy(mut, os.path.join(ev, "mutants"))
        for line in open(mut, encoding="utf-8", errors="replace"):
            m = rx_m.match(line)
            if m:
                lines.append(f"| {m.group(2)} | `{m.group(1)}` | {m.group(3)} | {m.group(5)} | {m.group(6)} |")
            c = rx_c.match(line.strip())
            if c:
                controls.append(f"| {c.group(1)} | `{c.group(2)}` | {c.group(3)} | {c.group(4)} |")
    lines += ["", "Controls (the unchanged tree with the same switches):", "", "| Tree | Switches | Result | Sets |", "|---|---|---|---|"]
    lines += controls
    lines += ["", "Evidence: `evidence/mutants/`.", ""]
    with open(os.path.join(pack, "BENCH.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    n_files = sum(len(fs) for _, _, fs in os.walk(ev))
    size = sum(os.path.getsize(os.path.join(d, x)) for d, _, fs in os.walk(ev) for x in fs)
    print(f"BENCH.md written; evidence: {n_files} files, {size / 1e6:.2f} MB", flush=True)


if __name__ == "__main__":
    main()
