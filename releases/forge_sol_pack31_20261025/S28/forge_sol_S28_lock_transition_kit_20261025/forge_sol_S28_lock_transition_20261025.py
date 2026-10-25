#!/usr/bin/env python3
"""Isolated, observational lock-transition qualification; dry run unless --execute."""
from __future__ import annotations
import argparse
import base64
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

DATE = '20261025'
DEPTHS = (11, 13, 16, 20, 22)
NETS = {
    '74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b': {
        'label': 'current_h256_e12', 'refs': [308972, 745494, 2460422, 11901452, 31111774]},
    '0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661': {
        'label': 'candidate_e48f006_not_adopted', 'refs': [328459, 945640, 3024381, 9162399, 20421972]},
}
PIN_SHA = 'd64465edb75a69e517e153f394e570766a4debcfedcb5417376bf94cb0c097c6'
ROOT_FILES = ('CMakeLists.txt', 'README.md', 'IDEA_SOURCE.md')
ROOT_DIRS = ('src', 'include', 'tests', 'bench', 'tools')
KIWIPETE = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
OLD_FAILS = ['FAIL: WAC 001 expected g3g6 got f6h5',
             'FAIL: WAC 001 score 661 below 31997',
             'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def dump(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def raw(data):
    return {'encoding': 'base64', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'data': base64.b64encode(data).decode('ascii')}


def within(path, root):
    return path == root or root in path.parents


def regular(path, label):
    p = Path(path).absolute()
    if p.is_symlink() or any(a.is_symlink() for a in p.parents):
        raise ValueError(label + ' has a symlink component')
    if not p.is_file():
        raise ValueError(label + ' is not a regular file')
    return p.resolve()


def input_files(tree):
    files = []
    for name in ROOT_FILES + ROOT_DIRS:
        p = tree / name
        if not p.exists():
            if name in ('README.md', 'IDEA_SOURCE.md'):
                continue
            raise ValueError('missing build input ' + name)
        if p.is_symlink():
            raise ValueError('symlink build input ' + name)
        if p.is_file():
            files.append(p)
        else:
            for child in sorted(p.rglob('*')):
                if child.is_symlink():
                    raise ValueError('symlink build input ' + str(child))
                if child.is_file():
                    files.append(child)
    return sorted(files)


def snapshot(paths):
    return {str(p): sha(p) for p in sorted(set(paths))}


def validate_patch(patch):
    data = patch.read_bytes()
    headers = 0
    for line in data.splitlines():
        if line.startswith((b'--- ', b'+++ ')):
            token = line[4:].split(b'\t', 1)[0].split(b' ', 1)[0]
            if token == b'/dev/null':
                continue
            name = token.decode('utf-8', 'strict')
            parts = Path(name).parts
            if len(parts) < 2 or parts[0] not in ('a', 'b') or '..' in parts or Path(name).is_absolute():
                raise ValueError('unsafe patch path')
            headers += 1
    if not headers:
        raise ValueError('patch has no supported unified paths')


def queue_rows(path):
    if path is None:
        return []
    rows = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(rows, dict):
        rows = rows['items']
    if not isinstance(rows, list):
        raise ValueError('queue must be a list or items list')
    ids = {'base'}
    result = []
    for row in rows:
        row = dict(row)
        name = row['id']
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,39}', name) or name in ids:
            raise ValueError('invalid or duplicate queue id')
        ids.add(name)
        if not isinstance(row['option'], str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9 ]{0,79}', row['option']):
            raise ValueError('invalid option name')
        if type(row['value']) is not int or row['value'] == 0:
            raise ValueError('ON value must be a nonzero integer')
        row['path'] = str(regular(row.get('path', row.get('patch')), 'queue patch'))
        for field, hashfield in (('path', 'sha256'), ('repair_path', 'repair_sha256')):
            if field not in row:
                continue
            p = regular(row[field], field)
            expected = row[hashfield]
            if not re.fullmatch(r'[0-9a-f]{64}', expected) or sha(p) != expected:
                raise ValueError('patch SHA mismatch for ' + name + ' ' + field)
            validate_patch(p)
            row[field] = str(p)
        row['time_only'] = bool(row.get('time_only', False))
        result.append(row)
    return result


