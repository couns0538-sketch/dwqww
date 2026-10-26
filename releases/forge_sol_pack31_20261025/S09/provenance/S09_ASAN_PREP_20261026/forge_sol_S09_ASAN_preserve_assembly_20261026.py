"""Seal transport copies of existing native assembly logs; retain every raw byte."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT=Path('/tmp/forge_sol_S09_native_20261026')
HELPER=Path('/workspace/forge-pack24-20261026/S09_TORCHRAM_20261026/forge_sol_S09_torchram_probe_v2_20261026.py')
HELPER_SHA='e43b6ec82a611e9fd03a1b44b70487189b7df1ed32cfe5734de9e139b055d7bb'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert sha(HELPER)==HELPER_SHA
    spec=importlib.util.spec_from_file_location('s09_existing_gzip_preservation',HELPER)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    out=ROOT/'forge_sol_S09_ASAN_assembly_transport_20261026';out.mkdir(exist_ok=False)
    rows=[]
    for tag in ('Lprime','B'):
        original=ROOT/(tag+'_ASAN_FULL_once_20261026')/'whole_ELF_assembly.stdout'
        manifest=original.parent/('forge_sol_S09_ASAN_'+tag+'_FULL_SHA256SUMS_20261026.txt')
        recorded={name:value for value,name in (line.split('  ',1) for line in manifest.read_text().splitlines())}
        before=sha(original);assert before==recorded[original.name]
        destination=out/('forge_sol_S09_ASAN_'+tag+'_whole_ELF_assembly_20261026.stdout.gz')
        packed=helper.preserve_evidence(original,destination)
        assert packed['raw_sha256']==before and packed['raw_size']==original.stat().st_size
        with (out/(tag+'_GNU_decode.stderr')).open('xb') as stderr:
            process=subprocess.Popen(['gzip','-cd',str(destination)],stdout=subprocess.PIPE,stderr=stderr,start_new_session=True)
            digest=hashlib.sha256();count=0
            try:
                while block:=process.stdout.read(1048576):
                    count+=len(block)
                    if count>packed['raw_size']:raise ValueError('GNU decode exceeded exact original size')
                    digest.update(block)
                code=process.wait(timeout=30)
            finally:
                if process.poll() is None:process.kill();process.wait()
                process.stdout.close()
        assert code==0 and count==packed['raw_size'] and digest.hexdigest()==before
        assert (out/(tag+'_GNU_decode.stderr')).stat().st_size==0 and sha(original)==before
        rows.append({'original':str(original),'original_manifest_sha256':sha(manifest),
            'transport':packed,'Python_decode':'PASS exact rawhash/size in reused preservation helper',
            'GNU_decode':{'returncode':code,'bytes':count,'sha256':digest.hexdigest(),'leader_reaped':True},
            'original_retained_unchanged':True})
    result={'status':'PASS_TWO_LOSSLESS_TRANSPORTS','source_sha256':sha(__file__),
        'reused_helper_sha256':HELPER_SHA,'Torch_or_CPU_library_archive_execution':False,'records':rows}
    target=out/'forge_sol_S09_ASAN_assembly_transport_binding_20261026.json'
    target.open('x').write(json.dumps(result,indent=2)+'\n')
    files=sorted(out.iterdir());manifest=out/'forge_sol_S09_ASAN_assembly_transport_SHA256SUMS_20261026.txt'
    manifest.open('x').write(''.join(sha(p)+'  '+p.name+'\n' for p in files))
    print(json.dumps(result,indent=2));print('transport_manifest_sha256',sha(manifest))


if __name__=='__main__':main()
