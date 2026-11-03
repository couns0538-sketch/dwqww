#!/usr/bin/env python3
"""test_scope.py [--dll DLL] [--binpack FILE] - Opus R14-B item 1 (bug hunt #7, 2026-11-02): the fast loader must
refuse everything outside its proven scope with a clear message instead of giving batches that differ from the old
loader: a feature set other than K32H3, not exactly one binpack, DDP with more than one rank, filtered /
wld_filtered / simple-eval skipping, a skip config without a field or none at all, a missing DLL, a missing or
unreadable binpack, and (patch 0005) a FORGE_FAST_LOADER_DIR without forge_fastloader.py. One positive control: the
live npt line's settings on a real binpack give a batch. Standard library + the DLL only (no torch, no GPU runtime);
the torch Dataset class calls the same scope check first. One PASS / FAIL line per case; exit 0 = all PASS.
Damaged binpack files are fl_fuzz.py's job (bug hunt #4).
"""
import argparse
import importlib.util
import os
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # python -I does not add the script folder
sys.path.insert(0, os.path.join(HERE, "..", "fastloader"))
import forge_fastloader as ffl  # noqa: E402
from fl_equal import SkipCfg  # noqa: E402  (the npt line's skip settings: --no-filtered --no-wld-filtered)

FAILS = []


def case(name, fn, want_exc=None, text=""):
    """want_exc None = must not raise; else the exception type and a text its message must contain."""
    try:
        got = fn()
    except Exception as e:  # noqa: BLE001 - every exception is a verdict here
        ok = want_exc is not None and isinstance(e, want_exc) and text in str(e)
        print(f"{'PASS' if ok else 'FAIL'} {name}: {type(e).__name__}: {str(e)[:150]}")
        if not ok:
            FAILS.append(name)
        return None
    ok = want_exc is None
    print(f"{'PASS' if ok else 'FAIL'} {name}: no exception{'' if ok else f', wanted {want_exc.__name__}'}"
          f"{f' ({got})' if got is not None else ''}")
    if not ok:
        FAILS.append(name)
    return got


def skip(**changes):
    s = SkipCfg()
    for k, v in changes.items():
        setattr(s, k, v)
    return s


def first_batch(path, dll, cfg=None, cyclic=False):
    st = ffl.FastStream(path, 1024, threads=1, cyclic=cyclic, skip_config=cfg or SkipCfg(), window_entries=4096,
                        lib_path=dll)
    try:
        p = st.next_raw()
        if p is None:
            return "no batch (end of a finite stream)"
        size = p.contents.size
        st.release(p)
        return f"first batch of {size} positions"
    finally:
        st.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dll", default=r"D:\o14b\fl\b5_install\forge_fastloader.dll")
    ap.add_argument("--binpack", default=r"C:\o14b\fuzz_2052\base.binpack", help="a small valid unchained binpack")
    a = ap.parse_args()
    for f in (a.dll, a.binpack):
        if not os.path.isfile(f):
            ap.error(f"not found: {f}")
    print(f"DLL {ffl.library_info(a.dll)['sha256'][:16]}..., binpack {a.binpack}")

    # scope checked when the trainer's dataset is built (FastSparseBatchDataset.__init__ calls _check_scope first)
    one = [a.binpack]
    case("scope_feature_set_K32H3", lambda: ffl._check_scope("K32H3", one, None))
    case("scope_feature_set_bytes", lambda: ffl._check_scope(b"K32H3", one, None))
    case("scope_feature_set_other", lambda: ffl._check_scope("HalfKAv2_hm", one, None), ValueError,
         "supports feature set K32H3 only")
    # the trainer passes model.input_feature_name (INPUT_FEATURE_NAME): "K32H3" for the factorized K32H3^
    case("scope_feature_set_virtual", lambda: ffl._check_scope("K32H3^", one, None), ValueError,
         "supports feature set K32H3 only")
    case("scope_two_files", lambda: ffl._check_scope("K32H3", one * 2, None), ValueError, "exactly one binpack")
    case("scope_no_file", lambda: ffl._check_scope("K32H3", [], None), ValueError, "exactly one binpack")
    case("scope_ddp_one_rank", lambda: ffl._check_scope("K32H3", one, types.SimpleNamespace(world_size=1)))
    case("scope_ddp_two_ranks", lambda: ffl._check_scope("K32H3", one, types.SimpleNamespace(world_size=2)),
         ValueError, "does not support DDP")

    # skip settings checked when the stream starts (before the first batch)
    case("skip_live_line", lambda: ffl.make_config(1024, 1, True, SkipCfg()) and "accepted")
    for name, ch in (("filtered", {"filtered": True}), ("wld_filtered", {"wld_filtered": True}),
                     ("simple_eval", {"simple_eval_skipping": 1})):
        case(f"skip_{name}", lambda ch=ch: ffl.make_config(1024, 1, True, skip(**ch)), ValueError,
             "supports --no-filtered --no-wld-filtered without simple-eval skipping only")
    case("skip_none", lambda: ffl.make_config(1024, 1, True, None), ValueError, "a skip config is required")
    partial = types.SimpleNamespace(**{k: getattr(SkipCfg, k) for k in dir(SkipCfg) if not k.startswith("_")
                                       and k != "pc_y3"})
    case("skip_missing_field", lambda: ffl.make_config(1024, 1, True, partial), ValueError,
         "skip config has no field 'pc_y3'")
    case("stream_filtered_refused_before_reading", lambda: first_batch(a.binpack, a.dll, skip(filtered=True)),
         ValueError, "supports --no-filtered")

    # files and the DLL
    case("positive_control_live_settings", lambda: first_batch(a.binpack, a.dll))
    case("binpack_missing", lambda: first_batch(a.binpack + ".no_such_file", a.dll), RuntimeError, "fast loader:")
    with tempfile.TemporaryDirectory(prefix="ffl_scope_") as tmp:
        case("binpack_is_a_folder", lambda: first_batch(tmp, a.dll), RuntimeError, "fast loader:")
        missing_dll = os.path.join(tmp, "forge_fastloader.dll")
        case("dll_missing", lambda: ffl.load_library(missing_dll), OSError, "forge_fastloader.dll")
        # patch 0005: train.py loads forge_fastloader.py from FORGE_FAST_LOADER_DIR (or next to train.py)
        def load_from(d):
            spec = importlib.util.spec_from_file_location("forge_fastloader", os.path.join(d, "forge_fastloader.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return "loaded"
        case("loader_dir_without_py", lambda: load_from(tmp), FileNotFoundError, "forge_fastloader.py")
    print(f"test_scope: {'all PASS' if not FAILS else 'FAIL: ' + ', '.join(FAILS)}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
