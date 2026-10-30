"""Regenerate min25 bookkeeping from archived responses, without executing Forge."""
from pathlib import Path
import dataclasses,datetime,gzip,hashlib,json,sys,time
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'tools/data'))
import generate_openings as target
here=Path(__file__).resolve().parent
source=root/'validation/astra-a1-data/openings-unbalanced-25/standard-one'
settings=json.loads((source/'settings.json').read_text());process=json.loads((source/'probe/process.json').read_text())
with gzip.open(source/'probe/requests.tsv.gz','rt') as stream:requests=[line.rstrip('\n').split('\t') for line in stream]
with gzip.open(source/'probe/responses.jsonl.gz','rt') as stream:responses=[json.loads(line) for line in stream]
assert len(requests)==len(responses)==process['successful_requests']==process['response_count']
assert process['returncode']==0 and process['binary_unchanged'] is True
class ArchivedProbe:
    binary_sha256=process['binary_sha256']
    def __init__(self):self.cursor=0
    def query(self,fen,op='analyze',request_id=None):
        expected=requests[self.cursor];response=responses[self.cursor]
        assert expected==[str(self.cursor),op,fen]
        assert response['id']==str(self.cursor) and response['fen']==fen
        assert response['operation']==op and response['ok'] is True
        assert response['nodes_limit']==settings['nodes'] and response['hash_mb']==settings['hash_mb'] and response['threads']==1
        if op=='analyze':
            assert response['analyzed'] is True and response['depth']>0 and 0<response['nodes']<=settings['nodes']
        self.cursor+=1
        return response
start=datetime.datetime.now(datetime.timezone.utc).isoformat();clock=time.monotonic()
config=target.Config(out=here/'opening_replay',**{f.name:settings[f.name] for f in dataclasses.fields(target.Config) if f.name!='out'})
probe=ArchivedProbe();result=target.generate(config,probe)
assert probe.cursor==len(requests)
files={}
for filename in ('settings.json','generation.json','metadata.jsonl','openings.moves'):
    actual=(config.out/filename).read_bytes();expected=(source/filename).read_bytes()
    assert actual==expected,filename
    files[filename]={'bytes':len(actual),'sha256':hashlib.sha256(actual).hexdigest()}
report={'status':'PASS_ARCHIVED_RESPONSE_REPLAY','started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wall_seconds':time.monotonic()-clock,'queries_replayed':probe.cursor,'native_searches':0,'attempts':result['attempts'],'accepted':result['accepted'],'byte_identical_files':files,'scope':'Current Python opening generator deterministically reproduces original min25 metadata/book and request order from exact archived native responses. No independent second native generation or Windows execution.'}
(here/'opening_replay.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
