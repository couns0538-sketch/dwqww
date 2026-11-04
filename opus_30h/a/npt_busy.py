"""npt_busy.py - prints the number of npt-like python processes (the GPU guard's own rule, o30_gpu_guard.npt_like:
command line names the npt data / trainer tree, or is unreadable = counted, fail closed). Opus 30-h job, own code."""
import sys

sys.path.insert(0, 'D:/o30/wt/opus_30h/a')
from o30_gpu_guard import npt_like  # noqa: E402

print(len(npt_like()))
