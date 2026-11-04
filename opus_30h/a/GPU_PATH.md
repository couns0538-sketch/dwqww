# Item A - the GPU path (R14 ROCm trainer) - design note, NOT run in this job

Why not run: the GPU was booked by the npt keeper for the whole job (window to 2026-11-08 00:00 PC; live line s39,
next s40 at 15:48 Nov 3); no written release from Engine QA. Everything below is CPU-side preparation for the window;
the CPU fine-tune (o30_fit.py) produced this job's candidates instead.

## What R14 left (unchanged, ready)
- `forge-v2-bullet` (branch opus-r13-p4-v2nets, `opus_r13/p4/forge_v2_bullet/src/main.rs`, MIT trainer library
  da426a49 as a tool, never linked into Forge), ROCm build `D:\o14a\p4\target_rocm\release\forge-v2-bullet.exe`
  sha256 0028dd9c...; request `opus_r14/b/GPU_REQUEST.md`. It trains PURE nets (sigmoid(out) vs the blended score) from
  the J1 binpack, 1 king bucket, 8 output buckets, export with residual = False.

## What a residual v2 run needs (the shape this job chose; the engine side is done: EvalFileV2)
1. Residual target: the trainer library computes targets inside its value mapper (crates/bullet_lib/src/value.rs,
   make_mapper) and has dense model inputs ("targets", "entry_weights"). Add a third dense input "base" (1 x 1) filled
   per row with hce_stm / eval_scale and add it to the network output before the loss (builder.rs + main.rs: ~30 lines in
   a PRIVATE copy of the library under D:\o30, never F:\bullet_hip\src). Export with the residual flag.
2. HCE per row: the J1 binpack has no HCE; read the FPOS + FHCE shards instead (they ARE the binpack's rows, 304,999,573,
   see DATA.md) with an own DataReader (32-byte board + score + meta + int16 HCE) - also gives the skip lists / jobA
   overrides of `D:\o30\data` for free. The library's DirectSequentialDataLoader needs on-disk 32-byte records (9.8 GB:
   too big for D: under the 50 GB floor), so the reader must stream from the FPOS files.
3. King buckets: ForgeV2::map_features with the king map (+ mirror) exactly as include/forge/nnue_v2.hpp
   (kr = own king square in the perspective's frame, bucket = map[kr], flip = 7 for files e-h of a mirrored net);
   prove it with parity_o30.sh on random nets (reference + engine builds already exist).
4. Warm start from the lock net (o30_v2net.py from-lock) so a short GPU run starts at the lock's loss, and the
   per-checkpoint holdout scores of o30_score_v2.exe (the library has no validation pass).
5. Checks before every GPU minute: the R14 GPU_REQUEST list (written window, keeper says npt not running, RAM >= 8 GB,
   disk) - run_fit.sh has the same checks for the CPU trainer.

## What the CPU results say about priorities (see RESULTS.md)
Fine-tuning the lock shape with output buckets moves the S31 loss by < 1e-6 in 30M positions; the lock net is converged
on the 5k-node self-play labels. A GPU run of the same data mainly buys more capacity (king buckets, H512) - worth it only
if the KB4 CPU decider shows that capacity helps; better labels (the 50M relabel) are the other lever.
