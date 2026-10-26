# S08 authorized profile corpus, 2026-10-26

The sealed selection has **2,000 distinct legal boards: 300 WAC, seven nonduplicate original bench boards, and 1,693 original Forge opening boards**. The eighth bench board duplicates WAC001 and is not counted twice. All selected boards passed python-chess validity; all 20,316 opening moves were replayed as legal moves and matched the supplied final FEN. No engine was executed by this preparation.

`MISSING_INPUTS_20261025.md`, SHA256 `11e1be8ac83c6ce78d7e609059c4a96ec4b002ae923d44683077a0df038862b2`, explicitly permits WAC300 + bench + tools/openings in place of the absent STS suite. The generated openings are synthetic original quiet-development positions, not WAC or STS. The original WAC/STS-only shortfall remains **1,700** and is separately reported. No best moves are invented for the substitutes.

The helper pins every input and selects in source order; two actual new-directory executions produced byte-identical corpus, manifest and provenance files. Existing files are never overwritten. Full source hashes and original line/index provenance are retained in the generated JSON. The `line` entry on BENCH rows identifies the common source array; the ordered IDs identify its individual entries.

The successor collector requires an explicit pinned handoff authorization and per-file hashes for BENCH/OPENING. It reports `COMPLETE_AUTHORIZED_SUBSTITUTE`; it still rejects training boards, undeclared substitutes and wrong authority/input hashes. Only `_epd` and `corpus_metadata` ASTs differ from the preserved bf5 collector. Process supervision, final-drain checks, packet parsing, collect and main ASTs are unchanged.

Tests: 11 new tests pass. The current original test module `S08/test_forge_sol_S08_collect_profiles_20261026.py` contains **23** unittest cases, and all 23 pass against the successor. The historical filename `forge_sol_S08_successor_existing29_GREEN_20261026.log` reflects a stale expected count; its actual output says 23. Do not report it as 29. The original implementation rejects the authorized opening case (captured RED); it was not modified.

To regenerate using the current pinned supplied paths:

```bash
PYTHONPATH=/workspace/.cloud-setup/venv/lib/python3.12/site-packages python -B \
  /workspace/forge-pack24-20261026/S08_corpus_20261026/forge_sol_S08_authorized_corpus_20261026.py \
  --output /workspace/forge-pack24-20261026/S08_corpus_20261026/NEW_DIRECTORY
```

Native collection is root-owned and **has not been run by this helper**. Exact example with a 20,000-node per-position budget; source paths are absolute and output must be new. Run from the corpus directory because the manifest deliberately uses portable relative filenames:

```bash
cd /workspace/forge-pack24-20261026/S08_corpus_20261026/forge_sol_S08_selected2000_once_20261026
python -B ../forge_sol_S08_collect_profiles_substitute_20261026.py \
  --engine /workspace/forge-pack24-20261026/S08/forge_sol_S08_v2_Release_ON_window1_20261026/build/forge \
  --suite forge_sol_S08_WAC_profile_corpus_20261026.epd \
  --suite forge_sol_S08_BENCH_profile_corpus_20261026.epd \
  --suite forge_sol_S08_OPENING_profile_corpus_20261026.epd \
  --corpus-manifest forge_sol_S08_authorized_corpus_manifest_20261026.json \
  --required 2000 --nodes 20000 --timeout 600 \
  --output /workspace/forge-pack24-20261026/S08/NEW_PROFILE_OUTPUT
```

No speed or strength claim; the eventual firing-frequency table applies to this declared mixed profile sample and the fixed work budget, not a 2k tactics score.
