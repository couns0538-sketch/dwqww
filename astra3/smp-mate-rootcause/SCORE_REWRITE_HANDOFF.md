# A2 score-only rewrite experiment — implementation handoff

Baseline diagnostic revision: `dbab8484536465080c33df9bb03904a26ed997fd`. Engine source remains `926c55f33227bc4a030d7ce5b1140528aeba75af`; no engine/header/CMake changes. IDEA_SOURCE: the observed serial helper-seed miss, the user's one-entry intervention request, and Forge's public TT store/probe contract.

New mode: `--mode rewrite`. It runs five independently fresh conditions for K1, optionally K2 (the requested seed-depth range is capped at 2):

1. `rewrite_no_touch`: helper seed then main, without any pre-main probe/store.
2. `rewrite_root_identical`: probe/rewrite/re-probe the root, retaining every value.
3. `rewrite_root_mask`: the same operations, replacing only the raw score with ValueNone.
4. `rewrite_child_identical`: identical rewrite at the position after d5c5.
5. `rewrite_child_mask`: replace only that child's raw score with ValueNone.

Only round 1 is intervened on. Both rounds still run and retain TT/worker histories; every condition starts from its own fresh 16 MB TT/workers. Helper is quiescent during intervention and main. Existing v1 logs/binaries are untouched.

`rewrite_entries.tsv` records actual BEFORE and AFTER entries. The harness requires generation 1, a hit, a matching key32, and current generation. No entry is inserted on a miss: it logs `NO_INTERVENTION` and fails with exit 2. Already-ValueNone mask targets likewise fail explicitly. After store, it verifies key32, move, eval, depth, complete gen_bound (bound/PV/generation), rule50 clock and padding are unchanged, and the score equals the requested replacement. Equal depth guarantees payload admission (`depth + 4 > stored depth`) on this serialized same-key store. ValueNone=32002 fits the TT's int16 range.

The requested 64-bit key, cluster count and reconstructed cluster index are logged and checked. **Public TTProbe hides its actual cluster/slot handles**: the index is reconstructed from the frozen source's key/count indexing contract, not introspected. Serialized same-key probe/store/re-probe uses the same opaque handle and asserts all public payload fields; no private-access workaround or header change is used. Initial generation 1 of a fresh table means the pre-main probes cannot age entries from an earlier search.

Native build and execution of this new mode are **UNVERIFIED at handoff**. Root runs and publishes the experiment. First bounded invocation, after building into a new directory:

```sh
python3 astra3/smp-mate-rootcause/source/build_a2_repro.py \
  --repo /tmp/forge-astra3-smp-mate-rootcause \
  --core-build /tmp/forge-astra3-build-integration \
  --out /tmp/forge-astra3-smp-mate-rootcause/astra3/smp-mate-rootcause/build_score_rewrite

astra3/smp-mate-rootcause/build_score_rewrite/a2_tt_seed_repro \
  --mode rewrite --trials 1 --max-seed-depth 1 --main-depth 14 \
  --seed 20261029 --cpu CPU_NUMBER --smp-v2 1 --max-seconds 30 --trial-seconds 10 \
  --out astra3/smp-mate-rootcause/native_rewrite_k1
```

Use a verified permitted CPU and capture stdout/stderr to new files. For K1+K2 use `--max-seed-depth 2` and a new output path. The existing build helper records the complete g++ invocation and exact source/core hashes; only its output directory changes. Compare no-touch versus identical rewrites first. A masked-score recovery localizes a causal contribution of that seeded score; it does not prove a production fix, identify the original bound provenance, or establish Elo.
