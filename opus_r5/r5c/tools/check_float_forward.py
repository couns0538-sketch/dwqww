"""R5C M4 cross-check: export_fnn4.py's numpy float forward vs the J7 trainer's own torch Model.forward
(read-only copies of fable-fb2-j7 tools/nnue/fable_nnue_train.py + fable_nnue_v3.py in tmp/j7ref), on the first
N positions of positions_100k.fen. Prints the max |difference| in cp (expected ~1e-3: float32 vs float64).
Staging (copies, never Fable's files): mkdir F:/opus_scratch/r5/r5c/tmp/j7ref;
  git show origin/fable-fb2-j7:tools/nnue/fable_nnue_v3.py > .../j7ref/fable_nnue_v3.py
  git show origin/fable-fb2-j7:tools/nnue/fable_nnue_train.py > .../j7ref/j7_trainer_ref.py
usage: check_float_forward.py [N]   (venv python -I -B, OPENBLAS/OMP threads 1; 2000 positions: max 0.00055 cp)"""
import importlib.util
import sys

import numpy as np
import torch

torch.set_num_threads(1)
REF = "F:/opus_scratch/r5/r5c/tmp/j7ref"
sys.path.insert(0, REF)
sys.path.insert(0, "D:/grok-pc-data/dwqww/.claude/worktrees/opus-r5c-netv4/tools/nnue")
spec = importlib.util.spec_from_file_location("j7_trainer_ref", REF + "/j7_trainer_ref.py")
trainer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trainer)
import export_fnn4 as ex  # noqa: E402  (main() only runs as a script)

CK = "F:/opus_scratch/fable/fb2/j7/run_l2_60/best.pt"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 500
ck = torch.load(CK, map_location="cpu", weights_only=True)
cfg = ck["cfg"]
model = trainer.build_model(cfg, torch)
model.load_state_dict(ck["state"])
model.eval()

import chess  # noqa: E402
fens = [l.strip() for l, _ in zip(open("F:/opus_scratch/fable/parity/positions_100k.fen", encoding="utf-8"), range(N))]
codes = np.zeros((N, 64), np.uint8)
meta = np.zeros(N, np.int64)
for i, fen in enumerate(fens):
    b = chess.Board(fen)
    for sq, p in b.piece_map().items():
        codes[i, sq] = p.piece_type + (0 if p.color else 6)
    meta[i] = 0 if b.turn else 1
us, them, ob = trainer.batch_features(codes, meta, cfg)
with torch.no_grad():
    cp_torch = model(torch.from_numpy(us), torch.from_numpy(them), torch.from_numpy(ob)).double().numpy()

cfg2, steps, w1f, t = ex.load_ckpt(CK)
idx, pieces = ex.features(fens, np.asarray(cfg["king_map"], np.int64), bool(cfg["mirror"]))
cp_numpy = ex.float_forward(cfg2, w1f, t, idx, pieces)
diff = np.abs(cp_torch - cp_numpy)
print(f"positions {N}: max |torch - numpy| {diff.max():.6f} cp, mean {diff.mean():.6f} cp")
print("PASS" if diff.max() < 0.05 else "FAIL")
