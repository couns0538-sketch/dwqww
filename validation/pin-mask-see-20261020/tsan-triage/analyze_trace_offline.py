#!/usr/bin/env python3
"""Offline reassembly only; never runs a process or changes original raw evidence."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'diagnostic-attempt1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();statepath=OUT/'state.json';statehash=sha(statepath);state=json.loads(statepath.read_text());result={'scope':'OFFLINE_ONLY_NO_PROCESSES','executed_supervisor_sha256':state['supervisor_sha256'],'raw_runtime_state_sha256':statehash,'note':'Initial supervisor-derived fd byte exports were partial; these new exports reassemble unfinished/resumed calls and derive actual positive clone return values. Original files and executed scripts are unchanged.','cases':[]}
line_re=re.compile(r'^(?:\[pid\s+)?(\d+)(?:\])?\s+(\d+\.\d+)\s+(.*)$')
for row in state['results']:
 case=row['case'];trace=OUT/(case+'.strace.log');pending={};calls=[];unmatched=[]
 for index,line in enumerate(trace.read_text().splitlines(),1):
  match=line_re.match(line)
  if not match:continue
  pid=int(match[1]);stamp=float(match[2]);body=match[3]
  if '<unfinished ...>' in body:
   assert pid not in pending,(case,pid,index);pending[pid]={'pid':pid,'wall_seconds':stamp,'body':body.replace('<unfinished ...>',''),'start_line':index};continue
  resumed=re.match(r'<\.\.\. (\w+) resumed>(.*)',body)
  if resumed:
   if pid not in pending:unmatched.append({'line':index,'text':line});continue
   call=pending.pop(pid);call['body']+=resumed[2];call['finish_line']=index;calls.append(call);continue
  calls.append({'pid':pid,'wall_seconds':stamp,'body':body,'start_line':index,'finish_line':index})
 edges=[]
 for call in calls:
  if re.match(r'(?:clone3?|fork|vfork)\(',call['body']):
   returned=re.search(r'\)\s*=\s*(\d+)\b',call['body'])
   if returned and int(returned[1])>0:edges.append((call['pid'],int(returned[1])))
 pids={row['case_result']['engine_pid']}
 while True:
  children={child for parent,child in edges if parent in pids}
  if children<=pids:break
  pids|=children
 enginecalls=sorted([call for call in calls if call['pid'] in pids],key=lambda call:(call['wall_seconds'],call['start_line']));writes={1:[],2:[]};reads=[];unparsed=[]
 for call in enginecalls:
  name=re.match(r'(read|write)\((\d+),',call['body'])
  if not name:continue
  kind,fd=name[1],int(name[2])
  if not ((kind=='write' and fd in (1,2)) or (kind=='read' and fd==0)):continue
  parsed=re.match(r'(?:read|write)\(\d+,\s*"((?:\\x[0-9a-fA-F]{2})*)"\s*,\s*(\d+)\s*\)\s*=\s*(\d+)',call['body'])
  if not parsed:unparsed.append(call);continue
  raw=bytes.fromhex(parsed[1].replace('\\x',''));returned=int(parsed[3]);assert returned<=len(raw);payload=raw[:returned];entry=dict(call,bytes_hex=payload.hex(),returned=returned)
  if kind=='write':writes[fd].append(entry)
  else:reads.append(entry)
 paths={}
 for fd in (1,2):
  path=OUT/(case+'.offline-engine-fd'+str(fd)+'.raw');path.write_bytes(b''.join(bytes.fromhex(call['bytes_hex']) for call in writes[fd]));paths[str(fd)]={'path':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'write_calls':len(writes[fd])}
 stdinpath=OUT/(case+'.offline-engine-fd0.reads.raw');stdinpath.write_bytes(b''.join(bytes.fromhex(call['bytes_hex']) for call in reads));sourceevents=[json.loads(line) for line in (OUT/case/'events.jsonl').read_text().splitlines()];sent=next(e for e in sourceevents if e['kind']=='send_write_flush_return' and e['command']=='uci');firstreader=next(e for e in sourceevents if e['kind']=='reader_line');firstread=next(call for call in reads if call['returned']>0);firstwrite=next(call for call in writes[1] if call['returned']>0);execve=next(call for call in enginecalls if call['body'].startswith('execve('));handshake_reader=next(e for e in sourceevents if e['kind']=='reader_line' and e['raw_text'].strip()=='uciok');consumer=next(e for e in sourceevents if e['kind']=='queue_get_return' and e.get('item')=='uciok');firstpop=next(e for e in sourceevents if e['kind']=='Popen_enter')
 merged=(OUT/case/'stdout-stderr-merged.reader.txt').read_bytes();stdout=(OUT/paths['1']['path']).read_bytes();stderr=(OUT/paths['2']['path']).read_bytes();commands=(OUT/case/'stdin.commands.txt').read_bytes();stdin=stdinpath.read_bytes();assert stdout+stderr==merged;assert stdin==commands;pending_target=[call for pid,call in pending.items() if pid in pids and re.match(r'(?:read\(0,|write\([12],)',call['body'])];assert not unparsed and not unmatched and not pending_target
 caseinfo={'case':case,'raw_trace_sha256':sha(trace),'engine_process_and_thread_ids':sorted(pids),'raw_fd_exports':paths,'stdin_reads_path':stdinpath.name,'stdin_reads_sha256':sha(stdinpath),'all_engine_stdout_write_bytes_match_complete_merged_reader_capture':stdout+stderr==merged,'all_engine_stdin_read_bytes_match_sent_commands':stdin==commands,'unfinished_target_read_write_syscalls_left':len(pending_target),'other_unfinished_syscalls_at_process_exit':len(pending),'unmatched_resumes':len(unmatched),'unparsed_target_read_write_calls':len(unparsed),'timings_observed_only':{'parent_Popen_enter_to_engine_execve_syscall_seconds':execve['wall_seconds']-firstpop['wall_time_ns']/1e9,'parent_uci_flush_to_engine_first_stdin_read_syscall_seconds':firstread['wall_seconds']-sent['wall_time_ns']/1e9,'engine_first_stdin_read_to_first_output_write_syscall_seconds':firstwrite['wall_seconds']-firstread['wall_seconds'],'engine_first_output_write_syscall_to_first_reader_event_seconds':firstreader['wall_time_ns']/1e9-firstwrite['wall_seconds'],'parent_uci_flush_to_reader_uciok_seconds':(handshake_reader['monotonic_ns']-sent['monotonic_ns'])/1e9,'parent_uci_flush_to_consumer_uciok_seconds':(consumer['monotonic_ns']-sent['monotonic_ns'])/1e9},'first_stdin_read_trace_line':firstread['start_line'],'first_stdout_write_trace_line':firstwrite['start_line'],'engine_execve_trace_line':execve['start_line']}
 result['cases'].append(caseinfo)
assert sha(statepath)==statehash
result['status']='PASS_OFFLINE_CAPTURE_RECONSTRUCTION';result['original_runtime_state_unchanged']=True;result['offline_analysis_script_sha256']=sha(Path(__file__));(OUT/'offline-extraction.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
