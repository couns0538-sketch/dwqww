#!/usr/bin/env python3
"""S13-1 checker-fix re-review: extra controls against Sol's UNCHANGED source contract
(forge_sol_S13_source_contract_20261026.py, sha256 47938e15...), beyond his 10 tests.
Each control mutates the real candidate view in memory and records whether validate_source rejects it.
usage: python -B checker_rereview_controls.py <dir with Sol's contract .py> <base view> <candidate view>
Prints one line per control (EXPECTED / UNEXPECTED) and exits 1 if any outcome is unexpected."""
import importlib.util
import sys
from pathlib import Path

sol_dir, base_dir, cand_dir = (Path(p) for p in sys.argv[1:4])
spec = importlib.util.spec_from_file_location("sol_contract", sol_dir / "forge_sol_S13_source_contract_20261026.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)
base = contract.read_sources(base_dir)
cand = contract.read_sources(cand_dir)
NEW = "if (s13_tt_child_prefetch_) shared_.tt.prefetch(board.key());\n#endif"
FLAG = "FORGE_S13_TT_CHILD_PREFETCH"


def mutated(name, old, new, count=1):
    c = dict(cand)
    assert c[name].count(old) >= 1, (name, old)
    c[name] = c[name].replace(old, new, count)
    return c


controls = [
    # (description, candidate dict, expected outcome: "reject" or "accept")
    ("real candidate (production port 8557326e)", dict(cand), "accept"),
    ("nested non-feature #if/#else inside a feature block (conservatively rejected)",
     mutated("src/search.cpp", NEW, NEW.replace("#endif", "#if 1\n#else\n            return 0;\n#endif\n#endif")), "reject"),
    ("guard spelled #if defined(FLAG) (not erased: OFF text differs)",
     mutated("src/search.cpp", "#ifdef " + FLAG + "\n            if (s13", "#if defined(" + FLAG + ")\n            if (s13"), "reject"),
    ("#ifndef FLAG block adding OFF-path code",
     mutated("src/search.cpp", NEW, NEW + "\n#ifndef " + FLAG + "\n            ++null_tries_;\n#endif"), "reject"),
    ("unguarded extra prefetch in the OFF path",
     mutated("src/search.cpp", "        shared_.tt.prefetch(board.key());\n        const std::uint64_t nodes_before",
             "        shared_.tt.prefetch(board.key());\n        shared_.tt.prefetch(board.key());\n        const std::uint64_t nodes_before"), "reject"),
    ("#ifdef FLAG with trailing comment (not recognised as a guard)",
     mutated("src/search.cpp", "#ifdef " + FLAG + "\n            if (s13", "#ifdef " + FLAG + " // S13\n            if (s13"), "reject"),
    ("#define FLAG forced on in a production header",
     mutated("include/forge/search.hpp", "namespace forge {\n", "#define " + FLAG + " 1\nnamespace forge {\n"), "reject"),
    ("CMake option default ON",
     mutated("CMakeLists.txt", 'TtChildPrefetch experiment" OFF)', 'TtChildPrefetch experiment" ON)'), "reject"),
]
# Known limit (not a control): the contract reads only these files, so a change anywhere else is
# invisible to it; that part is covered by the branch's git diff file list and the compiled OFF build.
print("contract reads only:", ", ".join(contract.FILES))

unexpected = 0
for description, candidate, expected in controls:
    try:
        contract.validate_source(candidate, base)
        outcome, reason = "accept", ""
    except ValueError as error:
        outcome, reason = "reject", str(error)
    good = outcome == expected
    unexpected += 0 if good else 1
    print(f"{'EXPECTED  ' if good else 'UNEXPECTED'} {outcome:6} {description}" + (f" -- {reason}" if reason else ""))
print(f"{len(controls)} controls, {unexpected} unexpected")
sys.exit(1 if unexpected else 0)
