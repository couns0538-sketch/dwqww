"""Bounded native min-25 opening experiment; original outputs are retained.
IDEA_SOURCE: user Astra A1 unbalanced opening contract and repository probe API.
"""
from pathlib import Path
import datetime,hashlib,json,os,resource,subprocess,sys,time
ROOT=Path(__file__).resolve().parent
REPO=Path('/tmp/forge-astra-a1-data')
EXE=Path('/tmp/astra-a1-native-build/fixed/forge_data_probe')
GEN=REPO/'tools/data/generate_openings.py'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,obj):
 with (ROOT/name).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
def cpu():
 r=resource.getrusage(resource.RUSAGE_CHILDREN)
 return r.ru_utime+r.ru_stime
core=min(os.sched_getaffinity(0))
started_cpu=cpu()
for name,count,extra in [('standard-one',64,[]),('standard-two',64,[]),('chess960-style',16,['--format','fen','--chess960-style'])]:
 if cpu()-started_cpu>20:
  save(name+'.not_run.json',{'status':'UNVERIFIED_CPU_BUDGET','elapsed_child_cpu':cpu()-started_cpu})
  break
 argv=['taskset','-c',str(core),'nice','-n','19',sys.executable,str(GEN),'--probe',str(EXE),'--out',str(ROOT/name),'--count',str(count),'--seed','20261030','--nodes','1024','--hash-mb','1','--min-plies','6','--max-plies','16','--min-abs-cp','25','--max-abs-cp','150','--max-attempts','2000',*extra]
 record={'argv':argv,'started_utc':now(),'probe_sha256':digest(EXE),'generator_sha256':digest(GEN),'timeout_seconds':60,'cpu_seconds_before':cpu()}
 save(name+'-command.json',record)
 before=time.monotonic();before_cpu=cpu()
 with (ROOT/(name+'.stdout')).open('xb') as out,(ROOT/(name+'.stderr')).open('xb') as err:
  result=subprocess.run(argv,stdout=out,stderr=err,timeout=60,check=False)
 save(name+'-exit.json',{'exit_code':result.returncode,'finished_utc':now(),'wall_seconds':time.monotonic()-before,'child_cpu_seconds':cpu()-before_cpu})
 print(name,result.returncode,round(cpu()-before_cpu,3),'CPU sec',flush=True)
 if result.returncode:raise SystemExit(result.returncode)
save('generation_totals.json',{'total_child_cpu_seconds':cpu()-started_cpu,'finished_utc':now()})
