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
sys.dont_write_bytecode = True

DATE = '20261025'
DEPTHS = (11, 13, 16, 20, 22)
# Network oracles and helper digests are explicit checksum-bound inputs.
ROOT_FILES = ('CMakeLists.txt', 'README.md', 'IDEA_SOURCE.md')
ROOT_DIRS = ('src', 'include', 'tests', 'bench', 'tools')
KIWIPETE = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'


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
        value = Path(row.get('path', row.get('patch')))
        row['path'] = str(regular(value if value.is_absolute() else path.parent/value, 'queue patch'))
        for field, hashfield in (('path', 'sha256'), ('repair_path', 'repair_sha256')):
            if field not in row:
                continue
            value = Path(row[field])
            p = regular(value if value.is_absolute() else path.parent/value, field)
            expected = row[hashfield]
            if not re.fullmatch(r'[0-9a-f]{64}', expected) or sha(p) != expected:
                raise ValueError('patch SHA mismatch for ' + name + ' ' + field)
            validate_patch(p)
            row[field] = str(p)
        if 'time_only' in row and type(row['time_only']) is not bool:
            raise ValueError('time_only must be Boolean')
        row['time_only'] = row.get('time_only', False)
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


def checked_pin_cases(pins):
    if pins.get('status') not in ('PASS', 'RECORDED'):
        raise ValueError('pin observations are not closed PASS or RECORDED')
    rows = pins.get('cases')
    labels = ('WAC001', 'promotion_white', 'promotion_black')
    if not isinstance(rows, list) or len(rows) != 3 or Counter(c.get('case') for c in rows) != Counter(labels):
        raise ValueError('pin observations need exactly the three distinct cases')
    answer = {}
    for c in rows:
        depth = 12 if c['case'] == 'WAC001' else 1
        if c.get('status') != 'OBSERVED' or type(c.get('exit')) is not int or c['exit'] != 0 or c.get('unclosed_pid') is not None or c.get('stream_capture_complete') is not True:
            raise ValueError('pin case lacks zero exit and complete EOF')
        if type(c.get('depth')) is not int or c['depth'] != depth or c.get('requested_depth', depth) != depth or c.get('score_kind') != 'cp' or type(c.get('score')) is not int:
            raise ValueError('pin case depth or score kind changed')
        pv = c.get('pv')
        if not isinstance(pv, list) or not pv or pv[0] != c.get('bestmove') or not all(isinstance(m, str) and re.fullmatch(r'[a-h][1-8][a-h][1-8][nbrq]?', m) for m in pv):
            raise ValueError('pin PV and bestmove do not agree')
        expected_move = {'WAC001':'f6h5', 'promotion_white':'c6d7', 'promotion_black':'c3d2'}[c['case']]
        if c['bestmove'] != expected_move or (c['case'] != 'WAC001' and c['score'] <= 100):
            raise ValueError('pin observation changed its documented move class')
        answer[c['case']] = c
    return answer


