"""Bounded skill metadata/preservation and retained-COFF data checks; no workloads."""
from pathlib import Path
import datetime,difflib,hashlib,json,re,struct
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;S=R/'.agents/skills/validating-chess-simd/SKILL.md'
h=lambda b:hashlib.sha256(b).hexdigest();filehash=lambda p:h(p.read_bytes());checks=[]
def check(name,value):
 checks.append({'name':name,'pass':bool(value)})
 if not value:raise AssertionError(name)
def long_name(table,offset):
 assert 0<=offset<len(table)
 ends=[(table.find(b'\0',offset),'COFF_NUL'),(table.find(b'/\n',offset),'GNU_SLASH_NEWLINE')]
 ends=[item for item in ends if item[0]>=offset];assert ends
 end,kind=min(ends);name=table[offset:end].decode('ascii');assert name
 return name,kind
def archive(path):
 data=path.read_bytes();assert data[:8]==b'!<arch>\n';pos=8;table=b'';members={};formats={}
 while pos<len(data):
  assert pos+60<=len(data);header=data[pos:pos+60];assert header[58:60]==b'`\n'
  name=header[:16].decode('ascii').strip();size=int(header[48:58]);assert size>=0
  pos+=60;assert pos+size<=len(data);payload=data[pos:pos+size];pos+=size+size%2
  if name=='//':table=payload;continue
  if name in ('/','/SYM64/'):continue
  if name.startswith('/'):
   assert name[1:].isdigit();name,kind=long_name(table,int(name[1:]))
  else:name=name.rstrip('/');kind='SHORT_HEADER'
  assert name not in members;members[name]=payload;formats[name]=kind
 assert pos==len(data)
 return members,formats
def standard_amd64_coff(b):
 if len(b)<20:return None
 machine,sections,timestamp,symbols,count,optional,flags=struct.unpack_from('<HHIIIHH',b)
 if machine!=0x8664 or not sections or optional!=0 or 20+40*sections>len(b):return None
 for i in range(sections):
  at=20+40*i;size,raw,reloc,lines,nrel,nlines,characteristics=struct.unpack_from('<IIIIHHI',b,at+16)
  if raw and raw+size>len(b):return None
  if size and not raw and not characteristics&0x80:return None
  if nrel==0xffff:return None # Unsupported overflow layout must not be qualified.
  if nrel and (not reloc or reloc+10*nrel>len(b)):return None
  if nlines and (not lines or lines+6*nlines>len(b)):return None
 if bool(symbols)!=bool(count) or symbols+18*count>len(b):return None
 if symbols:
  string_at=symbols+18*count
  if string_at+4>len(b):return None
  string_size=struct.unpack_from('<I',b,string_at)[0]
  if string_size<4 or string_at+string_size>len(b):return None
 return {'machine':machine,'section_count':sections,'timestamp_u32':timestamp,'optional_header_bytes':optional,'layout':'ordinary20byteAMD64COFF'}
def qualified(a,b):
 return bool(standard_amd64_coff(a) and standard_amd64_coff(b) and len(a)==len(b) and a[:4]==b[:4] and a[8:]==b[8:])
text=S.read_text();before=(D/'before-SKILL.md').read_text();check('all_existing_SIMD_arithmetic_parity_instructions_preserved',text.startswith(before))
front=text.split('---\n',2)[1];metadata=dict(line.split(': ',1) for line in front.strip().splitlines())
check('two_scalar_frontmatter',len(front)<1024 and set(metadata)=={'name','description'} and re.fullmatch('[a-z0-9-]+',metadata['name']) and metadata['name']==S.parent.name and metadata['description'].startswith('Use when ') and len(metadata['description'])<500)
links=[]
for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',text):
 if '://' not in target and not target.startswith('#'):
  exists=(S.parent/target.split('#')[0]).resolve().is_file();links.append({'target':target,'exists':exists});check('relative_link:'+target,exists)
protected=json.loads((D/'PRIOR-PROOF-HASHES.json').read_text());check('all11_consumed_old_proofs_and_cores_unchanged',len(protected)==11 and all(filehash(Path(n))==v for n,v in protected.items()))
check('GNU_long_name_decoder',long_name(b'bitboard.cpp.obj/\n',0)==('bitboard.cpp.obj','GNU_SLASH_NEWLINE'))
for table,offset in [(b'unknown',0),(b'good\0',99)]:
 try:long_name(table,offset)
 except AssertionError:okay=True
 else:okay=False
 check('unsupported_name_or_bad_offset_rejected:'+str(offset),okay)
