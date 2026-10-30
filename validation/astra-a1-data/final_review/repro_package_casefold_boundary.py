from pathlib import Path
import importlib.util,json,tarfile
here=Path(__file__).resolve().parent
root=here.parents[2]
spec=importlib.util.spec_from_file_location('package_results',root/'validation/astra-a1-data/package_results.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
folder=here/'package_casefold_boundary';folder.mkdir()
source=folder/'source';(source/'A').mkdir(parents=True)
(source/'A'/'child.txt').write_text('Child under directory uppercase A\n')
(source/'a').write_text('File lowercase a\n')
result=module.package([{'sourcepath':str(source),'archiveprefix':'evidence','kind':'auxiliary'}],folder/'result.tar.gz')
with tarfile.open(folder/'result.tar.gz') as archive:
    members=[{'name':x.name,'isdir':x.isdir()} for x in archive]
folded={}
collisions=[]
for member in members:
    key=member['name'].casefold()
    if key in folded:collisions.append([folded[key],member])
    folded[key]=member
receipt={'package_status':result['status'],'members':members,'windows_casefold_file_directory_collisions':collisions}
(folder/'repro.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
assert not collisions,'Publisher accepted a file/directory name collision on case-insensitive extraction'