def known_failures(data, netsha, pins, documented_wac_score=661, actual_exit=0,
                   known_reason='h256_e12 net-evaluation horizon; original 6.4.24 expectation retained'):
    del netsha  # Source and net identity are bound by the caller, never inferred from a label.
    cases = checked_pin_cases(pins)
    if type(actual_exit) is not int or actual_exit not in (0, 1) or type(documented_wac_score) is not int:
        raise ValueError('unexpected test exit or documented pin')
    lines = data.decode('utf-8', 'strict').splitlines()
    fails = [x for x in lines if x.startswith('FAIL:')]
    known = [x for x in lines if x.startswith('KNOWN_FAILURE:')]
    mismatch = [x for x in lines if x.startswith('PIN_MISMATCH:')]
    reason = ' (' + known_reason + ')'
    promotion = []
    label = 'unrestricted search chooses the winning rook underpromotion over stalemating queen promotion'
    for case, rook in [('promotion_white', 'c7c8r'), ('promotion_black', 'c2c1r')]:
        c = cases[case]
        promotion.append('KNOWN_FAILURE: ' + label + ' expected ' + rook + ' score > 100 at d1 got ' + c['bestmove'] + ' score ' + str(c['score']) + ' at d1' + reason)
    wac = cases['WAC001']
    wac_known = ['KNOWN_FAILURE: WAC 001 expected g3g6 got ' + wac['bestmove'] + reason,
                 'KNOWN_FAILURE: WAC 001 score expected >= 31997 got ' + str(wac['score']) + reason]
    if not fails and not mismatch and Counter(known) == Counter(wac_known + promotion):
        if actual_exit != 0 or wac['score'] != documented_wac_score:
            raise ValueError('KNOWN output disagrees with the exact source pin or exit')
        status = 'KNOWN4_PASS'
    else:
        required_fail = ['FAIL: WAC 001 expected g3g6 got ' + wac['bestmove'],
                         'FAIL: WAC 001 score ' + str(wac['score']) + ' below 31997']
        required_mismatch = ('PIN_MISMATCH: WAC 001 documented f6h5/' + str(documented_wac_score) +
            '/d12/PV=f6h5, observed ' + wac['bestmove'] + '/' + str(wac['score']) +
            '/d12/PV=' + wac['pv'][0] + '; re-record Job C pins in a reviewed change if the lock changed')
        if actual_exit != 1 or wac['score'] == documented_wac_score or Counter(fails) != Counter(required_fail) or Counter(known) != Counter(promotion) or mismatch != [required_mismatch]:
            raise ValueError('unexpected, missing, extra or drifting FAIL/KNOWN/PIN output')
        status = 'PROPOSED_PIN_RERECORD_REQUIRED'
    return {'status':status, 'known_lines':known, 'pin_mismatch_lines':mismatch,
            'exact_fail_lines':fails, 'counts':dict(Counter(known + mismatch + fails)),
            'test_exit':actual_exit, 'documented_wac_score':documented_wac_score,
            'scope':'Exact closed observations; this classification never adopts a lock or edits expectations'}


def documented_test_pin(src):
    text = (src / 'tests/tests.cpp').read_text(encoding='utf-8')
    scores = re.findall(r'constexpr int documented_wac_score = (\d+);', text)
    reasons = re.findall(r'<< " \(([^"\n]+)\)\\n";', text)
    if len(scores) != 1 or len(reasons) != 1:
        raise ValueError('source is not the explicit Job C/S01 pin API')
    return int(scores[0]), reasons[0]


def load_refs(path, expected_sha256):
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha256) or sha(path) != expected_sha256:
        raise ValueError('trusted external reference SHA mismatch')
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('duplicate reference JSON key')
            value[key] = item
        return value
    data = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)
    if type(data.get('schema')) is not int or data['schema'] != 1 or data.get('depths') != list(DEPTHS) or any(type(data.get(k)) is not int for k in ('perft5','kiwipete5','whole_fma')) or data.get('perft5') != 4865609 or data.get('kiwipete5') != 193690690 or data.get('whole_fma') != 0:
        raise ValueError('reference format or fixed perft/FMA contract changed')
    nets = data.get('nets')
    if not isinstance(nets, dict) or not nets:
        raise ValueError('reference file has no net entries')
    for digest, entry in nets.items():
        if not re.fullmatch(r'[0-9a-f]{64}', digest) or not isinstance(entry, dict):
            raise ValueError('reference net key is not a full SHA256')
        nodes = entry.get('refs')
        if not isinstance(nodes, list) or len(nodes) != 5 or any(type(x) is not int or x <= 0 for x in nodes):
            raise ValueError('reference node list must contain five positive integers')
    return data


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


def decode_stream(record):
    if record.get('encoding') != 'base64':
        raise ValueError('unexpected stream encoding')
    data = base64.b64decode(record['data'], validate=True)
    if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('original stream length/digest mismatch')
    return data


def observe_pins(runner, args, helper, exe, pinout, tag, expected, observe_only):
    argv = [sys.executable,'-B',helper,exe,'--out',pinout,'--timeout','300']
    if observe_only: argv.append('--observe-only')
    proc, log = runner.run(tag+'_S01_observe',argv,pinout.parent)
    path = pinout/'forge_sol_S01_pin_results_20261025.json'
    pins = json.loads(path.read_text(encoding='utf-8'))
    cases = checked_pin_cases(pins)
    if pins.get('exe_sha256') != sha(exe) or pins.get('exe') != str(exe.resolve()):
        raise ValueError('S01 observations belong to a different executable')
    if pins['status'] != ('RECORDED' if observe_only else 'PASS'):
        raise ValueError('S01 helper mode/status mismatch')
    for label, c in cases.items():
        capture = json.loads((pinout/f'forge_sol_S01_{label}_raw_{DATE}.json').read_text())
        if capture.get('argv') != [str(exe)] or capture.get('exit') != 0 or capture.get('stream_capture_complete') is not True:
            raise ValueError('S01 case raw process did not close with the selected executable')
        decode_stream(capture['stdout'])
        if decode_stream(capture['stderr']):
            raise ValueError('S01 case wrote stderr')
        if expected is not None and any(c.get(k) != v for k,v in expected[label].items()):
            raise ValueError('S01 observation differs from the externally supplied exact pin observations')
    return pins, {'path':str(path),'sha256':sha(path),'helper_sha256':sha(helper),'raw':log,
                  'mode':'observe-only' if observe_only else 'expect-lock',
                  'status':pins['status'],'reference_pins':'UNVERIFIED' if expected is None else 'exact match'}


