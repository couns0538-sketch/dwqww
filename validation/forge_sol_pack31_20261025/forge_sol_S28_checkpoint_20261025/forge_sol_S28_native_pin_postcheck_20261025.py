#!/usr/bin/env python3
"""Read closed v2 native evidence and apply the added base/OFF pin equality guard."""
from __future__ import annotations
import argparse
import base64
from collections import Counter
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
import sys
sys.dont_write_bytecode = True

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_raw(record):
    if record['encoding'] != 'base64':
        raise ValueError('unexpected raw encoding')
    data = base64.b64decode(record['data'], validate=True)
    if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('captured stream hash or byte count mismatch')
    return data


def check_manifest(out, expected_sha256=None):
    manifest = out / 'forge_sol_S28_SHA256SUMS_20261025.txt'
    actual = sha(manifest)
    if expected_sha256 is not None and actual != expected_sha256:
        raise ValueError('manifest differs from original captured closed-run manifest SHA')
    p = subprocess.run(['sha256sum', '-c', manifest.name], cwd=out, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=False)
    receipt = {'argv': ['sha256sum', '-c', manifest.name], 'cwd': str(out), 'exit': p.returncode,
               'manifest_sha256': actual, 'original_captured_manifest_sha256': expected_sha256,
               'stdout_bytes': len(p.stdout), 'stdout_sha256': hashlib.sha256(p.stdout).hexdigest(),
               'stdout_base64': base64.b64encode(p.stdout).decode('ascii'),
               'stderr_bytes': len(p.stderr), 'stderr_sha256': hashlib.sha256(p.stderr).hexdigest(),
               'stderr_base64': base64.b64encode(p.stderr).decode('ascii'),
               'child_waited': True, 'stream_capture_complete': True}
    if p.returncode:
        raise ValueError('closed output SHA256SUMS check failed before result/pin data trusted: ' + json.dumps(receipt))
    return receipt


def check_pin_capture(pins):
    expected = Counter(['WAC001', 'promotion_white', 'promotion_black'])
    if pins['status'] != 'PASS' or Counter(c['case'] for c in pins['cases']) != expected:
        raise ValueError('pin capture lacks exactly the three observed cases')
    if any(c.get('status') != 'OBSERVED' or c.get('exit') != 0 or c.get('unclosed_pid') is not None or
           c.get('stream_capture_complete') is not True for c in pins['cases']):
        raise ValueError('pin capture did not close with all exits zero and complete EOF')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('native_output', type=Path)
    args = ap.parse_args()
    tool = Path(__file__).resolve().with_name('forge_sol_S28_lock_transition_20261025.py')
    spec = importlib.util.spec_from_file_location('s28_final_tool', tool)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    controller_path = args.native_output / 'forge_sol_S28_native_controller_result_20261025.json'
    controller = json.loads(controller_path.read_text())
    if controller['status'] != 'PASS' or len(controller['runs']) != 4:
        raise ValueError('native controller is not closed PASS with four cases')
    checks = []
    manifest_checks = []
    for row in controller['runs']:
        if row['status'] != 'PASS' or row['exit'] != 0:
            raise ValueError('native case is not closed PASS')
        argv = row['argv']
        out = Path(argv[argv.index('--out') + 1])
        original_reply = json.loads(decode_raw(row['stdout']))
        manifest_checks.append(check_manifest(out, original_reply['manifest']['sha256']))
        plan = json.loads((out / 'forge_sol_S28_plan_20261025.json').read_text())
        result_path = out / 'forge_sol_S28_results_20261025.json'
        result = json.loads(result_path.read_text())
        if result['status'] != 'PASS_OBSERVATIONAL_NOT_ADOPTED' or not result['input_immutability']['equal']:
            raise ValueError('native result not closed PASS/immutable')
        stages = result['stages']
        expected_ids = ['base'] + [item['id'] for item in plan['queue']]
        if [stage['id'] for stage in stages] != expected_ids:
            raise ValueError('stage IDs differ from the frozen plan base plus complete queue')
        for stage in stages:
            pinpath = out / f"forge_sol_S28_{stage['id']}_pins_20261025" / 'forge_sol_S01_pin_results_20261025.json'
            pins = json.loads(pinpath.read_text())
            check_pin_capture(pins)
            stage['pin_signature'] = m.pin_signature(pins)
            if stage is not stages[0]:
                m.require_base_pins(stages[0], stage)
            checks.append({'case': row['case'], 'stage': stage['id'], 'status': 'PASS',
                           'pins_sha256': m.sha(pinpath), 'result_sha256': m.sha(result_path),
                           'signature': stage['pin_signature'],
                           'base_off_pin_equality': stage is stages[0] or stage['base_off_pin_equality']})
    print(json.dumps({'status': 'PASS', 'checks': checks, 'manifest_checks': manifest_checks, 'tool_sha256': m.sha(tool),
                      'controller_sha256': m.sha(controller_path),
                      'policy': 'read-only postvalidation of exact original closed v2 evidence; no native rerun'}, indent=2))
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(1)
