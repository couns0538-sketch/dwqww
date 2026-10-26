# S08 OFF source-equivalence proof, 2026-10-26

PASS for preprocessing-token identity on all eight production TUs of Lprime and B. Fourteen comparisons match exact GCC `-E -P` stdout bytes. Both UCI comparisons differ in outside-token line formatting; native libclang19 finds identical500313token kinds and complete spellings. Five controls preserve literal whitespace/raw-string newlines and detect token joins. No source/string normalization is used.

Both original FAIL receipts remain unchanged: the first demanded raw-byte identity; the second completed all16pairs then incorrectly demanded zero output bytes from excluded profile.cpp. Its eight whitespace bytes contain zero lexical tokens. The final audit records this distinction. Clang's56nonfatal parser diagnostics per UCI input are not a compile pass; complete lexical ranges reach EOF.

OFF CMake excludes profile.cpp and prof_tests; all other CMake text is byte-identical. Original Lprime/B and repaired source hashes remain unchanged. Existing canonical OFF ELFs e3df99cd/55fa7e81 have340defined-symbol lines each and no profiling symbols.

This supports reuse of canonical OFF native evidence. No new v2 OFF binary was compiled or executed; no fresh binary hash, B-ON qualification, speed or Elo result is claimed. The B overlay is small and private; originals were untouched.