def bench_count(data, depth):
    values = re.findall(rb'^info string bench depth (\d+) nodes (\d+) time \d+ nps \d+\r?$', data, re.M)
    if len(values) != 1 or int(values[0][0]) != depth:
        raise ValueError('missing, duplicated, or wrong-depth bench summary')
    return int(values[0][1])


def perft_count(data):
    values = re.findall(rb'^nodes (\d+)\r?$', data, re.M)
    if len(values) != 1:
        raise ValueError('missing or duplicated perft total')
    return int(values[0])


def active_option(data, name, value):
    text = data.decode('utf-8', 'strict').replace('\r\n', '\n')
    matches = re.findall(r'^option name ' + re.escape(name) + r' type spin default (-?\d+) min (-?\d+) max (-?\d+)$', text, re.M)
    if len(matches) != 1:
        raise ValueError('requested ON option is not advertised exactly once: ' + name)
    default, low, high = map(int, matches[0])
    if default != 0 or not low <= value <= high or value == default:
        raise ValueError('unexpected option default/range or inactive ON value')
    return {'name': name, 'default': default, 'minimum': low, 'maximum': high, 'requested': value,
            'control_verified': 'advertised spin option and value in range; source patch hash retained'}


def fma_count(data):
    return len(re.findall(rb'^\s*[0-9a-f]+:\s+vf(?:n)?m(?:add|sub)[a-z0-9]*\b', data, re.M | re.I))


class Runner:
    def __init__(self, out):
        self.out = out
        self.number = 0
        self.env = dict(os.environ)
        tmp = out / ('forge_sol_S28_tmp_' + DATE)
        tmp.mkdir()
        self.env.update(TMPDIR=str(tmp), TMP=str(tmp), TEMP=str(tmp), PYTHONDONTWRITEBYTECODE='1')

    def run(self, label, argv, cwd, data=None, allowed=(0,)):
        self.number += 1
        p = subprocess.run([str(x) for x in argv], cwd=cwd, input=data, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, env=self.env, check=False)
        receipt = {'argv': [str(x) for x in argv], 'cwd': str(cwd), 'exit': p.returncode,
                   'stdin': raw(data or b''), 'stdout': raw(p.stdout), 'stderr': raw(p.stderr),
                   'stream_capture_complete': True, 'child_waited': True}
        name = f'forge_sol_S28_raw_{self.number:04d}_{label}_{DATE}.json'
        dump(self.out / name, receipt)
        if p.returncode not in allowed:
            raise RuntimeError(label + ' exit ' + str(p.returncode) + '; see ' + name)
        return p, name


def copy_tree(tree, dest, net):
    dest.mkdir()
    for name in ROOT_FILES:
        p = tree / name
        if p.is_file():
            shutil.copyfile(p, dest / name)
    for name in ROOT_DIRS:
        shutil.copytree(tree / name, dest / name)
    shutil.copyfile(net, dest / 'src/nnue_weights.inc')


def append_metadata(dest, netsha, label):
    section = (f'\n\n## S28 observational transition {DATE}\n\n'
               f'Copied input for {label}; network SHA256 {netsha}. '
               'This output is a qualification record and does not adopt a new lock.\n'
               'Idea source: supplied S28 transition specification and local source inspection only.\n')
    receipt = {}
    for name in ('README.md', 'IDEA_SOURCE.md'):
        p = dest / name
        before = p.read_bytes() if p.exists() else b''
        with p.open('ab') as f:
            f.write(section.encode())
        after = p.read_bytes()
        if not after.startswith(before):
            raise RuntimeError('metadata prefix changed')
        receipt[name] = {'old_bytes': len(before), 'old_sha256': hashlib.sha256(before).hexdigest(),
                         'appended_bytes': len(after) - len(before), 'prefix_preserved': True}
    return receipt


