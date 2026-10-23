from pathlib import Path,PurePosixPath
import zipfile,json,hashlib,subprocess,stat
h=Path('/workspace/forge-nnue-handoff-20261023');p=h/'forge-6.4.24-nnue-a52efa5f7864-trial-windows-zen5.zip';o=h/'windows-trial-root-package-verification-attempt1';o.mkdir(exist_ok=False)
expected='276598f6ea45eae76cea7016052e00c37e54ccf5c709c48448c1e3aadbf5c3ca';digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest==expected
source='6e9622fd5be18e0155fc3ed5fcf6c4586705cca6';engine='2adc0429d238208ae9ae1a7788d6c570d9eb649b58c737bd8358d6004703518e'
source_count=0
with zipfile.ZipFile(p) as z:
 names=z.namelist();assert len(names)==len(set(names))==310
 root=names[0].split('/')[0];m=json.loads(z.read(root+'/FILES-SHA256.json'));assert len(m)==309
 assert set(names)=={root+'/'+n for n in m}|{root+'/FILES-SHA256.json'}
 for rel,rec in m.items():
  path=PurePosixPath(rel);assert not path.is_absolute() and '..' not in path.parts and '\\' not in rel
  info=z.getinfo(root+'/'+rel);assert not stat.S_ISLNK(info.external_attr>>16)
  data=z.read(info);assert len(data)==rec['bytes'] and hashlib.sha256(data).hexdigest()==rec['sha256']
  if rel.startswith('source/'):
   original=subprocess.check_output(['git','show',source+':'+rel[len('source/'):]],cwd='/workspace/dwqww');assert data==original;source_count+=1
  if rel=='forge-6.4.24-nnue-a52efa5f7864-trial-zen5.exe':assert hashlib.sha256(data).hexdigest()==engine
 assert source_count==74
result={'status':'PASS_ROOT_ALL_DELIVERED_PAYLOAD_BYTES_AND_GIT_SOURCE','archive_sha256':digest,'archive_bytes':p.stat().st_size,'entries':310,'all_manifest_payloads_verified':309,'source_blobs_exactly_match_clean_source':74,'source_commit':source,'delivered_engine_sha256':engine,'scope':'Independent root static artifact/CRC/byte verification; actual Windows runtime evidence is original owner receipts, not rerun here.'}
(o/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
