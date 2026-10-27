# IDEA_SOURCE — sol_S25fix

- Fix-ups S25-1 and S25-2 (QA findings L4-L7): `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3 (QA, 2026-10-27).
- Base: Sol's S25 checker, allowlist, parser cases and CMake registration (17aa0cae, read only); his 10-option
  allowlist is kept (AL1 `src/uci.cpp`/`src/book.cpp` hashes equal his trusted hashes; re-observed on the lock exe).
- AL1 pins: the lock record (`forge-engine-verify` skill). Expose builds: AL1 `CMakeLists.txt` / `src/uci.cpp`
  (`FORGE_EXPOSE_TUNABLES`).
- Timeout/kill-own-child and marker-checked temp cleanup: Python standard library (`subprocess`, `tempfile`). No
  external project code.