def known_failures(data, netsha, pins):
    lines = [line for line in data.decode('utf-8', 'strict').splitlines() if line.startswith('FAIL:')]
    if len(lines) != 4:
        raise ValueError('expected exactly four original forge_tests FAIL lines')
    if netsha == next(iter(NETS)):
        if Counter(lines) != Counter(OLD_FAILS + [OLD_FAILS[2]]):
            raise ValueError('current-net original failure pins changed')
    else:
        cases = {c['case']: c for c in pins['cases']}
        wac = cases['WAC001']
        required = ['FAIL: WAC 001 expected g3g6 got ' + wac['bestmove'],
                    f"FAIL: WAC 001 score {wac['score']} below 31997", OLD_FAILS[2], OLD_FAILS[2]]
        if wac['bestmove'] != 'f6h5' or wac['score_kind'] != 'cp' or Counter(lines) != Counter(required):
            raise ValueError('candidate FAIL lines do not match independently observed pins')
        for label in ('promotion_white', 'promotion_black'):
            case = cases[label]
            if case['depth'] != 1 or case['score_kind'] != 'cp' or case['score'] <= 100:
                raise ValueError('unexpected promotion known-failure class')
    return {'exact_fail_lines': lines, 'counts': dict(Counter(lines)), 'status': 'OBSERVED_KNOWN_ONLY',
            'scope': 'this exact source, binary and net; no expected test values modified'}


def pin_signature(pins):
    keys = ('case', 'depth', 'bestmove', 'score_kind', 'score', 'pv')
    return sorted(({key: row[key] for key in keys} for row in pins['cases']), key=lambda row: row['case'])


def require_base_pins(base, queued):
    if queued['pin_signature'] != base['pin_signature']:
        raise ValueError('queued OFF pins differ from the independent base OFF pins')
    if Counter(queued['known_fail_lines']) != Counter(base['known_fail_lines']):
        raise ValueError('queued OFF exact FAIL lines differ from the base allowlist')
    queued['base_off_pin_equality'] = True


def stage_summary(stage):
    return {'id': stage['id'],
            'off': {str(row['depth']): row['nodes'] for row in stage['off']},
            'on': ({str(row['depth']): row['nodes'] for row in stage['on']} if stage['on'] is not None else None),
            'perft': {row['position']: row['nodes'] for row in stage['perft']},
            'fma': {row['scope']: row['count'] for row in stage['fma']},
            'pc_precheck_depth': stage.get('pc_precheck_depth')}


