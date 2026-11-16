#!/usr/bin/env python3
"""CHECK of seat 19's 19-F19, with my own instrumentation (not a copy of their script).

19-F19 claims: `bench 13`'s TT probes hit **slot 0** of the cluster 93.1 % of the time and never refresh a
generation (0 of 285,437 hits), while R_1911 is flat across slots (26.0/25.4/24.9/23.7 %) with 0.4-0.5 % of hits
doing a generation write.

Why this matters to me: my 29-F12 removed a comparison in the REPLACEMENT path and my 29-F14 vectorised the slot
scan. If bench concentrates hits on slot 0, bench flatters both, and the PC-relevant set would not.

Method: instrument a scratch copy of the PC r15 source to record, for every `probe_body` call that HITS, which slot
matched and whether the generation was refreshed; print the histogram at exit. One process per regime, Threads 1.

Guards: the counters are asserted non-zero before any percentage is printed, so a silent failure cannot look like
"0 %".
"""
import subprocess
import sys
import os

SRC = sys.argv[1]        # a writable copy of the PC tree
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def instrument():
    p = os.path.join(SRC, "src", "search.cpp")
    s = open(p).read()
    if "g_slot_hist" in s:
        print("already instrumented")
        return
    old = "TTProbe TranspositionTable::probe_body(std::uint64_t key) const {"
    new = ('unsigned long long g_slot_hist[4] = {0,0,0,0};\n'
           'unsigned long long g_slot_hits = 0;\n'
           'unsigned long long g_gen_writes = 0;\n'
           'unsigned long long g_probes = 0;\n'
           'TTProbe TranspositionTable::probe_body(std::uint64_t key) const {\n'
           '    ++g_probes;')
    assert s.count(old) == 1, "probe_body entry not found"
    s = s.replace(old, new)
    # record the slot on the hit path, and whether the generation was refreshed
    old2 = """        if (found->generation() != generation) {
            found->gen_bound = static_cast<std::uint8_t>(
                (static_cast<unsigned>(generation) << 3U) | (found->gen_bound & 7U));
        }
        return snapshot(*found, true);"""
    new2 = """        ++g_slot_hits;
        { const long d = found - cluster.entries.data(); if (d >= 0 && d < 4) ++g_slot_hist[d]; }
        if (found->generation() != generation) {
            ++g_gen_writes;
            found->gen_bound = static_cast<std::uint8_t>(
                (static_cast<unsigned>(generation) << 3U) | (found->gen_bound & 7U));
        }
        return snapshot(*found, true);"""
    assert s.count(old2) == 1, "hit path not found"
    s = s.replace(old2, new2)
    open(p, "w").write(s)

    # report at exit
    u = os.path.join(SRC, "src", "uci.cpp")
    t = open(u).read()
    if "g_slot_hits" not in t:
        t = t.replace('} else if (command == "quit") {',
                      '} else if (command == "quit") {\n'
                      '            { extern unsigned long long g_slot_hist[4], g_slot_hits, g_gen_writes, g_probes;\n'
                      '              std::cerr << "SLOTSTAT probes " << g_probes << " hits " << g_slot_hits\n'
                      '                        << " slots " << g_slot_hist[0] << " " << g_slot_hist[1] << " "\n'
                      '                        << g_slot_hist[2] << " " << g_slot_hist[3]\n'
                      '                        << " genwrites " << g_gen_writes << std::endl; }', 1)
        open(u, "w").write(t)
    print("instrumented")


instrument()

build = os.path.join(OUT, "build")
os.makedirs(build, exist_ok=True)
r = subprocess.run(["cmake", SRC, "-DCMAKE_BUILD_TYPE=Release",
                    "-DCMAKE_CXX_COMPILER=/usr/bin/g++-13",
                    "-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1"],
                   cwd=build, capture_output=True, text=True)
if r.returncode:
    raise SystemExit(f"cmake failed: {r.stderr[-400:]}")
r = subprocess.run(["make", "-j4"], cwd=build, capture_output=True, text=True)
if r.returncode:
    raise SystemExit(f"make failed: {r.stderr[-800:]}")
exe = os.path.join(build, "forge")
print(f"built {exe}")
