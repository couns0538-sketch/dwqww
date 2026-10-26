#!/usr/bin/env python3
"""Seal S27 source and closed evidence only; no engine/compiler/Git execution."""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,shutil,subprocess,sys
P=Path(__file__).resolve().parent
OUT=P/'forge_sol_S27_delivery_20261026'
POS=P/'forge_sol_S27_current_Lp_build_positive_20261026'
CMP=POS/'Lp/forge_sol_S27_native_compare_20261026'
NEG=P/'forge_sol_S27_existing_negative_native_20261026'
SOURCES=['forge_sol_S27_hygiene_20261026.py','forge_sol_S27_buildcompare_20261026.py','forge_sol_S27_known_hashes_20261026.json','forge_sol_S27_README_20261026.md']
TESTS=['test_forge_sol_S27_hygiene_20261026.py','test_forge_sol_S27_buildcompare_20261026.py']
MANIFEST='forge_sol_S27_SHA256SUMS_20261026.txt'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,obj):Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def blob(data):return {'base64':base64.b64encode(data).decode(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def closed(path):
 d=json.loads(path.read_text())
 if not isinstance(d,dict) or not str(d.get('status','')).startswith('PASS'):raise ValueError('Expected closed PASS receipt: '+str(path))
 return d

def command(argv,cwd=None):
 r=subprocess.run([str(x)for x in argv],cwd=cwd,capture_output=True)
 return {'argv':[str(x)for x in argv],'cwd':str(cwd)if cwd else None,'exit':r.returncode,'stdout':blob(r.stdout),'stderr':blob(r.stderr)}

def manifest():
 rows=[]
 for f in sorted(OUT.iterdir()):
  if not f.is_file() or f.name==MANIFEST:continue
  rows.append(sha(f)+'  '+f.name+'\n')
 (OUT/MANIFEST).write_text(''.join(rows))
 check=command(['sha256sum','-c',MANIFEST],OUT)
 if check['exit']:raise ValueError('Final manifest failed')
 return check

def select_records(extra):
 records={}
 def add(path):
  path=Path(path)
  if not path.is_file() or path.is_symlink():raise ValueError('Not a regular evidence file: '+str(path))
  relative=path.relative_to(P.parent).as_posix()
  before=path.stat();data=path.read_bytes();after=path.stat()
  if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):raise ValueError('Evidence changed during read')
  if relative in records and records[relative]!=data:raise ValueError('Evidence-path collision')
  records[relative]=data
 for f in sorted(P.iterdir()):
  if f.is_file() and f.name.startswith('forge_sol_S27_') and f.suffix in {'.py','.json','.jsonl','.stdout','.stderr','.md'}:add(f)
 for f in sorted((P/'tests').glob('*.py')):add(f)
 static=P/'forge_sol_S27_current_Lp_static_20261026'
 for folder in [static,POS]:
  for f in sorted(folder.glob('forge_sol_S27_*.json')):add(f)
 for folder in [NEG,CMP]:
  for name in ['forge_sol_S27_comparison_20261026.json','forge_sol_S27_commands_20261026.json']:add(folder/name)
 for case in ['base','candidate']:
  build=CMP/f'forge_sol_S27_{case}_build_20261026'
  for rel in ['CMakeCache.txt','compile_commands.json','CMakeFiles/forge.dir/flags.make','CMakeFiles/forge.dir/link.txt','CMakeFiles/forge.dir/build.make','CMakeFiles/forge_core.dir/flags.make','CMakeFiles/forge_core.dir/link.txt','CMakeFiles/forge_core.dir/build.make']:
   add(build/rel)
 for path in extra:
  path=Path(path)
  if path.is_dir():
   for f in sorted(path.rglob('*')):
    if f.is_file() and (f.suffix in {'.json','.stdout','.stderr','.gz'} or f.name.endswith('.txt')):
     if any(q in f.name.casefold() for q in ['license','agents']) or f.suffix in {'.zip','.xz','.o','.a','.exe'}:raise ValueError('Disallowed extra evidence payload')
     add(f)
  else:add(path)
 return records

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--native-final',type=Path);ap.add_argument('--native-review',type=Path);ap.add_argument('--extra',type=Path,action='append',default=[]);ap.add_argument('--attach-binding',type=Path);a=ap.parse_args()
 if a.attach_binding:
  binding=closed(a.attach_binding);target=OUT/'forge_sol_S27_delivery_binding_review_20261026.json'
  if not OUT.is_dir() or target.exists():raise ValueError('Invalid attach state')
  previous=(OUT/MANIFEST).read_bytes();previous_sha=hashlib.sha256(previous).hexdigest();target.write_bytes(a.attach_binding.read_bytes());check=manifest()
  dump(P/'forge_sol_S27_final_seal_20261026.json',{'status':'PASS_FINAL_DELIVERY_SEALED','folder':str(OUT),'files':len(list(OUT.iterdir())),'manifest_sha256':sha(OUT/MANIFEST),'prior_manifest_sha256':previous_sha,'binding_sha256':sha(target),'check':check})
  print('SEALED',len(list(OUT.iterdir())),sha(OUT/MANIFEST));return
 if a.native_final is None or a.native_review is None:raise ValueError('Closed native-final and independent-review receipts required')
 native=closed(a.native_final);review=closed(a.native_review);positive=closed(CMP/'forge_sol_S27_comparison_20261026.json');main_result=closed(POS/'forge_sol_S27_result_20261026.json')
 extra_path=P/'forge_sol_S27_native_extra_qualification_20261026/forge_sol_S27_native_extra_receipt_20261026.json';extra=closed(extra_path)
 if not isinstance(extra.get('profiles'),list) or len(extra['profiles'])!=2:raise ValueError('Unexpected extra-qualification schema')
 for profile in extra['profiles']:
  if profile.get('perft5_nodes')!=[4865609,193690690] or profile.get('NNUE_FMA')!=0 or profile.get('whole_exe_FMA')!=0:raise ValueError('Extra perft/FMA qualification incomplete')
 if positive.get('mode') is None or not isinstance(positive.get('cases'),list) or len(positive['cases'])!=2:raise ValueError('Unexpected comparator schema')
 cases=positive['cases'];refs={11:308972,13:745494,16:2460422,20:11901452,22:31111774}
 for case in cases:
  if case.get('status')!='PASS' or not case.get('binary_identity_unchanged'):raise ValueError('Comparator case did not close')
  if {int(k):v['normalized']['nodes']for k,v in case['bench'].items()}!=refs:raise ValueError('Fixed-reference mismatch')
  if any(v.get('status')!='PASS'for v in case['bench'].values()) or case['uci']['status']!='PASS' or case['symbols']['status']!='PASS':raise ValueError('Incomplete case checks')
 if main_result['findings']:raise ValueError('Positive main CLI has findings')
 negative=json.loads((NEG/'forge_sol_S27_comparison_20261026.json').read_text())
 if negative.get('status')!='FAIL':raise ValueError('Expected retained-negative rejection')
 source_review=closed(P/'forge_sol_S27_main_final_review_20261026.json');helper_review=closed(P/'forge_sol_S27_helper_final_review_20261026.json');metadata_review=closed(P/'forge_sol_S27_helper_metadata_review_addendum_20261026.json')
 if sha(P/'forge_sol_S27_hygiene_20261026.py')!=source_review['source_sha256']:raise ValueError('Main source changed after review')
 if OUT.exists():raise ValueError('Delivery output must be NEW')
 records=select_records([a.native_final,a.native_review,extra_path.parent,*a.extra])
 OUT.mkdir()
 for name in SOURCES:shutil.copyfile(P/name,OUT/name)
 for name in TESTS:shutil.copyfile(P/'tests'/name,OUT/name)
 shutil.copyfile(Path('/workspace/dwqww/releases/forge_sol_pack31_20261025/S25_v2/forge_sol_S25_raw_restore_v2_20261025.py'),OUT/'forge_sol_S27_raw_restore_20261026.py')
 restore=OUT/'forge_sol_S27_raw_restore_20261026.py';restore.write_text(restore.read_text().replace('dated S25','dated S27'))
 archive=OUT/'forge_sol_S27_raw_evidence_20261026.jsonl.gz';rows=[]
 with archive.open('wb')as raw:
  with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0)as zipped:
   for name,data in sorted(records.items()):
    row={'relative_path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'base64':base64.b64encode(data).decode()};zipped.write((json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode());rows.append({k:row[k]for k in ['relative_path','bytes','sha256']})
 index={'schema':'S27_original_bytes_base64_v1','archive':archive.name,'archive_sha256':sha(archive),'records':len(rows),'original_bytes':sum(r['bytes']for r in rows),'files':rows,'scope':'Selected original source/test/control/native/recipe/review bytes. Full source trees, network contents, engine/object/cache files and generated hostile ZIP payloads are excluded. Original private input/candidate trees and compiled binaries remain local.'};dump(OUT/'forge_sol_S27_evidence_index_20261026.json',index)
 restored=P/'forge_sol_S27_delivery_restore_20261026'
 restored_run=command([sys.executable,'-B',restore,'--archive',archive,'--index',OUT/'forge_sol_S27_evidence_index_20261026.json','--out',restored])
 if restored_run['exit']:raise ValueError('Restore failed')
 for name,data in records.items():
  if (restored/name).read_bytes()!=data:raise ValueError('Restored byte mismatch')
 collision=command([sys.executable,'-B',restore,'--archive',archive,'--index',OUT/'forge_sol_S27_evidence_index_20261026.json','--out',restored])
 if collision['exit']==0:raise ValueError('Restore accepted an existing directory')
 dump(OUT/'forge_sol_S27_restore_verification_20261026.json',{'status':'PASS_ALL_ORIGINAL_BYTES_RESTORED_AND_COMPARED','records':len(records),'original_bytes':index['original_bytes'],'restore':restored_run,'existing_directory_rejected':collision,'native_executions':0})
 for src,name in [(P/'forge_sol_S27_main_final_review_20261026.json','forge_sol_S27_source_review_20261026.json'),(P/'forge_sol_S27_helper_final_review_20261026.json','forge_sol_S27_helper_review_20261026.json'),(P/'forge_sol_S27_helper_metadata_review_addendum_20261026.json','forge_sol_S27_helper_metadata_review_20261026.json'),(a.native_final,'forge_sol_S27_native_qualification_20261026.json'),(a.native_review,'forge_sol_S27_native_review_20261026.json'),(P/'forge_sol_S27_existing_skill_reference_proof_20261026.json','forge_sol_S27_skill_proof_20261026.json')]:shutil.copyfile(src,OUT/name)
 continuation={'status':'S27_QUALIFIED_WAITING_ROOT_PUBLICATION','source_sha256':{n:sha(OUT/n)for n in SOURCES+TESTS},'native_final_sha256':sha(a.native_final),'native_review_sha256':sha(a.native_review),'positive_CLI':'PASS on current Lprime with an explicitly empty-history S25 test-only known patch','accepted_engine':'h256_e12 unchanged; S27 is validation tooling, no engine patch/adoption','raw':{'records':len(records),'archive_sha256':sha(archive)},'not_claimed':['Fresh full CTest/ASan unless separately qualified in native-final','Native Windows/PC execution','Playing-strength/speed/Elo gain','New/global skill installation'],'next':'Root completes independent document binding, publication and per-file immutable downloads. Then S06 in saved order; preserve all S27 failures and exact controls.'};dump(OUT/'forge_sol_S27_continuation_20261026.json',continuation)
 # Source and final evidence identities are explicit; detailed native schema remains preserved verbatim.
 report=['# Forge S27 patch hygiene — 2026-10-26','','The standalone source checker and optional default-build comparator are implemented. All 47 main/static tests and the then-current combined 58-test suite pass. Actual historical buffix and Job C controls pass; Job A counters, advertised option and bench statistics each produce findings. No engine/backend change, speed or Elo gain is claimed. Accepted h256_e12 is unchanged. Publication is UNVERIFIED until root performs immutable GitHub readbacks.','','The normal CLI loads the bundled full-SHA history. Explicit empty history is reserved for labelled controlled tests. Repeated raw patch hashes, contained patch hashes and canonical ZIP-member content hashes are checked independently of filenames. Path/ZIP limits, actual Git-check/GNU-F0 application, exact changed-target sets, immutable source inventories and literal registration metadata are recorded. Static guard/configuration analysis is deliberately bounded; unsupported bracket/multiline CMake grammar fails closed. It is not a full C++/CMake/include interpreter, semantic proof or arbitrary-code sandbox.','','|Check|Status|Scope|','|---|---|---|','|Main/static suite|PASS47/47|Real supplied controls plus source/path/ZIP/history/guard tests|','|Combined tool suite|PASS58/58|47 main plus11 helper parser/integrity tests at freeze|','|Actual buffix/Job C positives|PASS|Explicit historical pre-patch file views and empty history; current merged inputs never reset|','|Actual Job A default defects|PASS expected rejection|Each of counters, advertised runtime option and bench statistics detected|','|Generated hostile ZIP|PASS expected rejection|Runtime fixture; original unavailable historical ZIP is not claimed tested|','|Known patch on full current Lprime|PASS|Actual main CLI plus Git/GNU-F0, explicit known-control empty history|','|Fresh default Release build comparison|PASS|Two fresh forge-only builds; all five fixed references, strict UCI/symbol equality and stable binary hashes|','|Retained actual default-defect negative|PASS expected rejection|Executed helper47d353 source retained and bound to metadata-only successor; no backend build or activation|','|Perft5 and FMA qualification|PASS fresh|Both new ELFs:4865609/193690690; NNUE-scoped0 and whole-executable0, original streams retained|','|Full new CTest/ASan matrix|NOT RUN|Only exact canonical prior qualification can be inherited; fresh engine-wide suites are not claimed|','|Windows/PC speed/Elo|UNVERIFIED / UNPROVEN|No PC or strength result|','','## Frozen source and native identity','']
 for n in SOURCES+TESTS:report.append('- '+n+': `'+sha(OUT/n)+'`')
 report+=['','The exact user baseline is code `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus the supplied h256_e12 network overlay; the raw commit network differs. Fixed d11/13/16/20/22 references remain308972/745494/2460422/11901452/31111774. Both fresh Release comparison cases pass every reference and strict default protocol/symbol checks. Their actual executable SHA256s are:','']
 for case in cases:report.append('- `'+case['sha256']+'`, pre/post unchanged='+str(case['binary_identity_unchanged'])+'.')
 report+=['','This native build comparison is current Lprime versus the same current tree plus the already-known S25 test-only patch with its switch left OFF. It is not a new algorithm candidate and does not include a B build. Empty history is explicit for this already-known regression control, while the ordinary CLI uses the bundled history. Both new ELF hashes equal the canonical Lprime engine; prior source-bound current S25 qualification may be inherited explicitly, but no new full CTest or ASan run is claimed.','','The fresh extra qualification records two perft totals and NNUE-scoped/whole FMA0 for each new ELF, with pre/post engine hashes stable. Its exact receipt SHA256 is `'+sha(extra_path)+'`.']
 report+=['','The comparator recipe and actual CMakeCache, compile_commands and forge/core compile/link recipes are retained with source/header/network inventories. Only the forge target was built; a full fresh CTest/ASan result is not inferred from compiler success. Exact canonical binary identity can support separately labelled inherited qualification. Numeric NPS/time fields are preserved as original raw output, never interpreted as speed evidence.','','The retained negative is a source-bound previously built shelved default-OFF executable. Its numeric d11 gate passes while strict post-summary bytes, typed UCI metadata and symbol comparisons reject it. It actually ran helper SHA256 `47d3534f01d7b716c6bd3b624be6c55e8afa640701c621a9ffc9fa3654393ee6`; the exact executed source is retained. Final helper SHA256 `9ec5f4a4ee64c5e583121ab8a5c9abe5100eabb240ee94daa8af8776489943b3` changes only the normal-child-exit metadata predicate, with a cryptographically verified single-delta binding. The negative was not rerun under that final helper hash. Its candidate is a static znver5 build while the canonical base is dynamic x86-64-v3; symbol differences are therefore compatibility findings, not isolated proof of backend symbol leakage. The three Job A source-default defects are established by the static source controls; the actual retained executable independently demonstrates the tail and typed extra-option defects. The full fresh positive uses the final helper. This is a new S27 comparison of a retained fixture, not a backend rebuild/activation or new chess experiment. Original generated license fixture payloads, full baseline/candidate source trees, engine binaries, net data, object/compiler caches, ZIPs and instruction files are not delivered.','','## Preserved attempts and skills','','Original stub RED, null-return/timeout false-safe controls, binary integrity metadata checks, path/guard/header/ZIP/history failures, CMake quote-overreach failure and later corrected GREEN controls are preserved. A GREEN word in an old filename does not turn its actual failed unittest output into a pass. Packaging read-only schema/typing observer errors are preserved separately from native outcomes. Every claim above is bound to final source/review hashes.','','Existing repository-local SIMD validation guidance was improved from real preprocessor false-safe controls. See the separate skill proof for exact before/after guide hashes and command evidence. It is reference maintenance, not a new or globally installed skill. Sources/ideas are the user S27 specification, reviewed Forge inputs and existing original Forge S25 contract design, plus standard Python/Git/GNU patch behavior; no foreign engine code or tuned chess constants are used.','','## Evidence and continuation','',f'The lossless archive contains {len(records)} selected original-byte records / {index["original_bytes"]} bytes. Every record was restored to a NEW directory and compared to its original; existing output was rejected. Full raw commands, original streams, compile recipes, protocols, source identities and independent reviews are indexed. Cache/build/source payloads referenced by recipes remain local-only.','','```sh','sha256sum -c '+MANIFEST,'python3 -B forge_sol_S27_raw_restore_20261026.py --archive '+archive.name+' --index forge_sol_S27_evidence_index_20261026.json --out NEW_OUTPUT_FOLDER','```','','The tool README gives normal-candidate and explicitly historical-control commands. Next: independent final document binding, root commit/push and per-file immutable readbacks, then S06. No accepted engine or playing-strength change follows from this validation tool.']
 (OUT/'forge_sol_S27_report_20261026.md').write_text('\n'.join(report)+'\n')
 shutil.copyfile(Path(__file__),OUT/Path(__file__).name)
 check=manifest();dump(P/'forge_sol_S27_pre_binding_seal_20261026.json',{'status':'PASS_PRE_BINDING_DELIVERY_ASSEMBLED','folder':str(OUT),'files':len(list(OUT.iterdir())),'manifest_sha256':sha(OUT/MANIFEST),'archive_sha256':sha(archive),'records':len(records),'check':check})
 print('ASSEMBLED',len(list(OUT.iterdir())),len(records),sha(OUT/MANIFEST))
if __name__=='__main__':main()
