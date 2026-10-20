#!/usr/bin/env python3
"""One authorized observed case; preserves original until/close and OwnBook run."""
import argparse,datetime,hashlib,importlib,json,os,queue,subprocess,sys,threading,time,traceback
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--case',choices=['parent15-handshake','candidate16-ownbook'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out;out.mkdir(exist_ok=False)
source=Path('/workspace/.cloud-setup/forge-pin-see-source' if a.case=='parent15-handshake' else '/workspace/.cloud-setup/forge-pin-mask-source');binary=Path('/workspace/.cloud-setup/forge-pin-see-tsan/forge' if a.case=='parent15-handshake' else '/workspace/.cloud-setup/forge-pin-mask-tsan/forge')
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
eventfile=(out/'events.jsonl').open('x',buffering=1);raw=(out/'stdout-stderr-merged.reader.txt').open('x',buffering=1);stdin=(out/'stdin.commands.txt').open('x',buffering=1);lock=threading.RLock();stats={'events':0,'logger_wall_ns':0,'logger_thread_cpu_ns':0,'logger_failed':False};engine=None

def event(kind,**data):
 start=time.monotonic_ns();cpu=time.thread_time_ns()
 row={'kind':kind,'monotonic_ns':start,'wall_time_ns':time.time_ns(),'thread_cpu_ns':cpu,'thread_ident':threading.get_ident(),**data}
 try:
  with lock:
   eventfile.write(json.dumps(row,sort_keys=True)+'\n');stats['events']+=1;stats['logger_wall_ns']+=time.monotonic_ns()-start;stats['logger_thread_cpu_ns']+=time.thread_time_ns()-cpu
 except BaseException:
  stats['logger_failed']=True;raise

result={'case':a.case,'source':str(source),'binary':str(binary),'status':'INSTRUMENTATION_SETUP_PENDING','default_until_seconds':15,'default_close_seconds':5,'transport':'Original stderr=STDOUT retained; raw fd1/fd2 syscall writes separately available in strace','strace_overhead':'Enabled by supervisor; not separately calibrated. Logger overhead measured per event, including logger lock wait.','environment':{k:os.environ.get(k) for k in ['TSAN_OPTIONS','PYTHONDONTWRITEBYTECODE','ASAN_OPTIONS','UBSAN_OPTIONS']}}
started=time.monotonic_ns();original_popen=subprocess.Popen;original_queue=queue.Queue
try:
 assert os.environ.get('TSAN_OPTIONS')=='halt_on_error=1:exitcode=66'
 assert sha(source/'tools/uci_regression.py')=='0ecfbdd3b04bf0ef4f6669ed43581d124e75ff3224926874da98c451649ee4cc'
 assert sha(source/'tools/ownbook_regression.py')=='2ebd2c43ba7d05caee77a10fc823214f16e46f3a4cee2c5dd8e21550b8d2f801'
 result['source_driver_sha256']={str(source/'tools'/name):sha(source/'tools'/name) for name in ['uci_regression.py','ownbook_regression.py']}
 sys.path.insert(0,str(source));uci=importlib.import_module('tools.uci_regression');ownbook=importlib.import_module('tools.ownbook_regression');Base=uci.Engine
 result['original_until_code_file']=Base.until.__code__.co_filename;result['original_until_code_line']=Base.until.__code__.co_firstlineno;result['original_close_code_file']=Base.close.__code__.co_filename;result['ownbook_run_code_file']=ownbook.run.__code__.co_filename
 class ObservedQueue(original_queue):
  def put(self,item,*args,**kwargs):
   event('queue_put_enter',item=item)
   value=super().put(item,*args,**kwargs);event('queue_put_return',item=item);return value
  def get(self,*args,**kwargs):
   event('queue_get_enter',timeout=kwargs.get('timeout'),block=kwargs.get('block',True))
   try:value=super().get(*args,**kwargs)
   except BaseException as error:event('queue_get_raise',error=repr(error));raise
   event('queue_get_return',item=value);return value
 def observed_popen(*args,**kwargs):
  event('Popen_enter',argv=[str(x) for x in args[0]],stderr_is_STDOUT=kwargs.get('stderr')==subprocess.STDOUT,text=kwargs.get('text'),bufsize=kwargs.get('bufsize'))
  child=original_popen(*args,**kwargs);result['engine_pid']=child.pid;event('Popen_return',pid=child.pid);return child
 class ObservedEngine(Base):
  def __init__(self,*args,**kwargs):
   global engine
   engine=self;event('Engine_init_enter');super().__init__(*args,**kwargs);event('Engine_init_return',pid=self.process.pid)
  def _read(self):
   event('reader_start')
   try:
    for line in self.process.stdout:
     raw.write(line);event('reader_line',raw_text=line)
     line=line.rstrip();self.transcript.append('< '+line);self.lines.put(line)
    self.lines.put(None);event('reader_eof')
   except BaseException as error:
    result['reader_error']=repr(error);event('reader_error',error=repr(error));raise
   finally:event('reader_finish')
  def send(self,command):
   stdin.write(command+'\n');event('send_enter',command=command)
   value=super().send(command);event('send_write_flush_return',command=command);return value
  def close(self):
   event('close_enter',returncode=self.process.poll())
   try:return super().close()
   finally:event('close_return',returncode=self.process.poll(),reader_alive=self.reader.is_alive())
 uci.subprocess.Popen=observed_popen;uci.queue.Queue=ObservedQueue;ownbook.Engine=ObservedEngine
 result['status']='RUNTIME_CASE_STARTED';event('case_start',case=a.case)
 if a.case=='parent15-handshake':
  e=ObservedEngine(binary)
  try:e.send('uci');lines=e.until(lambda line:line=='uciok');result['uciok_seen']=True;result['uci_identification']=lines
  finally:e.close()
 else:
  ownbook.run(binary,out/'ownbook-regression.json')
  checks=json.loads((out/'ownbook-regression.json').read_text());assert len(checks['checks'])==5 and all(row['PASS'] for row in checks['checks']) and checks['error'] is None;result['ownbook_five_checks']=checks['checks']
 result['status']='PASS_DIAGNOSTIC_ONLY'