def cpp_pin_tokens(text):
    tokens = re.findall(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|\d+|[^\s]',text,re.S)
    tokens = [t for t in tokens if not t.startswith(('//','/*'))]
    needle = ['constexpr','int','documented_wac_score','=']
    found = 0
    for i in range(len(tokens)-5):
        if tokens[i:i+4] == needle and tokens[i+4].isdigit() and tokens[i+5] == ';':
            tokens[i+4] = '<EXPLICIT_PIN>';found += 1
    if found != 1:
        raise ValueError('C++ pin declaration is not unique')
    return ['<KNOWN_REASON>' if t.startswith('" (') and 'net-evaluation horizon; original 6.4.24 expectation retained)' in t else t for t in tokens]


def helper_pin_ast(text):
    import ast
    tree = ast.parse(text)
    found = 0
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CASES' for t in node.targets):
            node.value.elts[0].elts[5] = ast.Constant(value='<EXPLICIT_PIN>');found += 1
    if found != 1:
        raise ValueError('helper CASES declaration is not unique')
    return ast.dump(tree,include_attributes=False)


def apply_pin_proposal(runner,args,src,build,tag,expected_wac):
    proposal = Path(args.pin_proposal)
    before = {str(p.relative_to(src)):sha(p) for p in input_files(src)}
    old_cpp = (src/'tests/tests.cpp').read_text()
    old_helper = (src/'tools/rerecord_pins.py').read_text()
    saved = runner.out/f'forge_sol_S28_v2_{tag}_tests_before_pin_{DATE}.elf'
    shutil.copyfile(build/'forge_tests',saved)
    proof = dry_patch_check(runner,src,{'id':tag+'_pin_proposal','path':str(proposal)})
    runner.run(tag+'_apply_explicit_pin_proposal',['patch','--batch','--no-backup-if-mismatch','--forward','-p1','-F0','--input',proposal],src)
    after = {str(p.relative_to(src)):sha(p) for p in input_files(src)}
    changed = [{'path':k,'before_sha256':before.get(k),'after_sha256':after.get(k)} for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)]
    paths = {r['path'] for r in changed}
    if not {'tests/tests.cpp','tools/rerecord_pins.py'} <= paths or not paths <= {'tests/tests.cpp','tools/rerecord_pins.py','README.md','IDEA_SOURCE.md'}:
        raise ValueError('explicit pin proposal changed unexpected paths')
    if cpp_pin_tokens(old_cpp) != cpp_pin_tokens((src/'tests/tests.cpp').read_text()) or helper_pin_ast(old_helper) != helper_pin_ast((src/'tools/rerecord_pins.py').read_text()):
        raise ValueError('pin proposal changes original expectations, test logic or helper logic')
    documented, reason = documented_test_pin(src)
    helper = helper_contract(src/'tools/rerecord_pins.py')
    if documented != expected_wac or helper['documented_wac_score'] != expected_wac:
        raise ValueError('provided proposal does not pin the independently observed exact WAC score in both locations')
    return {'status':'PROPOSED_EXACT_PIN_DELTA_ONLY','patch':str(proposal),'patch_sha256':sha(proposal),
            'file_changes':changed,'actual_apply_checks':proof,'pre_proposal_test_ELF':str(saved),
            'pre_proposal_test_ELF_sha256':sha(saved),'original_expression_and_helper_logic_unchanged':True,
            'policy':'Explicit external reviewed/proposed input in an isolated source copy; accepted lock unchanged'}


