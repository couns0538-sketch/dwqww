from pathlib import Path
import hashlib
import json
import sys
import numpy as np
sys.path.insert(0, '/workspace/dwqww/tools/nnue')
from include_parser import load_include

out = Path(__file__).parent
pilot = Path('/workspace/forge-nnue-handoff-20261023/pilot-fresh14895-zero20-attempt1/exports/epoch-0001')
def identity(p):
    data = p.read_bytes()
    return {'path': str(p), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
source_bin = Path(str(pilot) + '.bin').read_bytes()
roundtrip_bin = (out / 'roundtrip.bin').read_bytes()
source = load_include(Path(str(pilot) + '.inc'), expected_hidden=128)
roundtrip = load_include(out / 'roundtrip.inc', expected_hidden=128)
comparison = {}
for name in ('w1', 'b1', 'w2'):
    a, b = source[name], roundtrip[name]
    comparison[name] = {'shape': list(a.shape), 'elements': int(a.size),
                        'mismatches': int(np.count_nonzero(a != b)),
                        'exact': bool(np.array_equal(a, b))}
comparison['b2'] = {'elements': 1, 'exact': source['b2'] == roundtrip['b2'],
                    'mismatches': int(source['b2'] != roundtrip['b2'])}
result = {
    'status': 'passed' if source_bin == roundtrip_bin and all(x['exact'] for x in comparison.values()) and source['residual'] and roundtrip['residual'] else 'failed',
    'scope': 'Actual unchanged legacy C++ Network::load/save and write_include API methods via same-translation-unit wrapper; no training or optimizer calls',
    'float_binary': {'byte_exact': source_bin == roundtrip_bin, 'bytes': len(source_bin),
                     'float32_count': len(source_bin) // 4},
    'quantized_arrays': comparison,
    'quantized_total_elements': sum(x['elements'] for x in comparison.values()),
    'hidden_size': source['hidden'],
    'source_residual': source['residual'], 'roundtrip_residual': roundtrip['residual'],
    'outputs': [identity(out / 'roundtrip.bin'), identity(out / 'roundtrip.inc'), identity(out / 'loader_roundtrip')],
    'inputs_unchanged': json.loads((out / 'inputs-before.json').read_text()) == json.loads((out / 'inputs-after.json').read_text()),
    'original_cli_zero_epoch_export_supported': False,
    'production_engine_source_changed': False,
    'production_core_rebuilt': False,
    'optimizer_or_training_called': False,
    'native_search_or_elo_evidence': False,
}
(out / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
(out / 'REPORT.md').write_text(
    '# Legacy C++ loader API round-trip\n\n'
    + ('PASS' if result['status'] == 'passed' else 'FAIL')
    + ': the actual unchanged trainer source was included in an external C++20 wrapper. '
    'Its existing Network::load, Network::save and write_include methods were called directly; '
    'the original CLI main and all optimizer/training code were not invoked.\n\n'
    f'Float binary: {len(source_bin)} bytes, byte exact={result["float_binary"]["byte_exact"]}. '
    f'Quantized parameters: {result["quantized_total_elements"]} total; exact arrays={all(x["exact"] for x in comparison.values())}. '
    f'Hidden width: {source["hidden"]}; residual flags: {source["residual"]}/{roundtrip["residual"]}.\n\n'
    'Compiler/run commands, original stdout/stderr/exit codes, source/core/input identities and output hashes are retained here. '
    'The immutable core was linked without rebuilding it; all retained inputs were rehashed after execution. '
    'This verifies API format interoperability, not CLI zero-epoch export support, native evaluation parity, heldout loss or Elo. '
    'The separate legacy-loader-zero-epoch-inspection checkpoint remains valid.\n')
print(json.dumps({'status': result['status'], 'float_binary_byte_exact': result['float_binary']['byte_exact'],
                  'quantized_total_elements': result['quantized_total_elements'], 'array_mismatches': {k: v['mismatches'] for k,v in comparison.items()},
                  'inputs_unchanged': result['inputs_unchanged']}, indent=2))
if result['status'] != 'passed' or not result['inputs_unchanged']:
    raise SystemExit(1)
