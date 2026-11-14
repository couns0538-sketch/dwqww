# Narrow mate-alpha guard and round-4 validation

Task startUTC:2026-11-14T19:48:28.579Z. Owner authorized continued collaborative work after the original eight-hour window. Work order: Fable message0002, with owner compile-OFF and counts-only constraints retained.

Base:8e805fb482a97b7182f3fa4c12f26ce7e1d88c19. Audited baseline:12c791d5451b158fd6ed1b506b4869b15c8a5b4e. Four source-only audit fixes reapplied as separate commits:

- e349e3e859f2cc3d9b0eae08a5dd74e3b0e45705 -> 5ad7ac6e4aa15bcfb35bf54a7d826521423bcf64 (forge-combo29/src/search.cpp)
- bf4154454ddc7b226bc1734bfc84d75569cdfc07 -> bafb2d5bf3a542da5c51608bc9babf87f79cfa69 (forge-combo29/include/forge/search.hpp)
- 1ebc9b48084ac26db00a71b50fafccd2bfc8baa4 -> 8c4fb7d14fa5519d13e32914a4d97866a8b51a56 (forge-combo29/src/eval_params.cpp)
- efb3eaa37a84198cc8c0ac1c35d0dc5cf384376d -> 12c791d5451b158fd6ed1b506b4869b15c8a5b4e (forge-combo29/src/board.cpp)

Current phase: audited baseline validation. Guard not implemented or accepted. No runtime results are claimed yet. The four-hour successor soak budget starts only after guard acceptance; it has not started.

Proposed guardA affects only the two static-evaluation futility predicates when current alpha is a mate score. Existing LMP/history/SEE, TT conversion, qsearch and score reporting remain outside the change. New MateAlphaGuard UCI option false by default, behind compile gate FORGE_MATE_ALPHA_GUARD undefined/0 by default; toggle clears hash. No CMakeLists change; <=60 engine-line delta. If A does not reach the demonstrated d1c1 witness, record the failure and consult Fable before widening.

Original frozen source f27b197 and old evidence remain on integrate/combo29-all /soak/combo29-all. Completed old-tree matches total12000; remaining LMR4000 and broader old-tree sample were omitted following Fable's recommendation. Fault092 has10/10 direct repeats. Root oracleDTM15plies=UCI mate8; chosenb3f3 DTM17plies=mate9; original mate17 and isolated-arm mate11 are conservative reported deadlines.

Checkpoint 2026-11-14T19:55:54.257Z: Audited baseline validation. Audited baseline Release build completed, GCC14.2 x86-64-v4; Threads1 Hash16 OwnBookfalse pins312866 /862329 /4865609. Baseline binary SHA256 06a2b1d582c05bb4a762ef76f64ec171a8a2ca031230b27fe3a5d2bc8ed8bace. Exact commands and output are under tests_astra_mateguard/logs. Preparation encountered missing partial-clone metadata and a whitespace-trimmed patch serialization error; both tool failures and corrected commands are retained, with no engine workaround. Guard acceptance and successor soak are still pending.