def qualify(runner, args, src, build, row, netsha, refs):
    tag = row['id'] if row else 'base'
    exposure = 'ON' if row else 'OFF'
    flags = '-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
    runner.run(tag + '_configure', [args.cmake, '-S', src, '-B', build, '-DCMAKE_BUILD_TYPE=Release',
                                  '-DCMAKE_CXX_FLAGS=' + flags, '-DFORGE_EXPOSE_TUNABLES=' + exposure], src)
    runner.run(tag + '_build', [args.cmake, '--build', build, '--parallel', args.jobs], src)
    exe = build / 'forge'
    # This must remain the first invocation of each new engine.
    p, log = runner.run(tag + '_first_d11', [exe], src, b'bench 11\nquit\n')
    count = bench_count(p.stdout, 11)
    if count != refs[0]:
        raise ValueError('first OFF d11 mismatch; native work stops before later tests')
    result = {'id': tag, 'engine': str(exe), 'engine_sha256': sha(exe), 'first_d11': count,
              'first_invocation_raw': log, 'FORGE_EXPOSE_TUNABLES': exposure, 'off': [], 'on': None}
    for depth, expected in zip(DEPTHS, refs):
        commands = f'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench {depth}\nquit\n'
        p, rawname = runner.run(tag + '_off_d' + str(depth), [exe], src, commands.encode())
        actual = bench_count(p.stdout, depth)
        result['off'].append({'depth': depth, 'nodes': actual, 'expected': expected, 'raw': rawname})
        if actual != expected:
            raise ValueError(tag + ' OFF bench mismatch at depth ' + str(depth))
    result['perft'] = []
    for label, position, expected in [('startpos', 'startpos', 4865609), ('kiwipete', 'fen ' + KIWIPETE, 193690690)]:
        p, rawname = runner.run(tag + '_perft_' + label, [exe], src, ('position ' + position + '\ngo perft 5\nquit\n').encode())
        actual = perft_count(p.stdout)
        result['perft'].append({'position': label, 'nodes': actual, 'expected': expected, 'raw': rawname})
        if actual != expected:
            raise ValueError(label + ' perft mismatch')
    result['fma'] = []
    for label, binary in [('engine', exe), ('nnue_object', build / 'CMakeFiles/forge_core.dir/src/nnue.cpp.o')]:
        p, rawname = runner.run(tag + '_fma_' + label, [args.objdump, '-d', '-C', '--no-show-raw-insn', binary], src)
        count = fma_count(p.stdout)
        result['fma'].append({'scope': label, 'file_sha256': sha(binary), 'count': count, 'raw': rawname})
        if count:
            raise ValueError('FMA instructions present')
    if args.fma_checker:
        p, rawname = runner.run(tag + '_supplied_fma', [sys.executable, '-B', args.fma_checker, exe], src)
        result['supplied_fma_checker'] = {'path': args.fma_checker, 'sha256': sha(args.fma_checker), 'raw': rawname,
                                          'scope': 'supplied checker; independent full-engine and NNUE-object counts above'}
    if row:
        p, rawname = runner.run(tag + '_option_advertisement', [exe], src, b'uci\nquit\n')
        result['on_control'] = active_option(p.stdout, row['option'], row['value'])
        result['on_control']['raw'] = rawname
        result['on'] = []
        for depth in DEPTHS:
            commands = (f'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\n'
                        f"setoption name {row['option']} value {row['value']}\nbench {depth}\nquit\n")
            p, rawname = runner.run(tag + '_on_d' + str(depth), [exe], src, commands.encode())
            result['on'].append({'depth': depth, 'nodes': bench_count(p.stdout, depth), 'raw': rawname})
        result['pc_precheck_depth'] = next((a['depth'] for a, b in zip(result['off'], result['on']) if a['nodes'] != b['nodes']), None)
        result['time_only'] = row['time_only']
        if row['time_only'] and result['pc_precheck_depth'] is not None:
            raise ValueError('time-only patch changed a fixed-depth bench')
    pinout = runner.out / f'forge_sol_S28_{tag}_pins_{DATE}'
    runner.run(tag + '_rerecord_pins', [sys.executable, '-B', args.pin_helper, exe, '--out', pinout, '--timeout', '300'], src)
    pins = json.loads((pinout / 'forge_sol_S01_pin_results_20261025.json').read_text())
    if pins['status'] != 'PASS' or any(c.get('status') != 'OBSERVED' or c.get('exit') != 0 or
                                     c.get('unclosed_pid') is not None or not c.get('stream_capture_complete') for c in pins['cases']):
        raise ValueError('pin capture did not close cleanly')
    p, rawname = runner.run(tag + '_forge_tests', [build / 'forge_tests'], src, allowed=(0, 1))
    allow = known_failures(p.stdout + p.stderr, netsha, pins)
    allow.update(net_sha256=netsha, engine_sha256=sha(exe), source_sha256=snapshot(input_files(src)),
                 independent_pin_results=str(pinout / 'forge_sol_S01_pin_results_20261025.json'), original_tests_raw=rawname)
    dump(runner.out / f'forge_sol_S28_{tag}_known_fail_allowlist_{DATE}.json', allow)
    result['known_fail_lines'] = allow['exact_fail_lines']
    result['pin_signature'] = pin_signature(pins)
    p, rawname = runner.run(tag + '_ctest', [args.ctest, '--test-dir', build, '--output-on-failure', '--parallel', '1'], src, allowed=(0, 8))
    text = (p.stdout + p.stderr).decode('utf-8', 'replace')
    failing = re.findall(r'^\s*\d+\s+-\s+(\S+)\s+\(Failed\)\s*$', text, re.M)
    ctest_fail_lines = [line for line in text.splitlines() if line.startswith('FAIL:')]
    if p.returncode != 8 or failing != ['forge_tests']:
        raise ValueError('CTest failure set differs from the single original forge_tests target')
    if Counter(ctest_fail_lines) != Counter(allow['exact_fail_lines']):
        raise ValueError('actual CTest FAIL lines differ from the independently observed exact allowlist')
    if re.search(r'ERROR: (?:AddressSanitizer|UndefinedBehaviorSanitizer)|runtime error:|SUMMARY: .*Sanitizer', text):
        raise ValueError('sanitizer diagnostic found in actual CTest output')
    result['ctest'] = {'raw': rawname, 'exit': p.returncode, 'failed_targets': failing, 'exact_fail_lines': ctest_fail_lines,
                        'policy': 'only original forge_tests known-four failure target permitted'}
    result['status'] = 'PASS_OBSERVATIONAL_NOT_ADOPTED'
    return result


