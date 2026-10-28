#!/usr/bin/env python3
"""Caller attribution of one callee (default: memset) in a callgrind profile, per call site.

The profile must be written with
  valgrind --tool=callgrind --dump-instr=yes --compress-strings=no --compress-pos=no ...
so that every cost line carries an absolute instruction address and every name is spelled out.
For each call of a function whose name matches --callee, the script records the calling function, the
call-site address, the call count and the inclusive cost. With --exe, call sites inside that executable are
mapped to their inline chain with addr2line (-f -i -C); the run-time load bias of a PIE executable is found
from the entry addresses of several functions (callgrind address of the lowest cost line of a function minus
its `nm` address) and must agree for all of them.

Each site is put in a group from its inline chain and caller:
  move_buffers   MovePicker or MoveList construction (the zero-fill of the S14 follow-up), including the
                 Board functions that declare a MoveList (has_legal_move, perft, legal_moves, pseudo_legal_moves)
  tt_clear       TranspositionTable (resize/clear)
  histories      history, counter-move and correction tables (Worker construction, Worker/Searcher::clear)
  eval_cache     Evaluator (pawn cache)
  other          anything else
usage: callgrind_callers.py <callgrind.out> [--exe forge] [--callee REGEX] [--json out.json]
"""
import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict


def parse(path, callee_rx):
    """Returns (total_cost, calls, fn_min_addr). calls: list of dicts (caller, obj, site, callee, count, cost)."""
    total = None
    fn = ob = None
    cfn = cob = None
    pending = None
    calls = []
    fn_min = {}
    with open(path, encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if not line:
                continue
            head = line[0]
            if head.isdigit() or head in "+-*":
                cols = line.split()
                if pending is not None:
                    site = int(cols[0], 16) if cols[0].startswith("0x") else int(cols[0])
                    cost = int(cols[2]) if len(cols) > 2 else 0
                    pending["site"] = site
                    pending["cost"] = cost
                    calls.append(pending)
                    pending = None
                    continue
                if cols[0].startswith("0x") and fn is not None:
                    addr = int(cols[0], 16)
                    key = (ob, fn)
                    if key not in fn_min or addr < fn_min[key]:
                        fn_min[key] = addr
                continue
            if line.startswith("fn="):
                fn = line[3:]
                cfn = cob = None
            elif line.startswith("ob="):
                ob = line[3:]
            elif line.startswith("cfn="):
                cfn = line[4:]
            elif line.startswith("cob="):
                cob = line[4:]
            elif line.startswith("calls="):
                count = int(line[6:].split()[0])
                if cfn is not None and callee_rx.search(cfn):
                    pending = {"caller": fn, "obj": ob, "callee": cfn, "callee_obj": cob or ob, "count": count}
                cfn = cob = None
            elif line.startswith("totals:") or line.startswith("summary:"):
                value = int(line.split(":", 1)[1].split()[0])
                total = value if total is None else max(total, value)
    return total, calls, fn_min


def base_name(fn):
    """callgrind marks recursion levels with 'N; drop that suffix."""
    return re.sub(r"'\d+$", "", fn)


NM_TEXT_LINE = re.compile(r"^([0-9a-fA-F]+) ([tTwW]) (.+)$")


def nm_text_symbols(text):
    """Defined text symbols of `nm -C` output. Undefined symbols (no address, e.g. glibc's in a dynamic ELF) and
    other symbol types are skipped."""
    table = {}
    for line in text.splitlines():
        m = NM_TEXT_LINE.match(line)
        if m:
            table.setdefault(m.group(3), int(m.group(1), 16))
    return table


def nm_addresses(exe):
    return nm_text_symbols(subprocess.run(["nm", "-C", exe], capture_output=True, text=True, check=True).stdout)


def bias_from(table, fn_min, exe_name):
    """Bias = callgrind address - link address, voted over every executed function of the executable that nm
    lists (the lowest recorded address of a function is its entry). Returns (bias, votes for it, all votes)."""
    votes = defaultdict(int)
    for (obj, fn), addr in fn_min.items():
        if obj is None or not obj.endswith(exe_name):
            continue
        link = table.get(base_name(fn))
        if link is not None:
            votes[addr - link] += 1
    if not votes:
        raise SystemExit("cannot determine the load bias: no function of the executable matched nm")
    bias, count = max(votes.items(), key=lambda kv: kv[1])
    return bias, count, sum(votes.values())


def load_bias(exe, fn_min):
    return bias_from(nm_addresses(exe), fn_min, exe.replace("\\", "/").split("/")[-1])


def inline_chains(exe, addresses):
    if not addresses:
        return {}
    args = ["addr2line", "-e", exe, "-f", "-i", "-C", "-a"] + [hex(a) for a in addresses]
    return parse_addr2line(subprocess.run(args, capture_output=True, text=True, check=True).stdout.splitlines())


def parse_addr2line(out):
    """addr2line -f -i -C -a output: an address line, then (function, file:line) pairs, innermost first."""
    chains = {}
    current = None
    i = 0
    while i < len(out):
        line = out[i]
        if line.startswith("0x"):
            current = int(line, 16)
            chains[current] = []
            i += 1
            continue
        func = line
        loc = out[i + 1] if i + 1 < len(out) else "?"
        loc = re.sub(r" \(discriminator \d+\)", "", loc)
        loc = re.sub(r"^.*/(src|include|tools|bench|tests)/", r"\1/", loc)
        chains[current].append(f"{func} @ {loc}")
        i += 2
    return chains


MOVE_LIST_FUNCTIONS = ("Board::has_legal_move", "Board::perft", "Board::legal_moves", "Board::pseudo_legal_moves")


def group_of(chain_text, caller):
    text = chain_text + " " + caller
    if "MovePicker::" in text or "MoveList::" in text or any(f in text for f in MOVE_LIST_FUNCTIONS):
        return "move_buffers"
    if "TranspositionTable" in text:
        return "tt_clear"
    if any(k in text for k in ("History", "CounterMove", "Correction", "Worker::Worker", "Worker::clear",
                               "Searcher::clear")):
        return "histories"
    if "Evaluator" in text:
        return "eval_cache"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profile")
    ap.add_argument("--exe")
    ap.add_argument("--callee", default=r"(^|_)memset")
    ap.add_argument("--json")
    a = ap.parse_args()
    total, calls, fn_min = parse(a.profile, re.compile(a.callee))
    if total is None:
        raise SystemExit("no totals/summary line in " + a.profile)
    sites = defaultdict(lambda: {"count": 0, "cost": 0, "callers": set(), "callees": set()})
    for c in calls:
        s = sites[(c["obj"], c["site"])]
        s["count"] += c["count"]
        s["cost"] += c["cost"]
        s["callers"].add(base_name(c["caller"]))
        s["callees"].add(c["callee"])
    bias = 0
    chains = {}
    if a.exe:
        bias, agree, seen = load_bias(a.exe, fn_min)
        print(f"load bias {hex(bias)} (agreed by {agree} of {seen} executed functions found in nm)")
        exe_sites = [addr for (obj, addr) in sites if obj and obj.endswith(a.exe.split("/")[-1])]
        chains = inline_chains(a.exe, sorted(addr - bias for addr in exe_sites))
    callee_total = sum(s["cost"] for s in sites.values())
    print(f"program total {total:,}; callee /{a.callee}/ inclusive {callee_total:,} "
          f"({100.0 * callee_total / total:.2f}%) over {sum(s['count'] for s in sites.values()):,} calls "
          f"from {len(sites)} call sites")
    rows = []
    for (obj, addr), s in sites.items():
        chain = chains.get(addr - bias, []) if a.exe and obj and obj.endswith(a.exe.split("/")[-1]) else []
        caller = ";".join(sorted(s["callers"]))
        rows.append({
            "site": hex(addr - bias) if chain else hex(addr),
            "object": obj,
            "caller": caller,
            "inline_chain": chain,
            "callees": sorted(s["callees"]),
            "calls": s["count"],
            "inclusive": s["cost"],
            "per_call": s["cost"] / s["count"] if s["count"] else 0.0,
            "share_of_callee": s["cost"] / callee_total if callee_total else 0.0,
            "share_of_program": s["cost"] / total,
            "group": group_of(" | ".join(chain), caller),
        })
    rows.sort(key=lambda r: -r["inclusive"])
    groups = defaultdict(lambda: [0, 0])
    for r in rows:
        groups[r["group"]][0] += r["calls"]
        groups[r["group"]][1] += r["inclusive"]
    print("\ngroup          calls          inclusive   %callee  %program")
    for g in ("move_buffers", "tt_clear", "histories", "eval_cache", "other"):
        n, cost = groups.get(g, [0, 0])
        print(f"{g:<12} {n:>9,} {cost:>18,} {100.0 * cost / callee_total if callee_total else 0:8.2f} "
              f"{100.0 * cost / total:8.2f}")
    print("\nper call site (largest first):")
    for r in rows:
        print(f"- {r['site']} calls {r['calls']:,} inclusive {r['inclusive']:,} ({100 * r['share_of_callee']:.2f}% of callee, "
              f"{100 * r['share_of_program']:.2f}% of program) per call {r['per_call']:.1f} group {r['group']}")
        print(f"    caller: {r['caller']}")
        for link in r["inline_chain"]:
            print(f"    at {link}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as out:
            json.dump({"total": total, "callee_regex": a.callee, "callee_total": callee_total, "bias": bias,
                       "groups": {g: {"calls": v[0], "inclusive": v[1]} for g, v in groups.items()}, "sites": rows},
                      out, indent=1)


if __name__ == "__main__":
    main()
