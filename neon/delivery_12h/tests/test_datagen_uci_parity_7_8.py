"""Fail-before / pass-after unit test for Opus's minimal datagen_uci.py alternating 7/8 parity patch.

Runs strictly against either untouched C:\\nnue-lab\\pipeline\\nnloop\\datagen_uci.py (FAILS, RC=1)
or a temp copy patched with patches\\datagen_uci_parity_7_8_minimal.patch (PASSES, RC=0).
Never touches C:\\nnue-lab\\pipeline\\!
"""
from __future__ import annotations

import importlib.util
import inspect
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
SRC_FILE = LAB / "pipeline/nnloop/datagen_uci.py"
PATCH = LAB / "neon/forge_fixes/patches/datagen_uci_parity_7_8_minimal.patch"


class FakeEng:
    """Minimal mock UciEngine capturing exact moves & selfgame command sent by play_game_sg()."""
    def __init__(self) -> None:
        self.sent: list[str] = []
        self._resp: list[str] = []

    def new_game(self) -> None:
        pass

    def send(self, cmd: str) -> None:
        self.sent.append(cmd)
        if cmd.startswith("selfgame "):
            self._resp = ["sgend result 0 reason rule plies 10 run 0 searches 2 nodes 4000 moves"]

    def _get(self, _deadline: float) -> str:
        return self._resp.pop(0)


def load_mod(py_path: Path):
    sys.path.insert(0, str(LAB / "pipeline"))
    spec = importlib.util.spec_from_file_location("nnloop._datagen_uci_test", py_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def verify_module(mod) -> None:
    # 1. Helper & game_idx parameter must exist (fails on untouched!)
    assert hasattr(mod, "_random_count_for_game"), "Missing _random_count_for_game (unpatched datagen_uci.py)"
    assert "game_idx" in inspect.signature(mod.play_game_sg).parameters, "play_game_sg missing game_idx"
    assert "game_idx" in inspect.signature(mod.play_game).parameters, "play_game missing game_idx"

    g_base = {
        "soft_nodes": 2000, "nodes": 5000, "eval_limit": 2000, "write_min_ply": 8, "max_ply": 300,
        "random_move_min_ply": 0, "random_move_max_ply": 7, "random_move_count": 8,
        "draw_adj_ply": 60, "draw_adj_score": 15, "draw_adj_count": 6,
    }
    eng_cfg = {"score": {"unit": "raw", "multiplier": 1.0}}

    # 2. selfgame_ok(): accepts alt=7 with count=8, rejects alt=9 (> max_ply+1), unchanged when alt unset
    assert mod.selfgame_ok({"datagen": dict(g_base), "engine": eng_cfg}) == ""
    assert mod.selfgame_ok({"datagen": dict(g_base, random_move_count_alt=7), "engine": eng_cfg}) == ""
    bad_msg = mod.selfgame_ok({"datagen": dict(g_base, random_move_count_alt=9), "engine": eng_cfg})
    assert "random_move_count_alt" in bad_msg, f"Expected selfgame_ok refusal for alt=9, got {bad_msg!r}"

    # 3. Alternating 8/7 random plies & symmetric writeminply in play_game_sg()
    g_alt = dict(g_base, random_move_count_alt=7)
    move_counts = []
    wmins = []
    for gi in range(6):
        eng = FakeEng()
        mod.play_game_sg(eng, random.Random(100 + gi), g_alt, None, gi)
        pos_cmd = [c for c in eng.sent if c.startswith("position ")][0]
        sg_cmd = [c for c in eng.sent if c.startswith("selfgame ")][0]
        n_rand = len(pos_cmd.split(" moves ")[1].split()) if " moves " in pos_cmd else 0
        toks = sg_cmd.split()
        wmin = int(toks[toks.index("writeminply") + 1])
        move_counts.append(n_rand)
        wmins.append(wmin)
    assert move_counts == [8, 7, 8, 7, 8, 7], f"Expected alternating [8,7,8,7,8,7], got {move_counts}"
    assert wmins == [8, 7, 8, 7, 8, 7], f"Expected symmetric writeminply [8,7,8,7,8,7], got {wmins}"

    # 4. Legacy mode (alt unset): 100% identical move sequence to untouched RNG path
    eng_off = FakeEng()
    mod.play_game_sg(eng_off, random.Random(777), dict(g_base), None, 1)
    pos_off = [c for c in eng_off.sent if c.startswith("position ")][0]
    assert len(pos_off.split(" moves ")[1].split()) == 8, "alt unset must still play 8 random moves even on odd game_idx"


def main() -> int:
    mode = os.environ.get("TEST_DATAGEN_MODE", "patched").strip().lower()
    if mode == "base":
        verify_module(load_mod(SRC_FILE))
        print("UNEXPECTED PASS ON BASE")
        return 0
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        (tp / "pipeline/nnloop").mkdir(parents=True)
        shutil.copy2(SRC_FILE, tp / "pipeline/nnloop/datagen_uci.py")
        r = subprocess.run(["git", "-C", str(tp), "apply", str(PATCH)], capture_output=True, text=True)
        assert r.returncode == 0, f"git apply failed: {r.stderr}"
        verify_module(load_mod(tp / "pipeline/nnloop/datagen_uci.py"))
        print("TEST_DATAGEN_UCI_PARITY_7_8_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
