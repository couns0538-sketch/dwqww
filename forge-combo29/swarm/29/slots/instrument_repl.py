#!/usr/bin/env python3
"""Verify seat 19's 19-F18 with my own instrumentation: how many TT probes actually reach the age/depth REPLACEMENT
scan, on bench 13 versus a real-game set, at Hash 16 and Threads 1?

19-F18 claims: Hash 16, bench 13 -> 50 of 861,904 probes (0.006 %) reach the scan; real-game set -> 54.7 %; and
10.1 % of its probes find an empty slot (bench 66.9 %). Hash 32 -> 44.1 %.

Instrumentation (mine): counters incremented at the top of probe_body and at the point where the hit loop has failed
and the replacement scan begins. Printed at exit. Aborts if probes == 0.
"""
import os
import subprocess
import sys

SRC = sys.argv[1]
OUT = sys.argv[2]


def instrument():
    p = os.path.join(SRC, "src", "search.cpp")
    s = open(p).read()
    if "g_repl_reached" in s:
        return
    # counters above the template line
    anchor = "#if FORGE_SPD_TT_NOTLS\ntemplate <bool TakeLock>\nTTProbe TranspositionTable::probe_body"
    assert s.count(anchor) == 1, "probe_body anchor not found"
    s = s.replace(anchor,
                  "#if FORGE_SPD_TT_NOTLS\n"
                  "unsigned long long g_probes = 0, g_misses = 0, g_repl_reached = 0, g_empty_slot = 0;\n"
                  "template <bool TakeLock>\nTTProbe TranspositionTable::probe_body")
    # count probes
    s = s.replace("TTProbe TranspositionTable::probe_body(std::uint64_t key) const {",
                  "TTProbe TranspositionTable::probe_body(std::uint64_t key) const {\n    ++g_probes;", 1)
    # count misses (no hit found) and replacement-scan entry
    old = """    TTEntry* replace = &cluster.entries[0];
    int replace_score = replace->occupied()"""
    new = """    ++g_misses;
    ++g_repl_reached;
    TTEntry* replace = &cluster.entries[0];
    int replace_score = replace->occupied()"""
    assert s.count(old) == 1, "replacement scan start not found"
    s = s.replace(old, new)
    # count empty-slot early returns inside the scan
    # two occurrences exist; only the one INSIDE the replacement scan follows the `++g_repl_reached` marker
    old2 = """    ++g_repl_reached;
    TTEntry* replace = &cluster.entries[0];"""
    assert s.count(old2) == 1, "replacement marker missing"
    idx = s.index(old2)
    tail = s[idx:]
    target = "        if (!entry.occupied()) return snapshot(entry, false);"
    j = tail.index(target)
    tail = tail[:j] + "        if (!entry.occupied()) { ++g_empty_slot; return snapshot(entry, false); }" + tail[j+len(target):]
    s = s[:idx] + tail
    open(p, "w").write(s)

    u = os.path.join(SRC, "src", "uci.cpp")
    t = open(u).read()
    if "g_repl_reached" not in t:
        t = t.replace('} else if (command == "quit") {',
                      '} else if (command == "quit") {\n'
                      '  { extern unsigned long long g_probes, g_misses, g_repl_reached, g_empty_slot;\n'
                      '    std::cerr << "REPLSTAT probes " << g_probes << " misses " << g_misses\n'
                      '              << " repl_reached " << g_repl_reached\n'
                      '              << " empty_slot " << g_empty_slot << std::endl; }', 1)
        open(u, "w").write(t)
    print("instrumented")


instrument()
b = os.path.join(OUT, "build")
os.makedirs(b, exist_ok=True)
for cmd in (["cmake", SRC, "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=/usr/bin/g++-13",
             "-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1"], ["make", "-j4"]):
    r = subprocess.run(cmd, cwd=b, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"{cmd[0]} failed: {r.stderr[-600:]}")
print("built", os.path.join(b, "forge"))
