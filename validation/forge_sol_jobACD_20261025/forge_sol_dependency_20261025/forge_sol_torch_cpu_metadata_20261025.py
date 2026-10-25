from pathlib import Path
import urllib.request,struct,json,hashlib
out=Path('/workspace/forge-jobACD-dependency-20261025');p=out/'forge_sol_torch_cpu_probe_20261025.json';r=json.loads(p.read_text());url=r['candidate_url'];total=int(r['headers']['content-length'])
def fetch(start,end):
 assert 0<end-start+1<=2*1024*1024,'metadata bound'
 with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}'}),timeout=25) as f:
  assert f.status==206;data=f.read(end-start+2);assert len(data)==end-start+1
  return data
# ZIP central directory only. No wheel body or package installation is downloaded.
tail=fetch(total-65536,total-1);i=tail.rfind(b'PK\x05\x06');assert i>=0
_,disk,cddisk,ndisk,n,size,offset,comment=struct.unpack('<4s4H2LH',tail[i:i+22]);assert disk==cddisk==0 and ndisk==n
cd=fetch(offset,offset+size-1);pos=0;files=[]
while pos<len(cd):
 assert cd[pos:pos+4]==b'PK\x01\x02';h=struct.unpack_from('<4s6H3L5H2L',cd,pos);nl,xl,cl=h[10:13];name=cd[pos+46:pos+46+nl].decode();files.append({'name':name,'compressed':h[8],'uncompressed':h[9]});pos+=46+nl+xl+cl
assert len(files)==n
r['metadata_attempt1']=r['zip_metadata_probe'];r['zip_metadata_probe']={'status':'PASS_RANGE_METADATA_ONLY','wheel_files':n,'wheel_compressed_bytes':total,'unpacked_total_bytes':sum(f['uncompressed'] for f in files),'central_directory_bytes':size,'central_directory_sha256':hashlib.sha256(cd).hexdigest(),'metadata_network_bytes_final_attempt':len(tail)+len(cd),'largest_members':sorted(files,key=lambda x:x['uncompressed'],reverse=True)[:12]}
p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['zip_metadata_probe'],indent=2))
