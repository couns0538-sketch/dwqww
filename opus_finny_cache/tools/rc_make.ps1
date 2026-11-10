# rc_make.ps1 (opus2, PS 5.1) - D3 cache gate: make an INSTRUMENTED SCRATCH copy of parent P (never shipped, never gated)
# that counts nnue::refresh / update / evaluate calls, in-tree refreshes, root refreshes and the walk-back length per lazy
# update, and prints them on the extra UCI command 'rcdump'. Anchored edits, each must match exactly once (fail closed).
param([string]$Src = 'D:\forge_jobs_20261107\opus2\out\src\p', [string]$Dst = 'D:\forge_jobs_20261107\opus2\out\scratch\rc\src')
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Dst) { throw "exists: $Dst" }
New-Item -ItemType Directory -Force -Path $Dst | Out-Null
Copy-Item -Recurse -LiteralPath (Join-Path $Src 'include') -Destination $Dst
Copy-Item -Recurse -LiteralPath (Join-Path $Src 'src') -Destination $Dst
function Edit-Once([string]$Rel, [string]$Old, [string]$New) {
  $f = Join-Path $Dst $Rel; $t = [System.IO.File]::ReadAllText($f)
  $n = ([regex]::Matches($t, [regex]::Escape($Old))).Count
  if ($n -ne 1) { throw "anchor count $n in $Rel for: $Old" }
  [System.IO.File]::WriteAllText($f, $t.Replace($Old, $New))
}
# nnue.hpp: declarations
Edit-Once 'include\forge\nnue.hpp' "#include <array>`n" "#include <array>`n#include <atomic>`n"
Edit-Once 'include\forge\nnue.hpp' "extern bool enabled;`n" ("extern bool enabled;`n// RC scratch instrumentation (D3 gate only)`n" +
  "extern std::atomic<unsigned long long> rc_refresh, rc_update, rc_eval, rc_tree_refresh, rc_root_refresh;`n" +
  "extern std::atomic<unsigned long long> rc_back[10];`nvoid rc_dump();`n")
# nnue.cpp: definitions + counters
Edit-Once 'src\nnue.cpp' "bool enabled = true;`n" ("bool enabled = true;`n" +
  "std::atomic<unsigned long long> rc_refresh{0}, rc_update{0}, rc_eval{0}, rc_tree_refresh{0}, rc_root_refresh{0};`n" +
  "std::atomic<unsigned long long> rc_back[10];`n" +
  "void rc_dump() {`n    std::printf(""info string RC refresh %llu update %llu eval %llu tree_refresh %llu root_refresh %llu back"", rc_refresh.load(), rc_update.load(), rc_eval.load(), rc_tree_refresh.load(), rc_root_refresh.load());`n" +
  "    for (auto& b : rc_back) std::printf("" %llu"", b.load());`n    std::printf(""\n""); std::fflush(stdout);`n}`n")
Edit-Once 'src\nnue.cpp' "#include ""forge/nnue.hpp""`n" "#include ""forge/nnue.hpp""`n#include <cstdio>`n"
Edit-Once 'src\nnue.cpp' "void refresh(const Board& board, Accumulator& accumulator) {`n" "void refresh(const Board& board, Accumulator& accumulator) {`n    rc_refresh.fetch_add(1, std::memory_order_relaxed);`n"
Edit-Once 'src\nnue.cpp' "void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty) {`n" "void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty) {`n    rc_update.fetch_add(1, std::memory_order_relaxed);`n"
Edit-Once 'src\nnue.cpp' "int evaluate(const Board& board, const Accumulator& accumulator) {`n" "int evaluate(const Board& board, const Accumulator& accumulator) {`n    rc_eval.fetch_add(1, std::memory_order_relaxed);`n"
# search.cpp: in-tree refresh, walk-back histogram, root refresh
Edit-Once 'src\search.cpp' "            nnue::refresh(board, ss->accumulator);`n            if (residual) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);`n        } else {`n" ("            nnue::rc_tree_refresh.fetch_add(1, std::memory_order_relaxed);`n            nnue::refresh(board, ss->accumulator);`n            if (residual) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);`n        } else {`n" +
  "            nnue::rc_back[back < 9 ? back : 9].fetch_add(1, std::memory_order_relaxed);`n")
Edit-Once 'src\search.cpp' "        nnue::refresh(board, ss->accumulator);`n        if (nnue::residual()) ss->runtime_psqt" "        nnue::rc_root_refresh.fetch_add(1, std::memory_order_relaxed);`n        nnue::refresh(board, ss->accumulator);`n        if (nnue::residual()) ss->runtime_psqt"
# uci.cpp: rcdump command
Edit-Once 'src\uci.cpp' "        } else if (command == ""ponderhit"") {" "        } else if (command == ""rcdump"") {`n            forge::nnue::rc_dump();`n        } else if (command == ""ponderhit"") {"
"rc scratch source ready: $Dst"
