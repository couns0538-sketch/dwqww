from pathlib import Path
import subprocess,json,hashlib,sys,numpy as np
H=Path('/workspace/forge-nnue-handoff-20261023');R=Path('/workspace/dwqww');O=H/'legacy-loader-final-net-roundtrip-attempt1';O.mkdir(exist_ok=False)
sys.path.insert(0,str(R/'tools/nnue'));from include_parser import load_include
old=H/'legacy-loader-method-roundtrip-attempt1';net=H/'full-trained-net-freeze-attempt1'
def identity(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert identity(R/'tools/tune/nnue_train.cpp')['sha256']=='57186e129418d5aca0fe91211bcc74db2d626e54fbf33df6c85c1972cef0efcd'
inputs=[identity(p) for p in [old/'loader_roundtrip',R/'tools/tune/nnue_train.cpp',R/'include/forge/nnue.hpp',net/'nnue_weights.bin',net/'nnue_weights.inc']]
(O/'inputs-before.json').write_text(json.dumps(inputs,indent=2)+'\n')
cmd=[str(old/'loader_roundtrip'),str(net/'nnue_weights.bin'),str(O/'roundtrip.bin'),str(O/'roundtrip.inc')];(O/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (O/'stdout').open('wb') as out,(O/'stderr').open('wb') as err:r=subprocess.run(cmd,cwd=O,stdout=out,stderr=err,timeout=60)
(O/'actual-exit.json').write_text(json.dumps({'returncode':r.returncode,'owned_process_reaped':True})+'\n');assert r.returncode==0
original=load_include(net/'nnue_weights.inc',128);reloaded=load_include(O/'roundtrip.inc',128)
arrays={n:int(np.count_nonzero(np.asarray(original[n])!=np.asarray(reloaded[n]))) for n in ['w1','b1','w2','b2']}
assert (net/'nnue_weights.bin').read_bytes()==(O/'roundtrip.bin').read_bytes() and not any(arrays.values()) and original['residual'] and reloaded['residual']
assert [identity(Path(i['path'])) for i in inputs]==inputs
result={'status':'PASS_ACTUAL_UNCHANGED_LEGACY_CPP_LOADER_API_ROUNDTRIP_FINAL_NET','source_cpp_sha256':inputs[1]['sha256'],'candidate_inc_sha256':inputs[-1]['sha256'],'float_binary_bytes':(O/'roundtrip.bin').stat().st_size,'binary_byte_exact':True,'quantized_parameters':98689,'quantized_mismatches':arrays,'all_inputs_unchanged':True,'scope':'Existing originalNetwork load/save/write_include via previously compiled same-TU API wrapper; no CLItraining/optimizer/runtimeEvalFile claim','outputs':[identity(O/'roundtrip.bin'),identity(O/'roundtrip.inc')]}
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
