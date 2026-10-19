# P2: lazy check-mask speed hypothesis
src/search.cpp:248-276 eagerly computes masks; direct_check at :392-395 uses them only in generate_quiets :441-452 and generate_evasions :455-469. Capture-only qsearch :336-346 never consumes them. Defer exact mask math to those two consumers in isolated candidate. Risk: uninitialized masks on evasion path or changed tie order. No measured speed claim.
