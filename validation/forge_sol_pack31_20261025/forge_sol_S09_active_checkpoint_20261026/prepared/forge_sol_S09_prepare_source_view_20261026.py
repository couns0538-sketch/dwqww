"""Prepare a private S09 source view after the root disk/build grant.

Patch targets are owned regular copies. Unchanged inputs use ordinary symlinks,
which do not enforce read-only access. Force bytecode off in every runtime and
verify the complete frozen baseline inventory after runtime. No compilation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import os
import sys

FILES=Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
BASES={'L':FILES/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src',
       'Lprime':FILES/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src',
       'B':FILES/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
PATCH=Path(__file__).with_name('forge_sol_S09_native_delta_20261026.patch')
PATCH_SHA='4e148af7db21b9531bb89353ad89323b501421c0f0ecff4a673b79a5a2ff9cc7'
STEP1=FILES/'17_buckets8_step1/fc_buckets8_h256e12/fc_buckets8_h256e12.patch'
STEP1_SHA='ed28132d48b75496732f0ecf25753ad869787c84a4939aaf004b3de8580a9704'
BASELINE_MANIFEST=Path(__file__).with_name('forge_sol_S09_original_baselines_20261026.json')
BASELINE_SHA='ba6be5afd8fa0608979df9fd9a92500e05f94ed31f81b5b79b61021f56e72e02'
TARGETS={'CMakeLists.txt','include/forge/nnue.hpp','src/nnue.cpp',
         'tests/nnue_heads_tests.cpp','tests/nnue_heads_contract.cpp',
         'tools/nnue/heads_parity.cpp','tools/nnue/make_heads_inc.py'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def inventory(source):
    source=Path(source)
    return {p.relative_to(source).as_posix():sha(p) for p in sorted(source.rglob('*')) if p.is_file()}


def verify_inventory(source,expected):
    actual=inventory(source)
    new=sorted(actual.keys()-expected.keys());missing=sorted(expected.keys()-actual.keys())
    modified=sorted(k for k in actual.keys()&expected.keys() if actual[k]!=expected[k])
    return {'unchanged':not(new or missing or modified),'new':new,'missing':missing,'modified':modified}


def frozen_baselines():
    if sha(BASELINE_MANIFEST)!=BASELINE_SHA:raise ValueError('frozen baseline manifest changed')
    data=json.loads(BASELINE_MANIFEST.read_text())['baselines']
    if set(data)!=set(BASES) or any(v['root']!=str(BASES[k]) for k,v in data.items()):raise ValueError('baseline roots differ')
    return data


def verify_all_baselines():
    return {k:verify_inventory(v['root'],v['files']) for k,v in frozen_baselines().items()}


def selected_dependency_patch():
    if sha(STEP1)!=STEP1_SHA:raise ValueError('original reviewed step1 changed')
    lines=STEP1.read_text().splitlines(keepends=True);result='';i=0
    while i<len(lines):
        if not lines[i].startswith('--- '):i+=1;continue
        name=lines[i+1][4:].split('\t',1)[0].strip();j=i+2
        while j<len(lines) and not lines[j].startswith(('diff -','--- ')):j+=1
        if name not in {'CMakeLists.txt','src/nnue_weights.inc'}:
            if name not in TARGETS:raise ValueError('unexpected selected dependency target')
            new=name.startswith(('tests/','tools/'))
            result+='diff --git a/'+name+' b/'+name+'\n'+('new file mode 100644\n' if new else '')+'--- '+('/dev/null' if new else 'a/'+name)+'\n+++ b/'+name+'\n'+''.join(lines[i+2:j])
        i=j
    return result


def integrate_original_cmake(text):
    # Exact reviewed declarations; bind unique anchors to preserve B's tests.
    targets='add_executable(forge_nnue_heads_tests tests/nnue_heads_tests.cpp)\ntarget_link_libraries(forge_nnue_heads_tests PRIVATE forge_core Threads::Threads)\n\n'
    anchor='add_executable(forge_bench bench/benchmark.cpp)'
    test='add_test(NAME forge_pv_metadata_tests COMMAND forge_pv_metadata_tests)\n'
    if text.count(anchor)!=1 or text.count(test)!=1 or 'forge_nnue_heads_tests' in text:raise ValueError('step1 CMake anchor is not unique/unpatched')
    return text.replace(anchor,targets+anchor).replace(test,test+'add_test(NAME forge_nnue_heads_tests COMMAND forge_nnue_heads_tests)\n')


def make_source_view(source,out,changed):
    source=Path(source).resolve();out=Path(out)
    if out.resolve().is_relative_to(source):raise ValueError('output must not be inside frozen source')
    for rel in changed:
        p=Path(rel)
        if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe patch target')
    entries=sorted(source.rglob('*'))
    if any(p.is_symlink() for p in entries):raise ValueError('source symlink is outside this frozen source-view contract')
    out.mkdir(parents=False,exist_ok=False)
    for p in entries:
        rel=p.relative_to(source);q=out/rel
        if p.is_dir():q.mkdir(parents=True,exist_ok=True)
        elif p.is_file():
            q.parent.mkdir(parents=True,exist_ok=True)
            if rel.as_posix() in changed:shutil.copy2(p,q)
            else:q.symlink_to(p)


def main():
    os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--base',choices=BASES);ap.add_argument('--out',type=Path);ap.add_argument('--verify-only',action='store_true');args=ap.parse_args()
    audits=verify_all_baselines()
    if args.verify_only:
        print(json.dumps({'baseline_audit':audits,'all_unchanged':all(v['unchanged'] for v in audits.values())},sort_keys=True));return 0 if all(v['unchanged'] for v in audits.values()) else 2
    if not args.base or args.out is None:ap.error('--base and --out are required for preparation')
    if not all(v['unchanged'] for v in audits.values()):raise ValueError('baseline inventory changed: '+json.dumps(audits))
    assert sha(PATCH)==PATCH_SHA
    source=BASES[args.base]
    allowed=Path('/workspace/forge-pack24-20261026/S09_NATIVE_20261026')
    if not args.out.is_absolute() or args.out.resolve()!=args.out or not args.out.is_relative_to(allowed) or args.out==allowed:
        ap.error('output must be a new descendant of S09_NATIVE_20261026')
    before=inventory(source)
    make_source_view(source,args.out,TARGETS)
    for rel in TARGETS:
        q=args.out/rel
        assert not q.is_symlink(), 'refuse patch through baseline link'
    dependency=selected_dependency_patch()
    r=subprocess.run(['patch','-p1','-F0','--batch','--no-backup-if-mismatch'],input=dependency,cwd=args.out,text=True,capture_output=True)
    (args.out/'S09_dependency_apply.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError(r.stdout+r.stderr)
    cmake=args.out/'CMakeLists.txt';cmake.write_text(integrate_original_cmake(cmake.read_text()))
    r=subprocess.run(['patch','-p1','-F0','--batch','--no-backup-if-mismatch','-i',str(PATCH)],cwd=args.out,text=True,capture_output=True)
    (args.out/'S09_delta_apply.log').write_text(r.stdout+r.stderr)
    after=inventory(source)
    assert before==after,'baseline changed'
    assert r.returncode==0,r.stdout+r.stderr
    assert sha(args.out/'src/nnue_weights.inc')==before['src/nnue_weights.inc']
    assert all(v['unchanged'] for v in verify_all_baselines().values())
    receipt={'base':args.base,'baseline':str(source),'private_source':str(args.out.resolve()),'new_delta_sha256':PATCH_SHA,'original_step1_sha256':STEP1_SHA,'selected_dependency_sha256':hashlib.sha256(dependency.encode()).hexdigest(),'dependency_selection':'exact original core/header/test/helper payloads; original CMake declarations integrated by unique anchors; embedded replicated-net hunk omitted so default stored-head count remains1','source_before':before,'source_after':after,'baseline_unchanged':True,'owned_changed_paths':sorted(TARGETS),'unchanged_inputs_are_ordinary_source_symlinks':True,'PYTHONDONTWRITEBYTECODE':'1','post_runtime_inventory_audit_required':True,'compiler_or_engine_executions':0}
    (args.out/'S09_source_view.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'source':str(args.out),'baseline_unchanged':True,'copied_large_net':False}))


if __name__=='__main__':raise SystemExit(main())
