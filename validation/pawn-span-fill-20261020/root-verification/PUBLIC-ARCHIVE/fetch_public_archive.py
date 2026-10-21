#!/usr/bin/env python3
"""Public commit-pinned HTTP readback; no credentials, engines, Git or archive edits.

Large public parts are streamed directly into per-part and combined SHA-256
hashers. Original response status/headers, raw small response bodies, stdout and
stderr are preserved under this NEW transport evidence directory. The immutable
local archive is only read to authenticate the expected external manifest.
"""
from pathlib import Path
import datetime,hashlib,json,sys,urllib.error,urllib.request
OUT=Path(__file__).resolve().parent
REPO=Path('/workspace/dwqww')
COMMIT='7aed6c969135c5761f8b7c89db2220668b871db0'
REL='validation/pawn-span-fill-20261020/archive-complete/'
BASE='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+COMMIT+'/'+REL
NAME='forge-pawn-span-fc23918-20261020-complete'
MANIFEST_SHA='9f12841fbdba3a9575d53c36bae5e6ae105d3f5c78a42c44b358c696fb789478'
FINAL_SHA='8504ea11ff5e64de48972289450b5ffc0248979d669bc205028928d74fc9f892'
COMBINED_SHA='ee1bdd21707175cd57107a3a4a1c1daacd106975974b53d40338f0b9f1a22f7e'
COMBINED_BYTES=113855291
BLOCK=1024*1024
REQUEST_HEADERS={'User-Agent':'Forge-public-archive-verification/1.0','Accept-Encoding':'identity'}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(data):return hashlib.sha256(data).hexdigest()
def write_new(name,data):
 with (OUT/name).open('xb') as f:f.write(data)
def json_new(name,data):write_new(name,(json.dumps(data,indent=2)+'\n').encode())
def fetch(filename,label,expected_size,expected_sha,combined=None,save_body=False):
 url=BASE+filename
 row={'filename':filename,'url':url,'method':'GET','request_headers':REQUEST_HEADERS,'started_utc':now(),'expected_size':expected_size,'expected_sha256':expected_sha,'body_saved':save_body}
 hasher=hashlib.sha256();received=0;body=[]
 try:
  request=urllib.request.Request(url,headers=REQUEST_HEADERS,method='GET')
  with urllib.request.urlopen(request,timeout=60) as response:
   row.update({'http_status':response.status,'final_url':response.geturl(),'response_headers':list(response.headers.items())})
   write_new(label+'.headers.txt',response.headers.as_bytes())
   if response.status!=200:raise ValueError('Expected HTTP200')
   while True:
    block=response.read(BLOCK)
    if not block:break
    hasher.update(block);received+=len(block)
    if combined is not None:combined.update(block)
    if save_body:body.append(block)
  if save_body:write_new(label+'.body',b''.join(body))
  row.update({'received_bytes':received,'sha256':hasher.hexdigest()})
  row['passed']=received==expected_size and hasher.hexdigest()==expected_sha
  if not row['passed']:row['error']='Public response size/hash differs from pinned expected identity'
 except Exception as error:
  row.update({'passed':False,'error':type(error).__name__+': '+str(error),'received_bytes':received,'partial_sha256':hasher.hexdigest()})
  if isinstance(error,urllib.error.HTTPError):
   row['http_status']=error.code;row['response_headers']=list(error.headers.items())
   write_new(label+'.error-headers.txt',error.headers.as_bytes())
   write_new(label+'.error-body',error.read())
  if save_body and body and not (OUT/(label+'.body')).exists():write_new(label+'.partial-body',b''.join(body))
 row['completed_utc']=now()
 json_new(label+'.http.json',row)
 print(json.dumps({'label':label,'status':row.get('http_status'),'bytes':received,'sha256':hasher.hexdigest(),'passed':row['passed']}),flush=True)
 return row

def main():
 started=now()
 local_manifest=REPO/REL/(NAME+'.manifest.json')
 local_final=REPO/REL/'FINAL-VERIFICATION.json'
 manifest_bytes=local_manifest.read_bytes();final_bytes=local_final.read_bytes()
 assert sha(manifest_bytes)==MANIFEST_SHA and sha(final_bytes)==FINAL_SHA
 manifest=json.loads(manifest_bytes)
 assert manifest['archive']['size']==COMBINED_BYTES and manifest['archive']['sha256']==COMBINED_SHA
 assert len(manifest['parts'])==2
 command={'command':[sys.executable,'-B',str(Path(__file__).resolve())],'cwd':str(REPO),'started_utc':started,'helper_sha256':sha(Path(__file__).read_bytes()),'commit':COMMIT,'expected_manifest_sha256':MANIFEST_SHA,'expected_final_receipt_sha256':FINAL_SHA,'expected_archive_sha256':COMBINED_SHA,'expected_archive_bytes':COMBINED_BYTES,'network':'Unauthenticated HTTPS GETs to exact public commit; no Git or API mutations','only_write_directory':str(OUT),'skill_reference_qualification':'preserve-chess-evidence SKILL.md read; referenced evidence-contract.md and validation-scope.md resources unavailable through skills provider; no repeated optional troubleshooting','no_engines_compilers_git_or_archive_writes':True}
 json_new('COMMAND.json',command)
 requests=[]
 requests.append(fetch(NAME+'.manifest.json','public-manifest',len(manifest_bytes),MANIFEST_SHA,save_body=True))
 requests.append(fetch('FINAL-VERIFICATION.json','public-final-verification',len(final_bytes),FINAL_SHA,save_body=True))
 combined=hashlib.sha256();total=0
 for index,part in enumerate(manifest['parts'],1):
  assert Path(part['file']).name==part['file'] and part['file']==NAME+'.zip.part'+str(index).zfill(4)
  row=fetch(part['file'],'public-part'+str(index).zfill(4),part['size'],part['sha256'],combined=combined)
  requests.append(row);total+=row['received_bytes']
 parts_pass=all(r['passed'] for r in requests[2:])
 whole_pass=parts_pass and total==COMBINED_BYTES and combined.hexdigest()==COMBINED_SHA
 passed=len(requests)==4 and all(r['passed'] for r in requests) and whole_pass
 receipt={'status':'PASS_PUBLIC_EXACT_COMMIT_ARCHIVE_READBACK' if passed else 'FAILED_PUBLIC_EXACT_COMMIT_ARCHIVE_READBACK_PRESERVED','started_utc':started,'completed_utc':now(),'commit':COMMIT,'source_candidate_commit':'fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e','requests':requests,'combined_archive':{'received_bytes':total,'sha256':combined.hexdigest(),'ordered_part_responses_complete_and_identity_verified':whole_pass},'local_immutable_archive_inputs_modified':False,'large_response_bodies_streamed_not_reconstructed':True,'remote_mutations_engines_compilers_git_executed':False,'scope':'Public byte readback at exact GitHub commit only; no new chess correctness/speed/Elo claim.'}
 json_new('RESULT.json',receipt)
 print(json.dumps({'status':receipt['status'],'requests':len(requests),'combined_archive':receipt['combined_archive']},indent=2),flush=True)
 return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
