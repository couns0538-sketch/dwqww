#!/usr/bin/env python3
"""Archive both original boundary attempts and exact source/build inputs."""
from pathlib import Path
import hashlib,importlib.util,json,shutil
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
STAGE=Path('/workspace/.cloud-setup/double-extension-boundary-complete-stage')
STAGE.mkdir(exist_ok=False)
OUT=HERE/'archive-complete'
helper=REPO/'.github/hosted-tt-strength/archive_results.py'
expected='952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(helper)==expected
originals={}
def copy_file(p,q):
    q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);h=sha(p);assert sha(q)==h;originals[str(p)]=h
def copy_tree(p,q):
    for a in sorted(p.rglob('*')):
        if a.is_file():copy_file(a,q/a.relative_to(p))
for n in ['boundary-attempt1','boundary-attempt2']:
    copy_tree(HERE.parent/n,STAGE/'validation'/n)
for n in ['double-extension-boundary-baseline-source','double-extension-boundary-proposal-source','double-extension-boundary-baseline-build','double-extension-boundary-proposal-build']:
    copy_tree(Path('/workspace/.cloud-setup')/n,STAGE/n)
base=Path('/workspace/.cloud-setup/forge-clock-contract-release')
for n in ['forge','libforge_core.a','compile_commands.json','CMakeFiles/forge.dir/src/uci.cpp.o','CMakeFiles/forge.dir/link.txt']:
    copy_file(base/n,STAGE/'frozen-baseline'/n)
copy_file(helper,STAGE/'trusted-archive-helper.py')
(STAGE/'ORIGINALS-SHA256.json').write_text(json.dumps(originals,indent=2)+'\n')
s=importlib.util.spec_from_file_location('trusted_boundary_archive',helper);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=m.archive_results(STAGE,OUT,'double-extension-synthetic-boundary-cecf0b9');manifest=m.verify_archive(p)
for n,h in originals.items():assert sha(n)==h,n
receipt={'status':'PASS','manifest':p.name,'manifest_sha256':sha(p),'archive':manifest['archive'],'parts':manifest['parts'],'payload_files':len(manifest['files']),'payload_bytes':sum(r['size'] for r in manifest['files']),'all_copied_originals_rehashed':len(originals),'all_originals_unchanged':True,'trusted_helper_sha256':expected,'scope':'Both boundary attempts including harness failures; all six original engine cases; independent audit/oracle; frozen baseline/proposal source/core/object/executable/build provenance. No engine execution during archival.'}
(OUT/'VERIFY-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