except BaseException as error:
 result['status']='RUNTIME_PROBE_FAILED' if result['status']=='RUNTIME_CASE_STARTED' else 'INSTRUMENTATION_FAILED';result['error']=repr(error);result['traceback']=traceback.format_exc();event('case_error',error=repr(error))
finally:
 subprocess.Popen=original_popen;queue.Queue=original_queue
 if engine is not None and hasattr(engine,'process'):
  result['engine_returncode']=engine.process.poll();result['reader_alive_after_case']=engine.reader.is_alive();result['transcript']=engine.transcript
  if result['reader_alive_after_case'] or result.get('reader_error'):result['status']='INSTRUMENTATION_FAILED';result['capture_complete']=False
  else:result['capture_complete']=True
 event('case_finish',status=result['status']);result['elapsed_ns']=time.monotonic_ns()-started;result['observer']=dict(stats);result['source_driver_sha256_after']={str(source/'tools'/name):sha(source/'tools'/name) for name in ['uci_regression.py','ownbook_regression.py']};result['engine_sha256_after']=sha(binary)
 raw.close();stdin.close();eventfile.close()
 text=(out/'stdout-stderr-merged.reader.txt').read_text()
 import re
 result['warning_or_sanitizer_lines']=[line for line in text.splitlines() if re.search(r'^\s*(?:WARNING|FATAL|ERROR)\b|ThreadSanitizer',line,re.I)]
 if result['warning_or_sanitizer_lines'] and result['status']=='PASS_DIAGNOSTIC_ONLY':result['status']='RUNTIME_PROBE_FAILED'
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
sys.exit(0 if result['status']=='PASS_DIAGNOSTIC_ONLY' else 2 if result['status']=='RUNTIME_PROBE_FAILED' else 3)
