"""lm_det.py - Opus R14-B: run the trainer's train.py reproducibly on the CPU (loss match). Used as the script that
opus_tools/guard_exec.py runs: `guard_exec.py <this file> <train.py args...>`, working directory = the trainer copy.

Two things make the npt trainer non-reproducible run to run, independent of the data loader (found 2026-11-02):
1. train.py builds the model before it applies --seed, and this torch build (2.11.0+rocm7.13.0) seeds its default
   generator from the clock per process, so the initial weights differ in every run. This wrapper seeds torch,
   random and numpy with the --seed value BEFORE train.py runs (train.py seeds again later with the same value).
2. Multi-threaded CPU kernels: run with --threads 1 (OMP/MKL 1) and torch's deterministic algorithms (set here).
"""

import os
import random
import runpy
import sys

import numpy as np
import torch

args = sys.argv[1:]
seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 42  # 42 = the trainer's default
torch.manual_seed(seed)
random.seed(seed)
np.random.seed(seed)
torch.use_deterministic_algorithms(True)
sys.path.insert(0, os.getcwd())  # the trainer root (train.py imports data_loader, model, trainer from there)
sys.argv = ["train.py"] + args
runpy.run_path(os.path.join(os.getcwd(), "train.py"), run_name="__main__")
