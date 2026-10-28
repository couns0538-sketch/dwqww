#!/usr/bin/env python3
"""Plant one of two S11 table bugs into a COPY of include/forge/material_key_table.hpp (byte-exact edit).
  1: Contributions[0][8] + 1 (eight white pawns): the key of one material class moves by one; the
     correction slots are only relabelled, so bench nodes cannot see it; the unit test must.
  2: Contributions[0][8] = Contributions[0][7]: 8 and 7 white pawns share a key term, two material
     classes merge; bench nodes with MaterialKeyTable on must change.
usage: plant_bug.py <1|2> <path to the copied material_key_table.hpp>"""
import sys
from pathlib import Path

OLD = b"values[slot][count] = factor * (static_cast<std::uint64_t>(count) + 1U);"
NEW = {
    "1": b"values[slot][count] = factor * (static_cast<std::uint64_t>(count) + 1U) + (slot == 0 && count == 8 ? 1U : 0U);  // PLANTED BUG 1",
    "2": b"values[slot][count] = factor * (static_cast<std::uint64_t>(count) + 1U - (slot == 0 && count == 8 ? 1U : 0U));  // PLANTED BUG 2",
}
which, path = sys.argv[1], Path(sys.argv[2])
if "worktrees/opus_sol_s11/" in path.as_posix():
    raise SystemExit("refusing to edit the worktree; pass a copy")
text = path.read_bytes()
if text.count(OLD) != 1:
    raise SystemExit("unexpected header contents")
path.write_bytes(text.replace(OLD, NEW[which]))
print(f"planted bug {which} in {path}")