def qualify(runner,args,src,build,row,netsha,refs,flavour):
    name = row['id'] if row else 'base'
    tag = name+'_'+flavour
    exposure = 'ON' if flavour=='expose' else 'OFF'
    flags = '-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
    runner.run(tag+'_configure',[args.cmake,'-S',src,'-B',build,'-DCMAKE_BUILD_TYPE=Release',
                                  '-DCMAKE_CXX_FLAGS='+flags,'-DFORGE_EXPOSE_TUNABLES='+exposure],src)
    runner.run(tag+'_build',[args.cmake,'--build',build,'--parallel',args.jobs],src)
    exe = build/'forge'
    # The first invocation remains a bare fixed-depth OFF gate, before any UCI options.
    proc, firstlog = runner.run(tag+'_first_bare_d11',[exe],src,b'bench 11\nquit\n')
    if proc.stderr or bench_count(proc.stdout,11) != refs[0]:
        raise ValueError('first bare OFF d11 mismatch or stderr; no later engine tests')
    result = {'id':tag,'queue_id':name,'build_flavour':flavour,'FORGE_EXPOSE_TUNABLES':exposure,
              'CMAKE_BUILD_TYPE':'Release','CMAKE_CXX_FLAGS':flags,'engine':str(exe),
              'engine_sha256':sha(exe),'net_sha256':netsha,'first_invocation_raw':firstlog,'off':[],'on':None}
    for depth,expected in zip(DEPTHS,refs):
        proc,log = runner.run(tag+'_off_d'+str(depth),[exe],src,f'bench {depth}\nquit\n'.encode())
        if proc.stderr or bench_count(proc.stdout,depth)!=expected:
            raise ValueError('OFF fixed-reference mismatch')
        result['off'].append({'depth':depth,'nodes':expected,'raw':log})
    # Terminal S47 repeat oracle is needed for the release net-only base, not every queue flavour.
    if row is None and flavour=='release':
        result['off_repeat']=[]
        for depth,expected in zip(DEPTHS,refs):
            proc,log=runner.run(tag+'_repeat_d'+str(depth),[exe],src,f'bench {depth}\nquit\n'.encode())
            if proc.stderr or bench_count(proc.stdout,depth)!=expected:
                raise ValueError('repeated fixed-reference mismatch')
            result['off_repeat'].append({'depth':depth,'nodes':expected,'raw':log})
    result['perft']=[]
    for label,position,expected in [('startpos','startpos',4865609),('kiwipete','fen '+KIWIPETE,193690690)]:
        proc,log=runner.run(tag+'_perft_'+label,[exe],src,('position '+position+'\ngo perft 5\nquit\n').encode())
        if proc.stderr or perft_count(proc.stdout)!=expected: raise ValueError('perft mismatch')
        result['perft'].append({'position':label,'nodes':expected,'raw':log})
    result['fma']=[]
    for scope,binary in [('whole_executable',exe),('NNUE_object',build/'CMakeFiles/forge_core.dir/src/nnue.cpp.o')]:
        proc,log=runner.run(tag+'_fma_'+scope,[args.objdump,'-d','-C','--no-show-raw-insn',binary],src)
        count=fma_count(proc.stdout)
        if count:raise ValueError('FMA instruction present')
        result['fma'].append({'scope':scope,'count':count,'file_sha256':sha(binary),'raw':log})
    if args.fma_checker:
        _,log=runner.run(tag+'_supplied_fma',[sys.executable,'-B',args.fma_checker,exe],src)
        result['supplied_fma_checker']={'scope':'supplied NNUE checker, separate from whole count','raw':log,'sha256':sha(args.fma_checker)}
    proc,log=runner.run(tag+'_uci',[exe],src,b'uci\nquit\n')
    if proc.stderr:raise ValueError('UCI stderr')
    options=[x.decode('utf-8') for x in proc.stdout.splitlines() if x.startswith(b'option name ')]
    if not options or len(options)!=len(set(options)):raise ValueError('empty or duplicate UCI options')
    result['uci']={'build_flavour':flavour,'options':options,'raw':log}
    if row:
        if flavour=='expose':result['on_control']=active_option(proc.stdout,row['option'],row['value'])
        else:result['on_control']={'scope':'hidden release tunable; same source/core is independently qualified with expose flavour','name':row['option'],'value':row['value']}
        result['on']=[]
        for depth in DEPTHS:
            data=f"setoption name {row['option']} value {row['value']}\nbench {depth}\nquit\n".encode()
            proc,log=runner.run(tag+'_on_d'+str(depth),[exe],src,data)
            if proc.stderr:raise ValueError('ON bench stderr')
            result['on'].append({'depth':depth,'nodes':bench_count(proc.stdout,depth),'raw':log})
        result['pc_precheck_depth']=next((a['depth'] for a,b in zip(result['off'],result['on']) if a['nodes']!=b['nodes']),None)
        if row['time_only'] and result['pc_precheck_depth'] is not None:raise ValueError('time-only patch changed a fixed-depth search')
    netentry=args.refs_data['nets'][netsha]
    expectedpins=netentry.get('pins')
    initialout=runner.out/f'forge_sol_S28_v2_{tag}_pins_observed_{DATE}'
    initial,initialrecord=observe_pins(runner,args,Path(args.pin_helper),exe,initialout,tag+'_initial',expectedpins,True)
    documented,reason=documented_test_pin(src)
    proc,log=runner.run(tag+'_tests_before_pin',[build/'forge_tests'],src,allowed=(0,1))
    initialclass=known_failures(proc.stdout+proc.stderr,netsha,initial,documented,proc.returncode,reason)
    result['initial_pin_capture']=initialrecord
    result['initial_test_classification']={**initialclass,'raw':log}
    pins=initial
    if initialclass['status']=='PROPOSED_PIN_RERECORD_REQUIRED' and args.pin_proposal:
        if expectedpins is None:raise ValueError('cannot apply a pin proposal without independent external exact pin observations')
        before_engine=sha(exe)
        result['pin_proposal']=apply_pin_proposal(runner,args,src,build,tag,expectedpins['WAC001']['score'])
        runner.run(tag+'_rebuild_current_tests_only',[args.cmake,'--build',build,'--target','forge_tests','--parallel',args.jobs],src)
        if sha(exe)!=before_engine:raise ValueError('test-only pin proposal changed the engine ELF')
        pins,record=observe_pins(runner,args,src/'tools/rerecord_pins.py',exe,runner.out/f'forge_sol_S28_v2_{tag}_pins_proposed_{DATE}',tag+'_proposed',expectedpins,False)
        result['proposed_pin_capture']=record
    documented,reason=documented_test_pin(src)
    proc,log=runner.run(tag+'_final_forge_tests',[build/'forge_tests'],src,allowed=(0,1))
    final=known_failures(proc.stdout+proc.stderr,netsha,pins,documented,proc.returncode,reason)
    result['test_classification']={**final,'raw':log}
    result['known_fail_lines']=final['known_lines']
    result['pin_signature']=pin_signature(pins)
    proc,log=runner.run(tag+'_full_ctest',[args.ctest,'--test-dir',build,'--output-on-failure','--parallel','1'],src,allowed=(0,8))
    text=(proc.stdout+proc.stderr).decode('utf-8','strict')
    failed=re.findall(r'^\s*\d+\s+-\s+(\S+)\s+\(Failed\)\s*$',text,re.M)
    if final['status']=='KNOWN4_PASS':
        if proc.returncode!=0 or failed:raise ValueError('current merged CTest not fully green after explicit pin handling')
    else:
        diagnostic=[s for s in text.splitlines() if s.startswith(('FAIL:','KNOWN_FAILURE:','PIN_MISMATCH:'))]
        expected=final['exact_fail_lines']+final['known_lines']+final['pin_mismatch_lines']
        if proc.returncode!=8 or failed!=['forge_tests'] or Counter(diagnostic)!=Counter(expected):raise ValueError('unexpected CTest failure set beyond exact recorded pin drift')
    last=(build/'Testing/Temporary/LastTest.log').read_bytes()
    dump(runner.out/f'forge_sol_S28_v2_{tag}_LastTest_{DATE}.json',raw(last))
    if re.search(rb'ERROR: (?:AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer)|runtime error:|AddressSanitizer:DEADLYSIGNAL',last+proc.stdout+proc.stderr):raise ValueError('sanitizer diagnostic in complete CTest evidence')
    result['ctest']={'raw':log,'exit':proc.returncode,'failed_targets':failed,'complete_LastTest_preserved':True}
    result['source_sha256']=snapshot(input_files(src))
    result['status']='PROPOSED_PIN_QUALIFIED_NOT_ADOPTED' if final['status']=='KNOWN4_PASS' and expectedpins is not None else 'PROPOSED_PIN_RERECORD_REQUIRED'
    return result


