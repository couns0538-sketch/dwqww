from pathlib import Path
import datetime
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import time

from pipeline_gate import load_freeze
FREEZE=load_freeze()
COMMIT=FREEZE['source_commit']
SOURCE=Path('/workspace/.cloud-setup/windows6421-source')
BUILD=Path('/workspace/.cloud-setup/windows6421-build')
BASE=Path('/workspace/dwqww/validation/nearest-pawn-windows-20261021')
OUT=BASE/'runtime-attempt1'
WINE=Path('/workspace/.cloud-setup/wine/usr/lib/wine/wine64')
TOOLS=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64/bin')
WRAPPER=BASE/'forge-nearest-pawn-wine'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
win=lambda p:'Z:'+str(p).replace('/','\\')
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n')
assert json.loads((BASE/'WINDOWS-BUILD-CLEAR.json').read_text())['authorization']=='21 WINDOWS BUILD CLEAR'
OUT.mkdir(exist_ok=False)
environment=os.environ.copy();environment.update(WINEPREFIX='/workspace/.cloud-setup/wine-prefix-ready',
 WINEDEBUG='-all',XDG_CACHE_HOME='/workspace/.cloud-setup/font-cache',PYTHONDONTWRITEBYTECODE='1')
WRAPPER.write_text('#!/usr/bin/env bash\nexport WINEPREFIX=/workspace/.cloud-setup/wine-prefix-ready\nexport WINEDEBUG=-all\nexport XDG_CACHE_HOME=/workspace/.cloud-setup/font-cache\nexec /workspace/.cloud-setup/wine/usr/lib/wine/wine64 /workspace/.cloud-setup/windows6421-build/forge.exe "$@"\n')
WRAPPER.chmod(0o755)
# Evidence-only adapter: preserve every production test assertion and exchange,
# translating only the Linux-created book path to Wine's existing Z: drive.
ownbook_original=SOURCE/'tools/ownbook_regression.py'
ownbook_adapted=OUT/'ownbook-wine-regression.py'
ownbook_text=ownbook_original.read_text()
assert ownbook_text.count('str(book)')==2
assert ownbook_text.count('{book} with 1 entries')==2
ownbook_new=ownbook_text.replace('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path('+repr(str(SOURCE))+')')
ownbook_new=ownbook_new.replace('            e.send("setoption name Book File value " + str(book))',
                               '            book_sent = "Z:" + str(book).replace("/", "\\\\")\n            e.send("setoption name Book File value " + book_sent)',1)
ownbook_new=ownbook_new.replace(' + str(book))', ' + book_sent)')
ownbook_new=ownbook_new.replace('{book} with 1 entries', '{book_sent} with 1 entries')
ownbook_adapted.write_text(ownbook_new)
compile(ownbook_new,str(ownbook_adapted),'exec')
(OUT/'ownbook-evidence-adaptation.diff').write_text(''.join(difflib.unified_diff(
 ownbook_text.splitlines(keepends=True),ownbook_new.splitlines(keepends=True),
 fromfile='frozen-source/tools/ownbook_regression.py',tofile='evidence/ownbook-wine-regression.py')))
inputs={p.name:p for p in BUILD.glob('*.exe')}
inputs.update(core_library=BUILD/'libforge_core.a',core_flags=BUILD/'CMakeFiles/forge_core.dir/flags.make',
 compile_commands=BUILD/'compile_commands.json',uci_tool=SOURCE/'tools/uci_regression.py',ponder_tool=SOURCE/'tools/ponder_regression.py',
 fixtures=SOURCE/'tests/legal_witness_fixtures.tsv',corpus=SOURCE/'tools/openings/forge-10000.epd',
 ownbook_tool=ownbook_original,ownbook_wine_adapter=ownbook_adapted,wrapper=WRAPPER,wine_loader=WINE,disassembler=TOOLS/'llvm-objdump')
