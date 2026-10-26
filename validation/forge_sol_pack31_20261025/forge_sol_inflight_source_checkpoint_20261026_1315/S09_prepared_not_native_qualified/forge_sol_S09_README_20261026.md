# S09 bucket trainer/export source preparation, 2026-10-26

Prepared independently for later ordered root integration. This is a source
checkpoint, not a completed S09 strength experiment. No engine base, trainer
input, net, gate or GPU queue was changed. No compiler/native-engine, training,
Git or network operation was run.

This work builds directly on the CR-passed step 1, preserved unchanged at
step1_dependency/fc_buckets8_h256e12.patch, SHA256
`ed28132d48b75496732f0ecf25753ad869787c84a4939aaf004b3de8580a9704`.
Its README_BUCKETS8 and IDEA_SOURCE are preserved too. The step-1 utility
make_heads_inc.py was extracted unchanged from that patch (SHA256
`39ec705a93fed1cb80773fc37ea4a2dfe20008c628fcd38b462620c1c112b6b0`).
The new converter reuses its parser/formatter; it does not restart engine
plumbing or implement a second include parser. A managed-read adapter avoids
the dependency's unclosed-file warning without editing its source bytes.
The original engine patch is referenced under its original name and hash;
there is no newly named resubmission or claimed native qualification of it.

forge_sol_S09_train_resid_v3b_20261026.py is a new source copy of supplied v3b.
forge_sol_S09_trainer_20261026.patch is its canonical a/train_resid_v3b.py to
b/train_resid_v3b.py unified diff. GNU patch --dry-run and actual application
with -p1 -F0 on a fresh owned source copy both pass; applied bytes equal the
prepared trainer. Git application and engine/L/Lprime/B build qualification
remain pending root integration. The unchanged qa_adam_dml.py dependency is
bundled and hash-pinned so the default optimizer import is not missing.

The trainer adds --buckets 1|8, default 1. At 1, the original forward arithmetic,
initialization shapes and export formatting remain unchanged. At 8, the output
layer has eight rows and selects a position's head using all occupied squares,
including kings: clamp((pieces-1)//4, 0, 7). Output weights and biases are
exported head-major as NnueW2[8*2*H] and NnueB2[8], with
FORGE_NNUE_OUTPUT_HEADS 8. No accumulator narrowing or integer inference path
was added. The existing int16/4096 include storage is dequantized to float by
the preserved engine loader.

CLI defaults follow the observed f006 run: H256, residual, 48 epochs, batch8192,
lr0.000707, warmup300, blend-end0.6, seed25 and final full validation. These
come from NETS_snapshot_20261025_1030.md line1627 and its final-holdout result;
the run name's bs16k_lr10e4 text is stale. The original referenced f006 settings
files are absent, so the displayed learning-rate precision and inherited
v3b defaults are not represented as a recovered exact settings dump. Unspecified
defaults, such as val_positions=4M and min_lr_frac=0.01, remain v3b defaults.
Updating the recipe defaults is intentional; the single-bucket equivalence
claim concerns equal parameters/configuration and exported bytes, not equality
between old and new CLI recipes.

Convert a supported one-head include into a new eight-head include:

```sh
python3 -B forge_sol_S09_buckets_20261026.py replicate input.inc new_output.inc
python3 -B forge_sol_S09_buckets_20261026.py check new_output.inc
```

The converter supports legacy scalar B2, singleton B2 arrays, and literal
HEADS/BUCKETS=1 spellings with line/block comments. It validates dimensions,
storage range and consistent head declarations, then preserves feature weights
and repeats the output head exactly eight times. Validation and replacement
use the same head-directive spans. Unknown macro expressions fail closed.
Outputs must be new and outside protected paths; source bytes are re-hashed.
Results are deterministic across destination names. General C++ preprocessing
is outside this generated-include format contract.

Run source/export tests:

```sh
OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  taskset -c 1 nice -n19 python3 -B forge_sol_S09_tests_20261026.py
```

Fifteen tests pass. They execute the actual old/new export functions extracted
with AST, using real NumPy arrays behind parameter-access adapters. Single-head
.inc and .bin outputs are byte-identical; eight-head arrays, every bias,
shape/range refusals, unchanged inputs, deterministic conversion and numeric
roundtrip are covered. Other checks cover all piece-count boundaries, all eight
heads via a known-answer bias control, feature perspective, float32 accumulation,
actual argparse defaults and malformed commented head directives. TDD RED/GREEN
logs retain failures and fixes. These are export/math tests, not a Torch forward
or gradient run. The public interpreter has no Torch; a separately proposed
private CPU recovery remains pending root validation.

The bounded numeric audit used the existing f006 include and the first10000
rows of supplied synthetic h000.pos. Its FPOS/FHCE loader and nibble decoding
were AST-executed unchanged from v3b, rather than reimplemented. A NumPy float32
reference using the preserved fixed16-lane association observed:

- 10000/10000 logits bit-identical; CP mismatches0; max absolute difference0.
- A deliberately changed per-head bias caused10000/10000 CP mismatches.
- Actual sample head counts: [0,109,1442,4163,3274,915,95,2]. Head0 was exercised
  by the separate known-answer control, not by this sample prefix.
- All source hashes unchanged; single CPU1, nice19, BLAS/MKL/OMP threads1;
  peak RSS about66MiB. The converted include was temporary and removed.

This establishes duplicate-head NumPy equivalence only. The required native
1M-position parity, Std tests, actual Torch CPU forward/gradients, holdout loss
and trained-net null-pruning regression are UNVERIFIED. No trained eight-head
candidate exists here, and no held-out loss or playing-strength result is
invented. Those checks need the root's authorized runtime/build phase. Any
future net remains offline and UNPROVEN until the stated CR and crew process.

The receipt records full hashes and commands. Source inputs are preserved,
raw reports remain separate from historical step-1 claims, and SHA256SUMS is
checked from this folder. S16 and S34 sealed preparations were not modified.
