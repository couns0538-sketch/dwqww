"""CPU-only verification suite for FORGE V3P 5-Surface Placement (Wave 6, Stream A).

Covers:
  1. Surface 5 (`datagen_uci_parity_7_8_minimal.patch`): clean git apply & 7/8 parity logic.
  2. Surface 3 (`forge_train_v3p_loop_adapter.py`) & Surface 2 (`forge_v3p.py`):
     load_model(), atomic cmd_export(), round-trip checksum/eval parity, trainer template, --selftest.
  3. Surface 4a/4b patches (`v3_parity.py`, `v3_model_check.py`) + existing Surface 2 & 4 CPU tests.
  4. `train_v3p_stream.py --ob-reweight cc0`: --selftest, CLI flag, clamped CC0 LUT & Anchor Weight-Exemption Rule.
"""
from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HIP_VISIBLE_DEVICES"] = "-1"
os.environ["ROCR_VISIBLE_DEVICES"] = "-1"

import ast
import copy
import importlib.util
import shutil
import subprocess
import tempfile
import types
import zlib
from contextlib import contextmanager
from pathlib import Path

import chess
import numpy as np
import pytest
import torch

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon" / "forge_fixes"
PATCHES = FIX / "patches"
PIPELINE = LAB / "pipeline"
TMP_ROOT = Path(r"C:\Users\Administrator\.gemini\antigravity\scratch\teamwork_tmp\920a117f-2049-40eb-b207-171a3f51da0d")

EXPECTED_CC0_LUT = [1.50, 1.089, 1.167, 0.978, 0.922, 0.883, 0.891, 0.70]


@contextmanager
def scratch_subdir(prefix: str):
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    td = Path(tempfile.mkdtemp(prefix=prefix, dir=str(TMP_ROOT)))
    try:
        yield td
    finally:
        shutil.rmtree(td, ignore_errors=True)
        try:
            if TMP_ROOT.exists() and not any(TMP_ROOT.iterdir()):
                TMP_ROOT.rmdir()
        except OSError:
            pass