before={name:sha(path) for name,path in inputs.items()}
source_before=json.loads((BASE/'source-hashes.json').read_text())
assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==source_before
commands=[('core',[str(WINE),str(BUILD/'forge_tests.exe')]),
 ('correction-history',[str(WINE),str(BUILD/'forge_correction_history_tests.exe')]),
 ('runtime-psqt',[str(WINE),str(BUILD/'forge_runtime_psqt_tests.exe')]),
 ('pawn-span',[str(WINE),str(BUILD/'forge_pawn_span_tests.exe')]),
 ('nearest-pawn',[str(WINE),str(BUILD/'forge_nearest_pawn_tests.exe')]),
 ('coherent-tt',[str(WINE),str(BUILD/'forge_tt_tests.exe')]),
 ('rule50',[str(WINE),str(BUILD/'forge_rule50_tests.exe')]),
 ('legal-witness',[str(WINE),str(BUILD/'forge_legal_witness_tests.exe'),win(inputs['fixtures']),win(inputs['corpus'])]),
 ('uci',[sys.executable,str(inputs['uci_tool']),str(WRAPPER),'--log',str(OUT/'uci-transcript.log')]),
 ('ponder',[sys.executable,str(inputs['ponder_tool']),str(WRAPPER)]),
 ('ownbook',[sys.executable,str(ownbook_adapted),str(WRAPPER),str(OUT/'ownbook-transcript.json')])]
bench_command=[str(WINE),str(BUILD/'forge.exe')]
bench_stdin=b'bench 11\nquit\n';(OUT/'bench-stdin.txt').write_bytes(bench_stdin)
simd_command=[str(TOOLS/'llvm-objdump'),'-d','--no-show-raw-insn',str(BUILD/'forge.exe')]
write('protocol.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_and_tests_commit':COMMIT,'input_sha256_before':before,'commands':commands,
 'bench_command':bench_command,'bench_stdin':bench_stdin.decode(),'bench_hash_mib':16,'bench_threads':1,
 'bench_expected_same_platform_parent_nodes':352313,'candidate_bench_expectation':352313,'bench_signature_policy':'Nearest-pawn distance geometry intends exact evaluation/search parity to20. Require frozen parent352313; preserve any mismatch and stop, never update expectation from candidate outcome','simd_command':simd_command,
 'environment_subset':{k:environment[k] for k in ('WINEPREFIX','WINEDEBUG','XDG_CACHE_HOME','PYTHONDONTWRITEBYTECODE')},
 'scope':'Wine functional correctness and bounded node signature only; no performance, Elo or native hardware claim',
 'core_perft_cases':{'start_depth4':197281,'kiwipete_depth3':97862,'position3_depth4':43238,
                    'position4_depth3':9467,'position5_depth3':62379,'position6_depth3':89890}})
