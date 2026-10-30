"""Exact, no-field-exclusions comparison of two sealed opening generations.
IDEA_SOURCE: current-helper attribution review and original evidence preservation.
"""
from pathlib import Path
import argparse,hashlib,json

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def verify(folder):
 success=json.loads((folder/'SUCCESS.json').read_text())
 if success['status']!='PASS' or sha(folder/'MANIFEST.sha256.json')!=success['manifest_sha256']:raise ValueError('seal mismatch: '+str(folder))
 for name,digest in json.loads((folder/'MANIFEST.sha256.json').read_text()).items():
  if sha(folder/name)!=digest:raise ValueError('manifest mismatch: '+str(folder/name))
 return {'success_sha256':sha(folder/'SUCCESS.json'),'manifest_sha256':sha(folder/'MANIFEST.sha256.json')}

def differences(a,b,path='$'):
 if type(a) is not type(b):return [{'field':path,'historical':a,'current':b}]
 if isinstance(a,dict):
  result=[]
  for key in sorted(set(a)|set(b)):
   if key not in a or key not in b:result.append({'field':path+'.'+key,'historical_present':key in a,'current_present':key in b,'historical':a.get(key),'current':b.get(key)})
   else:result.extend(differences(a[key],b[key],path+'.'+key))
  return result
 if isinstance(a,list):
  if len(a)!=len(b):return [{'field':path+'.length','historical':len(a),'current':len(b)}]
  return [change for i,(x,y) in enumerate(zip(a,b)) for change in differences(x,y,path+'['+str(i)+']')]
 return [] if a==b else [{'field':path,'historical':a,'current':b}]

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--historical',type=Path,required=True);p.add_argument('--current',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(exist_ok=False)
report={'status':'COMPARISON_COMPLETE','comparison_exclusions':[], 'historical':str(a.historical),'current':str(a.current),'seals':{'historical':verify(a.historical),'current':verify(a.current)},'files':{}}
for name in ('openings.moves','settings.json','generation.json','metadata.jsonl'):
 old=a.historical/name;new=a.current/name
 report['files'][name]={'historical_sha256':sha(old),'current_sha256':sha(new),'byte_identical':old.read_bytes()==new.read_bytes()}
old=[json.loads(line) for line in (a.historical/'metadata.jsonl').read_text().splitlines()]
new=[json.loads(line) for line in (a.current/'metadata.jsonl').read_text().splitlines()]
changes=differences(old,new)
report['metadata_record_counts']={'historical':len(old),'current':len(new)}
report['metadata_field_differences']=changes
report['metadata_difference_count']=len(changes)
report['difference_fields_by_leaf']={}
for change in changes:
 leaf=change['field'].rsplit('.',1)[-1]
 report['difference_fields_by_leaf'][leaf]=report['difference_fields_by_leaf'].get(leaf,0)+1
report['interpretation']='Book/settings/generation and every metadata field compared without exclusions. Binary provenance differences are retained explicitly. This is one finite corpus comparison, not general helper equivalence or a strength result.'
with (a.out/'comparison.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in report.items() if k!='metadata_field_differences'},indent=2))
