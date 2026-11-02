import argparse,hashlib,json,pathlib,shutil
p=argparse.ArgumentParser();p.add_argument('--threads',type=int,choices=[1],required=True);p.parse_args()
root=pathlib.Path('D:/a10');out=root/'wt/astra_r10/job1/native-parity'
out.mkdir(exist_ok=False)
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
rows=[]
for label,source in [('evidence',root/'parity-r1'),('source-good',root/'c1'),('source-negative',root/'parity-negative'),('compiler-probe',root/'parity-compiler-probe01')]:
    shutil.copytree(source,out/label)
    for f in sorted(source.rglob('*')):
        if f.is_file():
            dest=out/label/f.relative_to(source)
            assert sha(f)==sha(dest)
            rows.append({'source':str(f),'path':str(dest.relative_to(out)),'sha256':sha(dest)})
(out/'ARCHIVE.json').write_text(json.dumps({'status':'PASS','scope':'Exact evidence copies, not new native execution','files':rows},indent=2))
print('Copied and verified',len(rows),'files')
