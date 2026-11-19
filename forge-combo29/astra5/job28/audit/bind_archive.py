"""Verify that the committed Git objects for every completed/partial arm match the audited frozen files."""
import argparse
from hashlib import sha1
from pathlib import Path
import subprocess


def git_blob(data):
    return sha1(b'blob '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('repo',type=Path);p.add_argument('game_root',type=Path);p.add_argument('revision');a=p.parse_args()
    base='forge-combo29/astra5/job28/matches/'
    ref=subprocess.check_output(['git','-C',str(a.repo),'rev-parse',a.revision],text=True).strip()
    items=subprocess.check_output(['git','-C',str(a.repo),'ls-tree','-r',ref,'--',base]).splitlines()
    index={}
    for row in items:
        meta,name=row.split(b'\t',1);index[name.decode()[len(base):]]=meta.split()[2].decode()
    count=0;total=0
    for receipt in sorted((a.game_root/'blocks').glob('block*/M?/receipt.json')):
        arm=receipt.parent;block=arm.parent.name
        for rawroot,prefix in ((arm,f'{block}/{arm.name}/'),(a.game_root/'hold-evidence'/block/arm.name,f'{block}/{arm.name}/hold-evidence/')):
            assert rawroot.is_dir(),rawroot
            for data in sorted(rawroot.iterdir()):
                if not data.is_file():continue
                raw=data.read_bytes();key=prefix+data.name
                assert key in index and index[key]==git_blob(raw),(ref,key,'Git object mismatch or not yet published')
                count+=1;total+=len(raw)
    print('Audited match and hold files agree with committed Git objects:',count,'files,',total,'bytes, revision',ref)
