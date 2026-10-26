"""Prepare a private S09 source view after the root disk/build grant.

Patch targets are owned regular copies. Other unchanged baseline inputs are
read-only build dependencies linked by absolute path, including the original
net. Never apply a patch through a source symlink. No compilation occurs here.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

FILES=Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
BASES={'L':FILES/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src',
       'Lprime':FILES/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src',
       'B':FILES/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
PATCH=Path(__file__).with_name('forge_sol_S09_buckets8_native_20261026.patch')
PATCH_SHA='bbe2561159689743357b2e9971f7cc3fe92dd1b8687e9015bb5dc1cc51656df0'
TARGETS={'CMakeLists.txt','include/forge/nnue.hpp','src/nnue.cpp',
         'tests/nnue_heads_tests.cpp','tests/nnue_heads_contract.cpp',
         'tools/nnue/heads_parity.cpp','tools/nnue/make_heads_inc.py'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


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
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--base',choices=BASES,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    assert sha(PATCH)==PATCH_SHA
    source=BASES[args.base]
    allowed=Path('/workspace/forge-pack24-20261026/S09_NATIVE_20261026')
    if not args.out.is_absolute() or args.out.resolve()!=args.out or not args.out.is_relative_to(allowed) or args.out==allowed:
        ap.error('output must be a new descendant of S09_NATIVE_20261026')
    before={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    make_source_view(source,args.out,TARGETS)
    for rel in TARGETS:
        q=args.out/rel
        assert not q.is_symlink(), 'refuse patch through baseline link'
    r=subprocess.run(['patch','-p1','-F0','--batch','-i',str(PATCH)],cwd=args.out,text=True,capture_output=True)
    (args.out/'S09_patch_apply.log').write_text(r.stdout+r.stderr)
    after={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    assert before==after,'baseline changed'
    assert r.returncode==0,r.stdout+r.stderr
    assert sha(args.out/'src/nnue_weights.inc')==before['src/nnue_weights.inc']
    receipt={'base':args.base,'baseline':str(source),'private_source':str(args.out.resolve()),'patch_sha256':PATCH_SHA,'source_before':before,'source_after':after,'baseline_unchanged':True,'owned_changed_paths':sorted(TARGETS),'unchanged_inputs_are_absolute_source_links':True,'compiler_or_engine_executions':0}
    (args.out/'S09_source_view.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'source':str(args.out),'baseline_unchanged':True,'copied_large_net':False}))


if __name__=='__main__':main()
