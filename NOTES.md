# B4 continuation checkpoint — 2026-10-29

Base b7c177222038e9332965a95ec53ea3b94e90dbc9; final source2beaad8.
All64 tunables advertised; unknown names diagnosed; accepted actual changes after B1-B4 presets diagnosed.
OFF resets preset tracking. Invalid/refused/no-op assignments retain old values and do not claim overrides.
Native Release150 and debug155 checks PASS; full CTest56/57 (onlyfourknownforge_testslines).
Allfive OFF pins and perft54865609 PASS, FMA0. No search values changed; no speed/Elo claim.
Actualfastchess-strict, Windows and full-engine sanitizer qualification remain UNVERIFIED.
Read astra2_evidence/B4/README.md for all original evidence and reproduction commands.

B1 final23e940b; B2 final45314a5 (additional baseline SMP mate-test failure preserved);
B3 final9a09e76. B5 now implementing defaultzero SingularV2/N1 on its own b7 branch.
B6 bench matrix and B7 final report remain. When combining branches, new B1/B2/B5 option setters
must use B4's assign_option observer and retain each feature's preset ownership rules.
IDEA_SOURCE: user strict-UCI requirements and Forge's own option registry.
