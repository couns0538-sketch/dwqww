"""ckpt_io.py - JOB E (own code, 2026-11-12): read a training checkpoint without running code stored in the file.

`torch.load(..., weights_only=False)` unpickles arbitrary objects, so a crafted .pt file could run code the moment it
is opened. Every tool of this job reads checkpoints through `load_checkpoint()` instead. It uses PyTorch's restricted
loader (tensors, containers, numbers, strings) and additionally allows the two numpy types that the FB2 CPU trainer
stored (numpy scalars inside its random-generator state). A file that needs any other type is refused, with PyTorch's
message naming that type; nothing from the file has run at that point.

Checked on 2026-11-12: all 41 checkpoints of this job and the FB2 warm-start checkpoint load, with content equal to
what the unrestricted loader returns; a file that carries a command is refused and the command does not run
(h512/tools/test_ckpt_io.py).
"""


def load_checkpoint(path, torch):
    """Return the checkpoint at `path` on the CPU. Raises pickle.UnpicklingError for anything but plain data."""
    import numpy as np
    try:
        scalar = np._core.multiarray.scalar     # numpy 2.x
    except AttributeError:
        scalar = np.core.multiarray.scalar      # numpy 1.x
    # the same function under the module name each numpy generation writes into a pickle
    allowed = [np.dtype, (scalar, "numpy.core.multiarray.scalar"), (scalar, "numpy._core.multiarray.scalar")]
    # numpy 2 builds a scalar's dtype as an instance of a per-type class; plain number types only
    for kind in (np.float64, np.float32, np.int64, np.int32, np.uint64, np.uint32, np.bool_):
        allowed.append(type(np.dtype(kind)))
    with torch.serialization.safe_globals(allowed):
        return torch.load(path, map_location="cpu", weights_only=True)
