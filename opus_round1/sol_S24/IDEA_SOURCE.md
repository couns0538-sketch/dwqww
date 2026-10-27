# S24 idea sources

- Spec: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 33 / inventory S24: put the Job A default-build leaks (dead uci
  option, extra stats line after bench, unconditional thread_local counters) under `#if`, in at most 30 changed
  lines, as a follow-up on top of e661a145.
- Sol's shelved patch `releases/forge_sol_jobACD_20261025/forge_sol_exactint32_h256e12_20261025.patch` (Sol's
  branch 17aa0cae). Its own macro `FORGE_NNUE_EXACT_INT32_AVX2` (default 0 in `nnue.hpp`) is reused; no new macro
  is introduced except the counting helper `FORGE_NNUE_COUNT`.
- The "compile diagnostics out" pattern is the usual one for hot-path counters, as in Stockfish's `dbg_hit_on`
  helpers, which exist only in debug builds.
