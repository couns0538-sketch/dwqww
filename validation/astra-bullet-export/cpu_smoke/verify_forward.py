#!/usr/bin/env python3
"""Replay every saved smoke row through PyTorch and the ordered export oracle."""
from pathlib import Path
import json
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/bullet'))
import train_lock_cpu_smoke as smoke
from forge_pos import PosReader, match_fen

run = Path(sys.argv[1]).resolve()
torch.set_num_threads(1)
state = torch.load(run / 'trained/state.pt', map_location='cpu', weights_only=True)
model = smoke.LockNet()
model.load_state_dict(state['state_dict'])
q = smoke.lock_export.load_quantized(run / 'trained/weights.bin', run / 'trained/manifest.json')
with PosReader(run / 'subset.pos', run / 'subset.hce') as reader:
    codes = np.zeros((len(reader), 64), dtype=np.int64)
    stm = np.zeros(len(reader), dtype=np.int64)
    fens = (run / 'subset.fen').read_text().splitlines()
    if len(fens) != len(reader):
        raise ValueError('subset FEN count mismatch')
    for index, row in enumerate(reader):
        match_fen(row, fens[index])
        board = np.frombuffer(row.board, dtype=np.uint8)
        codes[index, 0::2], codes[index, 1::2] = board & 15, board >> 4
        stm[index] = row.meta & 1
ours, theirs = smoke.dense_features(codes, stm)
bits = []
cp = []
with torch.no_grad():
    for start in range(0, len(codes), 128):
        value = model.residual(ours[start:start+128], theirs[start:start+128]).numpy()
        bits.extend(value.view(np.uint32).tolist())
        cp.extend(np.clip(value * np.float32(400) / np.float32(2.25), -30000, 30000).astype(np.int32).tolist())
bit_mismatches, cp_mismatches = [], []
for index, fen in enumerate(fens):
    expected_cp, expected_bits = smoke.lock_export.evaluate(q, fen)
    if bits[index] != expected_bits:
        bit_mismatches.append(index)
    if cp[index] != expected_cp:
        cp_mismatches.append(index)
receipt = {
    'status': 'PASS' if not bit_mismatches and not cp_mismatches else 'FAIL',
    'claim': 'Supplemental PyTorch CPU graph vs ordered lock export oracle; no native or Bullet execution claim.',
    'rows': len(fens), 'float32_output_bit_mismatches': bit_mismatches,
    'residual_cp_mismatches': cp_mismatches,
    'inputs': [smoke.artifact(run / name) for name in ('subset.pos', 'subset.fen', 'subset.hce',
               'trained/state.pt', 'trained/weights.bin', 'trained/manifest.json')],
    'implementation': [smoke.artifact(Path(__file__)), smoke.artifact(Path(smoke.__file__)),
                       smoke.artifact(Path(smoke.lock_export.__file__))],
}
smoke.write_json(run / 'forward_parity.json', receipt)
print(json.dumps({'status': receipt['status'], 'rows': len(fens),
                  'bit_mismatches': len(bit_mismatches), 'cp_mismatches': len(cp_mismatches)}))
raise SystemExit(int(receipt['status'] != 'PASS'))