def apply_queue(runner, src, row):
    argv = ['patch', '--batch', '--forward', '-p1', '-F0', '--reject-file=-', '--input', row['path']]
    p, log = runner.run(row['id'] + '_original_F0_dryrun', argv + ['--dry-run'], src, allowed=(0, 1))
    receipt = {'original_sha256': row['sha256'], 'original_dryrun_exit': p.returncode, 'original_dryrun_raw': log,
               'used_repair': False}
    chosen = row['path']
    if p.returncode:
        if 'repair_path' not in row:
            raise ValueError('original patch fails -F0 and no independently supplied repair exists')
        chosen = row['repair_path']
        argv[-1] = chosen
        p, log = runner.run(row['id'] + '_repair_F0_dryrun', argv + ['--dry-run'], src)
        receipt.update(used_repair=True, repair_sha256=row['repair_sha256'], repair_dryrun_exit=p.returncode, repair_dryrun_raw=log)
    p, log = runner.run(row['id'] + '_chosen_F0_apply', argv, src)
    receipt.update(applied_path=chosen, applied_sha256=sha(chosen), apply_exit=p.returncode, apply_raw=log)
    return receipt


def seal(out):
    # Both generation and verification occur with the output directory as cwd.
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file())
    manifest = out / f'forge_sol_S28_SHA256SUMS_{DATE}.txt'
    p = subprocess.run(['sha256sum', '--', *files], cwd=out, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if p.returncode:
        raise RuntimeError('SHA256SUMS generation failed')
    manifest.write_bytes(p.stdout)
    p = subprocess.run(['sha256sum', '-c', manifest.name], cwd=out, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if p.returncode:
        raise RuntimeError('inside-output SHA256SUMS verification failed')
    return {'path': str(manifest), 'sha256': sha(manifest), 'checked_files': len(files),
            'check_exit': 0, 'verification_stdout_sha256': hashlib.sha256(p.stdout).hexdigest()}


def arguments(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tree', required=True)
    p.add_argument('--net', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--queue')
    p.add_argument('--pin-helper', required=True)
    p.add_argument('--net-sha256')
    p.add_argument('--cmake', default='cmake')
    p.add_argument('--ctest', default='ctest')
    p.add_argument('--objdump', default='objdump')
    p.add_argument('--fma-checker')
    p.add_argument('--jobs', type=int, choices=(1, 2), default=2)
    return p.parse_args(argv)


def run(args):
    tree = Path(args.tree).absolute()
    if tree.is_symlink() or any(a.is_symlink() for a in tree.parents) or not tree.is_dir():
        raise ValueError('tree must be an existing nonsymlink directory')
    tree = tree.resolve()
    sources = input_files(tree)
    net = regular(args.net, 'net')
    netsha = sha(net)
    if netsha not in NETS or (args.net_sha256 and args.net_sha256 != netsha):
        raise ValueError('unsupported net or net SHA mismatch; never infer refs from a new binary')
    helper = regular(args.pin_helper, 'pin helper')
    if sha(helper) != PIN_SHA:
        raise ValueError('pin helper SHA mismatch')
    args.pin_helper = str(helper)
    queue = regular(args.queue, 'queue manifest') if args.queue else None
    rows = queue_rows(queue)
    external = [net, helper, Path(__file__).resolve()]
    if queue:
        external.append(queue)
    if args.fma_checker:
        checker = regular(args.fma_checker, 'FMA checker')
        args.fma_checker = str(checker)
        external.append(checker)
    for row in rows:
        external.extend(Path(row[k]) for k in ('path', 'repair_path') if k in row)
    out0 = Path(args.out).absolute()
    if os.path.lexists(out0) or not out0.parent.is_dir() or any(a.is_symlink() for a in out0.parents):
        raise ValueError('output must be NEW with an existing nonsymlink parent')
    out = out0.resolve()
    if within(out, tree) or within(tree, out) or any(within(p, out) for p in external):
        raise ValueError('output overlaps an input')
    if any(c == 'baseline' or c.startswith('dist-') for c in out.parts):
        raise ValueError('output may not be a baseline or dist directory')
    before = snapshot(sources + external)
    out.mkdir()
    plan = {'mode': 'execute' if args.execute else 'dry-run', 'tree': str(tree), 'net': str(net),
            'net_sha256': netsha, 'oracle': NETS[netsha], 'queue': rows,
            'source_snapshot': before, 'tool_sha256': sha(__file__),
            'policy': 'observational new-output-only; candidate lock not adopted; no speed or Elo claim'}
    dump(out / f'forge_sol_S28_plan_{DATE}.json', plan)
    runner = None
    result = {'status': 'DRY_RUN', 'oracle': NETS[netsha], 'stages': []}
    try:
        if args.execute:
            runner = Runner(out)
            for row in [None] + rows:
                tag = row['id'] if row else 'base'
                src = out / f'forge_sol_S28_{tag}_source_{DATE}'
                build = out / f'forge_sol_S28_{tag}_build_{DATE}'
                copy_tree(tree, src, net)
                patch_receipt = apply_queue(runner, src, row) if row else None
                metadata = append_metadata(src, netsha, tag)
                stage = qualify(runner, args, src, build, row, netsha, NETS[netsha]['refs'])
                stage.update(metadata=metadata, patch=patch_receipt)
                if row:
                    require_base_pins(result['stages'][0], stage)
                result['stages'].append(stage)
                dump(out / f'forge_sol_S28_{tag}_stage_results_{DATE}.json', stage)
            result['status'] = 'PASS_OBSERVATIONAL_NOT_ADOPTED'
    except Exception as exc:
        result.update(status='FAIL', error=type(exc).__name__ + ': ' + str(exc))
    after = snapshot(sources + external)
    result['input_immutability'] = {'equal': before == after, 'before': before, 'after': after}
    if before != after:
        result.update(status='FAIL', error='input files changed')
    dump(out / f'forge_sol_S28_results_{DATE}.json', result)
    sealed = seal(out)
    print(json.dumps({'status': result['status'], 'out': str(out), 'manifest': sealed,
                      'stage_summaries': [stage_summary(stage) for stage in result['stages']]}, sort_keys=True))
    return 0 if result['status'] != 'FAIL' else 1


if __name__ == '__main__':
    try:
        sys.exit(run(arguments()))
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(2)
