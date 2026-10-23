import argparse
import hashlib
import importlib
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import chess
import chess.engine
import forge_selfplay as sp
import convert_training as conv
import train_nnue as tr
import torch
import numpy as np


def rows(count):
    board, rng = chess.Board(), random.Random(41)
    result = []
    for _ in range(count):
        board.push(rng.choice(list(board.legal_moves)))
        result.append((board.fen(en_passant="fen"), 20, 1.0))
    return result


class RulesTests(unittest.TestCase):
    def test_filter(self):
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        self.assertEqual(sp.eligible_score(board, move, chess.engine.Cp(-3000)), -3000)
        self.assertIsNone(sp.eligible_score(board, move, chess.engine.Cp(3001)))
        self.assertIsNone(sp.eligible_score(board, move, chess.engine.Mate(3)))
        self.assertIsNone(sp.eligible_score(board, move, chess.engine.Mate(-3)))
        board = chess.Board("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        self.assertIsNone(sp.eligible_score(board, chess.Move.from_uci("a7a8q"), chess.engine.Cp(50)))
        board = chess.Board()
        for uci in ["e2e4", "d7d5"]:
            board.push_uci(uci)
        self.assertIsNone(sp.eligible_score(board, chess.Move.from_uci("e4d5"), chess.engine.Cp(50)))
        board = chess.Board("4k3/8/8/8/8/8/4r3/4K2R w K - 0 1")
        self.assertTrue(board.is_check())
        self.assertIsNone(sp.eligible_score(board, next(iter(board.legal_moves)), chess.engine.Cp(10)))

    def test_result_rules(self):
        board = chess.Board()
        for uci in ["f2f3", "e7e5", "g2g4", "d8h4"]:
            board.push_uci(uci)
        self.assertEqual(sp.terminal_result(board, 300), 0.0)
        self.assertEqual(sp.terminal_result(chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"), 300), 0.5)
        self.assertEqual(sp.terminal_result(chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1"), 300), 0.5)
        self.assertEqual(sp.terminal_result(chess.Board("4k3/8/8/8/8/8/8/R3K3 w - - 100 60"), 300), 0.5)
        board = chess.Board()
        for uci in ["g1f3", "g8f6", "f3g1", "f6g8"] * 2:
            board.push_uci(uci)
        self.assertEqual(sp.terminal_result(board, 300), 0.5)
        self.assertEqual(sp.terminal_result(chess.Board(), 0), 0.5)

    def test_adjudication_tracks_winner_and_mates(self):
        class Engine:
            def __init__(self, white=False, alternating=False, mates=False):
                self.white, self.alternating, self.mates = white, alternating, mates
            def play(self, board, *args, **kwargs):
                value = 2200 if self.alternating or board.turn == self.white else -2200
                score = chess.engine.Mate(2 if value > 0 else -2) if self.mates else chess.engine.Cp(value)
                return chess.engine.PlayResult(next(iter(board.legal_moves)), None,
                                              {"score": chess.engine.PovScore(score, board.turn)})
        args = argparse.Namespace(opening_plies=0, max_ply=10, nodes=5000, depth=None,
                                  adjudicate_cp=2000, adjudicate_plies=4, max_score=3000)
        stop = mock.Mock()
        stop.is_set.return_value = False
        for color in [chess.WHITE, chess.BLACK]:
            records, result = sp.play_game(Engine(white=color), args, random.Random(1), stop)
            self.assertEqual(result, 1.0 if color else 0.0)
            self.assertEqual(len(records), 4)
        records, result = sp.play_game(Engine(alternating=True), args, random.Random(1), stop)
        self.assertEqual(result, 0.5)
        records, result = sp.play_game(Engine(white=True, mates=True), args, random.Random(1), stop)
        self.assertEqual((records, result), ([], 1.0))

    def test_windows_process_settings(self):
        process = mock.Mock(pid=99)
        process.cpu_affinity.return_value = [12, 13, 14, 15]
        process.nice.return_value = 64
        with mock.patch.object(sp, "WINDOWS", True), mock.patch.object(sp.psutil, "IDLE_PRIORITY_CLASS", 64, create=True):
            sp.constrain_process(process, [12, 13, 14, 15])
        process.cpu_affinity.assert_any_call([12, 13, 14, 15])
        process.nice.assert_any_call(64)


class StoreTests(unittest.TestCase):
    def test_rotation_global_dedup_resume_and_md5(self):
        with tempfile.TemporaryDirectory() as directory:
            data = rows(5)
            store = sp.OutputStore(directory, 2)
            self.assertEqual(store.append(data + [data[0]]), 5)
            store.close()
            paths = sorted(Path(directory).glob("*.txt"))
            self.assertEqual([len(p.read_text().splitlines()) for p in paths], [2, 2, 1])
            original = {p.name: p.read_bytes() for p in paths}
            for path in paths:
                self.assertEqual(path.with_suffix(".txt.md5").read_text().split()[0],
                                 hashlib.md5(path.read_bytes()).hexdigest())
            store = sp.OutputStore(directory, 2)
            self.assertEqual(store.next_number, 4)
            changed_counter = data[0][0].rsplit(" ", 2)[0] + " 88 99"
            self.assertEqual(store.append([(changed_counter, -800, 0.0)]), 0)
            self.assertEqual(store.append(rows(6)), 1)
            store.close()
            self.assertTrue((Path(directory) / "forge_selfplay_004.txt").exists())
            for name, content in original.items():
                self.assertEqual((Path(directory) / name).read_bytes(), content)

    def test_import_existing_and_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            row = rows(1)[0]
            path = Path(directory) / "forge_selfplay_017.txt"
            path.write_text(f"{row[0]} | {row[1]} | {row[2]:.1f}\n")
            store = sp.OutputStore(directory, 3)
            self.assertEqual(store.append([row]), 0)
            with self.assertRaises(RuntimeError):
                sp.OutputStore(directory)
            store.close()
            self.assertTrue(path.with_suffix(".txt.md5").exists())

    def test_crash_tail_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            code = """import os,sys,chess
from forge_selfplay import OutputStore
s=OutputStore(sys.argv[1],100)
s.append([(chess.Board().fen(),25,.5)])
s.file.write(b'partial broken line');s.file.flush();os.fsync(s.file.fileno())
os._exit(0)
"""
            env = dict(os.environ, PYTHONPATH=str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""))
            subprocess.run([sys.executable, "-c", code, directory], env=env, check=True)
            store = sp.OutputStore(directory)
            self.assertEqual(store.next_number, 2)
            self.assertEqual(store.append([(chess.Board().fen(), 25, .5)]), 0)
            store.close()
            path = Path(directory) / "forge_selfplay_001.txt"
            self.assertNotIn(b"partial", path.read_bytes())
            self.assertTrue(path.with_suffix(".txt.md5").exists())


class ConversionTests(unittest.TestCase):
    def test_plain_pov_and_scale(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.plain"
            board = chess.Board()
            board.push_uci("e2e4")
            path.write_text(f"fen {chess.STARTING_FEN}\nmove e2e4\nscore 208\nply 0\nresult 1\ne\n"
                            f"fen {board.fen()}\nmove e7e5\nscore -208\nply 1\nresult -1\ne\n")
            data = list(conv.plain_records(path, 100 / 208))
            self.assertEqual([(x[1], x[2]) for x in data], [(100, 1.0), (-100, 1.0)])
            path.write_text("fen " + chess.STARTING_FEN + "\n")
            with self.assertRaises(ValueError):
                list(conv.plain_records(path))


class TrainingTests(unittest.TestCase):
    def test_select_discrete_directml_gpu(self):
        directml = mock.Mock()
        directml.device_count.return_value = 2
        directml.device_name.side_effect = lambda i: ["AMD Radeon Graphics", "AMD Radeon RX 7900 XT"][i]
        directml.device.return_value = "directml-device-1"
        with mock.patch.dict(sys.modules, {"torch_directml": directml}):
            self.assertEqual(tr.device_for("directml", None), "directml-device-1")
        directml.device.assert_called_once_with(1)

    def test_features_and_label_pov(self):
        board = chess.Board()
        indices = tr.feature_indices(board)
        self.assertIn(0 * 64 + chess.E2, indices[0])
        self.assertIn(6 * 64 + chess.E7, indices[0])
        self.assertIn(0 * 64 + (chess.E7 ^ 56), indices[1])
        self.assertEqual(len(indices[0]), 32)
        board.push_uci("e2e4")
        _, target = tr.parse_sample(f"{board.fen()} | 0 | 1.0", 0.0, 2.25)
        self.assertEqual(target, 0.0)
        _, target = tr.parse_sample(f"{board.fen()} | 0 | 0.0", 0.0, 2.25)
        self.assertEqual(target, 1.0)

    def test_sharding_and_disjoint_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.txt"
            data = rows(100)
            path.write_text("".join(f"{fen} | {i} | {result}\n" for i, (fen, _, result) in enumerate(data)))
            files = [(str(path), path.stat().st_size)]
            total = []
            for worker in range(3):
                dataset = tr.TextPositions(files, False, 0, 1, 2.25, 0, 2)
                with mock.patch.object(tr, "get_worker_info", return_value=argparse.Namespace(id=worker,num_workers=3)):
                    total.extend(list(dataset))
            self.assertEqual(len(total), 100)
            targets = [sample[1] for sample in total]
            self.assertEqual(len(set(targets)), 100)
            train = list(tr.TextPositions(files, False, .2, 1, 2.25, 7, 5))
            val = list(tr.TextPositions(files, True, .2, 1, 2.25, 0, 5))
            self.assertEqual(len(train) + len(val), 100)
            self.assertFalse({x[1] for x in train} & {x[1] for x in val})

    def test_export_layout_and_cpp_inference(self):
        torch.manual_seed(1)
        model = tr.NNUE([256], qat=True)
        samples = [tr.parse_sample(f"{fen} | {cp} | {z}", .75, 2.25) for fen, cp, z in rows(30)]
        x, _ = tr.collate(samples)
        x = torch.from_numpy(x)
        with tempfile.TemporaryDirectory() as directory:
            stem = Path(directory) / "net"
            metadata = tr.export_forge(model, stem, 2.25)
            self.assertEqual(metadata["raw_float32_bytes"], (768 * 256 + 256 + 512 + 1) * 4)
            raw = np.fromfile(stem.with_suffix(".bin"), dtype="<f4")
            self.assertTrue(np.array_equal(raw[:768 * 256], model.ft.weight.detach().t().numpy().ravel()))
            code = r'''#include <algorithm>
#include <iostream>
#include <vector>
namespace forge::nnue { constexpr int InputCount=768, HiddenSize=256;
constexpr float SigmoidK=2.25F,WeightScale=4096,OutputScale=4096; }
#include "net.inc"
int main(){int n;while(std::cin>>n){float acc[2][256];for(auto &p:acc)for(int h=0;h<256;h++)p[h]=NnueB1[h]/4096.f;
for(int p=0;p<2;p++)for(int i=0;i<n;i++){int f;std::cin>>f;for(int h=0;h<256;h++)acc[p][h]+=NnueW1[f*256+h]/4096.f;}
float out=NnueB2/4096.f;for(int h=0;h<256;h++)for(int p=0;p<2;p++){float a=std::clamp(acc[p][h],0.f,1.f);out+=a*a*NnueW2[p*256+h]/4096.f;}
std::cout<<out*400/2.25<<"\n";}}
'''
            source = Path(directory) / "check.cpp"
            source.write_text(code)
            binary = Path(directory) / "check"
            subprocess.run(["g++", "-std=c++17", "-O2", str(source), "-o", str(binary)], check=True)
            lines = []
            for (perspectives, _) in samples:
                lines.append(str(len(perspectives[0])) + " " + " ".join(map(str, perspectives[0] + perspectives[1])))
            completed = subprocess.run([str(binary)], input="\n".join(lines), text=True, capture_output=True, check=True)
            cpp = np.array(list(map(float, completed.stdout.split())))
            python = model(x).detach().numpy().ravel() * 400 / 2.25
            self.assertLess(np.max(np.abs(cpp - python)), .01)


if __name__ == "__main__":
    unittest.main(verbosity=2)
