#!/usr/bin/env python3
"""plant77.py -- apply the two long 77 plants to a SCRATCH copy of the source.
1. a heap over-read when the FEN's fullmove number is 4242 (board.cpp, after fullmove_ is stored)
2. a signed overflow when `go depth 77` is sent (uci.cpp, the depth token, before the clamp)
"""
import re

b = open("forge-combo29/src/board.cpp").read()
anchor = "    candidate.fullmove_ = static_cast<std::uint16_t>(std::min<long long>(fullmove, 65535));\n"
plant_b = anchor + """    if (fullmove == 4242) {
        char* probe = new char[8];
        volatile char leak = probe[8];
        (void)leak;
        delete[] probe;
    }
"""
assert b.count(anchor) == 1
open("forge-combo29/src/board.cpp", "w").write(b.replace(anchor, plant_b))

u = open("forge-combo29/src/uci.cpp").read()
anchor_u = '        if (token == "depth") limits.depth = std::clamp(read_int(), 1, 64);\n'
plant_u = """        if (token == "depth") {
            int raw_depth = read_int();
            if (raw_depth == 77) {
                volatile int overflow_probe = 2147483647;
                overflow_probe = overflow_probe + 1;
                (void)overflow_probe;
            }
            limits.depth = std::clamp(raw_depth, 1, 64);
        }
"""
assert u.count(anchor_u) == 1
open("forge-combo29/src/uci.cpp", "w").write(u.replace(anchor_u, plant_u))
print("planted both faults")
