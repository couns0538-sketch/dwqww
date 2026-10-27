#!/usr/bin/env python3
"""Compare the data layout of two Forge executables (unstripped PE/ELF): every data symbol (.data, .rdata,
.bss) present in both, how far it moved, and whether the move keeps its offset modulo 64 / 4096.
usage: data_layout_check.py <exe_A> <exe_B>   (needs GNU nm and objdump on PATH)"""
import subprocess
import sys

HOT = ["forge::(anonymous namespace)::Z", "forge::(anonymous namespace)::CastlingMasks",
       "forge::(anonymous namespace)::SeeValue", "NnueW1", "forge::nnue::(anonymous namespace)::weights()::instance",
       "forge::(anonymous namespace)::Reductions", "forge::params::table", "forge::tune::LmrQuietBase",
       "forge::tune::RfpMargin", "forge::attacks::BetweenTable", "forge::attacks::RookMagics",
       "forge::attacks::KnightTable", "forge::detail::DistanceMasks"]


def symbols(exe):
    out = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, check=True).stdout
    table = {}
    for line in out.splitlines():
        parts = line.split(" ", 2)
        if len(parts) < 3 or not parts[0] or parts[1] not in "dDrRbB":
            continue  # undefined symbols have no address
        name = parts[2]
        if name.startswith(".") or "refptr" in name or name.startswith("__imp_") or "_head_" in name:
            continue
        table.setdefault(name, int(parts[0], 16))
    return table


def sections(exe):
    out = subprocess.run(["objdump", "-h", exe], capture_output=True, text=True, check=True).stdout
    rows = []
    for line in out.splitlines():
        f = line.split()
        if len(f) >= 4 and f[1] in (".text", ".data", ".rdata", ".bss", ".rodata"):
            rows.append(f"{f[1]} size {f[2]} vma {f[3]}")
    return rows


def main():
    a, b = sys.argv[1], sys.argv[2]
    print("sections A:", "; ".join(sections(a)))
    print("sections B:", "; ".join(sections(b)))
    sa, sb = symbols(a), symbols(b)
    common = sorted(set(sa) & set(sb), key=lambda n: sa[n])
    not64 = [n for n in common if (sb[n] - sa[n]) % 64]
    not4096 = [n for n in common if (sb[n] - sa[n]) % 4096]
    print(f"data symbols in both: {len(common)}; moved by a non-multiple of 64: {len(not64)}; "
          f"of 4096: {len(not4096)}")
    print("forge/NNUE symbols moved by a non-multiple of 64:",
          [n for n in not64 if "forge" in n or "Nnue" in n] or "none")
    for n in HOT:
        if n in sa and n in sb:
            print(f"hot {n}: {sa[n]:#x} -> {sb[n]:#x} (delta {sb[n] - sa[n]:#x}, mod 4096 kept: "
                  f"{(sb[n] - sa[n]) % 4096 == 0})")
    print("only in B:", sorted(((hex(sb[n]), n) for n in set(sb) - set(sa))))


if __name__ == "__main__":
    main()
