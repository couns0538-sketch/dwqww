"""Read-only source/index validation; explicitly no Torch, NumPy or staging."""
import importlib.util
import argparse
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'forge_sol_S18_train_selected_v2_20261026.py'
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
if args.out.parent.resolve()!=HERE or args.out.exists() or args.out.is_symlink():raise ValueError('NEW result file inside this preparation folder required')
spec=importlib.util.spec_from_file_location('S18_smoke_source_only_validation',SOURCE)
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
if 'torch' in sys.modules or 'numpy' in sys.modules:raise ValueError('source validator must remain Torch/NumPy free')
index,plans,inputs=tool.load_index(tool.DEFAULT_INDEX)
plan=tool.source_plan()
if 'torch' in sys.modules or 'numpy' in sys.modules:raise ValueError('source validation imported a runtime framework')
result={'status':'PASS_SOURCE_AND_READONLY_DATA_INDEX','controller_sha256':tool.sha(SOURCE),'arms_index_sha256':tool.sha(tool.DEFAULT_INDEX),
 'Torch_imports':0,'NumPy_imports':0,'actual_views_staged':0,'trainer_calls':0,'postscore_calls':0,
 'CPU_affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),
 'old_prep_sha256':tool.sha(Path('/tmp/forge_sol_S18_TRAIN_PREP_20261026/forge_sol_S18_train_20261026.py')),
 'prior_unpinned_index_check':'Read-only earlier check returned through tool output only; no runtime or timing claim. This separate pinned check preserves original raw stdout/stderr.',
 'recipe':plan,'plans':{n:{k:v for k,v in value.items() if k!='files'} for n,value in plans.items()},
 'exact_none_trainer_argv':tool.trainer_argv(Path('/tmp/forge_sol_S18_TRAIN_RUN_20261026/none_smoke_v2_new_20261026/none/data'),
 [Path('/tmp/forge_sol_S18_TRAIN_RUN_20261026/none_smoke_v2_new_20261026/none/data')/p.name for p in plans['none']['files'] if p.suffix=='.pos'],
 Path('/tmp/forge_sol_S18_TRAIN_RUN_20261026/none_smoke_v2_new_20261026/none/trainer-run'))}
with args.out.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps(result,sort_keys=True))
