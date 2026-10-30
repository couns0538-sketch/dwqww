"""R10: an untrained K32H3^ net written by nnue-pytorch's own NNUEWriter (a freshly initialised model), for load,
parity and NPS checks at production sizes. Evaluations of such a net are meaningless.
  NNUE_REPO=<clone> NNUE_FT_BACKEND=torch <venv python> -I -B make_init_net.py <out.nnue> --l1 1024 [--l2 32 --l3 32] [--seed 1]"""
import os
import sys

a = sys.argv
out = a[1]


def opt(name, default):
    return int(a[a.index(name) + 1]) if name in a else default


sys.path.insert(0, os.environ["NNUE_REPO"])
import torch  # noqa: E402

import model as M  # noqa: E402
from model.utils.serialize import NNUEWriter  # noqa: E402

torch.manual_seed(opt("--seed", 1))
cfg = M.ModelConfig(L1=opt("--l1", 1024), L2=opt("--l2", 32), L3=opt("--l3", 32))
m = M.NNUEModel("K32H3^", cfg)
w = NNUEWriter(m, description=f"R10 untrained K32H3^ L1 {cfg.L1} (nnue-pytorch NNUEWriter, seed {opt('--seed', 1)})",
               verbose=False)
with open(out, "xb") as f:
    f.write(w.buf)
print(f"wrote {out}: {len(w.buf)} bytes, L1 {cfg.L1} L2 {cfg.L2} L3 {cfg.L3}")
