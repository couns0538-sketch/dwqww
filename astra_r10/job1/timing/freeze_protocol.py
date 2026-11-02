"""Freeze actual reviewed prerequisite identities, only after native checks PASS."""
import argparse,hashlib,json,pathlib,sys
from math_checks import validate_binding
R=pathlib.Path('D:/a10'); J=R/'wt/astra_r10/job1'; T=J/'timing'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    a=argparse.ArgumentParser();a.add_argument('--threads',type=int,choices=[1],required=True);a.parse_args()
    p=read(T/'protocol.template.json')
    paths={'baseline_binary':R/'inputs/lock.exe','candidate_binary':R/'b/pc1-a/src_copy/forge_ltopgo_pc1-a.exe',
        'source_manifest':R/'wt/astra_r9/evidence/c1-source.json','network':R/'c1/src/nnue_weights.inc',
        'compiler':R/'inputs/gcc-15.2-gpp.exe','original_kit':R/'kit/build_ltopgo.ps1',
        'corpus':R/'inputs/fens_12k.txt','adapter':T/'run_timing.py','uci_adapter':T/'uci_adapter.py',
        'arithmetic':T/'math_checks.py','host_topology':J/'host.json'}
    candidate=sha(paths['candidate_binary']); source_hash=sha(paths['source_manifest'])
    b=read(J/'build-proof01/REPORT.json')
    assert len(b['checks'])==9 and all(x['status']=='PASS' for x in b['checks'])
    assert b['checks'][-1]['name']=='reproducible_builds' and b['checks'][-1]['sha256']==candidate
    assert b['source_commit']=='f43a26aeed2448379fc2916b25f31ead8707b0ec'
    for label in ['smoke','sanitizer']:
        receipt=read(J/(label+'-01')/'REPORT.json')
        expected=candidate if label=='smoke' else 'a56762278935af93344680ba147a9076f63b52504e2495a686d7fe5f28a4a2aa'
        assert receipt['binary_sha256']==expected
        assert receipt['inputs_sha256'][str(paths['source_manifest'])]==source_hash
        assert all(sha(pathlib.Path(k))==v for k,v in receipt['inputs_sha256'].items())
    parity=read(J/'parity/check-launch01/stdout.log')
    assert parity['compared_rows']==12000 and parity['mismatches']==0
    assert parity['negative_control_mismatches']>0 and parity['parity_gate_satisfied'] is True
    prepared=read(R/'parity-r1/prepared.json'); builds=read(R/'parity-r1/builds.json')
    assert prepared['authoritative_manifest_sha256']==source_hash
    assert prepared['source_files']=={k.replace('\\','/'):v for k,v in read(paths['source_manifest']).items()}
    assert builds['prepared_sha256']==sha(R/'parity-r1/prepared.json')
    for info in builds['binaries'].values():assert sha(pathlib.Path(info['path']))==info['sha256']
    for name in ['prepared.json','builds.json','eval-parity.json','native-summary.log']:
        paths['diagnostic_'+name]=R/'parity-r1'/name
    record=read(R/'parity-r1/eval-parity.json')
    for role in ['scalar_binary','candidate_binary','network','native_log','scalar_trace','candidate_trace']:
        ref=record[role];path=(R/'parity-r1'/ref['path']).resolve();assert sha(path)==ref['sha256'];paths['parity_'+role]=path
    for role in ['network','trace','binary']:
        ref=record['negative_control'][role];path=(R/'parity-r1'/ref['path']).resolve();assert sha(path)==ref['sha256'];paths['negative_'+role]=path
    p['inputs']=[{'role':role,'path':str(path),'sha256':sha(path)} for role,path in paths.items()]
    p['network_sha256']=sha(paths['network'])
    proofs={'build_pair':J/'build-proof01/REPORT.json','off_on_pins':J/'build-proof01/REPORT.json',
        'perft':J/'build-proof01/REPORT.json','t1_smoke':J/'smoke-01/REPORT.json',
        'asan_ubsan':J/'sanitizer-01/REPORT.json','raw_bit_parity':J/'parity/check-launch01/stdout.log',
        'weight_negative_control':J/'parity/check-launch01/stdout.log'}
    for name,path in proofs.items():
        raw=read(path)
        assert raw['status']=='PASS',(name,raw)
        p['prerequisites'][name]={'status':'PASS','evidence_scope':'native','candidate_sha256':sha(paths['candidate_binary']),
            'path':str(path),'sha256':sha(path)}
    p['limitations']=['T4 UNVERIFIED: loaded host. No strength gate or match.',
        'Raw bits use diagnostic binaries from exact production source; sanitizer binary recovered unchanged with R9 provenance.',
        'Compiler D copy for identity only; original C toolchain performed both reviewed kit builds.']
    validate_binding(p)
    with (T/'protocol.json').open('x') as f:json.dump(p,f,indent=2)
    print('FROZEN',sha(T/'protocol.json'))
if __name__=='__main__':main()
