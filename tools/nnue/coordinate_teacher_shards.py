#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Coordinate four unchanged single-worker external-teacher labeler processes.

Only declared, hashed original generator chunks enter deterministic index-mod-4
input shards. Verified symlinks preserve the canonical original source identity.
Previously completed labels are reused byte-for-byte. Aggregate paths are exact
hardlinks to original committed label/metadata bytes; raw UCI streams and child
manifests retain their original bytes and historical execution configurations.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import label_teacher_games as labeler

TOTAL_KEYS=('games','input_positions','accepted','mate','score_cap','capture','promotion',
            'gives_check','terminal','accepted_nodes','accepted_time_ms','searched_positions',
            'searched_nodes','searched_time_ms','searched_wall_ms')
SCIENCE_KEYS=('teacher_binary','teacher_bytes','teacher_sha256','teacher_network_sha256','depth','options','policy','tool_sha256','timeout_s')


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')


def read_json(path):
    raw=Path(path).read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()


def check_hash(path,expected):
    path=Path(path)
    if not path.is_file() or labeler.sha256(path)!=expected:
        raise ValueError('artifact hash mismatch: '+str(path))


class Coordinator:
    def __init__(self,input_dir,output_dir,initial_manifest,teacher,network_sha,labeler_path,depth=3,workers=4):
        if workers!=4:raise ValueError('this execution topology requires four independent processes')
        self.input_dir=Path(input_dir).resolve();self.output_dir=Path(output_dir).resolve()
        self.labeler_path=Path(labeler_path).resolve();self.teacher=Path(teacher).resolve()
        self.initial_manifest=Path(initial_manifest).resolve();self.workers=workers
        if (self.output_dir/'manifest.json').exists():
            raise ValueError('output manifest already exists; preserve it and use a fresh output directory')
        self.output_dir.mkdir(parents=True,exist_ok=True)
        self.bindings={};self.assigned={};self.completed={};self.last_generation=None
        self.configuration={'teacher_binary':str(self.teacher),'teacher_sha256':labeler.sha256(self.teacher),
            'teacher_bytes':self.teacher.stat().st_size,'teacher_network_sha256':network_sha,
            'teacher_network_identity':'embedded network bound to teacher binary SHA256',
            'options':dict(labeler.OPTIONS),'policy':dict(labeler.POLICY),'depth':depth,'workers':workers,
            'timeout_s':60,'input_dir':str(self.input_dir),'tool_sha256':labeler.sha256(self.labeler_path),
            'coordinator_sha256':labeler.sha256(Path(__file__)),
            'execution_model':'4_independent_python_processes','workers_per_process':1,
            'shard_assignment':'declared original chunk filename index modulo 4',
            'initial_manifest':str(self.initial_manifest)}
        initial,initial_sha=read_json(self.initial_manifest)
        if initial.get('status')!='complete':raise ValueError('initial label manifest must be closed and complete')
        self.validate_science(initial['configuration'])
        self.initial=initial;self.initial_sha=initial_sha
        self.configuration['initial_manifest_sha256']=initial_sha
        self.generation=self.load_generation();self.generation_config=self.generation['configuration']
        for source,record in self.original_chunks.items():self.bind(source,'canonical_generation_chunk',record['sha256'])
        snapshot=self.output_dir/'generation-at-start.json';snapshot.write_bytes(self.generation_snapshot_bytes)
        self.bind(snapshot,'original_generation_manifest_at_start',self.last_generation['snapshot_sha256'])
        # Authenticate every reused label/source/metadata/raw transcript before any child launch.
        self.ingest('initial',self.initial_manifest,initial,initial_sha,closed=True)
        self.verify_source_pins()
        for path,key in ((self.teacher,'teacher_sha256'),(self.labeler_path,'tool_sha256'),(Path(__file__),'coordinator_sha256')):
            self.bind(path,'pinned_execution_source',self.configuration[key])
        for worker in range(workers):
            (self.input_root(worker)/'chunks').mkdir(parents=True,exist_ok=True)
            self.worker_root(worker).mkdir(parents=True,exist_ok=True)
        self.save_assignments()

    def worker_root(self,worker):return self.output_dir/('worker%d'%worker)
    def input_root(self,worker):return self.output_dir/'inputs'/('worker%d'%worker)
    def stop_path(self,worker):return self.worker_root(worker)/'STOP_LABELING'

    def child_configuration(self,worker):
        result={key:value for key,value in self.configuration.items() if key in (
            'teacher_binary','teacher_sha256','teacher_bytes','teacher_network_sha256',
            'teacher_network_identity','options','policy','depth','timeout_s','tool_sha256')}
        result.update(workers=1,input_dir=str(self.input_root(worker)))
        return result

    def validate_science(self,configuration):
        for key in SCIENCE_KEYS:
            if configuration.get(key)!=self.configuration[key]:
                raise ValueError('teacher scientific/source contract changed: '+key)

    def bind(self,path,kind,expected=None):
        path=Path(path).resolve();key=str(path)
        digest=labeler.sha256(path) if expected is None else expected
        old=self.bindings.get(key)
        if old is not None:
            if old['sha256']!=digest:raise ValueError('conflicting artifact hash: '+key)
            return
        check_hash(path,digest)
        self.bindings[key]={'path':key,'sha256':digest,'bytes':path.stat().st_size,'kind':kind}

    def hardlink(self,source,destination,kind,expected):
        source=Path(source).resolve();destination=Path(destination)
        self.bind(source,kind,expected)
        destination.parent.mkdir(parents=True,exist_ok=True)
        if not destination.exists():os.link(source,destination)
        elif os.stat(source).st_ino!=os.stat(destination).st_ino or os.stat(source).st_dev!=os.stat(destination).st_dev:
            raise ValueError('aggregate path is not the authenticated hardlink: '+str(destination))
        self.bind(destination,'aggregate_'+kind,expected)

    def load_generation(self):
        raw=(self.input_dir/'manifest.json').read_bytes();manifest=json.loads(raw)
        digest=hashlib.sha256(raw).hexdigest();self.generation_snapshot_bytes=raw
        config=dict(manifest['configuration']);declared=config.pop('config_sha256')
        if hashlib.sha256(encoded(config)).hexdigest()!=declared:
            raise ValueError('generator configuration hash mismatch')
        if hasattr(self,'generation_config') and manifest['configuration']!=self.generation_config:
            raise ValueError('generator configuration changed')
        canonical={};indices=set()
        for record in manifest['chunks']:
            path=(self.input_dir/record['path']).resolve()
            try:path.relative_to(self.input_dir/'chunks')
            except ValueError:raise ValueError('generator chunk escapes original chunks directory')
            match=re.fullmatch(r'games-(\d+)\.jsonl\.gz',path.name)
            if match is None:raise ValueError('invalid declared generator chunk name')
            index=int(match.group(1))
            if str(path) in canonical or index in indices:raise ValueError('duplicate declared generator chunk')
            indices.add(index);canonical[str(path)]={**record,'index':index,'source_path':str(path)}
        self.original_chunks=canonical
        self.last_generation={'path':str(self.input_dir/'manifest.json'),'snapshot_sha256':digest,
            'configuration_sha256':declared,'status':manifest.get('status'),'chunks':len(canonical),
            'note':'Manifest observation; producer may append. Canonical source chunk bindings are immutable.'}
        return manifest

    def verify_source_pins(self):
        check_hash(self.labeler_path,self.configuration['tool_sha256'])
        check_hash(Path(__file__),self.configuration['coordinator_sha256'])
        check_hash(self.teacher,self.configuration['teacher_sha256'])

    def verify_all_bindings(self):
        self.verify_source_pins();self.load_generation()
        for source,record in self.original_chunks.items():self.bind(source,'canonical_generation_chunk',record['sha256'])
        for record in self.bindings.values():check_hash(record['path'],record['sha256'])
        for source,digest in self.completed.items():
            declared=self.original_chunks.get(source)
            if declared is None or declared['sha256']!=digest:
                raise ValueError('completed source no longer matches generator manifest')
            check_hash(source,digest)

    def ingest(self,segment,manifest_path,manifest,manifest_sha,closed):
        self.validate_science(manifest['configuration'])
        source_root=Path(manifest_path).parent
        # Never relabel or adopt a chunk absent from the canonical generator manifest.
        for metadata in manifest['chunks']:
            original=str(Path(metadata['source_path']).resolve())
            declared=self.original_chunks.get(original)
            if declared is None or declared['sha256']!=metadata['source_sha256']:
                raise ValueError('teacher source not bound to original generator manifest')
            check_hash(original,metadata['source_sha256']) if original not in self.bindings else None
            self.bind(original,'canonical_generation_chunk',metadata['source_sha256'])
            if segment.startswith('worker'):
                worker=int(segment[len('worker'):]);assignment=self.assigned.get(original)
                if assignment is None or assignment['worker']!=worker:
                    raise ValueError('child completed an unassigned or wrong-shard original chunk')
            self.completed[original]=metadata['source_sha256']
            relative=Path(metadata['path'])
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('unsafe child chunk path')
            original_label=source_root/'chunks'/relative
            self.hardlink(original_label,self.output_dir/'chunks'/segment/relative,
                          'teacher_chunk',metadata['sha256'])
            metadata_path=original_label.parent/'metadata.json'
            raw_metadata,raw_sha=read_json(metadata_path)
            if raw_metadata!=metadata:raise ValueError('child raw chunk metadata differs from manifest')
            self.hardlink(metadata_path,self.output_dir/'chunks'/segment/relative.parent/'metadata.json',
                          'raw_chunk_metadata',raw_sha)
        if closed:
            if manifest.get('status')!='complete':raise ValueError('child label manifest did not complete')
            self.bind(manifest_path,'closed_'+segment+'_manifest',manifest_sha)
            if segment=='initial':
                self.hardlink(manifest_path,self.output_dir/'initial'/'manifest.json','initial_manifest',manifest_sha)
        for session in manifest.get('transcript_sessions',[]):
            if closed and not session.get('complete'):raise ValueError('closed child has incomplete UCI transcript')
            if not session.get('complete'):continue
            directory=Path(session['directory'])
            if directory.is_absolute() or '..' in directory.parts:raise ValueError('unsafe transcript directory')
            for record in session['segments']:
                filename=Path(record['path'])
                if filename.is_absolute() or '..' in filename.parts:raise ValueError('unsafe transcript path')
                source=source_root/directory/filename
                if source.stat().st_size!=record['bytes']:raise ValueError('raw transcript size/hash mismatch')
                self.bind(source,'original_'+segment+'_uci_transcript',record['sha256'])
                if segment=='initial':
                    self.hardlink(source,self.output_dir/'initial'/directory/filename,
                                  'initial_uci_transcript',record['sha256'])

    def save_assignments(self):
        labeler.write_json_atomic(self.output_dir/'assignments.json',{
            'configuration':self.configuration,'generation_observation':self.last_generation,
            'assignments':list(self.assigned.values())})

    def assign_inputs(self,max_pending=2):
        self.load_generation();pending=Counter(row['worker'] for source,row in self.assigned.items() if source not in self.completed)
        selected=[]
        for source,record in sorted(self.original_chunks.items(),key=lambda pair:pair[1]['index']):
            if source in self.completed or source in self.assigned:continue
            worker=record['index']%self.workers
            if pending[worker]>=max_pending:continue
            check_hash(source,record['sha256']);pending[worker]+=1
            selected.append((source,record,worker))
        result=[]
        for source,record,worker in selected:
            alias=self.input_root(worker)/'chunks'/Path(source).name
            alias.parent.mkdir(parents=True,exist_ok=True)
            if alias.exists() or alias.is_symlink():raise ValueError('untracked existing input alias')
            temporary=alias.with_name(alias.name+'.part')
            os.symlink(source,temporary);os.replace(temporary,alias)
            row={'source_path':source,'sha256':record['sha256'],'index':record['index'],'worker':worker,
                 'alias':str(alias),'generator_manifest_snapshot_sha256':self.last_generation['snapshot_sha256'],
                 'generator_configuration_sha256':self.last_generation['configuration_sha256']}
            self.assigned[source]=row;result.append(row)
        if result:self.save_assignments()
        return result

    def publish(self,status,stop_reason=None):
        self.load_generation();segments=[];chunks=[];sessions=[];seen=set();sources=set();totals=Counter()
        current_identities=[];network_messages=set();advertised=[]
        manifests=[('initial',self.initial_manifest,self.initial,self.initial_sha,True)]
        for worker in range(self.workers):
            path=self.worker_root(worker)/'manifest.json'
            if not path.exists():
                if status=='complete':raise ValueError('missing closed child manifest')
                continue
            manifest,digest=read_json(path)
            if manifest['configuration'].get('workers')!=1:raise ValueError('child is not a single-worker labeler')
            if manifest['configuration'].get('input_dir')!=str(self.input_root(worker)):
                raise ValueError('child input shard path changed')
            manifests.append(('worker%d'%worker,path,manifest,digest,status=='complete'))
            current_identities.extend(manifest.get('teacher_identities',[]))
            network_messages.update(manifest.get('teacher_network_messages',[]))
            advertised=manifest.get('teacher_advertised_options',advertised)
        for segment,path,manifest,digest,closed in manifests:
            self.ingest(segment,path,manifest,digest,closed)
            segments.append({'segment':segment,'manifest_path':str(path),'manifest_sha256':digest,'closed':closed,
                'configuration':manifest['configuration'],'historical_workers':manifest['configuration']['workers'],
                'teacher_identities':manifest.get('teacher_identities',[])})
            for metadata in manifest['chunks']:
                canonical=str(Path(metadata['source_path']).resolve())
                if canonical in sources:raise ValueError('duplicate completed canonical source chunk')
                sources.add(canonical)
                for identity in metadata['game_ids']:
                    if identity in seen:raise ValueError('duplicate game_id across initial/shard segments')
                    seen.add(identity)
                if len(metadata['game_ids'])!=metadata['games']:raise ValueError('child game count mismatch')
                chunks.append({**metadata,'path':segment+'/'+metadata['path'],'segment':segment})
                for key in TOTAL_KEYS:totals[key]+=metadata.get(key,0)
            for session in manifest.get('transcript_sessions',[]):
                sessions.append({**session,'directory':segment+'/'+session['directory'],'segment':segment})
        if status=='complete':
            self.verify_all_bindings()
            snapshot=self.output_dir/'generation-at-close.json';snapshot.write_bytes(self.generation_snapshot_bytes)
            self.bind(snapshot,'original_generation_manifest_at_close',self.last_generation['snapshot_sha256'])
            if len(current_identities)!=self.workers:raise ValueError('expected four actual teacher identities')
        result={'schema':'forge-independent-teacher-games-v1','configuration':self.configuration,
            'execution_model':'4_independent_python_processes','segments':segments,'chunks':chunks,
            'totals':dict(totals),'teacher_identities':current_identities,
            'teacher_advertised_options':advertised,'teacher_network_messages':sorted(network_messages),
            'transcript_sessions':sessions,'artifact_bindings':list(self.bindings.values()),
            'generation_observation':self.last_generation,'status':status,'stop_reason':stop_reason,
            'assigned_chunks':len(self.assigned),'unprocessed_assigned_chunks':sum(source not in sources for source in self.assigned)}
        labeler.write_json_atomic(self.output_dir/'manifest.json',result)
        return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--initial-manifest',type=Path,required=True)
    parser.add_argument('--teacher',type=Path,required=True)
    parser.add_argument('--teacher-network-sha256',required=True)
    parser.add_argument('--labeler',type=Path,default=Path(__file__).with_name('label_teacher_games.py'))
    parser.add_argument('--depth',type=int,default=3)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--follow',action='store_true')
    parser.add_argument('--idle-timeout',type=float,default=86400)
    parser.add_argument('--stop-file',type=Path)
    parser.add_argument('--poll-seconds',type=float,default=0.5)
    args=parser.parse_args(argv)
    if args.depth!=3 or args.workers!=4:parser.error('frozen topology uses depth 3 and four processes')
    coordinator=Coordinator(args.input_dir,args.output_dir,args.initial_manifest,args.teacher,
                            args.teacher_network_sha256,args.labeler,args.depth,args.workers)
    children=[];streams=[];stopping=False;reason=None;failure=None;last_activity=time.monotonic()
    owned_teachers={}
    def capture_owned_teachers():
        parents={child.pid for child in children}
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():continue
            try:
                status={line.partition(':')[0]:line.partition(':')[2].strip() for line in (entry/'status').read_text().splitlines() if ':' in line}
                if int(status.get('PPid','-1')) in parents:
                    command=(entry/'cmdline').read_bytes().split(b'\0')[0].decode()
                    if command==str(args.teacher.resolve()):
                        owned_teachers[int(entry.name)]=(entry/'stat').read_text().split()[21]
            except (FileNotFoundError,ProcessLookupError,PermissionError,ValueError):pass
    requested=False
    def request_stop(signum,frame):
        nonlocal requested
        requested=True
    old={number:signal.signal(number,request_stop) for number in (signal.SIGINT,signal.SIGTERM)}
    def request_drain():
        for worker in range(args.workers):coordinator.stop_path(worker).touch()
    try:
        coordinator.assign_inputs()
        commands=[]
        for worker in range(args.workers):
            command=[sys.executable,str(args.labeler.resolve()),'--input-dir',str(coordinator.input_root(worker)),
                '--output-dir',str(coordinator.worker_root(worker)),'--teacher',str(args.teacher.resolve()),
                '--depth',str(args.depth),'--workers','1','--follow','--idle-timeout','86400',
                '--stop-file',str(coordinator.stop_path(worker)),
                '--teacher-network-sha256',args.teacher_network_sha256]
            stdout=(coordinator.worker_root(worker)/'stdout.log').open('wb')
            stderr=(coordinator.worker_root(worker)/'stderr.log').open('wb');streams.extend((stdout,stderr))
            process=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,
                                     env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
            children.append(process);commands.append({'worker':worker,'pid':process.pid,'argv':command})
        labeler.write_json_atomic(args.output_dir/'commands.json',commands)
        states=None;latest=coordinator.publish('running')
        while True:
            if requested or (args.stop_file is not None and args.stop_file.exists()):
                reason='signal' if requested else 'stop_file';stopping=True;request_drain()
            for worker,child in enumerate(children):
                code=child.poll()
                if code is not None and (code!=0 or not stopping):
                    raise RuntimeError('labeler worker %d exited unexpectedly: %s'%(worker,code))
            newstates=[]
            for worker in range(args.workers):
                path=coordinator.worker_root(worker)/'manifest.json'
                newstates.append((path.stat().st_mtime_ns,path.stat().st_size) if path.exists() else None)
            if len(owned_teachers)<args.workers or newstates!=states:capture_owned_teachers()
            if newstates!=states:
                latest=coordinator.publish('running',reason);states=newstates;last_activity=time.monotonic()
                print(json.dumps({'status':'running','totals':latest['totals'],'chunks':len(latest['chunks'])}),flush=True)
            if not stopping:
                assigned=coordinator.assign_inputs()
                if assigned:last_activity=time.monotonic()
                if not args.follow and all(source in coordinator.completed for source in coordinator.original_chunks):
                    stopping=True;reason='all_declared_chunks_complete';request_drain()
                elif time.monotonic()-last_activity>=args.idle_timeout:
                    stopping=True;reason='idle_timeout';request_drain()
            if stopping and all(child.poll() is not None for child in children):break
            time.sleep(max(0.05,args.poll_seconds))
        for stream in streams:stream.close()
        for worker in range(args.workers):
            for name in ('stdout.log','stderr.log'):
                coordinator.bind(coordinator.worker_root(worker)/name,'closed_child_'+name)
        labeler.write_json_atomic(args.output_dir/'process-exits.json',[
            {'worker':worker,'pid':child.pid,'returncode':child.returncode} for worker,child in enumerate(children)])
        for name in ('commands.json','process-exits.json','assignments.json'):
            coordinator.bind(args.output_dir/name,'coordinator_'+name)
        latest=coordinator.publish('complete',reason)
        print(json.dumps({'status':'complete','totals':latest['totals'],'chunks':len(latest['chunks'])}),flush=True)
    except BaseException as error:
        failure=error;capture_owned_teachers()
        # Existing labeler SIGTERM handler stops every owned teacher before exiting.
        for child in children:
            if child.poll() is None:child.terminate()
        deadline=time.monotonic()+20
        while any(child.poll() is None for child in children) and time.monotonic()<deadline:time.sleep(0.05)
        for child in children:
            if child.poll() is None:child.kill()
            child.wait()
        for pid,started in owned_teachers.items():
            try:
                if (Path('/proc')/str(pid)/'stat').read_text().split()[21]==started:
                    os.killpg(pid,signal.SIGKILL)
            except (FileNotFoundError,ProcessLookupError,PermissionError):pass
        try:coordinator.publish('failed',str(error))
        except BaseException:pass
    finally:
        for stream in streams:
            if not stream.closed:stream.close()
        for number,handler in old.items():signal.signal(number,handler)
    if failure:raise failure
    return 0


if __name__=='__main__':raise SystemExit(main())
