# Independent-teacher data pipeline — progress

Parent27070fe remains intact. New branch: forge/independent-teacher-20261023.
No old training data, production source changes, strength matches or net promotion.

The six-hour job began11:04AM PDT on October23. Stop new work4:34PM; handoff by5:04PM PDT.
Target: at least5M fresh game-identified positions, whole-game train/validation/audit,
externalStockfish teacher, fixed40% result blend and one8-epoch residual training run.
Teacherdepth8 is being screened before the generation/label protocol is frozen.

Current: trainer/compare updates and compact generator/labeler are being implemented
with meaningful regression tests. Exact5101 executable recovered from original
source-bound build, SHA377eec6ea5b8ca8219f70132366f2a96eecbc528603b066be4f679d4b2fa9819.
Stockfish19 is an external tool only; no source or licence text is copied.
MIT SPDX notice added to trainer; original12 tools tests pass. Both current checksum indices now verify all39 entries; the original18-entry
pack index is preserved verbatim. Fixed-target training/audit support passes8new,
25legacytrainer and13holdout tests with an independent clean source review. No dataset/training/audit result or Elo gain is claimed yet.

Progress commits and exact settings/artifact hashes are recorded in manifest.json.

First source checkpoint: trainer and manifest ready; production generation and
teacherlabeler are still under bounded throughput/lifecycle validation. No5M
dataset or trained net has been claimed. See source-checks-01.zip for exact receipts.
