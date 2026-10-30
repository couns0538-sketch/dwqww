import sys,pathlib,json,hashlib,contextlib,subprocess,datetime
root=pathlib.Path('/tmp/forge-astra-fen-convert')
sys.path.insert(0,str(root/'tools/data2'));import convert_dataset as c
from forge_pos import PosReader,PosWriter,text_record
work=pathlib.Path('/tmp/astra-qa-real-slice-holdout-20261030');work.mkdir(exist_ok=False)
evidence=root/'validation/astra-converter-20261030/qa_final_review/real_slice_audit';evidence.mkdir(exist_ok=False)
out=pathlib.Path('/tmp/astra-qa-disk-100k-72i2m604/output_0')
keys=set()
for chunk in c.read_chunks(out):
 with (out/chunk['text']).open() as f:
  keys.update(c.key(text_record(line)[0]) for line in f)
inside=[];outside=[]
with PosReader('/tmp/astra-a1-data-input/extracted/forge_selfplay_003.pos') as reader:
 for record in reader:
  pool=inside if c.key(record) in keys else outside
  if len(pool)<1000:pool.append(record)
  if len(inside)==len(outside)==1000:break
results={}
for label,records,want in [('intentional_overlap',inside,'FAIL'),('zero_overlap',outside,'PASS')]:
 holdouts=[]
 for number,part in [('013',records[:500]),('014',records[500:])]:
  folder=evidence/(label+'_fake_'+number)
  with contextlib.closing(PosWriter(folder,'fake'+number,False)) as writer:
   for r in part:writer.append(r)
   writer.seal()
  p=folder/('fake'+number+'.pos');holdouts.append((number,p,hashlib.sha256(p.read_bytes()).hexdigest()))
 command=[sys.executable,str(root/'tools/data2/audit_holdout_clearance.py'),'--out',str(out),'--work-dir',str(work),'--min-free-mb','0','--report',str(evidence/(label+'.json'))]
 for n,p,h in holdouts:command+=['--holdout-'+n,str(p),'--holdout-'+n+'-rows','500','--holdout-'+n+'-sha256',h]
 (evidence/(label+'.command.json')).write_text(json.dumps(command,indent=2)+'\n')
 with (evidence/(label+'.stdout')).open('xb') as stdout,(evidence/(label+'.stderr')).open('xb') as stderr:
  result=subprocess.run(command,stdout=stdout,stderr=stderr)
 report=json.loads((evidence/(label+'.json')).read_text())
 assert report['status']==want,(label,report)
 assert result.returncode==(0 if want=='PASS' else 1)
 results[label]={'exit_code':result.returncode,'status':report['status'],'output_rows':report['output']['rows'],'overlap_unique_keys':report['overlap_unique_keys'],'overlap_output_rows':report['overlap_output_rows'],'fake_holdout_rows':1000,'index':report['index']}
results['scope']='New audit on49,999 real-derived outputrows using fakeholdouts from real003, NOT private013/014 or trainingclearance. reserve0override forboundedcloudonly.'
results['tool_sha256']=c.sha(root/'tools/data2/audit_holdout_clearance.py')
(evidence/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
