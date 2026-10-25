#!/usr/bin/env python3
"""Read-only consistency checker for the user's authoritative AUTOLOCK checklist.
No PC call, promotion, file write, approval creation or S46 simulation occurs.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re,stat
from pathlib import Path

SOURCE_CHECKLIST_SHA256='56b36813b2fc791d0c8c2676188ca56a31eb59b32c6a269d14f6e084405d3160'
SOURCE_CHECKLIST='forge_sol_S28_v2_user_autolock_rules_20261025.md'
F006='0fae54a4c0c437432ddb5da85512b5f4'; MISSING=object()
PIN_ATTACHMENTS={'3aecb403afebae7a5046e9e4bd3f8f97':'692b164b2601cf84411a7ea8c4b7892b255a219b2a07e5bdf7167b2cad77a35e','5a4ed6758d7778e26d2d4c504f3a47bb':'5685e836373afaecafba0e284f35d62402df478beedda7b0f3f40564ef2ccbca'}

def integer(v):return type(v) is int and v>=0

def number(v):return type(v) in (int,float) and math.isfinite(v)

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)

class Check:
 def __init__(self,packet,name):self.packet=packet;self.name=name;self.fail=[];self.missing=[];self.warnings=[]
 def value(self,value,label,kind=None):
  if value is MISSING:self.missing.append(label);return MISSING
  valid=True if kind is None else(type(value) is kind if kind in (bool,int) else isinstance(value,kind))
  if not valid:self.fail.append(label+': invalid type');return MISSING
  return value
 def get(self,path,kind=None):
  value=self.packet
  for key in path.split('.'):
   if not isinstance(value,dict):
    if value is not MISSING:self.fail.append(path+': non-object parent')
    return self.value(MISSING,path,kind)
   value=value.get(key,MISSING)
   if value is MISSING:break
  return self.value(value,path,kind)
 def field(self,row,key,kind,label):
  if not isinstance(row,dict):self.fail.append(label+': record is not an object');return MISSING
  return self.value(row.get(key,MISSING),label+'.'+key,kind)
 def expect(self,condition,label):
  if not condition:self.fail.append(label)
 def equal(self,a,b,label):
  if a is not MISSING and b is not MISSING:self.expect(canonical(a)==canonical(b),label)
 def hash(self,path,length=64):
  value=self.get(path,str)
  if value is MISSING:return MISSING
  if re.fullmatch('[0-9a-fA-F]+',value) and len(value)<length:self.missing.append(path+': full hash required, prefix only supplied');return MISSING
  if not re.fullmatch('[0-9a-fA-F]{'+str(length)+'}',value):self.fail.append(path+': invalid full hash');return MISSING
  return value.lower()
 def artifact(self,path):
  filename=self.get(path+'.path',str);claimed=self.hash(path+'.sha256')
  if filename is MISSING:return MISSING
  target=Path(filename)
  try:
   if target.is_symlink() or not stat.S_ISREG(target.stat().st_mode):self.fail.append(path+': artifact is not a regular nonsymlink file');return MISSING
   raw=target.read_bytes();actual=hashlib.sha256(raw).hexdigest();self.equal(actual,claimed,path+': artifact SHA256 mismatch');return raw,actual
  except OSError:self.missing.append(path+': artifact unavailable');return MISSING
 def done(self):return {'check':self.name,'status':'FAIL' if self.fail else('UNVERIFIED' if self.missing else 'PASS'),'failures':self.fail,'missing':self.missing,'warnings':self.warnings}

def artifact_PASS(p,artifact,label,identity):
 if artifact is MISSING:return
 lines=[line.strip().lstrip('#* ').strip() for line in artifact[0].decode('utf-8-sig','replace').splitlines() if line.strip()]
 header=lines[0] if lines else ''
 found=re.match(r'^(?:CR[ _-]+)?(PASS|FAIL)(?:\b|_)',header,re.I)
 if found is None:p.missing.append(label+': unambiguous actual PASS/FAIL header unavailable')
 elif found.group(1).upper()!='PASS':p.fail.append(label+': actual artifact verdict is FAIL despite metadata')
 elif identity is not MISSING:
  token_chars=r'A-Za-z0-9_' if re.fullmatch('[0-9a-fA-F]{64}',identity) else r'A-Za-z0-9_.-'
  exact=r'(?<!['+token_chars+'])'+re.escape(identity)+r'(?!['+token_chars+'])'
  if not re.search(exact,header[found.end():],re.I):p.missing.append(label+': actual PASS header does not bind the exact complete covered identity token')

def sha_map(p,value,label):
 if value is MISSING:return MISSING
 if not isinstance(value,dict) or not value or any(not isinstance(k,str) or not k or not isinstance(v,str) or not re.fullmatch('[0-9a-fA-F]{64}',v) for k,v in value.items()):p.fail.append(label+': nonempty file/SHA256 map required');return MISSING
 return {k:v.lower() for k,v in value.items()}

def audit_autolock(packet=None):
 malformed=packet is not None and not isinstance(packet,dict);packet=packet if isinstance(packet,dict) else {};checks=[];additions=[]
 def run(name,fn,target=checks):
  p=Check(packet,name)
  if malformed:p.fail.append('Packet is not an object')
  try:fn(p)
  except (TypeError,ValueError,KeyError,AttributeError) as e:p.fail.append('Invalid metadata: '+str(e))
  target.append(p.done())
 def c1(p):
  live=p.hash('script.live_sha256');snapshot=p.artifact('script.snapshot');p.equal(p.get('script.no_autopromote_absent',bool),True,'NO_AUTOPROMOTE was present')
  if snapshot is not MISSING:p.equal(live,snapshot[1],'Live script identity differs from supplied measured snapshot')
  if live is not MISSING and not live.startswith(('f41cf92f','896663b0')):
   review=p.artifact('script.review');p.equal(p.get('script.review.external',bool),True,'Successor review is not external');p.equal(p.get('script.review.decision',str),'PASS','Successor CR review is not PASS');p.equal(p.hash('script.review.script_sha256'),live,'Successor review covers different script')
   artifact_PASS(p,review,'Successor external review',live)
   if review is not MISSING:p.expect(live in review[0].decode('utf-8','replace').lower(),'External successor review does not bind complete script hash')
 run('01_live_script_identity_and_NO_AUTOPROMOTE',c1)
 def c2(p):
  for side in ('parent','confirm'):
   base='winner.'+side;p.equal(p.get(base+'.void_file_exists',bool),False,side+' has VOID.txt');text=p.get(base+'.result_md',str)
   if text is not MISSING:p.expect('**void**' not in text.casefold(),side+' RESULT.md contains **VOID**')
   text=p.get(base+'.options_check',str)
   if text is not MISSING:
    lines=[v.strip() for v in text.splitlines() if v.strip()];last=lines[-1] if lines else '';p.expect(bool(re.search(r'\bPASS\b',last)) and not re.search(r'\b(?:FAIL|VOID)\b|NOT\s+PASS',last,re.I),side+' final option-check line is not PASS')
 run('02_nonVOID_parent_confirm_final_options_PASS_HIGH1',c2)
 def c3(p):
  status=p.get('race.g104c',str);expired=p.get('race.cap_expired',bool);winner=p.get('race.winner_id',str);tag=p.get('race.winner_tag',str);rework=p.get('race.rework_list',list);r104=p.get('race.g104_rebase_gates',list);r120=p.get('race.g120_rebase_gates',list);event=p.get('event',str)
  if status is not MISSING:p.expect(status in ('H1','H0','CAPPED','PENDING'),'Unknown G104c race status')
  if expired is True and status in ('H1','H0','CAPPED'):p.fail.append('Conflicting same-decision race facts: terminal G104c and expired wait cap')
  if winner=='G120' and tag is not MISSING:p.expect(bool(re.match(r'^gate120(?:_|$)',tag,re.I)),'G120 winner tag does not identify gate120')
  if status=='H1':
   p.equal(winner,'G104','G104c H1 requires G104 winner');p.equal(tag,'gate104_e48f006','G104 winner tag incorrect');p.equal(p.get('race.g120_status',str),'PARKED-E32','G120 not PARKED-E32')
   if rework is not MISSING:p.expect('G120' in rework,'G120 absent from REWORK_LIST')
   if r120 is not MISSING:p.expect(not r120,'G120 has forbidden rebase gate')
  elif expired is True:
   p.equal(winner,'G120','Cap-expiry winner must be G120')
   if r104 is not MISSING:p.expect('gate104_e48f006_rebase_vs_AL1' in r104,'Missing cap rebase gate104')
   p.equal(p.get('cap_late.ag_rebase_exempt24',bool),True,'Cap rebase exempt24 missing');p.equal(p.get('cap_late.crew_alert.level',str),'INFO','Cap crew alert not INFO');p.equal(p.get('cap_late.crew_alert.visible',bool),True,'Cap alert not crew-visible')
   a,b=p.get('cap_late.srand',int),p.get('cap_late.original_srand',int)
   if a is not MISSING and b is not MISSING:p.expect(integer(a) and integer(b) and a!=b,'Cap rebase srand not fresh')
  elif status in ('H0','CAPPED'):
   p.equal(winner,'G120','G104 H0/capped winner must be G120')
   if rework is not MISSING:p.expect('G104' in rework,'G104 absent from REWORK_LIST')
   if r104 is not MISSING:p.expect(not r104,'G104 H0/capped must not re-gate')
  elif status is not MISSING and expired is False:p.missing.append('Pending race has no terminal outcome/cap decision')
  if event=='first':
   p.equal(p.get('lock.gate_tag',str),tag,'First lock differs from race winner tag');p.equal(p.get('lock.gate_id',str),winner,'First lock gate ID differs from race winner ID')
 run('03_RHQ_race_winner_park_rework_or_cap',c3)
 def c4(p):
  n=p.get('lock.n',int);tag=p.get('lock.tag',str);path=p.get('lock.path',str);event=p.get('event',str);parent=p.get('lock.parent_tag',str);kind=p.get('lock.kind',str);diff=p.get('lock.tree_diff',list)
  p.equal(p.get('lock.directory_new',bool),True,'AUTOLOCK directory is not new');p.equal(p.get('lock.orphan_lower_n_dirs',list),[],'Orphan lower-number AUTOLOCK directory exists')
  if n is not MISSING:p.expect(n>0,'AUTOLOCK number must be positive')
  if n is not MISSING and tag is not MISSING:p.expect(bool(re.fullmatch(r'AUTOLOCK_'+str(n)+r'_.+',tag)),'AUTOLOCK tag/number mismatch')
  if path is not MISSING and tag is not MISSING:p.expect(Path(path.replace('\\','/').rstrip('/')).parts[-2:]==('locks',tag),'AUTOLOCK path is not locks/AUTOLOCK_n_tag')
  exe=p.hash('lock.exe_sha256');parent_exe=p.hash('winner.parent.candidate_sha256');confirm_exe=p.hash('winner.confirm.candidate_sha256');p.equal(exe,parent_exe,'Lock exe differs from parent RUN_INFO candidate');p.equal(exe,confirm_exe,'Lock exe differs from confirm RUN_INFO candidate');p.equal(parent_exe,confirm_exe,'Parent and confirm candidates differ')
  if event=='first':p.equal(parent,'h256_e12','First AUTOLOCK parent is not h256_e12')
  elif event=='later_cap_late':
   if parent is not MISSING:p.expect(bool(re.fullmatch(r'AUTOLOCK_1(?:_.+)?',parent)),'Later CAP-LATE parent is not AUTOLOCK_1')
   p.equal(kind,'net','Later CAP-LATE kind must be net')
   p.equal(p.get('lock.gate_tag',str),'gate104_e48f006_rebase_vs_AL1','Later CAP-LATE promoted wrong gate');p.equal(p.get('lock.gate_tag',str),p.get('cap_late.queued_gate',str),'Later promoted gate differs from queued CAP-LATE gate')
  elif event is not MISSING:p.fail.append('Unknown AUTOLOCK event kind')
  if kind=='net' and diff is not MISSING:p.expect(diff in (['src/nnue_weights.inc'],['src\\nnue_weights.inc']),'Net lock has non-net Tree-Diff (including applied pins/docs)')
  net=p.hash('lock.net_md5',32);manifest_net=p.hash('lock.net_manifest_md5',32);p.equal(net,manifest_net,'Net differs from nnue_weights.inc.md5')
  gate_tag=p.get('lock.gate_tag',str);f006_profile=gate_tag in ('gate104_e48f006','gate104_e48f006_rebase_vs_AL1')
  if f006_profile:
   p.equal(net,F006,'e48f006 gate carries wrong authoritative net MD5');p.equal(manifest_net,F006,'e48f006 sidecar carries wrong authoritative net MD5');p.equal(kind,'net','Actual e48f006 AUTOLOCK must remain net-only')
   if diff is not MISSING:p.expect(diff in (['src/nnue_weights.inc'],['src\\nnue_weights.inc']),'Actual e48f006 source includes applied qualification/pin delta')
  if f006_profile or net==F006:
   refs=p.get('lock.pins_refs',dict);p.equal(p.get('lock.pins_applied',bool),False,'f006 pins were applied to actual AUTOLOCK')
   if refs is not MISSING:
    normal={str(k).lower():v for k,v in refs.items()}
    if len(normal)!=len(refs):p.fail.append('Duplicate pin references after hash case normalization')
    for md5 in PIN_ATTACHMENTS:
     keys=[key for key in normal if key.startswith(md5[:8])]
     if not keys:p.missing.append('lock.pins_refs.'+md5[:8])
     for key in keys:
      p.expect(key in (md5[:8],md5),'Pin reference differs from authoritative original attachment MD5');p.equal(p.value(normal[key],'lock.pins_refs.'+key,str),'attached',key+' pin proposal is not attached-only')
   observed=packet.get('lock',{}).get('pin_attachment_sha256',MISSING)
   if observed is not MISSING:
    if not isinstance(observed,dict):p.fail.append('Invalid attachment SHA256 map')
    else:
     for md5,digest in observed.items():
      if not isinstance(md5,str) or not isinstance(digest,str) or not re.fullmatch('[0-9a-fA-F]{32}',md5) or not re.fullmatch('[0-9a-fA-F]{64}',digest):p.fail.append('Invalid attachment full MD5/SHA256')
      elif md5.lower() in PIN_ATTACHMENTS:p.equal(digest.lower(),PIN_ATTACHMENTS[md5.lower()],'Wrong original attached proposal SHA256; rebased qualification delta is not a real attachment')

 run('04_new_lock_RUN_INFO_net_parent_attached_pins',c4)
 def c5(p):
  for path,total in [('checks.perft5',4865609),('checks.kiwipete5',193690690),('checks.fma',0)]:p.equal(p.get(path,int),total,path+' mismatch')
  p.equal(p.get('checks.bench_reference_source',str),'gate.prebench.cand_off','Bench oracle is not gate prebench.cand_off');rows=[p.get('checks.'+key,dict) for key in ('bench_reference','bench_first','bench_repeat')]
  for row in rows:
   if row is not MISSING:p.expect(set(row)=={'11','13','16','20','22'} and all(type(v) is int and v>0 for v in row.values()),'Bench must contain five positive integer counts')
  p.equal(rows[0],rows[1],'First bench differs from gate fixed reference');p.equal(rows[0],rows[2],'Repeated bench differs from gate fixed reference');p.equal(rows[1],rows[2],'Two observed bench runs differ')
  check_fields=packet.get('checks',{});ratio=check_fields.get('nps_ratio',MISSING) if isinstance(check_fields,dict) else MISSING
  if ratio is MISSING:p.warnings.append('Advisory qualification NPS not supplied')
  else:
   if not number(ratio):p.fail.append('Advisory NPS ratio is invalid')
   elif not 0.9<=ratio<=1.1:p.warnings.append('Qualification NPS ratio outside10%; advisory here, no acceptance inferred')
 run('05_PERFT_FMA_two_benches_gate_reference',c5)
 def c6(p):
  a,b=p.hash('old_lock.exe_before_sha256'),p.hash('old_lock.exe_after_sha256');p.equal(a,b,'h256_e12 executable changed')
  for value in (a,b):
   if value is not MISSING:p.expect(value.startswith('e3df99cd'),'Old executable is not specified e3df99cd h256_e12 identity')
  before=sha_map(p,p.get('old_lock.sources_before',dict),'old before');after=sha_map(p,p.get('old_lock.sources_after',dict),'old after');p.equal(before,after,'Old source hashes changed');p.equal(p.get('old_lock.read_only_attributes_only',bool),True,'Old lock was modified beyond read-only attributes')
  snapshot=p.get('old_lock.source_snapshot',str)
  if snapshot is not MISSING:
   try:
    base=Path(snapshot);actual={}
    if not base.exists():p.missing.append('Old source snapshot unavailable')
    elif not base.is_dir() or base.is_symlink():p.fail.append('Old source snapshot is not regular directory')
    else:
     for file in sorted(base.rglob('*')):
      if file.is_symlink():p.fail.append('Old source snapshot contains symlink');continue
      if file.is_file():actual[file.relative_to(base).as_posix()]=hashlib.sha256(file.read_bytes()).hexdigest()
     p.equal(after,actual,'Old source manifest incomplete/stale against supplied snapshot')
   except OSError:p.missing.append('Old source snapshot unavailable')
  backup=p.artifact('old_lock.pointer_backup');filename=p.get('old_lock.pointer_backup.path',str)
  if filename is not MISSING:p.expect(bool(re.fullmatch(r'CURRENT_LOCK\.json\.bak_pre_.+_.+',Path(filename).name)),'Pointer backup filename incorrect')
  steps=p.get('old_lock.steps',list);tag=p.get('lock.tag',str)
  if steps is not MISSING and tag is not MISSING:
   selected=[(i,s) for i,s in enumerate(steps) if isinstance(s,dict) and s.get('tag')==tag and s.get('action') in ('CREATE','POINTER')];actions=[s['action'] for _,s in selected];p.expect(actions==['CREATE','POINTER'],'AUTOLOCK_STEPS lacks CREATE then POINTER for current tag')
   if actions==['CREATE','POINTER']:
    x,y=selected[0][1].get('hashes'),selected[1][1].get('hashes');p.expect(isinstance(x,dict) and bool(x) and isinstance(y,dict),'CREATE/POINTER hashes missing')
    normalized=lambda v:{k:(value.lower() if isinstance(value,str) else value) for k,value in v.items()} if isinstance(v,dict) else v
    p.equal(normalized(x),normalized(y),'CREATE/POINTER hashes differ')
    for hashes in (x,y):
     if isinstance(hashes,dict):
      for key,value in hashes.items():
       if not isinstance(key,str) or not isinstance(value,str) or not re.fullmatch('[0-9a-fA-F]+',value):p.fail.append('Invalid CREATE/POINTER hash metadata')
       elif len(value) not in (32,64):p.missing.append('CREATE/POINTER full hash unavailable: '+key)
      step_exe=p.value(hashes.get('exe_sha256',MISSING),'CREATE/POINTER exe_sha256',str)
      if step_exe is not MISSING:p.equal(step_exe.lower(),p.hash('lock.exe_sha256'),'CREATE/POINTER executable hash differs from actual lock')
      if 'net_md5' in hashes and isinstance(hashes['net_md5'],str):p.equal(hashes['net_md5'].lower(),p.hash('lock.net_md5',32),'CREATE/POINTER net hash differs from actual lock')
 run('06_old_lock_immutable_backup_CREATE_POINTER',c6)
 def c7(p):
  tag=p.get('lock.tag',str);promoted=p.get('state.promotes_last_tag',str);pointer=p.get('state.pointer_tag',str);p.equal(promoted,tag,'Last promote tag differs from lock');p.equal(pointer,tag,'Pointer tag differs from lock');p.equal(promoted,pointer,'Last promote and pointer disagree');p.equal(p.get('state.datagen_pending',bool),True,'datagen.pending not set');seen=p.get('state.seen',dict);gate=p.get('lock.gate_tag',str);combine=p.get('state.combine_list',list);chain=p.get('lock.chain_id',str)
  if seen is not MISSING and gate is not MISSING:p.equal(p.value(seen.get(gate,MISSING),'state.seen current gate',str),'PROMOTED','Promoted gate not PROMOTED in seen')
  if combine is not MISSING and chain is not MISSING:p.expect(chain not in combine,'Promoted chain remains in COMBINE_LIST (MED-4)')
 run('07_pointer_promotes_seen_pending_COMBINE',c7)
 def c8(p):
  backup=p.artifact('gates.manifest_backup');filename=p.get('gates.manifest_backup.path',str)
  if filename is not MISSING:p.expect(bool(re.fullmatch(r'forge_gates\.json\.bak_rebuild_\d+_.+',Path(filename).name)),'Gate manifest backup filename incorrect')
  before=p.get('gates.started_before',dict);after=p.get('gates.started_after',dict);p.equal(before,after,'Started gate edited versus manifest backup')
  if backup is not MISSING:
   try:
    manifest=json.loads(backup[0].decode('utf-8-sig'));records=manifest.get('gates') if isinstance(manifest,dict) else None
    if not isinstance(records,list) or any(not isinstance(row,dict) or not isinstance(row.get('tag'),str) for row in records):p.fail.append('Actual manifest backup lacks valid gates array')
    else:
     by_tag={row['tag']:row for row in records}
     if len(by_tag)!=len(records):p.fail.append('Duplicate gate tags in actual manifest backup')
     if before is not MISSING:
      for key,row in before.items():
       if key not in by_tag:p.fail.append('Started gate absent from actual manifest backup: '+key)
       else:p.equal(row,by_tag[key],'Started-gate before record differs from actual manifest backup: '+key)
   except (ValueError,UnicodeError):p.fail.append('Actual manifest backup is not valid JSON')
  rows=p.get('gates.rebuilt_net',list);tag=p.get('lock.tag',str)

  if rows is not MISSING:
   for row in rows:
    note=p.field(row,'notes',str,'rebuilt gate');a=p.field(row,'before_srand',int,'rebuilt gate');b=p.field(row,'srand',int,'rebuilt gate');base=p.field(row,'base_override',str,'rebuilt gate');previous=p.field(row,'ag_prev',None,'rebuilt gate')
    if note is not MISSING:p.expect('REBUILT on ' in note,'Missing REBUILT on note')
    if a is not MISSING and b is not MISSING:p.expect(integer(a) and integer(b) and a!=b,'Rebuilt gate srand is not fresh')
    p.equal(base,tag,'Rebuilt gate base_override differs from new lock')
    if previous is not MISSING:p.expect(previous not in (None,'',{},[]),'Rebuilt gate ag_prev not stored')
  rows=p.get('gates.search_option',list)
  if rows is not MISSING:
   for row in rows:
    kind=p.field(row,'kind',str,'search/option gate');label=p.field(row,'label',str,'search/option gate')
    if kind is not MISSING:p.expect(kind in ('search','option'),'Unknown search/option gate kind')
    if label is not MISSING:p.expect('vs h256_e12' in label,'Search/option gate not labelled vs h256_e12')
 run('08_rebuilt_gates_fresh_seed_base_agprev_started_immutable',c8)
 def c9(p):
  p.equal(p.get('high2.all_chains_inspected',bool),True,'All chains were not inspected for HIGH-2');rows=p.get('high2.chains',list)
  if rows is not MISSING:
   for row in rows:
    double=p.field(row,'double_h1',bool,'chain');status=p.field(row,'seen_status',str,'chain');reason=p.field(row,'seen_reason',str,'chain')
    if double is True and status=='INELIGIBLE' and reason is not MISSING:p.expect(not any(s in reason.casefold() for s in ('no forge_results.csv row','run_info.json missing')),'Double H1 still INELIGIBLE due HIGH-2')
    if isinstance(row,dict) and row.get('was_high2_ineligible') is True:
     note=p.field(row,'crew_visible_clear_note',str,'chain')
     if note is not MISSING:p.expect(bool(note.strip()),'Manual HIGH-2 clear lacks crew-visible note')
 run('09_HIGH2_double_H1_not_wrongly_INELIGIBLE',c9)
 def c10(p):
  done=p.get('datagen.switch_completed',bool);boundary=p.get('datagen.file_boundary',bool);ratio=p.get('datagen.nps_ratio');p.equal(p.hash('datagen.trainer_before_sha256'),p.hash('datagen.trainer_after_sha256'),'NNUE trainer changed')
  if done is False:p.missing.append('Datagen switch has not completed; boundary not yet observed')
  if done is True:p.equal(boundary,True,'Datagen switch occurred away from file boundary')
  if ratio is not MISSING:p.expect(number(ratio) and 0.9<=ratio<=1.1,'Datagen NPS ratio not within10%')
 run('10_datagen_boundary_NPS10pct_trainer_untouched',c10)
 def c11(p):
  count=p.get('cr.chained_without_cr',int)
  if count is not MISSING:p.expect(0<=count<=2,'More than two chained AUTO-LOCKs without CR_PASS')
  evidence=p.artifact('cr.external_pass');p.equal(p.get('cr.external_pass.external',bool),True,'CR_PASS is not external');p.equal(p.get('cr.external_pass.decision',str),'PASS','External CR decision is not PASS');tag=p.get('lock.tag',str);p.equal(p.get('cr.external_pass.lock_tag',str),tag,'External CR_PASS covers different lock');name=p.get('cr.external_pass.record_name',str);n=p.get('lock.n',int)
  if name is not MISSING and n is not MISSING:p.equal(name,'CR_PASS_AUTOLOCK_'+str(n)+'.txt','External CR_PASS record name incorrect')
  artifact_PASS(p,evidence,'External CR_PASS',tag)
  if evidence is not MISSING and tag is not MISSING:p.expect(tag in evidence[0].decode('utf-8','replace'),'External CR_PASS artifact does not name lock')
 run('11_external_CR_PASS_and_max_two_without_CR',c11)
 def a1(p):
  p.equal(p.get('post_promote.inflight'),None,'autopromote inflight is not null');lines=p.get('post_promote.alerts_lines',list)
  if lines is not MISSING:p.expect(all(isinstance(s,str) and not re.search(r'\binflight_\w*',s,re.I) for s in lines),'ALERTS contains inflight_* lines or invalid entries')
 run('ADD_inflight_null_and_no_inflight_alert',a1,additions)
 def a2(p):
  expired=p.get('race.cap_expired',bool);event=p.get('event',str)
  if expired is not True and event!='later_cap_late':return
  p.equal(p.get('cap_late.queued_gate',str),'gate104_e48f006_rebase_vs_AL1','CAP-LATE queued gate incorrect');p.equal(p.get('cap_late.ag_rebase_exempt24',bool),True,'CAP-LATE missing exempt24');p.equal(p.get('cap_late.conc',int),5,'CAP-LATE concurrency must be5');a=p.get('cap_late.srand',int);b=p.get('cap_late.original_srand',int)
  if a is not MISSING and b is not MISSING:p.expect(integer(a) and integer(b) and a!=b,'CAP-LATE srand reused')
  enabled=p.get('cap_late.z2_enabled',bool);status=p.get('cap_late.g104c_current',str);queued=p.get('cap_late.queue_status',str)
  if enabled is True and status is not MISSING and status!='H1':p.equal(queued,'HELD','CAP-LATE gate not HELD until G104c H1')
  if event=='later_cap_late':
   p.equal(status,'H1','Later CAP-LATE promoted before G104c H1');p.equal(p.get('cap_late.later_promote_logged',bool),True,'Later CAP-LATE log missing');p.equal(p.get('cap_late.log_kind',str),'net','Later CAP-LATE log kind not net');parent=p.get('cap_late.log_parent_tag',str)
   if parent is not MISSING:p.expect(bool(re.fullmatch(r'AUTOLOCK_1(?:_.+)?',parent)),'Later CAP-LATE log parent not AUTOLOCK_1')
   p.equal(parent,p.get('lock.parent_tag',str),'Later CAP-LATE log/source parent mismatch')
 run('ADD_CAP_LATE_fresh_exempt24_conc5_HELD_later_net_parent_AL1',a2,additions)
 def a3(p):
  mode=p.get('race.mode',str);winner=p.get('race.winner_id',str)
  if mode is not MISSING:p.expect(mode in ('RH-Q1','RH-Q1 FALLBACK'),'Unknown RH-Q1 decision mode')
  if mode=='RH-Q1 FALLBACK' and winner=='G120':
   note=p.get('fallback.crew_visible_note',str)
   if note is not MISSING:p.expect(bool(note.strip()),'FALLBACK e32 lacks crew-visible note')
 run('ADD_RHQ1_FALLBACK_e32_crew_note',a3,additions)
 rows=checks+additions;status='FAIL' if any(r['status']=='FAIL' for r in rows) else('UNVERIFIED' if any(r['status']=='UNVERIFIED' for r in rows) else 'PASS')
 ready=all(r['status']=='PASS' for r in checks[:10]+additions)
 return {'status':status,'report_status':'READY_FOR_EXTERNAL_CR_REVIEW' if ready and checks[10]['status']=='UNVERIFIED' else('EVIDENCE_CONSISTENT_FOR_REVIEW' if status=='PASS' else 'UNVERIFIED_OR_FAILED_FACTS'),'source_checklist':SOURCE_CHECKLIST,'source_checklist_sha256':SOURCE_CHECKLIST_SHA256,'checks':checks,'additions':additions,'scope':'Authoritative user11points+later additions; read-only consistency of supplied evidence, not live-PC or promoter execution','synthetic_fixture':packet.get('synthetic_fixture') is True,'live_pc_verified':False,'writes_cr_pass':False,'expected_original_attachment_identities':PIN_ATTACHMENTS,'unavailable_original_artifacts':['Referenced files/10_cr/CR_autopromote_RHQ1.md was not in verified14:35snapshot','Referenced16:15prompt was not uploaded; supplied user clarification is authoritative']}

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--packet',type=Path);args=parser.parse_args();packet=json.loads(args.packet.read_text()) if args.packet else None;result=audit_autolock(packet);print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(0 if result['status']=='PASS' else 1)