def cpu_subprocess_env(tmp_dir: Path, extra_pythonpath: list[Path] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["HIP_VISIBLE_DEVICES"] = "-1"
    env["ROCR_VISIBLE_DEVICES"] = "-1"
    env["TMP"] = str(tmp_dir)
    env["TEMP"] = str(tmp_dir)
    env["TMPDIR"] = str(tmp_dir)
    if extra_pythonpath:
        joined = os.pathsep.join(str(p) for p in extra_pythonpath)
        prev = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{joined}{os.pathsep}{prev}" if prev else joined
    return env


def test_cpu_only_guard_active():
    assert sys.dont_write_bytecode is True
    assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "-1"
    assert os.environ.get("ROCR_VISIBLE_DEVICES") == "-1"
    assert torch.cuda.device_count() == 0
    assert not torch.cuda.is_available()


# ---------------------------------------------------------------------------
# Area 1: Surface 5 (datagen_uci_parity_7_8_minimal.patch)
# ---------------------------------------------------------------------------

def test_datagen_parity_7_8_patch_apply_and_logic():
    patch_path = PATCHES / "datagen_uci_parity_7_8_minimal.patch"
    assert patch_path.exists()

    with scratch_subdir("w6_s5_") as td:
        nn_dir = td / "pipeline" / "nnloop"
        nn_dir.mkdir(parents=True)
        shutil.copy2(PIPELINE / "nnloop" / "__init__.py", nn_dir / "__init__.py")
        shutil.copy2(PIPELINE / "nnloop" / "common.py", nn_dir / "common.py")
        shutil.copy2(PIPELINE / "nnloop" / "engine.py", nn_dir / "engine.py")
        shutil.copy2(PIPELINE / "nnloop" / "datagen_uci.py", nn_dir / "datagen_uci.py")

        r_chk = subprocess.run(
            ["git", "-C", str(td), "apply", "--check", str(patch_path)],
            capture_output=True, text=True,
        )
        assert r_chk.returncode == 0, r_chk.stderr

        r_ap = subprocess.run(
            ["git", "-C", str(td), "apply", str(patch_path)],
            capture_output=True, text=True,
        )
        assert r_ap.returncode == 0, r_ap.stderr

        # Load patched module in an isolated namespace without touching C:\nnue-lab\pipeline
        pkg_name = "_w6_temp_nnloop"
        pkg_spec = importlib.util.spec_from_file_location(
            pkg_name, str(nn_dir / "__init__.py"),
            submodule_search_locations=[str(nn_dir)],
        )
        pkg_mod = importlib.util.module_from_spec(pkg_spec)
        sys.modules[pkg_name] = pkg_mod
        try:
            for sub in ("common", "engine", "datagen_uci"):
                sub_spec = importlib.util.spec_from_file_location(f"{pkg_name}.{sub}", str(nn_dir / f"{sub}.py"))
                sub_mod = importlib.util.module_from_spec(sub_spec)
                sys.modules[f"{pkg_name}.{sub}"] = sub_mod
                sub_spec.loader.exec_module(sub_mod)
            du = sys.modules[f"{pkg_name}.datagen_uci"]

            # 1. _random_count_for_game
            g_alt = {"random_move_count": 8, "random_move_count_alt": 7}
            assert du._random_count_for_game(g_alt, 0) == (8, True)
            assert du._random_count_for_game(g_alt, 1) == (7, True)
            assert du._random_count_for_game(g_alt, 2) == (8, True)
            assert du._random_count_for_game(g_alt, 3) == (7, True)
            assert du._random_count_for_game({"random_move_count": 8}, 1) == (8, False)
            assert du._random_count_for_game({"random_move_count": 8, "random_move_count_alt": -1}, 1) == (8, False)

            # 2. selfgame_ok validation
            base_cfg = {
                "datagen": {
                    "soft_nodes": 5000, "random_multi_pv": 0,
                    "random_move_min_ply": 0, "random_move_max_ply": 7,
                    "random_move_count": 8, "random_move_count_alt": 7,
                },
                "engine": {"score": {"unit": "raw", "multiplier": 1.0}},
            }
            assert du.selfgame_ok(base_cfg) == ""
            bad_cfg = {
                "datagen": dict(base_cfg["datagen"], random_move_count_alt=9),
                "engine": base_cfg["engine"],
            }
            assert "random_move_count_alt" in du.selfgame_ok(bad_cfg)

            # 3. play_game & play_game_sg exact alternating 8/7 parity + write_min_ply
            class DummyEngine:
                def __init__(self):
                    self.sent: list[str] = []
                    self.sg_queue: list[str] = []
                    self.pos_cmds: list[str] = []

                def new_game(self):
                    self.sent.append("ucinewgame")

                def search(self, pos_cmd: str, go_cmd: str, timeout: float = 60.0):
                    self.pos_cmds.append(pos_cmd)
                    b = chess.Board()
                    if " moves " in pos_cmd:
                        for u in pos_cmd.split(" moves ", 1)[1].split():
                            b.push_uci(u)
                    mv = next(iter(b.legal_moves))
                    return mv.uci(), ("cp", 15)

                def send(self, line: str):
                    self.sent.append(line)
                    if line.startswith("selfgame "):
                        toks = line.split()
                        wmp = int(toks[toks.index("writeminply") + 1])
                        mp = int(toks[toks.index("maxply") + 1])
                        pos_line = next(x for x in reversed(self.sent) if x.startswith("position "))
                        b = chess.Board()
                        if " moves " in pos_line:
                            for u in pos_line.split(" moves ", 1)[1].split():
                                b.push_uci(u)
                        bm = next(iter(b.legal_moves)).uci()
                        self.sg_queue = [
                            f"sg {wmp} 12 {bm} {b.fen()}",
                            f"sgend result 0 reason plylimit plies {mp} moves",
                        ]

                def _get(self, deadline: float) -> str:
                    return self.sg_queue.pop(0)

            import random
            g_play = {
                "random_move_min_ply": 0, "random_move_max_ply": 7,
                "random_move_count": 8, "random_move_count_alt": 7,
                "write_min_ply": 8, "nodes": 5000, "soft_nodes": 5000,
                "eval_limit": 2000, "max_ply": 10,
                "draw_adj_ply": 80, "draw_adj_score": 5, "draw_adj_count": 8,
            }
            conv = lambda v, _b: int(v)

            for gidx, expected_first_ply in ((0, 8), (1, 7)):
                eng = DummyEngine()
                txt, nrec, _res, _plies = du.play_game(eng, random.Random(100 + gidx), g_play, conv, None, game_idx=gidx)
                assert nrec > 0
                plies_recorded = [int(ln.split()[1]) for ln in txt.splitlines() if ln.startswith("ply ")]
                assert plies_recorded[0] == expected_first_ply
                first_moves = eng.pos_cmds[0].split(" moves ", 1)[1].split()
                assert len(first_moves) == expected_first_ply

                eng_sg = DummyEngine()
                txt_sg, nrec_sg, _res_sg, _plies_sg = du.play_game_sg(eng_sg, random.Random(100 + gidx), g_play, None, game_idx=gidx)
                assert nrec_sg == 1
                pos_sent = next(x for x in eng_sg.sent if x.startswith("position "))
                assert len(pos_sent.split(" moves ", 1)[1].split()) == expected_first_ply
                sg_cmd = next(x for x in eng_sg.sent if x.startswith("selfgame "))
                assert f"writeminply {expected_first_ply} " in sg_cmd
                assert f"ply {expected_first_ply}\n" in txt_sg

            # Explicit write_min_ply != random_move_count must remain preserved
            g_custom = dict(g_play, write_min_ply=9, max_ply=11)
            eng_c = DummyEngine()
            txt_c, nrec_c, _, _ = du.play_game(eng_c, random.Random(5), g_custom, conv, None, game_idx=1)
            assert nrec_c > 0
            plies_c = [int(ln.split()[1]) for ln in txt_c.splitlines() if ln.startswith("ply ")]
            assert plies_c[0] == 9
        finally:
            for k in list(sys.modules):
                if k == pkg_name or k.startswith(pkg_name + "."):
                    sys.modules.pop(k, None)


# ---------------------------------------------------------------------------
# Area 2: Surface 3 (forge_train_v3p_loop_adapter.py) & Surface 2 (forge_v3p.py)
# ---------------------------------------------------------------------------

def test_loop_adapter_load_export_checksum_and_trainer_template():
    if str(PIPELINE) not in sys.path:
        sys.path.insert(0, str(PIPELINE))
    if str(FIX) not in sys.path:
        sys.path.insert(0, str(FIX))

    import forge_v3p
    import train_v3p as tv3p
    import forge_train_v3p_loop_adapter as adapter

    with scratch_subdir("w6_s3_") as td:
        torch.manual_seed(17)
        m = tv3p.ForgeNetV3P(hidden=128, king_buckets=8, out_buckets=8, mirror=True, pairwise=True, has_psqt=True)
        with torch.no_grad():
            m.w1.normal_(0.0, 0.05)
            m.b1.normal_(0.0, 0.05)
            m.out.weight.normal_(0.0, 0.1)
            m.out.bias.normal_(0.0, 0.05)
            m.psqt_w.normal_(0.0, 0.05)
        m.project()

        pt_path = td / "cand.pt"
        fnn3_path = td / "cand.fnn3"
        tv3p.save_model_p(m, pt_path)

        # load_model() contract
        m_loaded = adapter.load_model(pt_path)
        assert (m_loaded.hidden, m_loaded.king_buckets, m_loaded.out_buckets) == (128, 8, 8)
        assert m_loaded.pairwise is True and m_loaded.has_psqt is True
        for k, v in m.state_dict().items():
            assert torch.equal(v, m_loaded.state_dict()[k])

        # cmd_export() atomic .part -> os.replace + zero .part leftovers + checksum/reference parity
        rc = adapter.cmd_export(pt_path, fnn3_path)
        assert rc == 0
        assert fnn3_path.exists()
        assert not list(td.glob("*.part*"))

        net_rt = forge_v3p.read_net(str(fnn3_path))
        net_mem = tv3p.to_file_net_p(m_loaded)
        assert net_rt.hidden == 128 and net_rt.king_buckets == 8 and net_rt.output_buckets == 8
        assert net_rt.pairwise is True and net_rt.has_psqt is True

        codes = np.zeros(64, dtype=np.uint8)
        codes[4] = 6; codes[60] = 12; codes[12] = 1; codes[52] = 7; codes[3] = 5; codes[59] = 11
        ev_rt = forge_v3p.reference_eval(net_rt, codes, True)
        ev_mem = forge_v3p.reference_eval(net_mem, codes, True)
        assert ev_rt == ev_mem

        # Color-flip symmetry check
        flipped = np.zeros(64, dtype=np.uint8)
        for sq in range(64):
            c = codes[sq]
            if c:
                flipped[sq ^ 56] = (c + 6) if c <= 6 else (c - 6)
        assert forge_v3p.reference_eval(net_rt, flipped, False) == ev_rt

        # nnloop/trainer.py CLI template formatting without KeyError
        fields = {
            "datasets": '"a.plain" "b.plain"',
            "val": str(td / "val.plain"),
            "init": "",
            "init_net": "",
            "out_dir": str(td),
            "epochs": 40,
            "lr": 0.0005,
            "batch_size": 8192,
            "net": str(fnn3_path),
            "model": str(pt_path),
            "python": sys.executable,
        }
        train_tpl = (
            '"{python}" C:/nnue-lab/pipeline/forge_train_v3p.py train '
            '--datasets {datasets} --val "{val}" --out-model "{model}" '
            '--hce-exe C:/nnue-lab/forge/build/hce_dump.exe --epochs {epochs} '
            '--lr {lr} --batch-size {batch_size} --lr-cycles auto --w1-decay 0.3 '
            '--ob-smooth 2e-6 --mix 0.75 --distill-net C:/nnue-lab/runs/forge/r0067/train/cand.pt '
            '--distill-weight 0.2 --anchor-shards a.fqs.z b.fqs.z --anchor-repeat 25 --hidden 1024'
        )
        export_tpl = '"{python}" C:/nnue-lab/pipeline/forge_train_v3p.py export --model "{model}" --net "{net}"'
        assert "forge_train_v3p.py train" in train_tpl.format(**fields)
        assert "forge_train_v3p.py export" in export_tpl.format(**fields)

        # Subprocess --selftest
        r_st = subprocess.run(
            [sys.executable, "-B", str(FIX / "forge_train_v3p_loop_adapter.py"), "--selftest"],
            env=cpu_subprocess_env(td), capture_output=True, text=True,
        )
        assert r_st.returncode == 0, r_st.stdout + r_st.stderr
        assert "LOOP_ADAPTER_V3P_SELFTEST_PASS" in r_st.stdout


# ---------------------------------------------------------------------------
# Area 3: Surface 4a/4b patches + Existing Surface 2 & 4 CPU scripts
# ---------------------------------------------------------------------------

def test_surface4_patches_apply_and_model_check_cpu_dispatch():
    p4a = PATCHES / "v3p_surface4a_v3_parity.patch"
    p4b = PATCHES / "v3p_surface4b_v3_model_check.patch"
    assert p4a.exists() and p4b.exists()

    with scratch_subdir("w6_s4_") as td:
        tools_dir = td / "pipeline" / "tools"
        tools_dir.mkdir(parents=True)
        shutil.copy2(PIPELINE / "tools" / "v3_parity.py", tools_dir / "v3_parity.py")
        shutil.copy2(PIPELINE / "tools" / "v3_model_check.py", tools_dir / "v3_model_check.py")

        for pf in (p4a, p4b):
            r_chk = subprocess.run(
                ["git", "-C", str(td), "apply", "--check", str(pf)],
                capture_output=True, text=True,
            )
            assert r_chk.returncode == 0, f"{pf.name} check failed: {r_chk.stderr}"
            r_ap = subprocess.run(
                ["git", "-C", str(td), "apply", str(pf)],
                capture_output=True, text=True,
            )
            assert r_ap.returncode == 0, f"{pf.name} apply failed: {r_ap.stderr}"

        parity_src = (tools_dir / "v3_parity.py").read_text(encoding="utf-8")
        mc_src = (tools_dir / "v3_model_check.py").read_text(encoding="utf-8")
        compile(parity_src, str(tools_dir / "v3_parity.py"), "exec")
        compile(mc_src, str(tools_dir / "v3_model_check.py"), "exec")

        # Create a real arch='v3p' CPU checkpoint and exported .fnn3 in td
        if str(PIPELINE) not in sys.path:
            sys.path.insert(0, str(PIPELINE))
        if str(FIX) not in sys.path:
            sys.path.insert(0, str(FIX))
        import forge_v3p
        import train_v3p as tv3p

        pt_path = td / "v3p_cand.pt"
        fnn3_path = td / "v3p_cand.fnn3"
        m = tv3p.ForgeNetV3P(hidden=128, king_buckets=8, out_buckets=8, mirror=True, pairwise=True, has_psqt=True)
        tv3p.save_model_p(m, pt_path)
        forge_v3p.write_net(str(fnn3_path), tv3p.to_file_net_p(m))

        # Case A: patched v3_model_check with v3p=None invokes mc.main() on CPU and raises explicit RuntimeError at L44
        r_no_v3p = subprocess.run(
            [
                sys.executable, "-B", "-c",
                (
                    "import importlib.util, sys, torch; "
                    "sys.modules['forge_train_v3p'] = None; "
                    f"spec = importlib.util.spec_from_file_location('mc', r'{tools_dir / 'v3_model_check.py'}'); "
                    "mc = importlib.util.module_from_spec(spec); spec.loader.exec_module(mc); "
                    "assert mc.v3p is None; "
                    "_cpu = torch.device('cpu'); torch.device = lambda *_a, **_kw: _cpu; "
                    f"sys.argv = ['v3_model_check.py', r'{pt_path}', r'{fnn3_path}', 'unused.exe', '2']; "
                    "mc.main()"
                ),
            ],
            env=cpu_subprocess_env(td), capture_output=True, text=True,
        )
        assert r_no_v3p.returncode != 0
        assert "v3_model_check.py" in r_no_v3p.stderr and "in main" in r_no_v3p.stderr
        assert "RuntimeError: FORGENN3-P checkpoint requires pipeline/forge_train_v3p.py" in r_no_v3p.stderr

        # Case B: patched v3_model_check with staged forge_train_v3p + forge_v3p executes mc.main() on CPU up to Triton boundary
        stage = td / "stage"
        stage.mkdir()
        shutil.copy2(FIX / "forge_v3p.py", stage / "forge_v3p.py")
        shutil.copy2(FIX / "forge_train_v3p_loop_adapter.py", stage / "forge_train_v3p.py")
        shutil.copy2(FIX / "train_v3p.py", stage / "train_v3p.py")

        r_with_v3p = subprocess.run(
            [
                sys.executable, "-B", "-c",
                (
                    "import importlib.util, sys, traceback, torch\n"
                    f"spec = importlib.util.spec_from_file_location('mc', r'{tools_dir / 'v3_model_check.py'}')\n"
                    "mc = importlib.util.module_from_spec(spec); spec.loader.exec_module(mc)\n"
                    "assert mc.v3p is not None and mc.forge_v3.__name__ == 'forge_v3p'\n"
                    "_cpu = torch.device('cpu'); torch.device = lambda *_a, **_kw: _cpu\n"
                    "orig_load = mc.v3p.load_model; orig_read = mc.forge_v3.read_net; called = []\n"
                    "def spy_load(p):\n"
                    "    mdl = orig_load(p)\n"
                    "    called.append(('load_model', p, mdl.hidden, mdl.pairwise, mdl.has_psqt))\n"
                    "    return mdl\n"
                    "def spy_read(p):\n"
                    "    net = orig_read(p)\n"
                    "    called.append(('read_net', p, net.hidden, net.pairwise, net.has_psqt))\n"
                    "    return net\n"
                    "mc.v3p.load_model = spy_load; mc.forge_v3.read_net = spy_read\n"
                    f"sys.argv = ['v3_model_check.py', r'{pt_path}', r'{fnn3_path}', 'unused.exe', '2']\n"
                    "tb = ''\n"
                    "try:\n"
                    "    mc.main()\n"
                    "except RuntimeError:\n"
                    "    tb = traceback.format_exc()\n"
                    f"assert called == [('load_model', r'{pt_path}', 128, True, True), ('read_net', r'{fnn3_path}', 128, True, True)], called\n"
                    "assert 'v3_model_check.py' in tb and 'in main' in tb and 'model(codes, stm' in tb, tb\n"
                    "assert 'SparseRowsRaw' in tb and '0 active drivers' in tb, tb\n"
                    "print('MODELCHECK_V3P_CPU_DISPATCH_OK')\n"
                ),
            ],
            env=cpu_subprocess_env(td, extra_pythonpath=[stage]), capture_output=True, text=True,
        )
        assert r_with_v3p.returncode == 0, r_with_v3p.stdout + r_with_v3p.stderr
        assert "MODELCHECK_V3P_CPU_DISPATCH_OK" in r_with_v3p.stdout


def test_existing_surface2_and_surface4_scripts_cpu():
    with scratch_subdir("w6_s2_s4_scripts_") as td:
        env = cpu_subprocess_env(td)

        r_s2 = subprocess.run(
            [sys.executable, "-B", str(FIX / "test_v3p_surface2_format.py")],
            env=env, capture_output=True, text=True,
        )
        assert r_s2.returncode == 0, r_s2.stdout + r_s2.stderr
        assert "SURFACE_2_FAIL_BEFORE_PASS_AFTER_OK" in r_s2.stdout

        r_s4 = subprocess.run(
            [sys.executable, "-B", str(FIX / "test_v3p_surface4_parity_and_modelcheck.py")],
            env=env, capture_output=True, text=True,
        )
        assert r_s4.returncode == 0, r_s4.stdout + r_s4.stderr
        assert "SURFACE_4A_FAIL_BEFORE_PASS_AFTER_OK" in r_s4.stdout


# ---------------------------------------------------------------------------
# Area 4: train_v3p_stream.py --ob-reweight cc0 & Anchor Weight-Exemption Rule
# ---------------------------------------------------------------------------

def test_train_v3p_stream_selftest_and_cc0_ob_reweight_anchor_exemption():
    stream_path = FIX / "train_v3p_stream.py"
    assert stream_path.exists()

    with scratch_subdir("w6_stream_") as td:
        env = cpu_subprocess_env(td)

        # 1. Subprocess --selftest
        r_st = subprocess.run(
            [sys.executable, "-B", str(stream_path), "--selftest"],
            env=env, capture_output=True, text=True,
        )
        assert r_st.returncode == 0, r_st.stdout + r_st.stderr
        assert "STREAM_V3P_SELFTEST_PASS" in r_st.stdout

        # 2. CLI --ob-reweight cc0 acceptance via --help
        r_help = subprocess.run(
            [sys.executable, "-B", str(stream_path), "--help"],
            env=env, capture_output=True, text=True,
        )
        assert r_help.returncode == 0
        assert "--ob-reweight" in r_help.stdout and "cc0" in r_help.stdout

        # 3. Extract exact weight block (ast.If) from train_v3p_stream.py:main(), assert AST invariants, and exec on CPU
        src_text = stream_path.read_text(encoding="utf-8")
        tree = ast.parse(src_text)
        main_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")

        # Defense-in-depth: verify --ob-reweight choices=['none', 'm4', 'cc0'] in main() AST
        ob_choices = None
        for node in ast.walk(main_fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
                if any(isinstance(a, ast.Constant) and a.value == "--ob-reweight" for a in node.args):
                    for kw in node.keywords:
                        if kw.arg == "choices":
                            ob_choices = ast.literal_eval(kw.value)
        assert ob_choices == ["none", "m4", "cc0"], f"Unexpected --ob-reweight choices: {ob_choices}"

        matches = [
            n for n in ast.walk(main_fn)
            if isinstance(n, ast.If)
            and any(isinstance(x, ast.Attribute) and x.attr == "use_shard_weights" for x in ast.walk(n.test))
            and any(isinstance(x, ast.Attribute) and x.attr == "ob_reweight" for x in ast.walk(n.test))
        ]
        assert len(matches) == 1, f"Expected unique weight ast.If in main(), got {len(matches)}"
        w_if = matches[0]

        found_lut = None
        for node in ast.walk(w_if):
            if isinstance(node, ast.IfExp):
                if isinstance(node.orelse, ast.List) and len(node.orelse.elts) == 8:
                    vals = [ast.literal_eval(e) for e in node.orelse.elts]
                    if vals[0] == 1.50 and vals[-1] == 0.70:
                        found_lut = vals
                        break
        assert found_lut == EXPECTED_CC0_LUT, f"Unexpected CC0 LUT in AST: {found_lut}"

        aug_matches = [
            n for n in ast.walk(w_if)
            if isinstance(n, ast.AugAssign)
            and isinstance(n.op, ast.Div)
            and isinstance(n.target, ast.Subscript)
            and isinstance(n.target.value, ast.Name) and n.target.value.id == "w_g"
            and isinstance(n.target.slice, ast.Slice)
            and n.target.slice.lower is None
            and isinstance(n.target.slice.upper, ast.Name) and n.target.slice.upper.id == "n_main"
            and n.target.slice.step is None
            and isinstance(n.value, ast.Name) and n.value.id == "mw"
        ]
        assert len(aug_matches) == 1, "Missing w_g[:n_main] /= mw in extracted weight block"

        last_stmt = w_if.body[-1]
        assert (
            isinstance(last_stmt, ast.Assign)
            and len(last_stmt.targets) == 1
            and isinstance(last_stmt.targets[0], ast.Subscript)
            and isinstance(last_stmt.targets[0].value, ast.Name) and last_stmt.targets[0].value.id == "w_g"
            and isinstance(last_stmt.targets[0].slice, ast.Slice)
            and isinstance(last_stmt.targets[0].slice.lower, ast.Name) and last_stmt.targets[0].slice.lower.id == "n_main"
            and last_stmt.targets[0].slice.upper is None
            and last_stmt.targets[0].slice.step is None
            and ast.literal_eval(last_stmt.value) == 1.0
        ), "Missing final w_g[n_main:] = 1.0 Anchor Weight-Exemption Rule in extracted weight block"

        if str(FIX) not in sys.path:
            sys.path.insert(0, str(FIX))
        import train_v3p_stream as stream_mod

        codes = np.zeros(64, dtype=np.uint8)
        codes[4] = 6; codes[60] = 12; codes[3] = 5; codes[51] = 7
        pk = (codes[0::2] | (codes[1::2] << 4)).astype(np.uint8)

        # Build 2 main shards covering all 8 OB indices (bits 4..6 of flags) + adversarial weight_u8
        sdir = td / "shards"
        sdir.mkdir()
        adv_w0 = [0, 64, 128, 192, 255, 128, 128, 128]
        main_rows_per_shard = 8
        for s_idx in range(2):
            arr = np.zeros(main_rows_per_shard, dtype=stream_mod.FQS_DTYPE)
            for ob in range(8):
                arr[ob]["packed"] = pk
                arr[ob]["stm"] = (s_idx + ob) & 1
                arr[ob]["score16"] = 50 * (ob - 3)
                arr[ob]["res8"] = 0
                arr[ob]["flags"] = ob << 4  # bits 4..6 = OB index, in_check bit (2) = 0
                arr[ob]["weight_u8"] = adv_w0[ob] if s_idx == 0 else 128
            (sdir / f"main_{s_idx}.fqs.z").write_bytes(
                zlib.compress(stream_mod.FQS_MAGIC + arr.tobytes(), level=1)
            )

        # Anchor shard with extreme flags (OB=7/0 and mask_bits=0x03) and adversarial weight_u8 (250 / 0)
        anc_path = td / "anc.fqs.z"
        anc_in = np.zeros(4, dtype=stream_mod.FQS_DTYPE)
        for i, ob_val in enumerate((7, 0, 7, 0)):
            anc_in[i]["packed"] = pk
            anc_in[i]["stm"] = i & 1
            anc_in[i]["score16"] = 0
            anc_in[i]["res8"] = 1 if i < 2 else 0
            anc_in[i]["flags"] = (ob_val << 4) | 0x03
            anc_in[i]["weight_u8"] = 250 if i % 2 == 0 else 0
        anc_path.write_bytes(zlib.compress(stream_mod.FQS_MAGIC + anc_in.tobytes(), level=1))

        anc_arr = stream_mod.read_fqs_filtered(anc_path, 0)
        cat, n_main = stream_mod.load_superbatch_cpu(
            sorted(sdir.glob("*.fqs.z")), mask_bits=2, anc_arr=anc_arr,
        )
        n_sb = len(cat)
        assert n_main == 16 and len(anc_arr) == 4 and n_sb == 20

        dev = torch.device("cpu")
        w_mod = ast.Module(body=[copy.deepcopy(w_if)], type_ignores=[])
        ast.fix_missing_locations(w_mod)
        w_code = compile(w_mod, str(stream_path), "exec")

        mean_cc0_lut = sum(EXPECTED_CC0_LUT) / 8.0
        for use_shard_w, ob_rew in ((False, "cc0"), (True, "cc0"), (False, "none")):
            ns = {
                "args": types.SimpleNamespace(use_shard_weights=use_shard_w, ob_reweight=ob_rew),
                "n_sb": n_sb,
                "n_main": n_main,
                "dev": dev,
                "cat": cat,
                "torch": torch,
                "np": np,
                "w_g": None,
            }
            exec(w_code, ns)
            w_g = ns["w_g"]

            if ob_rew == "none" and not use_shard_w:
                assert w_g is None
            else:
                assert w_g is not None and w_g.shape == (n_sb,)
                assert float(w_g[:n_main].mean().item()) == pytest.approx(1.0, abs=1e-6)
                assert torch.all(w_g[n_main:] == 1.0), f"Anchors not strictly 1.0: {w_g[n_main:]}"
                if not use_shard_w:
                    for ob in range(8):
                        assert float(w_g[ob].item()) * mean_cc0_lut == pytest.approx(EXPECTED_CC0_LUT[ob], abs=1e-6)
                    assert float(w_g[0].item()) * mean_cc0_lut == pytest.approx(1.50, abs=1e-6)
                    assert float(w_g[7].item()) * mean_cc0_lut == pytest.approx(0.70, abs=1e-6)
                else:
                    assert float(w_g[0].item()) == 0.0
                    assert float(w_g[4].item()) > float(w_g[5].item())
