#!/usr/bin/env python3
"""Inject ONE undefined-behaviour fault per sanitizer check class into a scratch
copy of the engine, selected by -DFORGE_UB_PLANT=<n>.

Each plant is placed on a path the workload really drives:
  plants 1-6, 9-11 -> the `eval` command handler (workload Phase F: 240 positions)
  plants 7, 8      -> the `bench` handler (workload Phase A, the first thing run)
  plant 12         -> the `position` handler (Phase K protocol noise)

Run: inject_plants.py <src_tree> <plant_number>
"""
import sys

PLANTS = {
    # 1: signed integer overflow
    1: ("eval", """
            {   // PLANT 1: signed integer overflow
                volatile int big = 2147483640;
                volatile int add = 100;
                volatile int sink = big + add;
                (void)sink;
            }"""),
    # 2: shift exponent too large for the 64-bit type
    2: ("eval", """
            {   // PLANT 2: shift out of range
                volatile unsigned long long base = 1ULL;
                volatile int sh = 64;
                volatile unsigned long long sink = base << sh;
                (void)sink;
            }"""),
    # 3: bool loaded with a value that is not 0 or 1
    3: ("eval", """
            {   // PLANT 3: invalid bool value
                unsigned char raw = 2;
                volatile bool sink = *reinterpret_cast<bool*>(&raw);
                (void)sink;
            }"""),
    # 4: enum loaded with a value outside its (unfixed-underlying) range.
    # NOTE: an enum WITH a fixed underlying type (enum class P : unsigned char)
    # makes every value of the underlying type valid, so it is NOT UB and UBSan
    # correctly stays quiet. The plant must use a plain enum with a small range.
    4: ("eval", """
            {   // PLANT 4: invalid enum value (plain enum, range 0..1)
                enum Probe { ProbeA = 0, ProbeB = 1 };
                volatile int raw = 9;
                volatile Probe sink = *reinterpret_cast<Probe*>(const_cast<int*>(&raw));
                (void)sink;
            }"""),
    # 5: misaligned access. The buffer address must not be provably aligned at
    # compile time, so it is passed through a noinline function; an inline local
    # array with a constant offset lets the compiler drop the check entirely.
    5: ("eval", """
            {   // PLANT 5: misaligned load through an opaque pointer
                alignas(8) unsigned char buf[16] = {0};
                volatile unsigned int sink = forge_ub_plant_misaligned(buf + 1);
                (void)sink;
            }"""),
    # 6: null dereference
    6: ("eval", """
            {   // PLANT 6: null dereference
                volatile int* nullptr_probe = nullptr;
                volatile int sink = *nullptr_probe;
                (void)sink;
            }"""),
    # 7: negation overflow (INT_MIN negated)
    7: ("bench", """
            {   // PLANT 7: negation overflow
                volatile int lowest = -2147483647 - 1;
                volatile int sink = -lowest;
                (void)sink;
            }"""),
    # 8: division by zero
    8: ("bench", """
            {   // PLANT 8: division by zero
                volatile int zero = 0;
                volatile int sink = 100 / zero;
                (void)sink;
            }"""),
    # 9: integer multiplication overflow
    9: ("eval", """
            {   // PLANT 9: multiplication overflow
                volatile int big = 100000;
                volatile int sink = big * big * big;
                (void)sink;
            }"""),
    # 10: array index out of bounds (UBSan array-bounds)
    10: ("eval", """
            {   // PLANT 10: array index out of bounds
                volatile int idx = 8;
                int table[8] = {0};
                volatile int sink = table[idx];
                (void)sink;
            }"""),
    # 11: subtraction overflow
    11: ("eval", """
            {   // PLANT 11: subtraction overflow
                volatile int lowest = -2147483647 - 1;
                volatile int sub = 5;
                volatile int sink = lowest - sub;
                (void)sink;
            }"""),
    # 12: pointer overflow. The base must not be a compile-time constant that
    # the compiler can fold: it is passed through a noinline function, and the
    # index is chosen so the sum genuinely wraps the address space.
    12: ("position", """
            {   // PLANT 12: pointer index overflow
                int storage[4] = {0};
                volatile int* sink = forge_ub_plant_far(storage, 2305843009213693952LL);
                (void)sink;
            }"""),
}

ANCHORS = {
    "eval": '        } else if (command == "eval") {',
    "bench": '        } else if (command == "bench") {',
    "position": '        } else if (command == "position") {',
}

# Helpers that plants 5 and 12 call. Kept out of line so the compiler cannot
# prove the address aligned (5) or fold the pointer sum (12); an inlined probe
# gets optimized away and then reports nothing, which looks exactly like a
# sanitizer that does not work.
HELPERS = """
namespace {
__attribute__((noinline)) unsigned int forge_ub_plant_misaligned(unsigned char* p) {
    return *reinterpret_cast<unsigned int*>(p);
}
__attribute__((noinline)) int* forge_ub_plant_far(int* base, long long index) {
    return base + index;
}
}  // namespace
"""
HELPER_NEEDED = {5, 12}
HELPER_ANCHOR = "namespace forge {\n\nint uci_loop("


def insert_helpers(src):
    if HELPER_ANCHOR not in src:
        raise SystemExit("helper anchor not found")
    return src.replace(HELPER_ANCHOR, HELPERS.strip("\n") + "\n\n" + HELPER_ANCHOR, 1)


def main():
    tree, num = sys.argv[1], int(sys.argv[2])
    where, code = PLANTS[num]
    path = f"{tree}/src/uci.cpp"
    src = open(path).read()
    anchor = ANCHORS[where]
    if anchor not in src:
        raise SystemExit(f"anchor for {where} not found")
    src = src.replace(anchor, anchor + "\n" + code.strip("\n"), 1)
    if num in HELPER_NEEDED:
        src = insert_helpers(src)
    open(path, "w").write(src)
    print(f"planted {num} ({where})")


if __name__ == "__main__":
    main()
