# Forge PGO / native qualification provenance — 20261025

Idea source: user TaskC and GCC's documented profile-generate/profile-use mechanism; idea only, own implementation. No code/constants/tables were copied from another chess engine. No search/evaluation/network source change and no new UCI option. The lock source is f4911f2; baseline/profiled builds share the exact PC base flags. Stable per-TU object paths and a copied frozen gcda dataset prevent profile mismatch and keep later validation out of training. Training uses mandatorybench11, bench16 and six explicit varied depth8 FENs.

Win32 suspended launch, JobObject private-commit cap, affinity and Idle controls use the public Windows API; own implementation based on the previous Forge qualification workflow, not external engine code. Native vs software evidence, no-kill cleanup limits, and original-test timeout behavior are explicit.
