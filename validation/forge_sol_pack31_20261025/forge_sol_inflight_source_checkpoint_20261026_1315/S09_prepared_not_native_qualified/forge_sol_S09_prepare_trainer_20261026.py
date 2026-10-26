"""Prepare a new trainer source and canonical diff; never execute training."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path


def prepare(base):
    text = base.read_text()
    if hashlib.sha256(base.read_bytes()).hexdigest() != '5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f':
        raise ValueError('source trainer hash differs from supplied v3b')
    def replace(old, new):
        nonlocal text
        if text.count(old) != 1: raise ValueError('expected one source anchor: ' + old[:80])
        text = text.replace(old, new)
    replace('Model/export are the same Forge net (768 -> H per perspective, SCReLU, 2H -> 1, int16 QAT, scale 4096).',
            'S09: optional 8 piece-count output heads on the preserved step-1 contract; buckets=1 keeps the original forward/export math.\nModel/export use 768 -> H per perspective, SCReLU, 2H -> buckets, existing int16 storage/QAT, scale 4096; inference stays float.')
    replace('def __init__(self, hidden, qat=True, residual=True):', 'def __init__(self, hidden, qat=True, residual=True, buckets=1):')
    replace('        self.hidden, self.qat, self.residual = hidden, qat, residual\n',
            '        self.hidden, self.qat, self.residual = hidden, qat, residual\n        if type(buckets) is not int or buckets not in (1, 8):\n            raise ValueError("output buckets must be 1 or 8")\n        self.buckets = buckets\n')
    replace('        self.out = nn.Linear(2 * hidden, 1)', '        self.out = nn.Linear(2 * hidden, buckets)')
    old = '        out = F.linear(torch.cat([hs, ho], 1), self.q(self.out.weight), self.q(self.out.bias)).squeeze(1)'
    replace(old, '        if self.buckets == 1:\n    ' + old + '\n        else:\n            logits = F.linear(torch.cat([hs, ho], 1), self.q(self.out.weight), self.q(self.out.bias))\n            pieces = (codes > 0).sum(dim=1)  # includes both kings\n            head = torch.clamp(torch.div(pieces - 1, 4, rounding_mode="floor"), 0, 7).long()\n            out = logits.gather(1, head.unsqueeze(1)).squeeze(1)')
    replace('    hidden = model.hidden\n', '    hidden = model.hidden\n    buckets = getattr(model, "buckets", 1)\n    if type(buckets) is not int or buckets not in (1, 8):\n        raise ValueError("output buckets must be 1 or 8")\n')
    replace('    quant = []\n', '    if arrays[0].size != 768 * hidden or arrays[1].size != hidden or arrays[2].size != buckets * 2 * hidden or arrays[3].size != buckets:\n        raise ValueError("NNUE export shape does not match hidden/buckets")\n    quant = []\n')
    replace('    for name, v in zip(("NnueW1", "NnueB1", "NnueW2"), quant[:3]):',
            '    if buckets == 8:\n        lines.insert(3, "#define FORGE_NNUE_OUTPUT_HEADS 8")\n    for name, v in zip(("NnueW1", "NnueB1", "NnueW2"), quant[:3]):')
    replace('    lines.append(f"static const std::int16_t NnueB2 = {int(quant[3][0])};")',
            '    if buckets == 1:\n        lines.append(f"static const std::int16_t NnueB2 = {int(quant[3][0])};")\n    else:\n        lines.append("static const std::int16_t NnueB2[8] = {")\n        lines.append("  " + ", ".join(map(str, quant[3])) + ",")\n        lines.append("};")')
    replace('    ap.add_argument("--shape", type=int, default=128,', '    ap.add_argument("--shape", type=int, default=256,')
    replace('    ap.add_argument("--residual", action="store_true")',
            '    ap.add_argument("--residual", action="store_true", default=True)\n    ap.add_argument("--standalone", dest="residual", action="store_false")\n    ap.add_argument("--buckets", type=int, choices=[1, 8], default=1)')
    replace('    ap.add_argument("--epochs", type=int, default=8)', '    ap.add_argument("--epochs", type=int, default=48)')
    replace('    ap.add_argument("--batch-size", type=int, default=4096)', '    ap.add_argument("--batch-size", type=int, default=8192)')
    replace('    ap.add_argument("--lr", type=float, default=1e-3)', '    ap.add_argument("--lr", type=float, default=7.07e-4)')
    replace('    ap.add_argument("--seed", type=int, default=1)', '    ap.add_argument("--seed", type=int, default=25)')
    replace('    ap.add_argument("--final-full-val", action="store_true")', '    ap.add_argument("--final-full-val", action="store_true", default=True)')
    replace('residual=a.residual or a.baseline_only).to(dev)', 'residual=a.residual or a.baseline_only, buckets=a.buckets).to(dev)')
    replace('              "features": "forge768-relative-pieces-rank-flip",', '              "output_buckets": a.buckets,\n              "features": "forge768-relative-pieces-rank-flip",')
    return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('source', type=Path); args = parser.parse_args()
    out = Path(__file__).parent; original = args.source.read_text(); result = prepare(args.source)
    with (out / 'forge_sol_S09_train_resid_v3b_20261026.py').open('x') as stream: stream.write(result)
    patch = ''.join(difflib.unified_diff(original.splitlines(keepends=True), result.splitlines(keepends=True),
                                       fromfile='a/train_resid_v3b.py', tofile='b/train_resid_v3b.py'))
    with (out / 'forge_sol_S09_trainer_20261026.patch').open('x') as stream: stream.write(patch)
