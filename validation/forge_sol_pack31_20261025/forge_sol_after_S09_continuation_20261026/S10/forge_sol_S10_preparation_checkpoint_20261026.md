# S10 prepared experiments — 2026-10-26

This is a source preparation checkpoint. S10 is not delivered or native qualified. No compiler or engine was run by this work. No speed, strength or Elo claim.

All four standalone patches passed Git check, GNU dry run and GNU -p1 -F0 application on L/Lprime/B (36 operations). Original input hashes were unchanged. The six changed files per patch are CMakeLists.txt, search.hpp, search.cpp, uci.cpp, README.md and IDEA_SOURCE.md. Both compile and UCI switches default OFF. Atomic requests are snapshotted once before helper workers launch; hot recursive search uses worker-local state. The separate bench Searcher explicitly inherits the option.

|Feature|Patch SHA256|
|---|---|
|SingularSiblingLmr|`83b9e88b25347cf862761e54c1447d4f4edeccb1582c85dc6f5aff68d2712668`|
|QuietCheckLmpSurvival|`2c195c2d15f044128b68a2efc39500314b3310f551c53980b9965773358089e3`|
|ImprovingRazorGuard|`398a1bdac9606dea0b0b1b938dcd8e6ec7e6b8674435aee3584c3af6c8eda286`|
|CaptureHistoryLmp|`f7e9bf21fc8e80244545012f458024f7f42738cca22f498180d762408966ad63`|

18 pure safety tests pass, including replay of an original full16 CTest/JUnit inventory. These are tool tests, not new engine validation. The original activation guard had7 meaningful assertion failures; the original source and outputs remain. Two application harness predicates failed and were fixed without changing the engine patches: B legitimately has an extra test target, and GNU creates exact .orig backups for offset hunks.

The bounded native controller reuses published S07 transport/screens, S26-v4 all-configured-CTest and strict recipe validation, S05 FMA and S08 process containment. It builds only the main target first, runs bare OFF d11 before UCI, then checks actual d11 ON activation. Inert options are rejected before full Std/WAC. Passing activation proceeds to the required five-depth screen, compile-OFF full-token proof, full targets/Release+ASanUBSan CTest, perft5 and FMA0. ASAN uses Release -O2 -g0 with both sanitizers and leak checking; no speed comparison is made. A single 1000ms WAC ON screen per feature is registered on Lprime, threshold283; B does not repeat it. All remaining runtime stages are UNVERIFIED.

Example only; do not run until root grants this window:

```bash
PYTHONPATH=/workspace/.cloud-setup/venv/lib/python3.12/site-packages taskset -c 4 nice -n 19 python -B forge_sol_S10_native_controller_20261026.py --execute --authorization-reference ROOT_GRANT --feature singular_siblings --base Lprime --cpu 4 --out /tmp/forge_sol_S10_singular_Lprime_NATIVE_20261026 --max-seconds 2400
```

For sanitizers the owner must run through the permitted execution path supporting LSan; the controller never turns leak checking off. NEW /tmp storage avoids the nearly-full /workspace filesystem. Inputs and previously executed files are never overwritten. The dependency manifest pins exact published/recovered helper sources and the source-application proof. If /tmp source views are lost, recover exact authoritative bases and apply the corresponding patch; compare every resulting source hash against the retained application proof before build.

Next: root review, native authorization after S09, first frozen candidate; continue all candidates even when one is rejected.
