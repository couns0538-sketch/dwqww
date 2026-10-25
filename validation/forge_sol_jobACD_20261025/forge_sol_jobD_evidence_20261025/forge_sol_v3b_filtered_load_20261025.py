# Actual unchanged v3b full RAM/mmap readers, plus independent retained-field check.
from pathlib import Path
import hashlib,importlib.util,json,sys,numpy as np
h=Path('/workspace/forge-jobACD-20261025');trainer=h/'forge_sol_jobACD_pack_20261025/06_jobD/trainer/train_resid_v3b.py';expected='5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f';assert hashlib.sha256(trainer.read_bytes()).hexdigest()==expected
spec=importlib.util.spec_from_file_location('forge_actual_v3b',trainer);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=Path('/workspace/forge-jobACD-D-20261025/forge_sol_data32_filtered_threshold300_20261025');files=sorted(p.glob('*.pos'));ram=m.load_set(files,p);mapped=m.load_set_mmap(files,p);assert ram['n']==mapped['n']==157666;idx=np.arange(ram['n'])
for key in ['boards','score','meta','hce']:assert np.array_equal(ram[key],mapped[key][idx]),key
sample=h/'forge_sol_jobACD_pack_20261025/06_jobD/data32_sample/data32_sample_50k';original=m.load_set(sorted(sample.glob('t*.pos')),sample);lookup={}
for i in range(original['n']):
 meta=int(original['meta'][i]);key=original['boards'][i].tobytes()+bytes([meta&1]);assert key not in lookup
 lookup[key]=(int(original['score'][i]),meta,int(original['hce'][i]))
for i in range(ram['n']):
 meta=int(ram['meta'][i]);key=ram['boards'][i].tobytes()+bytes([meta&1]);assert lookup[key]==(int(ram['score'][i]),meta,int(ram['hce'][i]))
r={'status':'PASS_ACTUAL_UNCHANGED_V3B_RAM_AND_MMAP','trainer_sha256':expected,'original_records':original['n'],'filtered_records':ram['n'],'all_four_arrays_RAM_mmap_equal':True,'retained_records_original_score_meta_HCE_equal':ram['n'],'training_gain_claim':False};(h/'forge_sol_v3b_filtered_load_20261025.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
