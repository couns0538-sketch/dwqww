# S26 idea sources and reused project components — 2026-10-26

IDEA_SOURCE: the user's S26/S43 batch specification and supplied Forge h256_e12 CMake/UCI/test contracts. New orchestration, guard/report logic and regression fixtures were written for this job; no other engine implementation or tuned constants were copied.

Existing Forge project helpers are reused byte-for-byte: S07 screen/UCI parser, S05 NNUE FMA checker, merged S01 pin helper and S27 compiler-recipe guard. The original dependency registry and portable setup pin their SHA256 values. Exact original-byte evidence packaging reuses the unchanged S27 decoder. These are dependencies with their original provenance, not newly authored copies or global installations. The files/09_sol_returns and CR reports supply documentary comparison references; they do not authorize accepting a candidate or changing the lock.
