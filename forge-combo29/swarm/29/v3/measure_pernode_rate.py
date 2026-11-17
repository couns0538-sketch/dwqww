#!/usr/bin/env python3
"""THE DECIDING MEASUREMENT (29-F63's next step): what fraction of cont1/cont2 reads hit a block that has NEVER been
written — i.e. what a per-node "this table is empty" flag could actually capture?

29-F63 measured 59.6 % of reads return zero, but that is per-MOVE and an UPPER BOUND. A per-node flag can only skip a
read when the ENTIRE PieceToHistory block it points at has never been written. This measures exactly that.

Method: track which PieceToHistory blocks have been written (at every `update_continuation` apply site), then at each
read count whether its block was still unwritten. Scratch copy; repository untouched.
"""
import os
import subprocess
import sys

SRC = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

p = os.path.join(SRC, "src", "search.cpp")
s = open(p).read()
if "g_unwritten_reads" in s:
    print("already instrumented")
else:
    decl = ("#include <unordered_set>\n"
            "static std::unordered_set<const void*> g_written_blocks;\n"
            "unsigned long long g_block_reads = 0, g_unwritten_reads = 0;\n")
    qi = s.find("[[nodiscard]] inline int quiet_history_sum(")
    assert qi > 0, "quiet_history_sum not found"
    ni = s.rfind("namespace {", 0, qi)
    s = s[:ni] + decl + "\n" + s[ni:]

    old = """    if (cont1 != nullptr) score += (*cont1)[p][move.to];
    if (cont2 != nullptr) score += (*cont2)[p][move.to];"""
    new = """    if (cont1 != nullptr) { ++g_block_reads;
        if (g_written_blocks.find(static_cast<const void*>(cont1)) == g_written_blocks.end()) ++g_unwritten_reads;
        score += (*cont1)[p][move.to]; }
    if (cont2 != nullptr) { ++g_block_reads;
        if (g_written_blocks.find(static_cast<const void*>(cont2)) == g_written_blocks.end()) ++g_unwritten_reads;
        score += (*cont2)[p][move.to]; }"""
    assert s.count(old) == 1, "read sites not found"
    s = s.replace(old, new, 1)

    # mark blocks written at every continuation-history write
    oldw = """void Worker::update_continuation(SearchStack* ss, Piece piece, int to, int bonus) {"""
    neww = """void Worker::update_continuation(SearchStack* ss, Piece piece, int to, int bonus) {
    for (const int back : {1, 2, 4}) {
        const SearchStack* previous = ss - back;
        if (previous->continuation != nullptr) g_written_blocks.insert(static_cast<const void*>(previous->continuation));
    }"""
    assert s.count(oldw) == 1, "update_continuation not found"
    s = s.replace(oldw, neww, 1)

    # and at the two direct write sites in search (line ~1467/1468 use them read-only; the writes are via apply_history)
    open(p, "w").write(s)

    u = os.path.join(SRC, "src", "uci.cpp")
    t = open(u).read()
    if "g_block_reads" not in t:
        t = t.replace('} else if (command == "quit") {',
                      '} else if (command == "quit") {\n'
                      '  { extern unsigned long long g_block_reads, g_unwritten_reads;\n'
                      '    std::cerr << "BLOCKSTAT reads " << g_block_reads << " on_unwritten_block "\n'
                      '              << g_unwritten_reads << std::endl; }', 1)
        open(u, "w").write(t)
    print("instrumented")

b = os.path.join(OUT, "build")
os.makedirs(b, exist_ok=True)
for cmd in (["cmake", SRC, "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=/usr/bin/g++-13",
             "-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1"], ["make", "-j4"]):
    r = subprocess.run(cmd, cwd=b, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"{cmd[0]} failed: {r.stderr[-700:]}")
print("built", os.path.join(b, "forge"))