checks=[]
try:
    for name,command in commands:
        started=time.monotonic()
        with (OUT/(name+'-stdout.log')).open('x') as stdout,(OUT/(name+'-stderr.log')).open('x') as stderr:
            completed=subprocess.run(command,env=environment,cwd=BUILD,stdout=stdout,stderr=stderr,timeout=300)
        item={'name':name,'exit_code':completed.returncode,'elapsed_seconds':time.monotonic()-started}
        checks.append(item);write('progress.json',checks);print(json.dumps(item),flush=True)
        if completed.returncode:raise RuntimeError(name+' failed')
    correction=(OUT/'correction-history-stdout.log').read_text()
    correction_summary=re.findall(r'^SUMMARY checks=(\d+) failures=(\d+)\s*$',correction,re.M)
    assert len(correction_summary)==1 and int(correction_summary[0][0])>0 and int(correction_summary[0][1])==0
    assert int(correction_summary[0][0])==54
    runtime_psqt=(OUT/'runtime-psqt-stdout.log').read_text()
    runtime_summary=re.findall(r'^SUMMARY checks=(\d+) failures=(\d+)\s*$',runtime_psqt,re.M)
    assert runtime_summary==[(str(FREEZE['runtime_summary_checks']),'0')]
    assert len(re.findall(r'^PASS ',runtime_psqt,re.M))==FREEZE['runtime_summary_checks'] and not re.search(r'^FAIL ',runtime_psqt,re.M)
    pawn_raw=(OUT/'pawn-span-stdout.log').read_text()
    pawn_summary=re.findall(r'^pawn_span_tests: (\d+) checks, (\d+) failures\s*$',pawn_raw,re.M)
    assert pawn_summary==[(str(FREEZE['pawn_span_checks']),'0')] and not re.search(r'^FAIL ',pawn_raw,re.M)
    nearest_raw=(OUT/'nearest-pawn-stdout.log').read_text()
    nearest_summary=re.findall(r'^Nearest pawn distance: sets (\d+) checks (\d+) failures (\d+)\s*$',nearest_raw,re.M)
    assert nearest_summary==[(str(FREEZE['nearest_pawn_sets']),str(FREEZE['nearest_pawn_checks']),'0')]
    assert not re.search(r'^nearest mismatch ',nearest_raw,re.M)
    assert 'Correction-history residual increment contract' in correction and 'FAIL ' not in correction
    ownbook_result=json.loads((OUT/'ownbook-transcript.json').read_text())
    assert ownbook_result['error'] is None and len(ownbook_result['checks'])==5
    assert all(c['PASS'] and c['actual_book']==c['expected_book'] for c in ownbook_result['checks'])
    assert 'All8 TT coherence/regression groups passed' in (OUT/'coherent-tt-stdout.log').read_text()
    rule50=(OUT/'rule50-stdout.log').read_text()
    assert all(marker in rule50 for marker in ('targeted_regression_failures=0','reverse_q_direct','reverse_q_score_as_eval'))
    oracle=re.search(r'All (\d+) legal-witness Boolean comparisons passed',(OUT/'legal-witness-stdout.log').read_text())
    assert oracle and int(oracle[1])>10023
    with (OUT/'bench-stdout.log').open('xb') as stdout,(OUT/'bench-stderr.log').open('xb') as stderr:
        completed=subprocess.run(bench_command,input=bench_stdin,env=environment,cwd=BUILD,
                                 stdout=stdout,stderr=stderr,timeout=300)
    signature=re.findall(r'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$',
                         (OUT/'bench-stdout.log').read_text(),re.M)
    assert completed.returncode==0 and len(signature)==1 and int(signature[0])>0, 'Missing/invalid candidate21 bench signature: '+repr(signature)
    bench_nodes=int(signature[0])
    assert bench_nodes==352313, 'Candidate21 differs from preregistered same-platform parent signature'
    checks.append({'name':'stdin-bench11-signature','exit_code':completed.returncode,'nodes':bench_nodes})
    print(json.dumps(checks[-1]),flush=True)
    disassembly=subprocess.check_output(simd_command,text=True);(OUT/'disassembly.log').write_text(disassembly)
    simd={'avx2_minmax_ymm':bool(re.search(r'v(?:max|min)ps[^\n]*ymm',disassembly)),
          'avx2_multiply_ymm':bool(re.search(r'vmulps[^\n]*ymm',disassembly)),
          'avx2_add_ymm':bool(re.search(r'vaddps[^\n]*ymm',disassembly)),
          'fused_operations':re.findall(r'\bv(?:fmadd|fmsub|fnmadd|fnmsub)\w*\b',disassembly)}
    write('simd.json',simd)
    assert all(simd[key] for key in ('avx2_minmax_ymm','avx2_multiply_ymm','avx2_add_ymm')) and not simd['fused_operations']
    after={name:sha(path) for name,path in inputs.items()};assert after==before
    assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==source_before
    write('result.json',{'status':'passed','source_and_tests_commit':COMMIT,'checks':checks,'tt_groups':8,
     'nearest_pawn_sets':int(nearest_summary[0][0]),'nearest_pawn_checks':int(nearest_summary[0][1]),'nearest_pawn_failures':0,'nearest_constexpr_assertions':6,'pawn_span_checks':int(pawn_summary[0][0]),'pawn_span_failures':0,'pawn_constexpr_assertions':3,'runtime_psqt_checks':int(runtime_summary[0][0]),'runtime_psqt_failures':0,'correction_history_checks':int(correction_summary[0][0]),'correction_history_failures':0,'rule50_targeted_failures':0,'legal_witness_comparisons':int(oracle[1]),'bench11_nodes':bench_nodes,
     'core_reference_perft_passed':True,'ownbook_transitions':ownbook_result['checks'],'wine_book_path_adaptation_only':True,'simd':simd,'input_sha256_before':before,'input_sha256_after':after,
     'source_inputs_unchanged':True,'scope':'Wine correctness and node signatures only; native hardware, speed and Elo unproven'})
except Exception as error:
    write('result.json',{'status':'failed','source_and_tests_commit':COMMIT,'checks':checks,'error':str(error),
                         'input_sha256_after':{name:sha(path) for name,path in inputs.items()}})
    raise
print('All frozen6.4.21 Windows functional, oracle, signature and SIMD checks passed',flush=True)
