from pathlib import Path
import urllib.request,struct,json,hashlib,zlib,email
out=Path('/workspace/forge-jobACD-dependency-20261025');base=json.loads((out/'forge_sol_torch_cpu_probe_20261025.json').read_text());url=base['candidate_url'];size=int(base['headers']['content-length'])
def fetch(start,end):
 assert 0<end-start+1<=2*1024*1024
 with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}'}),timeout=25) as f:
  assert f.status==206
  data=f.read(end-start+2);assert len(data)==end-start+1
  return data
tail=fetch(size-65536,size-1);i=tail.rfind(b'PK\x05\x06');end=struct.unpack('<4s4H2LH',tail[i:i+22]);cdsize,cdoffset=end[5:7];cd=fetch(cdoffset,cdoffset+cdsize-1);pos=0;found=[]
while pos<len(cd):
 assert cd[pos:pos+4]==b'PK\x01\x02';h=struct.unpack_from('<4s6H3L5H2L',cd,pos);nl,xl,cl=h[10:13];name=cd[pos+46:pos+46+nl].decode()
 if name.endswith('.dist-info/METADATA'):found.append((name,h))
 pos+=46+nl+xl+cl
assert len(found)==1;name,h=found[0];offset=h[16];local=fetch(offset,offset+29);lh=struct.unpack('<4s5H3L2H',local);assert lh[0]==b'PK\x03\x04';nl,xl=lh[9:11];compressed=fetch(offset+30+nl+xl,offset+30+nl+xl+h[8]-1)
data=zlib.decompress(compressed,-15) if h[4]==8 else compressed
assert len(data)==h[9] and zlib.crc32(data)==h[7]
metadata=email.message_from_bytes(data);result={'status':'PASS_METADATA_ONLY','official_wheel_url':url,'metadata_entry':name,'metadata_bytes':len(data),'metadata_sha256':hashlib.sha256(data).hexdigest(),'metadata_crc32_verified':True,'package_name':metadata['Name'],'version':metadata['Version'],'requires_python':metadata['Requires-Python'],'requires_dist':metadata.get_all('Requires-Dist'),'wheel_sha256_from_official_index':json.loads((out/'forge_sol_torch_official_hash_20261025.json').read_text())['wheel_sha256'],'full_wheel_hash_verified':False,'no_install_performed':True}
(out/'forge_sol_torch_metadata_20261025.txt').write_bytes(data)
(out/'forge_sol_torch_requirements_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
