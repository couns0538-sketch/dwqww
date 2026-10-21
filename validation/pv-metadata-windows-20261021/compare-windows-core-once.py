"""Root-authorized read-only COFF/GNU AR comparison; never runs an engine/build."""
import datetime,hashlib,json,pathlib
HERE=pathlib.Path(__file__).resolve().parent
PARENT=pathlib.Path('/workspace/.cloud-setup/windows6421-build/libforge_core.a')
CANDIDATE=pathlib.Path('/workspace/.cloud-setup/windows6422-build/libforge_core.a')
EXPECTED={'bitboard.cpp.obj','board.cpp.obj','book.cpp.obj','eval.cpp.obj','eval_params.cpp.obj','nnue.cpp.obj','search.cpp.obj'}
sha=lambda data:hashlib.sha256(data).hexdigest()
def read_archive(path):
 data=path.read_bytes();assert data[:8]==b'!<arch>\n';pos=8;names=b'';objects={};formats={};tables=[]
 while pos<len(data):
  assert pos+60<=len(data)
  head=data[pos:pos+60];assert head[58:60]==b'`\n'
  name=head[:16].decode('ascii').strip();size=int(head[48:58]);assert size>=0
  pos+=60;assert pos+size<=len(data)
  payload=data[pos:pos+size];pos+=size+(size%2)
  if name=='//':names=payload;tables.append(payload.hex());continue
  if name in ('/','/SYM64/'):continue
  encoding='short_header'
  if name.startswith('/') and name[1:].isdigit():
   offset=int(name[1:]);assert 0<=offset<len(names)
   ends=[(names.find(b'\0',offset),'COFF_NUL'),(names.find(b'/\n',offset),'GNU_SLASH_NEWLINE')]
   ends=[item for item in ends if item[0]>=offset];assert ends,'No known long-name terminator'
   end,encoding=min(ends);name=names[offset:end].decode('ascii');assert name
  else:name=name.rstrip('/')
  assert name not in objects,'Duplicate archive member';objects[name]=payload;formats[name]=encoding
 assert pos==len(data) and set(objects)==EXPECTED
 return objects,{'path':str(path),'sha256':sha(data),'bytes':len(data),'member_formats':formats,'long_name_tables_hex':tables}
a,ap=read_archive(PARENT);b,bp=read_archive(CANDIDATE)
changed=[n for n in sorted(EXPECTED) if a[n]!=b[n]]
assert changed==['search.cpp.obj']
inputs={str(PARENT):ap['sha256'],str(CANDIDATE):bp['sha256']}
assert all(sha(pathlib.Path(n).read_bytes())==h for n,h in inputs.items())
record={'status':'PASS_ONLY_SEARCH_CORE_OBJECT_CHANGED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':'ff2e269c6058be84456e3b98344826d17b0056eb','parent_source_commit':'2e151d019bc58dff2ab4e76e99ef99516af8d222','checker_sha256':sha(pathlib.Path(__file__).read_bytes()),'original_failed_checker_source_sha256':sha((HERE/'supplemental-core-check-attempt1.submitted.py.txt').read_bytes()),'original_failure_receipt_sha256':sha((HERE/'SUPPLEMENTAL-CORE-CHECKER-FAILURE.json').read_bytes()),'parent_archive':ap,'candidate_archive':bp,'member_count':len(EXPECTED),'members':[{'member':n,'parent_sha256':sha(a[n]),'candidate_sha256':sha(b[n]),'bytes_equal':a[n]==b[n]} for n in sorted(EXPECTED)],'changed_members':changed,'unchanged_nonsearch_core_objects':6,'archive_inputs_unchanged':True,'engine_or_compiler_or_git_execution':False,'scope':'Single root-authorized corrected read-only comparison. Original auxiliary parser failure remains preserved; no producer/runtime rescue or repeated engine/build.'}
with (HERE/'WINDOWS-CORE-PARENT-IDENTITY.json').open('x') as output:output.write(json.dumps(record,indent=2)+'\n')
print(json.dumps({'status':record['status'],'member_count':7,'unchanged_nonsearch_core_objects':6,'changed_members':changed,'checker_sha256':record['checker_sha256']}))
