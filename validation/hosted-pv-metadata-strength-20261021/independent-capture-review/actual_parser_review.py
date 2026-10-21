#!/usr/bin/env python3
"""Exercise the actual frozen consumer on original/byte-extracted producer data.
No engine is executed; process creation and affinity mutation are forbidden.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from unittest.mock import patch
import os

ROOT = Path('/workspace/dwqww')
BASE = ROOT/'validation/hosted-pv-metadata-strength-20261021'
OUT = BASE/'independent-capture-review'
CAP = BASE/'capture-preparation/actual-five-captures'
NATIVE = ROOT/'validation/pv-metadata-native-20261021/release-signature-wrapper-attempt1'
RUNNER = ROOT/'.github/hosted-pv-metadata-strength/run_hosted.py'
PIN = '6ee3585f4def660a486fa7d199a12ebf18216038e8c4f7333675d18b1191fe6f'
inputs = {}
cases = []

def read(path):
    value = path.read_bytes()
    inputs[str(path)] = {'sha256':hashlib.sha256(value).hexdigest(),
        'bytes':len(value),'mode':path.stat().st_mode&0o7777}
    return value

def obj(path):return json.loads(read(path))
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(value)

def case(name,stdout,stderr,code,nodes,accept,origin):
    try:
        value = consumer.verify_candidate_bench_signature(stdout.decode('ascii'),
            stderr.decode('ascii'),code,nodes)
        actual=True; error=None
    except ValueError as e:
        value=None;actual=False;error=str(e)
    cases.append({'name':name,'expected_accept':accept,'actual_accept':actual,
        'pass':actual==accept,'result':value,'error':error,'origin':origin,
        'stdout_sha256':hashlib.sha256(stdout).hexdigest(),
        'stderr_sha256':hashlib.sha256(stderr).hexdigest(),
        'returncode_argument':code,'expected_nodes_argument':nodes})

assert hashlib.sha256(read(RUNNER)).hexdigest()==PIN
provenance=obj(CAP/'PROVENANCE.json')
assert inputs[str(CAP/'PROVENANCE.json')]['sha256']=='721611d1e6ade88f067d4e970875f046bccc5f837876acb22829394b5ff524b8'
native_command=obj(NATIVE/'bench11-command.json')
native_summary=obj(NATIVE/'summary.json')
native_stdout=read(NATIVE/'bench11.stdout.bin')
native_stderr=read(NATIVE/'bench11.stderr.bin')
native_stdin=read(NATIVE/'bench11.stdin.bin')
assert native_command['command']==['/workspace/.cloud-setup/pv-metadata-native-release/forge']
assert native_command['exit_code']==0 and native_command['timed_out'] is False and native_command['error'] is None
for kind,raw in [('stdout',native_stdout),('stderr',native_stderr),('stdin',native_stdin)]:
    assert native_command[kind+'_sha256']==hashlib.sha256(raw).hexdigest()
assert native_summary['status']=='PASS' and native_summary['source_commit']=='ff2e269c6058be84456e3b98344826d17b0056eb'
assert native_summary['bench11_expected_nodes']==292545 and native_summary['input_sha256_before']==native_summary['input_sha256_after']
assert native_summary['input_sha256_before']['candidate/forge']==provenance['captures']['candidate']['binary_sha256_before']['forge']
assert native_stdin==b'bench 11\nquit\n' and native_stderr==b''
write(OUT/'original-copy/native22-single-bench.stdout.bin',native_stdout)
write(OUT/'original-copy/native22-single-bench.stderr.bin',native_stderr)
write(OUT/'original-copy/native22-single-bench.stdin.bin',native_stdin)
spec=importlib.util.spec_from_file_location('actual_frozen_strength_consumer',RUNNER)
consumer=importlib.util.module_from_spec(spec)
with patch.object(subprocess,'Popen',side_effect=AssertionError('No process creation authorized')), \
     patch.object(subprocess,'run',side_effect=AssertionError('No process creation authorized')), \
     patch.object(os,'sched_setaffinity',side_effect=AssertionError('No affinity mutation authorized')):
    spec.loader.exec_module(consumer)
    case('genuine22_native_original_single_process_stdout',native_stdout,native_stderr,
        native_command['exit_code'],292545,True,
        {'kind':'original complete stdout of recorded native single-bench process',
         'source_path':str(NATIVE/'bench11.stdout.bin'),'command_path':str(NATIVE/'bench11-command.json')})
    for label,nodes in [('baseline',321912),('candidate',292545)]:
        record=provenance['captures'][label]
        facts=record['process_facts']
        original_path=Path(facts['stdout']);raw=read(original_path)
        assert hashlib.sha256(raw).hexdigest()==record['stdout_sha256']
        assert read(Path(facts['stderr']))==b''
        lines=raw.splitlines(keepends=True)
        assert len(lines)==5 and b''.join(lines)==raw
        offset=0
        for ordinal,line in enumerate(lines,1):
            derived=OUT/f'extracted/{label}-line-{ordinal:02d}.bin'
            write(derived,line)
            origin={'kind':'byte-extracted parser case; NOT a complete process capture',
                'source_path':str(original_path),'source_sha256':record['stdout_sha256'],
                'byte_start':offset,'byte_end_exclusive':offset+len(line),
                'original_line_1based':ordinal,'derived_path':str(derived)}
            case(f'{label}_extracted_original_line_{ordinal}',line,b'',0,nodes,True,origin)
            offset+=len(line)
        case(f'{label}_complete_five_row_stream_rejected_by_single_bench_consumer',raw,b'',0,nodes,False,
            {'kind':'complete original five-command stream; intentionally wrong cardinality for single-bench consumer',
             'source_path':str(original_path),'source_sha256':record['stdout_sha256']})
    mutations=[
      ('prefixless',native_stdout.replace(b'info string ',b'',1),b'',0,292545),
      ('malformed_time',native_stdout.replace(b' time ',b' time BAD',1),b'',0,292545),
      ('duplicate',native_stdout+native_stdout,b'',0,292545),
      ('nonempty_stderr',native_stdout,b'warning: injected control\n',0,292545),
      ('nonzero_exit',native_stdout,b'',1,292545),
      ('wrong_expected_nodes',native_stdout,b'',0,321912),
      ('warning_prefix',b'warning: injected control\n'+native_stdout,b'',0,292545),
      ('trailing_junk',native_stdout+b'junk\n',b'',0,292545),
      ('noncanonical_signed_nodes',native_stdout.replace(b'nodes 292545',b'nodes +292545'),b'',0,292545),
    ]
    for name,stdout,stderr,code,nodes in mutations:
        write(OUT/f'controls/{name}.stdout.bin',stdout)
        write(OUT/f'controls/{name}.stderr.bin',stderr)
        case('control_'+name,stdout,stderr,code,nodes,False,
            {'kind':'explicit synthetic mutation/control of genuine22 original single-bench data; not engine output',
             'source_path':str(NATIVE/'bench11.stdout.bin'),
             'source_sha256':hashlib.sha256(native_stdout).hexdigest()})
for path,info in inputs.items():
    p=Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256']
    assert p.stat().st_mode&0o7777==info['mode']
assert all(c['pass'] for c in cases),[c for c in cases if not c['pass']]
receipt={'status':'PASS_ACTUAL_PRODUCER_CANONICAL_PARSER_CASES_NO_ENGINE_EXECUTION',
    'runner_sha256':PIN,'parser':'verify_candidate_bench_signature',
    'capture_provenance_sha256':inputs[str(CAP/'PROVENANCE.json')]['sha256'],
    'case_count':len(cases),'passed_cases':sum(c['pass'] for c in cases),'cases':cases,
    'original_inputs':inputs,'new_engine_bench_test_processes':0,
    'scope':'Actual frozen consumer loaded with process creation and affinity mutation forbidden. Eleven accepted cases: one genuine complete native22 single-bench stdout and ten byte-extracted lines. Two complete five-row streams and nine synthetic controls rejected. Extracted lines are not independent process captures. No speed or Elo estimate.'}
target=OUT/'PARSER-REVIEW.json'
with target.open('x') as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'status':receipt['status'],'passed':receipt['passed_cases'],'cases':len(cases),
    'receipt_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