p=Path('/workspace/.cloud-setup/windows6421-build/libforge_core.a');q=Path('/workspace/.cloud-setup/windows6422-build/libforge_core.a');a,af=archive(p);b,bf=archive(q)
expected={'bitboard.cpp.obj','board.cpp.obj','book.cpp.obj','eval.cpp.obj','eval_params.cpp.obj','nnue.cpp.obj','search.cpp.obj'}
check('actual_both_seven_member_inventories',set(a)==set(b)==expected)
rows=[]
for name in sorted(expected):
 la=standard_amd64_coff(a[name]);lb=standard_amd64_coff(b[name]);check('actual_standard_AMD64_COFF:'+name,bool(la and lb))
 different=[i for i,(x,y) in enumerate(zip(a[name],b[name])) if x!=y];timestamp_only=qualified(a[name],b[name]);raw=a[name]==b[name]
 rows.append({'member':name,'parent_sha256':h(a[name]),'candidate_sha256':h(b[name]),'parent_bytes':len(a[name]),'candidate_bytes':len(b[name]),'parent_archive_name_format':af[name],'candidate_archive_name_format':bf[name],'parent_layout':la,'candidate_layout':lb,'raw_byte_identity':raw,'timestamp_qualified_identity':timestamp_only,'differing_bytes_common_prefix':len(different),'difference_offsets':different if timestamp_only else different[:64],'difference_offsets_complete':timestamp_only,'length_difference':len(b[name])-len(a[name])})
 if name!='search.cpp.obj':check('actual_nonsearch_only_two_timestamp_bytes:'+name,not raw and timestamp_only and different==[4,5])
 else:check('actual_search_code_change_negative_control',not timestamp_only and not raw and len(b[name])!=len(a[name]))
check('six_actual_timestamp_qualified_and_zero_raw_identical',sum(r['timestamp_qualified_identity'] for r in rows)==6 and not any(r['raw_byte_identity'] for r in rows))
# Derived in-memory guards only: never rewrite an original file or call these engine results.
n=a['nnue.cpp.obj'];pe=b'MZ'+n[2:];big=b'\0\0\xff\xff'+n[4:]
check('PE_and_bigobj_layouts_not_qualified',not qualified(pe,pe) and not qualified(big,big))
changed=bytearray(n);changed[-1]^=1;check('single_non_timestamp_byte_not_ignored',not qualified(n,bytes(changed)))
source=R/'validation/pv-metadata-windows-20261021/source-hashes.json';sources=json.loads(source.read_text());export=Path('/workspace/.cloud-setup/windows6422-source');check('frozen74_source_files_unchanged',len(sources)==74 and all(filehash(export/name)==v for name,v in sources.items()))
check('all_old_inputs_still_unchanged_after_comparison',all(filehash(Path(n))==v for n,v in protected.items()))
(D/'SKILL.md.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),text.splitlines(True),fromfile='before/SKILL.md',tofile='after/SKILL.md')))
report={'status':'PASS_STATIC_AND_RETAINED_ACTUAL_COFF_DATA_APPLICATION','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'skill_sha256':filehash(S),'old_skill_sha256':h(before.encode()),'relative_links':links,'old_instruction_prefix_preserved':True,'retained_archive_sha256':{str(p):filehash(p),str(q):filehash(q)},'member_results':rows,'timestamp_qualified_nonsearch_members':6,'raw_identical_objects':0,'real_search_negative_control_rejected':True,'derived_controls':'Decoder malformed/GNU cases and PE/bigobj/one-byte non-timestamp variants are in-memory derived data only, not new engine evidence.','old_proof_files_preserved':len(protected),'frozen_windows_source_files_preserved':74,'validator_structure_source':'validation/strength-skill-aa-20261021/validate_skill.py','engine_compiler_bench_git_network_executions':0,'availability':'Existing repository-local .agents/skills/validating-chess-simd/SKILL.md updated; no global/cloud installation attempted or claimed.','limits':'Qualified timestamp-only structural identity does not prove full semantic equivalence, arithmetic parity, search parity, performance or Elo; existing validation requirements remain.'};(D/'APPLICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','check_count','timestamp_qualified_nonsearch_members','raw_identical_objects','real_search_negative_control_rejected']}))
