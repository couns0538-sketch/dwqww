"""S18 source-prepared five-arm wrapper. Import/--describe never imports Torch.

Execution needs a separate exact root grant. The original trainer, reader,
targets, optimizer and training loop remain unchanged. Synthetic runs only
qualify the pipeline; neither real holdout isolation nor strength is established.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import math
import re
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace

FILES=Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
TRAINER=FILES/'06_jobD/trainer/train_resid_v3b.py'
ADAM=TRAINER.with_name('qa_adam_dml.py')
RECIPE=Path('/workspace/forge-pack24-20261026/S09/forge_sol_S09_f006_recipe_20261026.json')
DIAGNOSTIC=Path('/workspace/forge-pack24-20261026/S09_TORCHRAM_20261026/f023_forensics_20261026/forge_sol_S09_shutdown_diagnostic_20261026.py')
OWNED=Path('/workspace/forge-pack24-20261026/S08/forge_sol_S08_build_window_subreaper_20261026.py')
HOLDOUT=FILES/'06_jobD/data32_sample/data32_sample_50k'
PRIVATE=Path('/workspace/.cloud-setup/nnue-pipeline-20261023-venv')
LIBDIR=PRIVATE/'lib/python3.12/site-packages/torch/lib'
OUTROOT=Path('/tmp/forge_sol_S18_TRAIN_RUN_20261026')
DEFAULT_INDEX=Path(__file__).with_name('forge_sol_S18_training_arms_index_20261026.json')
POSTSCORE_PROTOCOL=Path(__file__).with_name('forge_sol_S18_postscore_preregistration_20261026.json')
ARMS={'none':None,'t200':200,'t300':300,'t400':400,'t500':500}
PINS={TRAINER:'5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f',
      ADAM:'799faa89bc7b8dbd8c9a8747dd6658085eb0a69b84800af191db5ca7fd660cba',
      RECIPE:'97b4a2a85f76af148055db951e7922ce92b535a55e33c3c94b96c27be137d800',
      DIAGNOSTIC:'84b3f7f5a773340dfaddb3c2942d117a03ee68f82faaec7bfef756a6e4648729',
      OWNED:'85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0',
      HOLDOUT/'h000.pos':'92c40ae25c3b650db9f5db235786133afed3e9a8f6691e7860dff6bdc5aa11b3',
      HOLDOUT/'h000.hce':'212e51e6c108f3ff6b879b0f247277925f9483102e34230b5024e5fb7ef2cc44',
      POSTSCORE_PROTOCOL:'aa8fed66b82399b62f77cf792f25d2582771aefabed39ab08c0e5e63ab771d7e'}


ACCEPTED_NET=FILES/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src/src/nnue_weights.inc'
F006_REFERENCE=FILES/'03_nets/resid_h256_e48_f006_b06_ep48.inc'
S09_SUCCESS=Path('/tmp/forge_sol_S09_native_20261026/full50k_actual_f006_holdout_CPU3_once_20261026/forge_sol_S09_full_holdout_result_20261026.json')
PINS.update({ACCEPTED_NET:'74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b',
             F006_REFERENCE:'0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661',
             S09_SUCCESS:'63487797d80f96de9cbb0cfad7a8de3487f58d0877ecd6bb662b0f1e25fc4fda',
             PRIVATE/'bin/python':'fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7'})

def free_disk_bytes(path):
    value=os.statvfs(path)
    return value.f_bavail*value.f_frsize

def require_disk_reserve(grant,extra=0):
    free=free_disk_bytes('/tmp')
    if free<grant['minimum_free_disk_bytes']+extra:raise ValueError('insufficient /tmp reserve for S11 parity')
    return free


def fingerprint(path):
    sha=hashlib.sha256();md5=hashlib.md5();size=0
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):sha.update(block);md5.update(block);size+=len(block)
    return {'sha256':sha.hexdigest(),'md5':md5.hexdigest(),'bytes':size,'mode':Path(path).stat().st_mode&0o777}

def sha(path):return fingerprint(path)['sha256']

def verify_pins():
    values={str(path):sha(path) for path in PINS}
    if any(values[str(path)]!=expected for path,expected in PINS.items()):raise ValueError('pinned source/holdout changed')
    return values

def original_tree():
    if sha(TRAINER)!=PINS[TRAINER]:raise ValueError('original trainer SHA changed')
    return ast.parse(TRAINER.read_text(),filename=str(TRAINER))

def original_parser():
    """Read argparse calls from the pinned AST; never import the trainer."""
    tree=original_tree();main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    parser=argparse.ArgumentParser()
    names={'int':int,'float':float}
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='K_DEFAULT' for t in node.targets):names['K_DEFAULT']=ast.literal_eval(node.value)
    def value(node):return names[node.id] if isinstance(node,ast.Name) else ast.literal_eval(node)
    for node in main.body:
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
            call=node.value
            if isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id=='ap' and call.func.attr=='add_argument':
                parser.add_argument(*(value(x) for x in call.args),**{k.arg:value(k.value) for k in call.keywords})
    return parser

def original_count(path):
    # Reuse precisely the original stdlib-only read_pos_header function AST.
    node=next(n for n in original_tree().body if isinstance(n,ast.FunctionDef) and n.name=='read_pos_header')
    space={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(TRAINER),'exec'),space)
    return space['read_pos_header'](path)

def trainer_argv(view,train_files,run):
    return ['--train',*[str(p) for p in sorted(train_files)],'--holdout',str(view/'h000.pos'),'--hce-dir',str(view),
            '--device','cpu','--shape','256','--residual','--epochs','2','--batch-size','8192','--lr','0.000707',
            '--warmup-steps','300','--blend-end','0.6','--seed','25','--final-full-val','--run-dir',str(run)]

def source_plan():
    pins=verify_pins();recipe=json.loads(RECIPE.read_text())
    effective=vars(original_parser().parse_args(trainer_argv(Path('/tmp/S18-view'),[Path('/tmp/S18-view/t.pos')],Path('/tmp/S18-new-run'))))
    observed=recipe['actual_observed']
    for observed_key,parsed_key in [('hidden','shape'),('residual','residual'),('batch_size','batch_size'),('lr_as_displayed','lr'),('warmup_steps','warmup_steps'),('blend_end','blend_end'),('seed','seed'),('final_full_validation','final_full_val')]:
        if effective[parsed_key]!=observed[observed_key]:raise ValueError('f006 observed recipe mismatch: '+observed_key)
    explicit={'train','holdout','hce_dir','device','shape','residual','epochs','batch_size','lr','warmup_steps','blend_end','seed','final_full_val','run_dir'}
    return {'status':'SOURCE_PREPARED_NOT_EXECUTED','observed_f006':observed,'effective':effective,
            'epoch_exception':{'observed':48,'requested':2},'initialization':'original seeded from-scratch residual model; no f006 weights or resume',
            'inherited_current_source_defaults_not_recovered_f006':{k:v for k,v in effective.items() if k not in explicit},
            'missing_historical_settings':recipe['referenced_settings_absent'],'filter_seed':20261025,'training_seed':25,
            'native_final_validation':{'supplied_rows':50000,'evaluated_rows':49152,'dropped_tail_rows':848,'batch_size':8192},
            'separate_post_training_validation':{'rows':50000,'dropped_tail_rows':0,'batch_size':8192,'last_batch_rows':848,'blends':[1.0,0.6,0.8],'checkpoint_selection':'FINAL_EPOCH2_PRESELECTED','preregistration_sha256':PINS[POSTSCORE_PROTOCOL]},
            'warmup_notice':'300 warmup steps retained; two-epoch sample arms have about38–48 steps and remain in warmup',
            'supported_runtime_scope':'synthetic_pipeline_only_known_h000','real_data_training':'BLOCKED_PENDING_REVIEW_OF_ACTUAL_PRODUCTION_S16_AND_OWNER_013_014_EVIDENCE',
            'source_pins':pins,'ordinary_Torch_environment_ready':False,'training_approved':False,'old_150_second_failure':'UNCHANGED_FAIL_NOT_RETRIED'}

def load_index(path):
    index=json.loads(Path(path).read_text())
    if index.get('schema')!='forge-S18-arms-v1' or index.get('status')!='PASS_DATA_PREPARATION' or set(index.get('arms',{}))!=set(ARMS):raise ValueError('complete PASS five-arm index required')
    for suffix in ('pos','hce'):
        original=HOLDOUT/('h000.'+suffix);meta=fingerprint(original)
        if Path(index['holdout'][suffix]).resolve()!=original.resolve() or index['holdout'][suffix+'_md5']!=meta['md5'] or index['holdout'][suffix+'_sha256']!=meta['sha256']:raise ValueError('same original h000 pair required')
    inputs={};plans={}
    for name,threshold in ARMS.items():
        arm=index['arms'][name];source=Path(arm['source_dir']).resolve(strict=True)
        report=source/'forge_sol_datafilter_summary_20261026.json';manifest=source/'forge_sol_datafilter_manifest_20261026.md5'
        if arm['threshold']!=threshold or sha(report)!=arm['summary_sha256'] or sha(manifest)!=arm['output_manifest_sha256']:raise ValueError('arm threshold/summary/manifest mismatch: '+name)
        summary=json.loads(report.read_text())
        if summary['disagreement_threshold']!=threshold or summary['supplied_holdout_overlap']!=0 or summary['output_duplicate_positions']!=0 or summary['input_md5']['h000.pos']!=index['holdout']['pos_md5']:raise ValueError('arm supplied-h000 qualification failed')
        pos=sorted(source.glob('*.pos'))
        expected={p for p in summary['outputs'] if p.endswith('.pos')}
        if not pos or {p.name for p in pos}!=expected or 'h000.pos' in expected:raise ValueError('exact train-only source pair inventory required')
        selected=[];count=0
        for p in pos:
            count+=original_count(p)
            for file in (p,p.with_suffix('.hce')):
                meta=fingerprint(file)
                if meta['md5']!=summary['outputs'].get(file.name):raise ValueError('sealed arm output checksum mismatch')
                inputs[str(file)]=meta;selected.append(file)
        if count!=summary['totals']['kept'] or count!=arm['kept'] or arm['input']!=summary['totals']['input'] or arm['dropped']!=summary['totals']['dropped']:raise ValueError('arm counts mismatch')
        # Preserve none's truthful input-identity proof; it is not a claimed repeat.
        if name=='none':
            if arm['proof_kind']!='REUSED_S16_OFF_INPUT_IDENTITY' or arm['repeat_verified'] is not False:raise ValueError('none identity proof must remain truthful')
        elif arm['repeat_verified'] is not True:raise ValueError('filtered arm repeat proof required')
        inputs[str(report)]=fingerprint(report);inputs[str(manifest)]=fingerprint(manifest)
        plans[name]={'files':selected,'rows':count,'steps_per_epoch':count//8192,'total_steps':2*(count//8192),'train_tail_per_epoch':count%8192,'summary_sha256':arm['summary_sha256'],'proof_kind':arm['proof_kind'],'repeat_verified':arm['repeat_verified']}
    for file in (HOLDOUT/'h000.pos',HOLDOUT/'h000.hce'):inputs[str(file)]=fingerprint(file)
    return index,plans,inputs

def require_scope(scope,index,certificate):
    if scope=='synthetic_pipeline_only':
        if index.get('sample_is_synthetic') is not True:raise ValueError('synthetic pipeline scope requires declared synthetic sample')
        return 'PIPELINE_ONLY_SYNTHETIC'
    if index.get('sample_is_synthetic') is True:raise ValueError('synthetic sample cannot be relabeled real')
    raise ValueError('real-data training blocked: actual completed PRODUCTION S16 result/certificate requires review: sealed_for_training and game_overlap_verified true, authentic_game_overlap=0, supplied_holdout_overlap=0, owner-attested013/014 hashes, exact producer SHA and manifest. No real-certificate schema is inferred by this synthetic-only runner.')

def selected_arms(names):
    if not isinstance(names,list) or not names or names!=[name for name in ARMS if name in names]:
        raise ValueError('grant arms must be a nonempty canonical ordered subset without duplicates')
    return names

def child_paths(armout):
    armout=Path(armout)
    return {'cwd':armout/'cwd','env':{'TMPDIR':str(armout/'tmp'),'XDG_CACHE_HOME':str(armout/'cache'),
        'TORCH_HOME':str(armout/'cache/torch'),'TORCH_EXTENSIONS_DIR':str(armout/'cache/extensions'),
        'TORCHINDUCTOR_CACHE_DIR':str(armout/'cache/inductor')}}

def read_rss_bytes(pid):
    with (Path('/proc')/str(pid)/'status').open('rb') as stream:raw=stream.read(8193)
    if len(raw)>8192:raise ValueError('owned status read cap exceeded')
    for line in raw.decode().splitlines():
        if line.startswith('VmRSS:'):
            fields=line.split()
            if len(fields)!=3 or fields[2]!='kB' or int(fields[1])<0:raise ValueError('malformed owned VmRSS')
            return int(fields[1])*1024
    raise ValueError('owned VmRSS unavailable')

class RSSGuard:
    """Poll-time guard for this actual NEW Popen only; unknown RSS fails closed."""
    def __init__(self,process,limit,disk_floor=0):
        self.process=process;self.limit=limit;self.disk_floor=disk_floor;self.minimum_sampled_free_disk_bytes=None;self.stop_reason=None;self.error=None
        self.max_sampled_rss_bytes=None;self.first_signal_monotonic=None;self.kill_sent=False
    def __getattr__(self,name):return getattr(self.process,name)
    def poll(self):
        result=self.process.poll()
        if result is not None:return result
        if self.stop_reason is None:
            try:
                rss=read_rss_bytes(self.process.pid)
                self.max_sampled_rss_bytes=max(self.max_sampled_rss_bytes or 0,rss)
                if rss>self.limit:self.stop_reason='RSS_LIMIT'
            except (OSError,ValueError,UnicodeError) as error:
                if self.process.poll() is not None:return self.process.returncode
                self.stop_reason='RSS_UNAVAILABLE';self.error=type(error).__name__+': '+str(error)[:500]
        if self.stop_reason is None and self.disk_floor:
            try:
                free=free_disk_bytes('/tmp');self.minimum_sampled_free_disk_bytes=min(self.minimum_sampled_free_disk_bytes if self.minimum_sampled_free_disk_bytes is not None else free,free)
                if free<self.disk_floor:self.stop_reason='DISK_RESERVE'
            except OSError as error:self.stop_reason='DISK_UNAVAILABLE';self.error=type(error).__name__+': '+str(error)[:500]
        if self.stop_reason:
            now=time.monotonic()
            if self.first_signal_monotonic is None:
                self.first_signal_monotonic=now
                try:os.killpg(self.process.pid,signal.SIGTERM)
                except ProcessLookupError:pass
            elif not self.kill_sent and now-self.first_signal_monotonic>=.2:
                self.kill_sent=True
                try:os.killpg(self.process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
        return self.process.poll()

def validate_grant(path,index_path,cpu):
    if path is None:raise ValueError('separate exact root grant required before execution')
    grant=json.loads(Path(path).read_text())
    if (grant.get('status')!='AUTHORIZED_S18_TRAINING' or grant.get('controller_sha256')!=sha(__file__)
        or grant.get('data_index_sha256')!=sha(index_path)
        or grant.get('cpu')!=[cpu] or grant.get('nice')!=19):raise ValueError('root grant does not bind exact controller/index/arms/CPU')
    selected_arms(grant.get('arms'))
    for name in ('work_seconds_per_arm','hard_seconds_per_arm','address_space_bytes','rss_limit_bytes','minimum_free_disk_bytes'):
        if type(grant.get(name)) is not int or grant[name]<=0:raise ValueError('explicit positive root resource limits required')
    if grant['hard_seconds_per_arm']-grant['work_seconds_per_arm']<60:raise ValueError('at least60s cleanup reserve required')
    if grant['rss_limit_bytes']>3221225472 or grant['minimum_free_disk_bytes']<6979321856:raise ValueError('RSS must be at most3GiB and disk reserve at least6.5GiB')
    if not isinstance(grant.get('authorization_reference'),str) or not grant['authorization_reference'].strip():raise ValueError('root authorization reference required')
    return grant

def validate_paths(args,grant):
    top=Path(grant.get('out',''))
    if not top.is_absolute() or top.resolve()!=top or top==OUTROOT or not top.is_relative_to(OUTROOT):raise ValueError('root grant output path must be an exact S18 /tmp descendant')
    expected=top/args.arm if args.child else top
    if args.out!=expected or args.out.resolve()!=args.out:raise ValueError('output path differs from root grant')
    if args.scope!=grant.get('scope'):raise ValueError('scope differs from root grant')
    if args.child and args.views!=top/'copied_views.json':raise ValueError('child copied views path differs from grant output')
    if args.child and args.arm not in selected_arms(grant.get('arms')):raise ValueError('child arm was not granted')

def stage_views(out,plans,inputs):
    views={}
    for name,plan in plans.items():
        view=out/name/'data';view.mkdir(parents=True,mode=0o700)
        inventory={}
        for source in [*plan['files'],HOLDOUT/'h000.pos',HOLDOUT/'h000.hce']:
            dest=view/source.name;before=fingerprint(source)
            if before!=inputs[str(source)]:raise ValueError('source changed before copy')
            with dest.open('xb'):pass
            shutil.copyfile(source,dest)
            if dest.stat().st_nlink!=1 or os.path.samefile(source,dest):raise ValueError('independent copied file required')
            copied=fingerprint(dest)
            if any(copied[k]!=before[k] for k in ('sha256','md5','bytes')) or fingerprint(source)!=before:raise ValueError('copy/source identity changed')
            dest.chmod(0o444);inventory[str(dest)]=fingerprint(dest)
        views[name]={'data':str(view),'train':[str(view/p.name) for p in plan['files'] if p.suffix=='.pos'],'inventory':inventory}
    return views

def validate_copied_view(view,armout,plan,inputs):
    data=armout/'data';sources=[*plan['files'],HOLDOUT/'h000.pos',HOLDOUT/'h000.hce']
    expected={str(data/p.name):inputs[str(p)] for p in sources}
    if (view['data']!=str(data) or view['train']!=[str(data/p.name) for p in plan['files'] if p.suffix=='.pos']
        or set(view['inventory'])!=set(expected)):raise ValueError('copied train/view inventory does not match indexed source pairs')
    for path,original in expected.items():
        dest=Path(path);meta=fingerprint(dest)
        if dest.resolve()!=dest or dest.stat().st_nlink!=1 or meta['mode']!=0o444 or view['inventory'][path]!=meta:raise ValueError('copied inventory/path/mode changed')
        if any(meta[k]!=original[k] for k in ('sha256','md5','bytes')):raise ValueError('copied bytes differ from indexed source')

def module(path,name):
    if sha(path)!=PINS[path]:raise ValueError('pinned runtime helper changed')
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value

def postscore_ranges():
    return [(begin,min(begin+8192,50000)) for begin in range(0,50000,8192)]

def final_checkpoint(run,training_rows):
    return run/('epoch002-step'+format(2*(training_rows//8192),'09d')+'.pt')

def postscore_final_checkpoint(old,run,training_rows,view,journal,diagnostic):
    """Separately score final epoch2, including the tail; never optimize/export."""
    import torch
    import numpy as np
    checkpoint=final_checkpoint(run,training_rows);checkpoint_before=fingerprint(checkpoint)
    hold_before={str(p):fingerprint(p) for p in (view/'h000.pos',view/'h000.hce')}
    rng_before=torch.random.get_rng_state().clone()
    diagnostic.emit(journal,'S18_POSTSCORE_BEGIN',checkpoint=checkpoint.name,rows=50000,preregistration_sha256=PINS[POSTSCORE_PROTOCOL])
    def model_hash(model):
        value=hashlib.sha256()
        for name,tensor in sorted(model.state_dict().items()):
            value.update(name.encode()+b'\0'+str(tensor.dtype).encode()+b'\0'+str(tuple(tensor.shape)).encode()+b'\0')
            value.update(tensor.detach().cpu().contiguous().numpy().tobytes())
        return value.hexdigest()
    try:
        ck=torch.load(checkpoint,map_location='cpu',weights_only=True)
        if ck['next_epoch']!=2 or ck['step']!=2*(training_rows//8192) or ck['config']['hidden']!=256 or ck['config']['residual'] is not True or ck['config']['qat'] is not True:raise ValueError('preselected epoch2 checkpoint/config mismatch')
        model=old.NNUE(256,qat=True,residual=True).cpu();model.load_state_dict(ck['model'],strict=True);model.eval()
        torch.random.set_rng_state(rng_before)
        state_before=model_hash(model);data=old.load_set([str(view/'h000.pos')],str(view))
        if data['n']!=50000:raise ValueError('postscore requires all50000 original h000 rows')
        blends=(1.0,0.6,0.8);net_sse={str(b):0. for b in blends};hce_sse={str(b):0. for b in blends};count=0;batches=[]
        with torch.no_grad():
            for begin,end in postscore_ranges():
                codes,stm,wres,score,hce=old.make_batch(data,np.arange(begin,end,dtype=np.int64))
                c=torch.from_numpy(codes.astype(np.int64));s=torch.from_numpy(stm.astype(np.int64))
                wr=torch.from_numpy(wres.astype(np.float32));sc=torch.from_numpy(score.astype(np.float32))
                hc=torch.from_numpy(hce.astype(np.float32))*(2.25/400.)
                logit=model(c,s,hc);pred=torch.sigmoid(logit);baseline=torch.sigmoid(hc)
                if not torch.isfinite(logit).all():raise ValueError('nonfinite postscore model logit')
                for blend in blends:
                    target=old.targets(sc,s,wr,2.25,blend)[2]
                    if not torch.isfinite(target).all():raise ValueError('nonfinite original postscore target')
                    net_sse[str(blend)]+=float((pred.double()-target.double()).square().sum())
                    hce_sse[str(blend)]+=float((baseline.double()-target.double()).square().sum())
                count+=end-begin;batches.append(end-begin)
                diagnostic.emit(journal,'S18_POSTSCORE_BATCH',begin=begin,end=end)
        state_after=model_hash(model)
        if count!=50000 or batches!=[8192]*6+[848] or state_after!=state_before or fingerprint(checkpoint)!=checkpoint_before or any(fingerprint(p)!=m for p,m in hold_before.items()):raise ValueError('postscore count/state/checkpoint/holdout integrity failed')
        result={'rows':count,'batch_size':8192,'batch_sizes':batches,'last_batch_rows':848,'dropped_tail_rows':0,
                'checkpoint_selection':'FINAL_EPOCH2_PRESELECTED','checkpoint':checkpoint.name,'checkpoint_sha256_before':checkpoint_before['sha256'],'checkpoint_sha256_after':sha(checkpoint),
                'net_MSE':{b:v/count for b,v in net_sse.items()},'HCE_baseline_MSE':{b:v/count for b,v in hce_sse.items()},
                'aggregation':'float64 squared errors summed by rows /50000; original float32 predictions/targets promoted before subtraction',
                'model_state_sha256_before':state_before,'model_state_sha256_after':state_after,'state_unchanged':True,
                'holdout_before':hold_before,'holdout_unchanged':True,'weight_updates':0,'exports':0,'original_trainer_sha256':PINS[TRAINER],'preregistration_sha256':PINS[POSTSCORE_PROTOCOL]}
    finally:torch.random.set_rng_state(rng_before)
    if not torch.equal(torch.random.get_rng_state(),rng_before):raise ValueError('postscore Torch RNG state changed')
    result['Torch_RNG_preserved']=True;diagnostic.emit(journal,'S18_POSTSCORE_DONE',rows=50000)
    return result

def native_final_metric(text):
    lines=[line for line in text.splitlines() if line.startswith('FINAL FULL HOLDOUT n=')]
    if len(lines)!=1:raise ValueError('exactly one native FINAL FULL HOLDOUT line required')
    match=re.fullmatch(r'FINAL FULL HOLDOUT n=([0-9,]+): net mse_teacher=(\S+) mse_b0\.6=(\S+) mse_b0\.8=(\S+) \| HCE (\S+)/(\S+)/b0\.8 (\S+)',lines[0])
    if match is None or int(match[1].replace(',',''))!=49152:raise ValueError('native metric must report original49152 rows')
    values=[float(match[i]) for i in range(2,8)]
    if not all(math.isfinite(v) for v in values):raise ValueError('nonfinite native metric')
    return {'actual_stdout_line':lines[0],'evaluated_rows':49152,'supplied_rows':50000,'dropped_tail_rows':848,
            'net_MSE':dict(zip(('1.0','0.6','0.8'),values[:3])),'HCE_baseline_MSE':dict(zip(('1.0','0.6','0.8'),values[3:])),
            'precision':'original native stdout six decimals; separate all50000 postscore retains full JSON precision'}

def run_child(args,grant,index,plans,inputs,scope):
    paths=child_paths(args.out)
    if Path.cwd()!=paths['cwd'] or any(os.environ.get(k)!=v for k,v in paths['env'].items()):raise ValueError('child requires exact NEW per-arm CWD/cache/tmp paths')
    views=json.loads(args.views.read_text());view=views[args.arm]
    validate_copied_view(view,args.out,plans[args.arm],inputs)
    diagnostic=module(DIAGNOSTIC,'forge_s18_frozen_diagnostic');load_only=diagnostic._work
    def work(_case,journal,report):
        load_only('load_only',journal,report);report['work_complete']=False
        trainer=module(TRAINER,'forge_s18_original_v3b')
        argv=trainer_argv(Path(view['data']),[Path(p) for p in view['train']],args.out/'trainer-run')
        saved=sys.argv
        try:
            sys.argv=[str(TRAINER),*argv];diagnostic.emit(journal,'S18_TRAINER_MAIN_BEGIN',arm=args.arm)
            code=trainer.main()
        finally:sys.argv=saved
        if code!=0:raise ValueError('original trainer returned '+str(code))
        diagnostic.emit(journal,'S18_TRAINER_MAIN_DONE',arm=args.arm)
        report['separate_post_training_all50000']=postscore_final_checkpoint(trainer,args.out/'trainer-run',plans[args.arm]['rows'],Path(view['data']),journal,diagnostic)
        if any(fingerprint(p)!=m for p,m in view['inventory'].items()):raise ValueError('staged input changed during trainer')
        report.update(work_complete=True,scope=scope,arm=args.arm,trainer_returncode=code,training_approved=False,
                      original_trainer_sha256=PINS[TRAINER],native_FINAL_FULL_rows=49152,native_dropped_tail_rows=848,
                      authentic_game_overlap='UNVERIFIED' if scope=='PIPELINE_ONLY_SYNTHETIC' else 'OWNER_CERTIFICATE_REQUIRED',
                      real_013_014_overlap='UNVERIFIED_SYNTHETIC_PIPELINE' if scope=='PIPELINE_ONLY_SYNTHETIC' else 'OWNER_CERTIFICATE_ONLY')
        diagnostic.emit(journal,'S18_TRAIN_AND_POSTSCORE_DONE',arm=args.arm)
    diagnostic._work=work
    return diagnostic.child(SimpleNamespace(out=args.out,toy_protocol_only=False,case='S18_'+args.arm,work_seconds=grant['work_seconds_per_arm']))

def run_controller(args,grant,index,plans,inputs,scope):
    out=args.out
    if not out.is_absolute() or out.resolve()!=out or not out.is_relative_to(OUTROOT) or out==OUTROOT or out.exists() or not out.parent.is_dir():raise ValueError('fresh exact S18 /tmp run descendant with existing parent required')
    if sorted(os.sched_getaffinity(0))!=[args.cpu] or os.getpriority(os.PRIO_PROCESS,0)!=19:raise ValueError('exact granted CPU and nice19 required')
    prepared=source_plan()
    disk_before=require_disk_reserve(grant,67108864)
    selected=selected_arms(grant['arms'])
    out.mkdir(mode=0o700);result={'status':'FAIL_S18_TRAINING','scope':scope,'training_approved':False,'source_plan':prepared,'root_grant':grant,'requested_arms':selected,'all_five_arms_completed':False,'arms':{},'inputs_before':inputs,'free_disk_before_bytes':disk_before,'expected_new_data_checkpoint_cache_allowance_bytes':67108864}
    try:
        views=stage_views(out,{name:plans[name] for name in selected},inputs);views_path=out/'copied_views.json';views_path.write_text(json.dumps(views,indent=2,sort_keys=True)+'\n')
        diagnostic=module(DIAGNOSTIC,'forge_s18_monitor');owned=module(OWNED,'forge_s18_owned_group')
        env=os.environ.copy();env.pop('LD_PRELOAD',None);env.pop('PYTHONPATH',None)
        env.update(LD_LIBRARY_PATH=str(LIBDIR),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
        for name in selected:
            require_disk_reserve(grant,67108864)
            armout=out/name;process=None;start=time.monotonic();paths=child_paths(armout)
            for directory in sorted({paths['cwd'],*[Path(v) for v in paths['env'].values()]},key=lambda q:(len(q.parts),str(q))):directory.mkdir(parents=True,exist_ok=False)
            child_env=dict(env,**paths['env'])
            command=[str(PRIVATE/'bin/python'),'-B',str(Path(__file__).resolve()),'--execute','--child','--arm',name,'--views',str(views_path),'--out',str(armout),'--arms-index',str(args.arms_index),'--root-grant',str(args.root_grant),'--cpu',str(args.cpu),'--scope',args.scope]
            try:
                with (armout/'stdout').open('xb') as so,(armout/'stderr').open('xb') as se,owned.SubreaperScope():
                    process=RSSGuard(subprocess.Popen(command,env=child_env,cwd=paths['cwd'],stdout=so,stderr=se,start_new_session=True),grant['rss_limit_bytes'],grant['minimum_free_disk_bytes'])
                    observed=diagnostic.monitor_process(process,armout,grant['work_seconds_per_arm'],grant['hard_seconds_per_arm'],start=start)
                    reaped,remaining=owned._reap_group(process.pid)
                    if remaining:more,remaining=owned._close_group(process);reaped+=more
                child=json.loads((armout/'child_result.json').read_text())
                passed=observed['returncode']==0 and observed['stop_reason'] is None and observed['observer_error'] is None and child.get('work_complete') is True and not remaining and process.stop_reason is None
                native_metric=None
                if passed:
                    if (armout/'stdout').stat().st_size>8388608:raise ValueError('native stdout exceeds8MiB parse budget; raw file preserved')
                    native_metric=native_final_metric((armout/'stdout').read_text())
                result['arms'][name]={'status':'PASS_PIPELINE_ONLY' if passed and scope=='PIPELINE_ONLY_SYNTHETIC' else 'PASS_OWNER_CERTIFIED_PROCESS' if passed else 'FAIL','observer':observed,'child':child,'remaining_owned':remaining,'reaped':reaped,'rows':plans[name]['rows'],'steps_per_epoch':plans[name]['steps_per_epoch'],'total_steps':plans[name]['total_steps'],'command':command,'cwd':str(paths['cwd']),'owned_cache_tmp_environment':paths['env'],'RSS_guard':{'limit_bytes':grant['rss_limit_bytes'],'max_sampled_rss_bytes':process.max_sampled_rss_bytes,'stop_reason':process.stop_reason,'error':process.error,'minimum_sampled_free_disk_bytes':process.minimum_sampled_free_disk_bytes},'peak_children_RSS_KiB':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'native_FINAL_FULL_metric':native_metric}
                if not passed:break
            finally:
                closure={'arm':name,'command':command,'cwd':str(paths['cwd']),'elapsed_seconds':time.monotonic()-start,'pid':None if process is None else process.pid}
                try:
                    if process is not None:
                        members=owned._all_members(process.pid)
                        if process.poll() is None or members:owned._close_group(process)
                        closure.update(returncode=process.returncode,leader_reaped=process.returncode is not None,all_owned_group_members_after_close=owned._all_members(process.pid),
                            resource_guard={'stop_reason':process.stop_reason,'error':process.error,'max_sampled_rss_bytes':process.max_sampled_rss_bytes,'minimum_sampled_free_disk_bytes':process.minimum_sampled_free_disk_bytes})
                except BaseException as error:closure['cleanup_error']=type(error).__name__+': '+str(error)[:1000]
                with (armout/'forge_sol_S18_owned_resource_receipt_20261026.json').open('x') as stream:json.dump(closure,stream,indent=2,sort_keys=True);stream.write('\n')
                if closure.get('all_owned_group_members_after_close') or closure.get('cleanup_error'):raise ValueError('owned arm cleanup failed; resource receipt preserved')
        if any(fingerprint(p)!=m for p,m in inputs.items()):raise ValueError('source bytes/modes changed during run')
        verify_pins();result['inputs_unchanged']=True;result['free_disk_after_bytes']=require_disk_reserve(grant)
        if list(result['arms'])==selected and all(v['status'].startswith('PASS_') for v in result['arms'].values()):
            result['all_five_arms_completed']=selected==list(ARMS)
            result['status']='PASS_SELECTED_SYNTHETIC_PIPELINE_ARMS' if scope=='PIPELINE_ONLY_SYNTHETIC' else 'PASS_SELECTED_OWNER_CERTIFIED_PROCESS'
    except BaseException as error:
        result['error']=type(error).__name__+': '+str(error);traceback.print_exc(limit=12)
    finally:(out/'forge_sol_S18_training_result_20261026.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'arms_completed':len(result['arms'])},sort_keys=True))
    return 0 if result['status'].startswith('PASS_') else 1

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--describe',action='store_true');ap.add_argument('--execute',action='store_true');ap.add_argument('--child',action='store_true')
    ap.add_argument('--arms-index',type=Path,default=DEFAULT_INDEX);ap.add_argument('--root-grant',type=Path);ap.add_argument('--out',type=Path)
    ap.add_argument('--cpu',type=int);ap.add_argument('--scope',choices=['synthetic_pipeline_only','real'])
    ap.add_argument('--arm',choices=list(ARMS));ap.add_argument('--views',type=Path);args=ap.parse_args(argv)
    if args.describe:
        if args.execute or args.child:ap.error('--describe cannot execute')
        print(json.dumps(source_plan(),indent=2,sort_keys=True));return 0
    if not args.execute:ap.error('source preparation is not execution permission; separate exact root grant required')
    grant=validate_grant(args.root_grant,args.arms_index,args.cpu)
    if args.out is None or args.scope is None:ap.error('--out and --scope required for execution')
    if args.child and (args.arm is None or args.views is None):ap.error('child requires exact arm and copied views')
    validate_paths(args,grant)
    verify_pins();index,plans,inputs=load_index(args.arms_index);scope=require_scope(args.scope,index,None)
    for path in [args.arms_index,args.root_grant]:inputs[str(path)]=fingerprint(path)
    resource.setrlimit(resource.RLIMIT_AS,(grant['address_space_bytes'],grant['address_space_bytes']))
    if args.child:
        if sorted(os.sched_getaffinity(0))!=[args.cpu] or os.getpriority(os.PRIO_PROCESS,0)!=19:ap.error('child CPU/nice grant mismatch')
        return run_child(args,grant,index,plans,inputs,scope)
    return run_controller(args,grant,index,plans,inputs,scope)

if __name__=='__main__':raise SystemExit(main())
