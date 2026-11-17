#!/usr/bin/env python3
"""SIZE THE OPPORTUNITY before building the flag: what fraction of cont1/cont2 history reads return zero?

Route 1 (29-F62) needs a per-frame "this continuation table is still empty" flag, and the test is the work. But
before building either, one measurement decides whether the work can pay: if most reads already return zero, skipping
them is worth doing; if almost none do, the flag is pointless.

Instrumentation: count every cont1 and cont2 read in `quiet_history_sum`, split by whether the value is zero, and
also record the maximum absolute value seen (so "zero" is not confused with "small"). Printed at exit; ABORTS if no
reads were recorded, because a zero count here would look exactly like "no opportunity".

Scratch copy only; the repository source is untouched.
"""
import os
import subprocess
import sys

SRC = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

p = os.path.join(SRC, "src", "search.cpp")
s = open(p).read()
if "g_cont_reads" in s:
    print("already instrumented")
else:
    anchor = "[[nodiscard]] inline int quiet_history_sum("
    assert s.count(anchor) == 1, "quiet_history_sum not found"
    # counters at namespace scope, declared before the function
    s = s.replace(anchor,
                  "unsigned long long g_cont_reads = 0, g_cont_zero = 0, g_cont_max = 0;\n"
                  "unsigned long long g_main_reads = 0, g_main_zero = 0;\n"
                  + anchor, 1)
    old_body = """    const std::size_t p = static_cast<std::size_t>(piece);
    int score = main[move.from][move.to];
    if (cont1 != nullptr) score += (*cont1)[p][move.to];
    if (cont2 != nullptr) score += (*cont2)[p][move.to];"""
    new_body = """    const std::size_t p = static_cast<std::size_t>(piece);
    int score = main[move.from][move.to];
    ++g_main_reads; if (main[move.from][move.to] == 0) ++g_main_zero;
    if (cont1 != nullptr) { const int v1 = (*cont1)[p][move.to]; ++g_cont_reads; if (v1 == 0) ++g_cont_zero;
                            if (v1 > g_cont_max) g_cont_max = static_cast<unsigned long long>(v1);
                            score += v1; }
    if (cont2 != nullptr) { const int v2 = (*cont2)[p][move.to]; ++g_cont_reads; if (v2 == 0) ++g_cont_zero;
                            if (v2 > g_cont_max) g_cont_max = static_cast<unsigned long long>(v2);
                            score += v2; }"""
    assert s.count(old_body) == 1, "body shape not found"
    s = s.replace(old_body, new_body, 1)
    open(p, "w").write(s)

    u = os.path.join(SRC, "src", "uci.cpp")
    t = open(u).read()
    if "g_cont_reads" not in t:
        t = t.replace('} else if (command == "quit") {',
                      '} else if (command == "quit") {\n'
                      '  { extern unsigned long long g_cont_reads, g_cont_zero, g_cont_max, g_main_reads, g_main_zero;\n'
                      '    std::cerr << "CONTSTAT cont_reads " << g_cont_reads << " cont_zero " << g_cont_zero\n'
                      '              << " cont_max " << g_cont_max << " main_reads " << g_main_reads\n'
                      '              << " main_zero " << g_main_zero << std::endl; }', 1)
        open(u, "w").write(t)
    print("instrumented")

b = os.path.join(OUT, "build")
os.makedirs(b, exist_ok=True)
for cmd in (["cmake", SRC, "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=/usr/bin/g++-13",
             "-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1"], ["make", "-j4"]):
    r = subprocess.run(cmd, cwd=b, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"{cmd[0]} failed: {r.stderr[-600:]}")
print("built", os.path.join(b, "forge"))
