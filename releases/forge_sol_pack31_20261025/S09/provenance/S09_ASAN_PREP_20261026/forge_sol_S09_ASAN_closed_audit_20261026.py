"""Read-only source/artifact/raw-output audit of a CLOSED S09 sanitizer run."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import xml.etree.ElementTree as ET

ROOT=Path('/tmp/forge_sol_S09_native_20261026')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--tag',choices=('Lprime','B'),required=True);a=ap.parse_args()
    paths={k:ROOT/(a.tag+'_ASAN_'+v+'_once_20261026') for k,v in [('build','static'),('first','FIRST'),('full','FULL')]}
    files={k:p/('forge_sol_S09_build_result_20261026.json' if k=='build' else 'forge_sol_S09_runtime_result_20261026.json') for k,p in paths.items()}
    r={k:json.loads(p.read_text()) for k,p in files.items()};b,f,u=r['build'],r['first'],r['full'];expected=16 if a.tag=='Lprime' else 17
    assert b['status']=='PASS_BUILD_ONLY' and f['status']==u['status']=='PASS'
    assert all(x['source_unchanged'] for x in r.values()) and f['all_artifacts_unchanged'] and u['all_artifacts_unchanged']
    assert f['all_engine_groups_closed'] and u['all_engine_groups_closed']
    assert all(x['profile']=='ASAN_UBSAN_STATIC_O2_DEBUG' for x in r.values())
    assert f['build_receipt_sha256']==u['build_receipt_sha256']==sha(files['build'])
    assert f['commands_sent']==['bench 11','quit'] and f['no_UCI_before_bench'] and f['bench_nodes']==308972
    assert (paths['first']/'FIRST_bare11.stdin').read_bytes()==b'bench 11\nquit\n'
    for p in paths.values():
        for stderr in p.glob('*.stderr'):
            if p!=paths['build']:assert stderr.stat().st_size==0,stderr
        for receipt in p.glob('*.receipt.json'):
            data=json.loads(receipt.read_text());assert type(data['returncode']) is int and data['returncode']==0
            assert data.get('stdout_complete',True) and data.get('stderr_complete',True)
            if 'leader_reaped' in data:assert data['leader_reaped'] and not data['all_group_members_after_reap'] and not data['stop_reason']
    for name,artifact in b['target_artifacts'].items():
        p=Path(artifact['path']);assert sha(p)==artifact['sha256'] and p.stat().st_size==artifact['bytes']
        with p.open('rb') as stream:assert stream.read(4)==(b'!<ar' if name=='core_archive' else b'\x7fELF')
    source=Path(b['source']);current={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    assert current==b['source_before']==b['source_after']==f['source_before']==f['source_after']==u['source_before']==u['source_after']
    build=paths['build']/'build';commands=json.loads((build/'compile_commands.json').read_text())
    for row in commands:
        tokens=row.get('arguments') or shlex.split(row['command'])
        assert {'-O2','-g','-DNDEBUG','-fsanitize=address,undefined','-fno-omit-frame-pointer',
            '-fno-fast-math','-ffp-contract=off','-DFORGE_NNUE_HIDDEN=256','-march=x86-64-v3','-mtune=znver5'}.issubset(tokens)
        assert all(not x.startswith(('-flto','-fprofile','-fauto-profile','-fno-sanitize')) and x!='-ffast-math' for x in tokens)
    full=paths['full'];cases=list(ET.parse(full/'full_ctest.xml').getroot().iter('testcase'))
    assert len(cases)==expected and not any(x.find('failure') is not None or x.find('error') is not None or x.find('skipped') is not None for x in cases)
    inventory=json.loads((full/'CTest_inventory_before.stdout').read_text());after=json.loads((full/'CTest_inventory_after.stdout').read_text())
    assert inventory==after and sorted(x['name'] for x in inventory['tests'])==sorted(x.attrib['name'] for x in cases)
    raw=(full/'full_CTest.stdout').read_text();lines=[re.sub(r'^\d+:\s?','',x) for x in raw.splitlines()]
    known=[x for x in lines if x.startswith('KNOWN_FAILURE:')]
    assert len(known)==4 and not any(x.startswith(('FAIL:','PIN_MISMATCH:')) for x in lines)
    assert f'100% tests passed, 0 tests failed out of {expected}' in raw
    assert re.findall(rb'(?m)^info string bench depth 11 nodes (\d+) time \d+ nps \d+\r?$',(full/'bench_11.stdout').read_bytes())==[b'308972']
    for name,nodes in [('startpos',197281),('kiwipete',4085603)]:
        assert re.findall(rb'(?m)^nodes (\d+)\r?$',(full/('perft4_'+name+'.stdout')).read_bytes())==[str(nodes).encode()]
    for name in ('FMA_NNUE_object','FMA_NNUE_scope_ELF'):
        x=json.loads((full/(name+'.stdout')).read_text());assert x['status']=='PASS' and type(x['fma_count']) is int and x['fma_count']==0
    assert not any(re.match(r'^\s*[0-9a-fA-F]+:\s+vf(?:n)?m(?:add|sub)[a-z0-9]*\b',x) for x in (full/'whole_ELF_assembly.stdout').read_text().splitlines())
    assert f['runtime_environment']==u['runtime_environment']=={'ASAN_OPTIONS':'detect_leaks=1:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1'}
    assert max(f['maximum_observed_owned_RSS_bytes'],u['maximum_observed_owned_RSS_bytes'],b['memory_protocol']['maximum_observed_owned_RSS_bytes'])<=4*1024**3
    result={'status':'PASS_CLOSED_ASAN_RAW_AUDIT','tag':a.tag,'audit_source_sha256':sha(__file__),
        'result_sha256':{k:sha(p) for k,p in files.items()},'source_files':len(current),'runtime_artifacts':len(b['target_artifacts']),
        'actual_CTest_cases':expected,'known_lines':known,'new_failures':0,'bench11_nodes':308972,
        'startpos_perft4':197281,'kiwipete_perft4':4085603,'FMA':0,'source_and_artifacts_unchanged':True,
        'ownership_receipts':len(f['engine_process_ownership'])+len(u['engine_process_ownership']),
        'build_elapsed_seconds':b['elapsed_seconds'],'first_elapsed_seconds':f['elapsed_seconds'],'full_elapsed_seconds':u['elapsed_seconds'],
        'build_max_sampled_owned_RSS_bytes':b['memory_protocol']['maximum_observed_owned_RSS_bytes'],
        'runtime_max_sampled_owned_RSS_bytes':max(f['maximum_observed_owned_RSS_bytes'],u['maximum_observed_owned_RSS_bytes']),
        'engine_sha256':b['target_artifacts']['forge']['sha256'],'scope':'actual ASan/UBSan correctness; no speed/Elo/Windows claim; build-only engine_executions0 is historical at build time'}
    target=full/('forge_sol_S09_ASAN_'+a.tag+'_closed_audit_20261026.json')
    with target.open('x') as output:json.dump(result,output,indent=2);output.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
