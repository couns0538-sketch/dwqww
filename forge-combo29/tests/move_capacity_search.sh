#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:-/tmp/forge-move-capacity}"
mkdir -p "$out/include/forge"
python3 - "$out" <<'PY'
from pathlib import Path
import sys
source=Path('include/forge/board.hpp').read_text()
needle='static constexpr std::size_t Capacity = 256;'
assert source.count(needle)==1
(Path(sys.argv[1])/'include/forge/board.hpp').write_text(source.replace(needle,'static constexpr std::size_t Capacity = 1024;'))
PY
"${CXX:-g++-14}" -std=c++20 -O2 -I"$out/include" -Iinclude tests/move_capacity_search.cpp src/board.cpp src/bitboard.cpp -o "$out/search"
"$out/search" | tee "$out/search.log"
