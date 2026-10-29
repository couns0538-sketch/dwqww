"""R6 planted-bug check: the RangerLite test must FAIL with the old kernel (plain tl.sqrt_rn)."""
import importlib.util
import os
import pathlib
import sys

clone = pathlib.Path("F:/opus_scratch/r6/nnue-pytorch-amd")
sys.path.insert(0, str(clone))
src = (clone / "model/optimizers/ranger_lite_triton.py").read_text(encoding="utf-8")
old = "    return tl.sqrt_rn(tl.where(x < _FLT_MIN, 0.0, x))"
assert src.count(old) == 1
mutant = src.replace(old, "    return tl.sqrt_rn(x)")
mpath = pathlib.Path(os.environ["TMP"]) / "ranger_lite_triton_mutant.py"
mpath.write_text(mutant, encoding="utf-8", newline="\n")
spec = importlib.util.spec_from_file_location("ranger_lite_triton_mutant", mpath)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

import model.optimizers.ranger_lite as rl  # noqa: E402

rl._rlt = mod
sys.argv = ["test"]
test = importlib.util.spec_from_file_location("t", clone / "tests/test_amd_triton_ranger.py")
t = importlib.util.module_from_spec(test)
test.loader.exec_module(t)
rc = t.main()
print("PLANTED BUG", "DETECTED (test failed as it should)" if rc != 0 else "NOT DETECTED")
sys.exit(0 if rc != 0 else 1)
