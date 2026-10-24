#!/usr/bin/env python3
"""Freeze a full buildable source ZIP and cumulative -p1 patch from Git blobs."""
import argparse, hashlib, json, subprocess, zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--commit',required=True);a=p.parse_args()
r=Path('/workspace/dwqww');o=r/'releases/sol-next-20261024';lock='f4911f2709bd5ae7e5fca7aea30aac5d87314a05'
commit=subprocess.check_output(['git','rev-parse',a.commit],cwd=r,text=True).strip()
roots=['.agents','AGENTS.md','CMakeLists.txt','IDEA_SOURCE.md','LICENSE','README.md','bench','include','src','tests','tools']
entries=subprocess.check_output(['git','ls-tree','-r',commit,'--',*roots],cwd=r,text=True).splitlines()
files=[];blobs={}
for line in entries:
 meta,path=line.split('\t',1);mode,kind,oid=meta.split()
 if '__pycache__' in Path(path).parts or path.endswith('.pyc'):continue
 if kind!='blob' or mode not in ['100644','100755']:raise ValueError((mode,kind,path))
 data=subprocess.check_output(['git','cat-file','blob',oid],cwd=r)
 files.append({'path':path,'mode':mode,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()});blobs[path]=data
assert blobs['src/nnue_weights.inc'] and hashlib.sha256(blobs['src/nnue_weights.inc']).hexdigest()=='74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b'
for f in ['src/nnue_int16.inc','tools/nnue_int16_parity.cpp','tools/nnue_int16_extremes.cpp','tools/nnue_null_counter_probe.cpp']:assert f in blobs
manifest={'source_commit':commit,'lock':lock,'scope':'Full buildable source/tests/tools and repository skills; historical validation/release payloads and Git objects excluded','experimental_option':'NnueInt16 check default false','acceptance':'Research source only; no speed or playing-strength acceptance','build_flags':'C++20 O3 DNDEBUG H256 FP strict march=znver5 static pthread; see CR_DRAFT and exact native receipts','files':files}
archive=o/'forge-int16-research-source.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for row in files:
  i=zipfile.ZipInfo(row['path'],(2026,10,24,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=int(row['mode'],8)<<16;z.writestr(i,blobs[row['path']])
 z.writestr('SOURCE_MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for row in files:assert z.read(row['path'])==blobs[row['path']]
patch=subprocess.check_output(['git','diff','--full-index','--no-ext-diff','--src-prefix=a/','--dst-prefix=b/',lock,commit,'--',*[x['path'] for x in files]],cwd=r)
assert b'GIT binary patch' not in patch and b'Binary files ' not in patch
patchpath=o/'int16_fix.patch';assert not patchpath.exists();patchpath.write_bytes(patch)
result={'source_commit':commit,'patch_base':lock,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'archive_bytes':archive.stat().st_size,'source_files':len(files),'patch_sha256':hashlib.sha256(patch).hexdigest(),'patch_bytes':len(patch),'scope':'Cumulative complete source delta vs lock: preserves inherited optional SIMD/alignment/completed-iteration code and buffer repair; new integer mode OFF by default','zip_all_git_blobs_verified':True,'clean_p1_verification':'PENDING independent delivery audit'}
(o/'int16-source-manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
