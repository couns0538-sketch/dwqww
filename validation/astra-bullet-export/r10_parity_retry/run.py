from pathlib import Path
import subprocess,json,hashlib
root=Path(__file__).resolve().parents[3]; ev=Path(__file__).resolve().parent; py='/tmp/astra-a1-torch-cpu-env/bin/python'; ex=root/'tools/bullet/export_forge.py'; fixture='/tmp/astra-r10-export-fixture/roundtrip'; fens='/tmp/forge-astra-r10-buildsrc/opus_r10/parity/fens_12k.txt'; run=[]
def call(name,args,want=0):
 with (ev/(name+'.stdout')).open('xb') as out,(ev/(name+'.stderr')).open('xb') as err: p=subprocess.run(list(map(str,args)),stdout=out,stderr=err)
 run.append({'name':name,'args':list(map(str,args)),'actual_exit':p.returncode,'expected_exit':want})
 (ev/'commands.json').write_text(json.dumps(run,indent=2)+'\n')
 if p.returncode != want:raise RuntimeError(name+' unexpectedexit')
base=[py,ex]
call('synthetic_bridge',[py,root/'tools/bullet/make_checkpoint_fixture.py','--net','/tmp/forge-astra-r10-buildsrc/opus_r10/nets/smoke_k32h3_l64.nnue','--out',fixture,'--l1','64','--l2','32','--l3','32'])
args=['--checkpoint',fixture+'/weights.bin','--manifest',fixture+'/manifest.json']
call('export',base+['export']+args+['--out','/tmp/astra-r10-export-fixture/exported.nnue'])
call('reference',base+['reference']+args+['--fens',fens,'--out',ev/'reference.txt'])
call('native',['/tmp/astra-r10-native/halfka_tool','eval','/tmp/astra-r10-export-fixture/exported.nnue',fens,ev/'native.txt'])
call('compare',base+['compare','--reference',ev/'reference.txt','--native',ev/'native.txt'])
call('mutate',base+['corrupt']+args+['--fens',fens,'--out','/tmp/astra-r10-export-fixture/mutated.nnue'])
call('native_mutated',['/tmp/astra-r10-native/halfka_tool','eval','/tmp/astra-r10-export-fixture/mutated.nnue',fens,ev/'native_mutated.txt'])
call('compare_mutated',base+['compare','--reference',ev/'reference.txt','--native',ev/'native_mutated.txt'],1)
(ev/'scope.txt').write_text('Synthetic Bullet checkpoint from existing R10 smoke net; NOT Bullet training. Exact byte roundtrip plus fresh native vs independent reference. Single-byte mutation expected parity FAIL. Original first invocation missing required dimensions failed; preserved in ../r10_parity/.\n')
print('R10 synthetic bridge/native parity and planted corruption PASS')
