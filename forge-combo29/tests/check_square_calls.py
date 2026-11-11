#!/usr/bin/env python3
"""Immutable-lock diagnostic counts, not timing. Only src/include snapshots."""
import argparse, hashlib, json, pathlib, re, subprocess, tempfile
LOCK='16833ecc03b425586f91f4c8834dea8807bf4c22'
p=argparse.ArgumentParser(); p.add_argument('--run', action='store_true'); p.add_argument('--output',type=pathlib.Path,required=True); p.add_argument('--codegen',type=pathlib.Path,required=True); a=p.parse_args()
if not a.run: p.exit(message='Default off; coordinate CPU availability before execution.\n')
repo=pathlib.Path(__file__).resolve().parents[2]
def git(*args): return subprocess.check_output(['git','-C',str(repo),*args])
def sha(x): return hashlib.sha256(x).hexdigest()
assert git('branch','--show-current').decode().strip()=='dot/review-20261110'
preamble=r'''
#include <cstdio>
namespace {
struct CheckSquareProbe {
    unsigned long long calls[2]{}, absent_bishop[2]{}, absent_rook[2]{}, both_absent[2]{};
    int stage=0;
    ~CheckSquareProbe() {
        for (int i=0;i<2;++i) std::fprintf(stderr,"CHECK_SQUARE_COUNTS {\"stage\":%d,\"calls\":%llu,\"absent_bishop_or_queen\":%llu,\"absent_rook_or_queen\":%llu,\"both_absent\":%llu}\n",i,calls[i],absent_bishop[i],absent_rook[i],both_absent[i]);
    }
} check_square_probe;
}
'''
entry='    void init_check_squares() {'
instrument=r'''
        const auto probe_us = board_.side_to_move();
        const bool probe_b = !(board_.pieces(probe_us, Bishop) | board_.pieces(probe_us, Queen));
        const bool probe_r = !(board_.pieces(probe_us, Rook) | board_.pieces(probe_us, Queen));
        const int probe_stage = check_square_probe.stage;
        ++check_square_probe.calls[probe_stage];
        check_square_probe.absent_bishop[probe_stage] += probe_b;
        check_square_probe.absent_rook[probe_stage] += probe_r;
        check_square_probe.both_absent[probe_stage] += probe_b && probe_r;
'''
flags=['-std=c++20','-O3','-DNDEBUG','-DFORGE_NNUE_HIDDEN=256','-DFORGE_EXPOSE_TUNABLES=1','-DFORGE_SPD_TT_NOTLS=1','-DFORGE_SPD_NO_ZERO_MOVELISTS=2','-DFORGE_SPD_PREFETCH_EARLY=1','-DFORGE_SPD_SLIDER_PEXT=1','-DFORGE_SPD_NNUE_ZMM=1','-ffp-contract=off','-fno-fast-math','-march=x86-64-v4','-pthread']
records=[]; assembly=[]
with tempfile.TemporaryDirectory(prefix='forge-check-square-') as tmp:
    root=pathlib.Path(tmp); manifest={}
    for name in git('ls-tree','-r','--name-only',LOCK,'forge-combo29/src','forge-combo29/include').decode().splitlines():
        assert pathlib.Path(name).suffix in ('.cpp','.h','.hpp','.inc')
        data=git('show',f'{LOCK}:{name}'); dest=root/pathlib.Path(name).relative_to('forge-combo29'); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data); manifest[name]=sha(data)
    source=root/'src/search.cpp'; original=source.read_text(); assert original.count(entry)==1
    inst=preamble+original.replace(entry,entry+instrument).replace('    void generate_quiets() {','    void generate_quiets() {\n        check_square_probe.stage=0;').replace('    void generate_evasions() {','    void generate_evasions() {\n        check_square_probe.stage=1;')
    for speed in (0,1):
        cfg=flags+[f'-DFORGE_SEARCH_SPEED2={speed}','-I'+str(root/'include')]
        for variant,contents in [('baseline',original),('instrumented',inst)]:
            source.write_text(contents); exe=root/f'{variant}-{speed}'
            command=['g++',*cfg,*map(str,sorted((root/'src').glob('*.cpp'))),'-o',str(exe)]
            subprocess.run(command,check=True,timeout=240)
            if variant=='baseline':
                obj=root/f'search-{speed}.o'; subprocess.run(['g++',*cfg,'-c',str(source),'-o',str(obj)],check=True)
                dis=subprocess.check_output(['objdump','-drC',str(obj)]).decode()
                # Retain complete MovePicker sections including relocations, not full unrelated object.
                sections=re.split(r'(?=^[0-9a-f]+ <)',dis,flags=re.M)
                chosen=[s for s in sections if 'MovePicker' in s.split('\n',1)[0]]
                assembly.append(f'PRISTINE LOCK SPEED2={speed}; object sha256={sha(obj.read_bytes())}\n'+''.join(chosen))
            for mode,pin in [('true',3024920),('false',2448617)]:
                commands=f'setoption name Threads value 1\nsetoption name OwnBook value false\nsetoption name UseNNUE value {mode}\nbench 16\nquit\n'
                result=subprocess.run([str(exe)],input=commands,text=True,capture_output=True,check=True,timeout=120,cwd=root)
                nodes=re.findall(r'info string bench depth 16 nodes (\d+)',result.stdout); assert nodes==[str(pin)],(speed,variant,mode,nodes)
                counts=[json.loads(x) for x in re.findall(r'^CHECK_SQUARE_COUNTS (.+)$',result.stderr,re.M)]
                assert len(counts)==(2 if variant=='instrumented' else 0)
                records.append(dict(speed2=speed,variant=variant,nnue=mode,nodes=int(nodes[0]),counts=counts,command=command,binary_sha256=sha(exe.read_bytes()),stdin=commands,stdout=result.stdout,stderr=result.stderr))
                print(speed,variant,mode,nodes,counts,flush=True)
    receipt=dict(lock=LOCK,purpose='Counts only; all reported engine times invalid for performance inference',compiler=subprocess.check_output(['g++','--version']).decode(),flags=flags,source_manifest=manifest,instrumented_search_sha256=sha(inst.encode()),script_sha256=sha(pathlib.Path(__file__).read_bytes()),runs=records)
    a.output.write_text(json.dumps(receipt,indent=2)+'\n'); a.codegen.write_text('\n'.join(assembly))
