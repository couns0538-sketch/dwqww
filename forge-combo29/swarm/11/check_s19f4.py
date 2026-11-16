#!/usr/bin/env python3
"""check_s19f4.py EXE — seat 11's INDEPENDENT check of seat 19's 19-F4.

19-F4 claims: "`Board::see_ge` (5.56 % self) costs nearly as much as all move generation
together (`fill_pseudo_legal<0/1/2>` = 5.69 %)."

I cannot sample a profiler, so I test the STRUCTURE of the claim: SEE is called on captures and
on quiet moves during ordering/pruning. If SEE's total cost is comparable to move generation's,
then a workload that produces many captures relative to nodes should cost MORE per node than a
quiet one, and the excess should be visible in nodes-per-second.

Falsifiable sub-claims I can reach:
  (1) the engine has a `Board::see_ge` symbol and a `fill_pseudo_legal` family, and the SEE
      symbol is reachable from the binary (i.e. the code exists as named), — necessary but weak;
  (2) the number of distinct SEE-related symbols is small (one function), so a "near-equal share"
      claim is a statement about ONE function vs the whole generator family — I test that the
      family really is several template instances.
The percentage comparison itself is NOT testable without a profiler and I say so.

Control: the same symbol search for a name that must NOT exist proves the search can fail.
"""
import re, subprocess, sys

EXE = sys.argv[1]
ok_all = True


def check(name, ok, detail=""):
    global ok_all
    ok_all = ok_all and ok
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")


nm = subprocess.run(["nm", "-C", EXE], capture_output=True, text=True).stdout
lines = nm.splitlines()

print("=== 1. do the named symbols exist? ===")
see = [l for l in lines if "see_ge" in l]
fill = [l for l in lines if "fill_pseudo_legal" in l]
print(f"  see_ge symbols          : {len(see)}")
for l in see[:5]:
    print(f"    {l.strip()}")
print(f"  fill_pseudo_legal symbols: {len(fill)}")
for l in fill[:8]:
    print(f"    {l.strip()}")
check("Board::see_ge exists as a symbol", len(see) >= 1)
check("a fill_pseudo_legal family exists", len(fill) >= 1)

print("\n=== 2. is the generator a template FAMILY (several instances)? ===")
inst = sorted({m.group(0) for l in fill
               for m in [re.search(r"fill_pseudo_legal<\(forge::Board::GenMode\)\d+>", l)] if m})
print(f"  distinct generator template instances: {len(inst)}")
for n in inst:
    print(f"    {n}")
check("move generation is more than one function", len(inst) > 1,
      f"{len(inst)} instances — so 19-F4 compares 1 function against a family")

print("\n=== control: a symbol that cannot exist ===")
bogus = [l for l in lines if "definitely_not_a_real_symbol_xyz" in l]
check("the symbol search CAN report zero", len(bogus) == 0)

print("\n=== what this does and does not show ===")
print("  SHOWN   : the two things 19-F4 compares both exist, and the generator side is a")
print("            multi-instance template family while SEE is a single function.")
print("  NOT SHOWN: the 5.56 % / 5.69 % shares. Those need seat 19's profiler; a symbol table")
print("            says nothing about time.")
if ok_all:
    print("\nRESULT: 19-F4 is CONSISTENT with the binary's structure (one SEE function vs a")
    print("        generator family) but its percentages are NOT reproduced here.")
else:
    print("\nRESULT: does not confirm 19-F4's structure — see FAIL lines.")
