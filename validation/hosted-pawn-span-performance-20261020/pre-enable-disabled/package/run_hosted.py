#!/usr/bin/env python3
"""One strict calibrated whole-process performance attempt. No gameplay/retries."""
import argparse,importlib.util,json,math,os,signal,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
common=load('perf_common',HERE/'common.py');analysis=load('perf_analysis',HERE/'analysis.py');owned=load('perf_owned',HERE/'owned_process.py');evidence=load('perf_evidence',HERE/'build_evidence.py')

def validate_sample(facts,out,cpu):
    if (facts.get('returncode_before_verdict')!=0 or facts.get('returncode')!=0 or facts.get('timed_out') is not False or facts.get('owned_group_empty_before_verdict') is not True or facts.get('owned_group_empty_after_cleanup') is not True or facts.get('measurement_affinity')!=[cpu] or facts.get('wall_stop_reason')!='wait4_leader_observed' or any(k in facts for k in ('error','cleanup_error','affinity_restore_error'))):raise ValueError('Faulted sample process; entire attempt invalid')
    for stream in ('stdout','stderr'):
        digest=common.sha(out/(stream+'.txt'))
        if facts.get(stream+'_sha256_before_verdict')!=digest or facts.get(stream+'_sha256')!=digest:raise ValueError('Sample original stream changed')
    if (out/'stderr.txt').read_bytes():raise ValueError('Sample stderr/warning invalidates attempt')
    for metric in ('cpu','wall'):analysis.positive(facts[metric+'_seconds_before_verdict'])
    limit=analysis.positive(facts['timeout_seconds'])
    if limit>60 or facts['wall_seconds_before_verdict']>limit:raise TimeoutError('Sample whole-process wall exceeded its strict deadline')
    user,system=facts['user_seconds_before_verdict'],facts['system_seconds_before_verdict']
    if any(type(x) not in (float,int) or not math.isfinite(x) or x<0 for x in (user,system)) or user+system!=facts['cpu_seconds_before_verdict']:raise ValueError('Exact-child CPU accounting differs')
    return analysis.parse_bench((out/'stdout.txt').read_bytes())

def run_experiment(cfg,baseline,candidate,out,cpu,deadline,report,sampler=None):
    sampler=sampler or owned.run_owned
    def block(phase,index,order):
        rows=[]
        for position,variant in enumerate(order):
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('Aggregate timing emergency invalidates attempt')
            binary_label='baseline' if phase=='aa' or variant=='A' else 'candidate'
            executable=baseline if binary_label=='baseline' else candidate
            identity=f'{phase}-{index:02d}-{position}';sample_out=out/identity
            facts=sampler([executable],common.STDIN,sample_out,cpu,min(60.,remaining))
            if time.monotonic()>deadline:raise TimeoutError('Aggregate timing emergency after sample invalidates attempt')
            records=validate_sample(facts,sample_out,cpu)
            row={'sample_id':identity,'phase':phase,'block':index,'index':position,'variant':variant,'binary_label':binary_label,'cpu_seconds':facts['cpu_seconds_before_verdict'],'wall_seconds':facts['wall_seconds_before_verdict'],'user_seconds':facts['user_seconds_before_verdict'],'system_seconds':facts['system_seconds_before_verdict'],'records':records,'facts_path':str(sample_out/'status.json')}
            rows.append(row);report.setdefault('all_samples',[]).append(row);common.save(out/'summary.json',report)
        return {'phase':phase,'block':index,'order':order,'samples':rows}
    report['warmup']=block('warmup',0,'ABBA');report['warmup']['excluded_from_analysis']=True
    report['aa_blocks']=[]
    for index in range(15):report['aa_blocks'].append(block('aa',index,'ABBA' if index%2==0 else 'BAAB'))
    report['calibration']=analysis.calibrate(report['aa_blocks']);common.save(out/'summary.json',report)
    if not report['calibration']['passed']:raise ValueError('Fresh-host A/A gate failed; STOP no A/B/no retry')
    report['ab_blocks']=[]
    for index in range(31):report['ab_blocks'].append(block('ab',index,'ABBA' if index%2==0 else 'BAAB'))
    report['analysis']=analysis.analyze_blocks(report['ab_blocks'])
    if time.monotonic()>deadline:raise TimeoutError('Aggregate timing emergency after analysis invalidates attempt')
    report['gain_qualifies_before_final_rehash']=report['analysis']['both_metrics_positive']
    report['status']='completed_gain_pending_final_integrity' if report['gain_qualifies_before_final_rehash'] else 'completed_no_verified_gain'

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.repo=a.repo.resolve(strict=True);a.baseline=a.baseline.resolve(strict=True);a.candidate=a.candidate.resolve(strict=True);a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    cfg=json.loads((HERE/'protocol.json').read_text());report={'status':'preflight','verified_hosted_gain':False,'protocol':cfg};common.save(a.out/'summary.json',report);frozen={};old_affinity=set(os.sched_getaffinity(0))
    try:
        common.require_ready(cfg)
        if os.environ.get('GITHUB_RUN_ATTEMPT')!='1':raise ValueError('Only one fresh first attempt permitted')
        paths=common.inventory(a.repo,HERE)+common.proof_paths(a.repo,cfg)
        workflow=a.repo/common.WORKFLOW
        if common.sha(workflow)!=cfg['workflow_sha256']:raise ValueError('Enabled workflow differs from frozen review')
        paths+=common.transport_paths(a.repo,cfg,analysis)
        paths+=evidence.verify_build_evidence(a.out.parent,cfg,a.baseline,a.candidate)
        frozen=common.snapshot(paths);report['frozen_inputs']=frozen;report['host_before']=common.host_context();report['status']='calibration_started';common.save(a.out/'summary.json',report)
        cpu=min(old_affinity);owned.pin_cpu(cpu);report['selected_cpu']=cpu
        def interrupted(signum,frame):raise KeyboardInterrupt('Termination signal '+str(signum))
        signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
        run_experiment(cfg,a.baseline,a.candidate,a.out,cpu,time.monotonic()+3600,report)
    except BaseException as error:
        report.update(status='failed_or_inconclusive_no_verified_gain',error=repr(error));raise
    finally:
        report['final_rehash']=common.rehash(frozen)
        try:common.inventory(a.repo,HERE)
        except (OSError,ValueError) as error:report['package_integrity_error']=repr(error)
        report['host_after']=common.host_context()
        try:os.sched_setaffinity(0,old_affinity)
        except BaseException as error:report['affinity_restore_error']=repr(error)
        integrity=bool(frozen) and report['final_rehash']['status']=='passed' and not any(k in report for k in ('package_integrity_error','affinity_restore_error'))
        report['verified_hosted_gain']=integrity and report.get('status')=='completed_gain_pending_final_integrity'
        if report['verified_hosted_gain']:report['status']='completed_verified_hosted_cpu_and_wall_gain'
        if not integrity:report.update(status='failed_or_inconclusive_no_verified_gain',verified_hosted_gain=False)
        common.save(a.out/'summary.json',report)
        if not integrity:raise RuntimeError('Final input byte/mode/package integrity failed; no gain')
if __name__=='__main__':main()