def apply_queue(runner, src, row):
    argv = ['patch', '--batch', '--no-backup-if-mismatch', '--forward', '-p1', '-F0', '--reject-file=-', '--input', row['path']]
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
            'check_exit': 0, 'verification_stdout_sha256': hashlib.sha256(p.stdout).hexdigest(),
            'verification_stdout':raw(p.stdout),'verification_stderr':raw(p.stderr)}


def arguments(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lock', dest='tree', required=True)
    p.add_argument('--net', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--refs', required=True)
    p.add_argument('--refs-sha256', required=True)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--queue')
    p.add_argument('--pin-helper')
    p.add_argument('--pin-helper-sha256', required=True)
    p.add_argument('--pin-proposal')
    p.add_argument('--pin-proposal-sha256')
    p.add_argument('--pin-proposal-net-sha256')
    p.add_argument('--net-sha256')
    p.add_argument('--flavours', choices=('release','expose','both'), default='both')
    p.add_argument('--audit-evidence')
    p.add_argument('--cmake', default='cmake')
    p.add_argument('--ctest', default='ctest')
    p.add_argument('--objdump', default='objdump')
    p.add_argument('--fma-checker')
    p.add_argument('--jobs', type=int, choices=(1, 2), default=2)
    return p.parse_args(argv)


def patch_paths(path):
    validate_patch(path)
    values = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('+++ ') and line[4:] != '/dev/null':
            token = line[4:].split('\t',1)[0].split(' ',1)[0]
            if not token.startswith('b/'):
                raise ValueError('patch lacks the b/ target prefix')
            values.append(token[2:])
    if not values or len(values) != len(set(values)):
        raise ValueError('patch paths missing or duplicated')
    return values


def helper_contract(path):
    import ast
    tree = ast.parse(path.read_text(encoding='utf-8'))
    matches = [node for node in tree.body if isinstance(node, ast.Assign) and
               any(isinstance(t, ast.Name) and t.id == 'CASES' for t in node.targets)]
    if len(matches) != 1:
        raise ValueError('helper does not declare the S01 CASES interface exactly once')
    cases = ast.literal_eval(matches[0].value)
    if len(cases) != 3 or [c[0] for c in cases] != ['WAC001','promotion_white','promotion_black']:
        raise ValueError('unexpected helper case identities')
    if cases[0][2:5] != (12,8,'f6h5') or type(cases[0][5]) is not int or cases[1][2:] != (1,1,'c6d7',None) or cases[2][2:] != (1,1,'c3d2',None):
        raise ValueError('helper case move/depth/hash API changed')
    text = path.read_text(encoding='utf-8')
    if not all(s in text for s in ["'--observe-only'", "'RECORDED'", "'stream_capture_complete'"]):
        raise ValueError('helper lacks observe-only and complete-stream API')
    return {'sha256':sha(path),'documented_wac_score':cases[0][5],
            'candidate_mode':'--observe-only returns RECORDED; never interpreted as adoption'}


def dry_patch_check(runner, tree, row):
    paths = patch_paths(Path(row['path']))
    if 'src/nnue_weights.inc' in paths:
        raise ValueError('queued source patch may not replace the separately selected net')
    checks = []
    for label, argv in [('git', ['git','apply','--check','--verbose',row['path']]),
                        ('GNU_F0', ['patch','--batch','--no-backup-if-mismatch','--forward','-p1','-F0','--dry-run','--input',row['path']])]:
        proc, rawname = runner.run(row['id']+'_'+label+'_dryrun',argv,tree,allowed=(0,1))
        checks.append({'tool':label,'exit':proc.returncode,'raw':rawname})
    if any(c['exit'] for c in checks):
        raise ValueError('queued patch failed a required read-only applicability check')
    return {'id':row['id'],'status':'PASS_GIT_AND_GNU_F0','paths':paths,'checks':checks,
            'candidate_equivalence':'Selected net is the only production-file difference and is not a patch target'}


def run(args):
    tree = Path(args.tree).absolute()
    if tree.is_symlink() or any(a.is_symlink() for a in tree.parents) or not tree.is_dir():
        raise ValueError('lock must be an existing nonsymlink source directory')
    tree = tree.resolve()
    sources = input_files(tree)
    refs_path = regular(args.refs, 'external references')
    refs_data = load_refs(refs_path, args.refs_sha256)
    net = regular(args.net, 'candidate net')
    netsha = sha(net)
    locksha = sha(tree / 'src/nnue_weights.inc')
    if netsha not in refs_data['nets'] or locksha not in refs_data['nets'] or (args.net_sha256 and args.net_sha256 != netsha):
        raise ValueError('net/lock SHA lacks explicitly trusted external references')
    helper = regular(args.pin_helper or tree/'tools/rerecord_pins.py', 'S01 pin helper')
    if not re.fullmatch(r'[0-9a-f]{64}',args.pin_helper_sha256) or sha(helper) != args.pin_helper_sha256:
        raise ValueError('source-bound S01 helper SHA mismatch')
    contract = helper_contract(helper)
    args.pin_helper = str(helper)
    args.refs_data = refs_data
    args.lock_sha256 = locksha
    queue = regular(args.queue, 'queue manifest') if args.queue else None
    rows = queue_rows(queue)
    proposal_fields = [args.pin_proposal,args.pin_proposal_sha256,args.pin_proposal_net_sha256]
    if any(proposal_fields) and not all(proposal_fields):
        raise ValueError('pin proposal needs path, full SHA256 and candidate-net SHA256')
    proposal = None
    if args.pin_proposal:
        proposal = regular(args.pin_proposal,'explicit pin proposal')
        if sha(proposal) != args.pin_proposal_sha256 or args.pin_proposal_net_sha256 != netsha:
            raise ValueError('pin proposal digest/net scope mismatch')
        allowed = {'tests/tests.cpp','tools/rerecord_pins.py','README.md','IDEA_SOURCE.md'}
        if not set(patch_paths(proposal)) <= allowed:
            raise ValueError('pin proposal touches engine or unapproved paths')
        args.pin_proposal = str(proposal)
    external = [net,helper,Path(__file__).resolve(),refs_path]
    for filename in ('forge_sol_S28_v2_audit_checks_20261025.py','forge_sol_S28_v2_autolock_checklist_20261025.py'):
        component = Path(__file__).with_name(filename)
        if component.is_file(): external.append(regular(component,'bundled audit component'))
    if queue: external.append(queue)
    if proposal: external.append(proposal)
    if args.audit_evidence:
        args.audit_evidence = str(regular(args.audit_evidence,'S47 evidence'))
        external.append(Path(args.audit_evidence))
    if args.fma_checker:
        checker = regular(args.fma_checker,'FMA checker');args.fma_checker = str(checker);external.append(checker)
    for row in rows:
        external.extend(Path(row[k]) for k in ('path','repair_path') if k in row)
    out0 = Path(args.out).absolute()
    if os.path.lexists(out0) or not out0.parent.is_dir() or any(a.is_symlink() for a in out0.parents):
        raise ValueError('output must be NEW with an existing nonsymlink parent')
    out = out0.resolve()
    if within(out,tree) or within(tree,out) or any(within(p,out) for p in external):
        raise ValueError('output overlaps an input')
    if any(c in ('baseline','lock','locks') or c.startswith('dist-') for c in out.parts):
        raise ValueError('output may not be a baseline, lock or dist directory')
    before = snapshot(sources + external)
    out.mkdir()
    plan = {'mode':'execute' if args.execute else 'dry-run','lock':str(tree),'lock_net_sha256':locksha,
            'net':str(net),'net_sha256':netsha,'oracle':refs_data['nets'][netsha],
            'references':{'path':str(refs_path),'sha256':sha(refs_path)},'helper':contract,
            'pin_proposal':({'path':str(proposal),'sha256':sha(proposal),'status':'explicit PROPOSED input; accepted lock unchanged'} if proposal else None),
            'build_flavours':['release','expose'] if args.flavours=='both' else [args.flavours],
            'queue':rows,'source_snapshot':before,'tool_sha256':sha(__file__),
            'policy':'Observational new-output-only; RECORDED/proposed pins are not accepted lock changes; no speed/Elo claim'}
    dump(out/f'forge_sol_S28_v2_plan_{DATE}.json',plan)
    runner = Runner(out)
    result = {'status':'DRY_RUN','stages':[],'queue_applicability':[],
              'S47':{'status':'UNVERIFIED','reason':'No actual AUTOLOCK/gate/confirm packet supplied; derived prose checks will be applied when evidence is present'}}
    try:
        for row in rows:
            result['queue_applicability'].append(dry_patch_check(runner,tree,row))
        if proposal:
            result['pin_proposal_applicability'] = dry_patch_check(runner,tree,{'id':'explicit_pin_proposal','path':str(proposal)})
        if args.execute:
            # A base release is the canonical comparison. Queue flavours are explicit.
            import importlib.util
            module_path = Path(__file__).with_name('forge_sol_S28_v2_audit_checks_20261025.py')
            spec = importlib.util.spec_from_file_location('s28_snapshot_checks',module_path)
            snapshot_checks = importlib.util.module_from_spec(spec);spec.loader.exec_module(snapshot_checks)
            base = None
            queue_flavours = ['release','expose'] if args.flavours=='both' else [args.flavours]
            for row in [None] + rows:
                for flavour in (['release'] if row is None else queue_flavours):
                    tag = (row['id'] if row else 'base')+'_'+flavour
                    src = out/f'forge_sol_S28_v2_{tag}_source_{DATE}'
                    build = out/f'forge_sol_S28_v2_{tag}_build_{DATE}'
                    copy_tree(tree,src,net)
                    pre_delta = snapshot_checks.netonly_tree(tree,src,refs_data['nets'][netsha]['net_md5'])
                    dump(out/f'forge_sol_S28_v2_{tag}_pre_proposal_netonly_{DATE}.json',pre_delta)
                    if netsha != locksha and pre_delta['status'] != 'PASS':
                        raise ValueError('clean copied candidate contains non-net changes before explicit patches')
                    application = apply_queue(runner,src,row) if row else None
                    stage = qualify(runner,args,src,build,row,netsha,refs_data['nets'][netsha]['refs'],flavour)
                    stage['queue_patch'] = application
                    stage['strict_netonly_before_queue_and_proposal'] = pre_delta
                    stage['raw_source_diff_after_explicit_proposal'] = snapshot_checks.netonly_tree(tree,src,refs_data['nets'][netsha]['net_md5'])
                    stage['scope'] = 'Isolated qualification candidate. Applied pin proposal is NOT the actual AUTOLOCK source, whose pin files must remain attached, not applied.'
                    if base is None:
                        base = stage
                    else:
                        require_base_pins(base,stage)
                        if flavour=='release' and stage['uci'] != base['uci']:
                            # Raw receipt names differ; compare like-flavour metadata only.
                            if stage['uci']['options'] != base['uci']['options']:
                                raise ValueError('release UCI option metadata changed')
                    result['stages'].append(stage)
                    dump(out/f'forge_sol_S28_v2_{tag}_stage_results_{DATE}.json',stage)
            result['status'] = ('QUALIFIED_PROPOSED_NOT_ADOPTED' if all(stage['status']=='PROPOSED_PIN_QUALIFIED_NOT_ADOPTED' for stage in result['stages']) else 'PROPOSED_PIN_RERECORD_REQUIRED')
        checklist_path = Path(__file__).with_name('forge_sol_S28_v2_autolock_checklist_20261025.py')
        if checklist_path.is_file():
            import importlib.util
            spec = importlib.util.spec_from_file_location('s28_user_checklist',checklist_path)
            checklist = importlib.util.module_from_spec(spec);spec.loader.exec_module(checklist)
            packet = json.loads(Path(args.audit_evidence).read_text()) if args.audit_evidence else None
            result['S47'] = checklist.audit_autolock(packet)
            result['S47']['checker_sha256'] = sha(checklist_path)
            if result['S47']['status']=='FAIL':
                raise ValueError('supplied AUTOLOCK packet contradicts the authoritative user checklist')
        else:
            result['S47'] = {'status':'UNVERIFIED','reason':'Authoritative checklist module has not been bundled; no AUTOLOCK qualification claimed'}
    except Exception as exc:
        result.update(status='FAIL',error=type(exc).__name__+': '+str(exc))
    after = snapshot(sources + external)
    result['input_immutability'] = {'equal':before==after,'before':before,'after':after}
    if before != after:
        result.update(status='FAIL',error='input files changed')
    dump(out/f'forge_sol_S28_v2_results_{DATE}.json',result)
    sealed = seal(out)
    print(json.dumps({'status':result['status'],'out':str(out),'manifest':sealed,
                      'build_flavours':plan['build_flavours'],'net_sha256':netsha},sort_keys=True))
    return 0 if result['status'] != 'FAIL' else 1


if __name__ == '__main__':
    try:
        sys.exit(run(arguments()))
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr)
        sys.exit(2)
