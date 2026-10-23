#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Collect, prepare and publish one independent-teacher CI shard. Never train.

Only an explicit CI invocation may publish. Archives preserve canonical absolute
paths (minus leading slash), original bytes and modes. No Git checkout/index is
changed: publication uses hash-object/mktree/commit-tree and ordinary pushes.
"""
from __future__ import annotations
import argparse
import base64
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

MIB = 1024 * 1024
CURRENT = '1ab50b2dd64d9b2f752f7f1285f6968cad2fd792'
OLD = '5101c2529d386b7c3a04ba9156a69ee34df6bb43'
NETWORK = '1a298aa575a085434d29027978dc36867fe9c5bcea9376654b7a8eba1e52dfc2'
SF_BINARY_SHA = '0f83d24cc46d2c66c60f16001af5444873bc112b7d028594513426894c12da19'
TARGET = 1450000
MINIMUM_SHARD = 1400000


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(MIB), b''): digest.update(block)
    return digest.hexdigest()


def atomic(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.pending')
    temporary.write_text(json.dumps(value, indent=2) + '\n'); os.replace(temporary, path)


def utc(): return datetime.now(timezone.utc).isoformat()


def batches(items, limit):
    result, current, size = [], [], 0
    for item in items:
        amount = item[1]
        if amount < 0 or amount > limit: raise ValueError('Publication item exceeds batch cap')
        if current and size + amount > limit: result.append(current); current, size = [], 0
        current.append(item); size += amount
    if current: result.append(current)
    return result


def scan_chunk(path, metadata, positions, games):
    """Count only hash-verified committed game frames, including zero-row games."""
    if sha(path) != metadata['sha256']: raise ValueError('Teacher chunk SHA differs')
    ids, accepted = [], 0
    with gzip.open(path, 'rt') as source:
        for line in source:
            game = json.loads(line); identity = game['game_id']
            if identity in games: raise ValueError('Repeated game identity')
            games.add(identity); ids.append(identity)
            for sample in game['samples']:
                if sample['game_id'] != identity: raise ValueError('Sample game identity differs')
                fields = sample['fen'].split()
                if len(fields) != 6: raise ValueError('Malformed FEN')
                positions.add(' '.join(fields[:4])); accepted += 1
    if ids != metadata['game_ids'] or len(ids) != metadata['games'] or accepted != metadata['accepted']:
        raise ValueError('Teacher chunk frame/count metadata differs')
    if sha(path) != metadata['sha256']: raise ValueError('Teacher chunk changed during scan')
    return accepted


class Runner:
    def __init__(self, args):
        self.args = args; self.repo = args.repo.resolve(); self.out = args.out.resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.state_path = self.out/'ci-state.json'
        self.state = json.loads(self.state_path.read_bytes()) if self.state_path.exists() else {
            'schema':'forge-teacher-ci-shard-v1', 'shard':args.shard, 'created_utc':utc(),
            'status':'STARTED_NO_DATA', 'children':{}, 'published_sources':{}, 'entries':{}, 'archives':[],
            'source_commit':os.environ.get('GITHUB_SHA'), 'run_id':os.environ.get('GITHUB_RUN_ID')}
        if self.state['shard'] != args.shard: raise ValueError('Shard state differs')
        self.processes = {}; self.streams = []
        self.branch = f"data/independent-teacher-ci-{os.environ.get('GITHUB_RUN_ID')}-{os.environ.get('GITHUB_RUN_ATTEMPT','1')}-shard-{args.shard}"
        self.save()

    def save(self): atomic(self.state_path, self.state)

    def event(self, kind, **values):
        with (self.out/'events.jsonl').open('a') as stream:
            stream.write(json.dumps({'utc':utc(),'kind':kind,**values})+'\n')

    def command(self, argv, name, allowed=(0,), timeout=900):
        process = self.start(argv, name)
        try: result = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=30)
            except subprocess.TimeoutExpired: os.killpg(process.pid, signal.SIGKILL); process.wait()
            self.record_exit(name); raise RuntimeError('Command timeout: '+name)
        self.record_exit(name)
        if result not in allowed: raise RuntimeError(f'{name} actual exit {result}')
        return result

    def start(self, argv, name):
        if name in self.state['children']: raise ValueError('Command already attempted: '+name)
        handles = [(self.out/(name+'.'+suffix)).open('xb') for suffix in ('stdout','stderr')]
        self.streams.extend(handles)
        process = subprocess.Popen([str(value) for value in argv], cwd=self.repo,
            stdout=handles[0], stderr=handles[1], start_new_session=True)
        self.processes[name] = process
        self.state['children'][name] = {'argv':[str(v) for v in argv], 'pid':process.pid,
            'proc_start_ticks':Path(f'/proc/{process.pid}/stat').read_text().split()[21],
            'started_utc':utc(),'actual_exit':None}
        self.save(); return process

    def record_exit(self, name):
        process = self.processes[name]; result = process.poll()
        self.state['children'][name]['actual_exit'] = result
        if result is not None: self.state['children'][name]['closed_utc'] = utc()
        self.save()

    def git(self, arguments, incoming=None):
        token = os.environ.get('GITHUB_TOKEN')
        if not token or os.environ.get('GITHUB_ACTIONS') != 'true': raise RuntimeError('Publication requires explicit hosted CI token')
        environment = dict(os.environ, GIT_CONFIG_COUNT='1',
            GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
            GIT_CONFIG_VALUE_0='AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+token).encode()).decode(),
            GIT_AUTHOR_NAME='Forge evidence CI',GIT_AUTHOR_EMAIL='forge-ci@users.noreply.github.com',
            GIT_COMMITTER_NAME='Forge evidence CI',GIT_COMMITTER_EMAIL='forge-ci@users.noreply.github.com')
        result = subprocess.run(['git',*arguments],cwd=self.repo,env=environment,input=incoming,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
        self.event('git',argv=arguments,actual_exit=result.returncode,
            stdout=result.stdout.decode(errors='replace')[-3000:],stderr=result.stderr.decode(errors='replace')[-3000:])
        if result.returncode: raise RuntimeError('Git publication command failed: '+arguments[0])
        return result.stdout.decode().strip()

    def commit_files(self, files, description):
        entries = dict(self.state['entries'])
        for name, path in files:
            entries[name] = self.git(['hash-object','-w',str(path)])
        def tree(mapping):
            children = defaultdict(dict); leaves = {}
            for name, oid in mapping.items():
                first, slash, rest = name.partition('/')
                if slash: children[first][rest] = oid
                else: leaves[first] = oid
            lines = [f'100644 blob {oid}\t{name}\n' for name,oid in sorted(leaves.items())]
            lines += [f'040000 tree {tree(child)}\t{name}\n' for name,child in sorted(children.items())]
            return self.git(['mktree'], ''.join(lines).encode())
        parent = self.state.get('published_commit')
        observed = self.git(['ls-remote','origin','refs/heads/'+self.branch])
        if (observed.split()[0] if observed else None) != parent: raise ValueError('Remote checkpoint branch differs; refusing overwrite')
        argv = ['commit-tree',tree(entries)] + (['-p',parent] if parent else [])
        commit = self.git(argv,(description+'\n').encode())
        self.git(['push','origin',commit+':refs/heads/'+self.branch])
        if self.git(['ls-remote','origin','refs/heads/'+self.branch]).split()[0] != commit:
            raise RuntimeError('Remote publication verification failed')
        self.state.update(entries=entries,published_commit=commit,publication_branch=self.branch)
        self.save()

    def snapshot(self, path, directory):
        if path.is_file():
            destination = directory/path.relative_to(self.out)
            destination.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,destination)
            return destination

    def publish(self, final=False):
        """Package immutable committed files and explicit closed snapshots only."""
        from multipart_dataset import pack
        index = self.state.get('snapshot_serial', 0)
        self.state['snapshot_serial'] = index + 1; self.save()
        snap = self.out/'snapshots'/f'{index:04d}'; snap.mkdir(parents=True,exist_ok=False)
        paths = set()
        for name in ('ci-state.json','events.jsonl','progress.json','games/manifest.json','labels/manifest.json'):
            copied = self.snapshot(self.out/name,snap)
            if copied: paths.add(copied)
        for root in ('build/bin','build/support','build/sources'):
            paths.update(p for p in (self.out/root).rglob('*') if p.is_file() and not p.is_symlink())
        for name in ('protocol.json','generation-command.json','external-tools-required.json','build/build-receipt.json','build/build-log.jsonl.gz','build/native-build.json'):
            if (self.out/name).is_file(): paths.add(self.out/name)
        receipt = self.out/'build/build-receipt.json'
        if receipt.exists():
            paths.update(Path(v) for v in json.loads(receipt.read_bytes())['paths'].values() if Path(v).is_file())
        generation = self.out/'games/manifest.json'
        if generation.exists():
            for item in json.loads(generation.read_bytes()).get('chunks',[]):
                path = generation.parent/item['path']
                if sha(path) != item['sha256']: raise ValueError('Generation chunk differs')
                paths.add(path)
        labels = self.out/'labels/manifest.json'
        if labels.exists():
            manifest = json.loads(labels.read_bytes())
            for item in manifest.get('artifact_bindings',[]):
                path = Path(item['path'])
                if sha(path) != item['sha256']: raise ValueError('Bound source artifact differs')
                paths.add(path)
            for item in manifest.get('chunks',[]):
                path = labels.parent/'chunks'/item['path']
                if sha(path) != item['sha256']: raise ValueError('Label chunk differs')
                paths.update((path,path.parent/'metadata.json'))
        paths.update(p for p in (self.repo/'tools/nnue').glob('*') if p.is_file() and p.suffix in ('.py','.cpp'))
        if final:
            for name in self.state['children']:
                if self.state['children'][name]['actual_exit'] is not None:
                    paths.update(self.out/(name+'.'+suffix) for suffix in ('stdout','stderr'))
            for root in ('games','labels','dataset'):
                paths.update(p for p in (self.out/root).rglob('*') if p.is_file() and not p.is_symlink()
                    and (root=='dataset' or p.name in ('manifest.json','metadata.json','process-exits.json','assignments.json') or p.suffix=='.gz'))
        # Group byte-identical aliases together, preserving every original path.
        identical = defaultdict(list)
        external = self.out/'build/bin/stockfish'
        for path in sorted(paths):
            path = path.absolute()
            # External GPL tools are hydrated by exact hash at restore, never bundled.
            if path == external or self.out/'build/external' in path.parents:continue
            if path.is_symlink(): continue
            digest = sha(path); size = path.stat().st_size
            old = self.state['published_sources'].get(str(path))
            if old is not None:
                if old != digest: raise ValueError('Previously published immutable source changed: '+str(path))
                continue
            identical[(digest,size,path.stat().st_mode & 0o777)].append(path)
        groups = batches([(key,key[1]) for key in identical],96*MIB) if all(k[1]<=96*MIB for k in identical) else None
        # A large single prepared array is sliced by the multipart writer; push batches remain bounded.
        if groups is None:
            groups = []; pending=[]; amount=0
            for key in identical:
                if pending and amount+key[1]>96*MIB: groups.append(pending);pending=[];amount=0
                pending.append((key,key[1]));amount+=key[1]
                if key[1]>96*MIB:groups.append(pending);pending=[];amount=0
            if pending:groups.append(pending)
        for group in groups:
            number=len(self.state['archives']); name=f'archive-{number:04d}'
            declaration={'status':'CLOSED_INPUTS_FROZEN','files':[],'aliases':[]}
            for key,_ in group:
                sources=identical[key]; first=sources[0]; member=str(first).lstrip('/')
                declaration['files'].append({'source':str(first),'member':member,'sha256':key[0],'bytes':key[1]})
                declaration['aliases'].extend({'source':str(p),'member':str(p).lstrip('/'),'target':member} for p in sources[1:])
            declaration_path=self.out/(name+'-inputs.json');atomic(declaration_path,declaration)
            packed=self.out/'publication'/name; pack(declaration_path,packed)
            manifest=packed/'RECOVERY-MANIFEST.json'; payload=[(p.name,p.stat().st_size) for p in sorted(packed.glob('dataset.zip.*'))]
            for batch in batches(payload,96*MIB):
                self.commit_files([(name+'/'+filename,packed/filename) for filename,_ in batch],f'{name}: verified opaque parts')
            self.commit_files([(name+'/RECOVERY-MANIFEST.json',manifest),(name+'/CLOSED-INPUTS.json',declaration_path)],f'{name}: complete recovery manifest')
            self.state['archives'].append({'path':name+'/RECOVERY-MANIFEST.json','sha256':sha(manifest),'parts':len(payload)})
            for key,_ in group:
                for path in identical[key]:self.state['published_sources'][str(path)]=key[0]
            self.save()
        status=self.out/'publication-status.json';atomic(status,{k:v for k,v in self.state.items() if k not in ('entries','published_sources')})
        self.commit_files([('STATUS.json',status)],'Honest shard status and recovery index')

    def pins(self):
        if sha(self.out/'protocol.json') != self.state['protocol_sha256']:raise ValueError('Frozen protocol changed')
        protocol=json.loads((self.out/'protocol.json').read_bytes())
        for name,digest in protocol['producer_source_sha256'].items():
            if sha(self.repo/name)!=digest:raise ValueError('Frozen producer source changed: '+name)

    def run(self):
        if 'build' in self.state['children']: raise ValueError('CI shard is once-only; use fresh run, not implicit resume')
        self.command([sys.executable,self.repo/'tools/nnue/build_teacher_ci.py','--repo',self.repo,
            '--out',self.out/'build','--shard',self.args.shard,'--jobs','2','--cxx','g++-14'],'build')
        receipt=json.loads((self.out/'build/build-receipt.json').read_bytes());paths=receipt['paths']
        if sha(paths['stockfish']) != SF_BINARY_SHA:raise ValueError('External SF binary identity differs')
        atomic(self.out/'external-tools-required.json', {'status':'EXTERNAL_TOOL_NOT_REDISTRIBUTED',
            'tools':[{'path':paths['stockfish'],'sha256':SF_BINARY_SHA,'network_sha256':NETWORK,
            'bytes':Path(paths['stockfish']).stat().st_size,
            'origin':'https://github.com/official-stockfish/Stockfish/releases/tag/sf_19',
            'restore':'Acquire independently; verify exact SHA256 and chmod executable before source replay. No binary/archive/network payload bundled.'}]})
        games=self.out/'games';labels=self.out/'labels';games.joinpath('chunks').mkdir(parents=True)
        tool=lambda name:self.repo/'tools/nnue'/name
        generation=[sys.executable,tool('generate_teacher_games.py'),'--engine',paths['native_current'],
            '--opponent',paths['native_5101'],'--source-commit',CURRENT,'--opponent-source-commit',OLD,
            '--network',paths['current_network'],'--opponent-network',paths['old_network'],'--out',str(games),
            '--games','1000000','--target-positions','0','--workers','1','--nodes','64','--seed',str(2026102301+self.args.shard),
            '--split-seed','2026102302','--validation-fraction','.05','--audit-fraction','.05','--opening-min','8',
            '--opening-max','24','--max-ply','256','--score-cap','1000','--chunk-games','256','--engine-timeout','15',
            '--time-limit-seconds','14400','--native-batch','--engine-core',paths['current_core'],'--opponent-core',paths['old_core'],
            '--engine-reference',paths['current_reference'],'--opponent-reference',paths['old_reference'],
            '--build-provenance',paths['build_provenance'],'--stop-file',str(games/'STOP_GENERATION')]
        atomic(self.out/'generation-command.json',{'argv':[str(p) for p in generation]})
        base=self.repo/'validation/independent-teacher-20261023/protocol.json';protocol=json.loads(base.read_bytes())
        protocol['dataset']['generation_seed']=2026102301+self.args.shard
        protocol['dataset']['data_stop_rule']=f'Per CI shard: stop at {TARGET} committed exact unique first4FEN, or frozen UTC cutoff; global merge must retain >=5000000. No loss-based stopping.'
        protocol.update(status='FROZEN_BEFORE_CI_SHARD_DATA',frozen_utc=utc(),
            parent_protocol_sha256=sha(base),native_build_provenance_sha256=sha(paths['build_provenance']),
            generation_command_prepared_sha256=sha(self.out/'generation-command.json'))
        protocol['producer_source_sha256']={str(p.relative_to(self.repo)):sha(p) for p in
            [tool(n) for n in ('generate_teacher_games.py','label_teacher_games.py','coordinate_teacher_shards.py','native_game_driver.cpp',
                               'run_teacher_ci_shard.py','build_teacher_ci.py','prepare_teacher_data.py')]}
        quota=Path('/sys/fs/cgroup/cpu.max')
        protocol['resources']={'host_logical_cpus':os.cpu_count(),
            'cgroup_cpu_max_raw':quota.read_text().strip() if quota.exists() else None,
            'process_affinity_cpus':sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,
            'production_generator_workers':1,'production_teacher_workers':4,
            'description':'Observed hosted resources; configured process counts are not a throughput or quota claim.'}
        protocol['execution']={'model':'CI four independent Python labelers, one external SF thread each',
            'shard':self.args.shard,'fresh_opening_seed':2026102301+self.args.shard,'source_commit':self.state['source_commit'],
            'build_receipt_sha256':sha(self.out/'build/build-receipt.json'),'collection_soft_cutoff_utc':self.args.stop_at,
            'minimum_shard_retained':MINIMUM_SHARD,'global_minimum':5000000,'per_shard_training_permitted':False,
            'restore_layout':'archive members preserve absolute canonical paths minus leading slash'}
        atomic(self.out/'protocol.json',protocol);self.state['protocol_sha256']=sha(self.out/'protocol.json');self.save()
        self.publish()
        initial=self.out/'labels-initial'
        self.command([sys.executable,tool('label_teacher_games.py'),'--input-dir',games,'--output-dir',initial,
            '--teacher',paths['stockfish'],'--teacher-network-sha256',NETWORK,'--depth','3','--workers','1'],'empty-initial',timeout=120)
        generator=self.start(generation,'generator')
        end=time.monotonic()+60
        while not (games/'manifest.json').exists():
            if generator.poll() is not None or time.monotonic()>end:raise RuntimeError('Generator did not publish initial manifest')
            time.sleep(.1)
        teacher=self.start([sys.executable,tool('coordinate_teacher_shards.py'),'--input-dir',games,'--output-dir',labels,
            '--initial-manifest',initial/'manifest.json','--teacher',paths['stockfish'],'--teacher-network-sha256',NETWORK,
            '--depth','3','--workers','4','--follow','--idle-timeout','86400','--stop-file',labels/'STOP_LABELING'],'teacher')
        self.state['status']='COLLECTING_FRESH_WHOLE_GAMES';self.save()
        positions=set();identities=set();completed=set();accepted=0;last=0;last_publish=time.monotonic();stop_time=None
        cutoff=datetime.fromisoformat(self.args.stop_at.replace('Z','+00:00')).timestamp()
        while generator.poll() is None or teacher.poll() is None:
            self.pins()
            manifest=labels/'manifest.json'
            if manifest.exists():
                for chunk in json.loads(manifest.read_bytes()).get('chunks',[]):
                    key=(chunk['path'],chunk['sha256'])
                    if key not in completed:
                        accepted+=scan_chunk(labels/'chunks'/chunk['path'],chunk,positions,identities);completed.add(key)
            now=time.monotonic()
            child_failure=any(p.poll() not in (None,0) for p in (generator,teacher))
            low_disk=shutil.disk_usage(self.out).free<700*MIB
            if stop_time is None and (len(positions)>=TARGET or time.time()>=cutoff or child_failure or low_disk):
                self.state['stop_reason']='child_failure' if child_failure else ('disk_low' if low_disk else ('unique_target' if len(positions)>=TARGET else 'utc_cutoff'))
                for flag in (games/'STOP_GENERATION',labels/'STOP_LABELING'):flag.parent.mkdir(parents=True,exist_ok=True);flag.touch()
                stop_time=now;self.save()
            if now-last>=60:
                progress={'utc':utc(),'accepted_rows':accepted,'unique_first4_fen':len(positions),'games':len(identities),'chunks':len(completed),
                    'generator_exit':generator.poll(),'teacher_exit':teacher.poll(),'stop_reason':self.state.get('stop_reason')}
                self.state.update(accepted_rows=accepted,unique_first4_fen=len(positions),games=len(identities));self.save()
                atomic(self.out/'progress.json',progress);self.event('progress',**progress);print(json.dumps(progress),flush=True);last=now
            if now-last_publish>=600 and stop_time is None:self.publish();last_publish=time.monotonic()
            if stop_time is not None and now-stop_time>300:
                raise RuntimeError('Graceful drain exceeded 300 seconds')
            time.sleep(1)
        for name in ('generator','teacher'):self.record_exit(name)
        # Include chunks committed during the final drain.
        for chunk in json.loads((labels/'manifest.json').read_bytes())['chunks']:
            if (chunk['path'],chunk['sha256']) not in completed:accepted+=scan_chunk(labels/'chunks'/chunk['path'],chunk,positions,identities)
        self.state.update(accepted_rows=accepted,unique_first4_fen=len(positions),games=len(identities));self.save()
        if generator.returncode or teacher.returncode or self.state.get('stop_reason') in ('child_failure','disk_low'):
            raise RuntimeError('Collection did not close cleanly')
        if len(positions)<MINIMUM_SHARD:raise RuntimeError('INCOMPLETE shard below 1400000 unique positions; no optimization')
        self.pins();self.state['status']='COLLECTED_NATIVE_PREPARATION';self.save();self.publish()
        self.command([sys.executable,tool('prepare_teacher_data.py'),'--teacher-manifest',labels/'manifest.json',
            '--generation-manifest',games/'manifest.json','--probe',paths['probe'],'--probe-source',paths['probe_source'],
            '--protocol',self.out/'protocol.json','--out',self.out/'dataset','--batch-size','20000','--min-positions','5000000'],
            'prepare',allowed=(0,2),timeout=2400)
        freeze=json.loads((self.out/'dataset/freeze.json').read_bytes())
        if freeze['total']<MINIMUM_SHARD:raise RuntimeError('Native prepared shard below declared minimum')
        if freeze['training_permitted'] is not False:raise RuntimeError('Per-shard data must remain globally unqualified')
        self.state.update(status='SHARD_PREPARED_NOT_GLOBAL_QUALIFIED',prepared_retained=freeze['total'],training_permitted=False)
        self.save()

    def ensure_closed(self):
        # A later always-step cannot wait/reap another shell's children. Never
        # publish mutable originals as closed or manufacture its return code.
        live=[]
        for name,record in self.state['children'].items():
            if record['actual_exit'] is not None:continue
            path=Path('/proc')/str(record['pid'])/'stat'
            if path.exists() and path.read_text().split()[21]==record.get('proc_start_ticks'):
                live.append(name)
        commands=self.out/'labels/commands.json'
        if commands.exists():
            for record in json.loads(commands.read_bytes()):
                cmdline=Path('/proc')/str(record['pid'])/'cmdline'
                if cmdline.exists() and str(self.out).encode() in cmdline.read_bytes():live.append('labeler-worker-'+str(record['worker']))
        for process in Path('/proc').iterdir():
            if not process.name.isdigit() or int(process.name)==os.getpid():continue
            try:command=(process/'cmdline').read_bytes()
            except (FileNotFoundError,PermissionError,ProcessLookupError):continue
            if str(self.out/'build/bin').encode() in command:live.append('native-or-teacher-'+process.name)
        if live:raise RuntimeError('Owned parents remain active; final raw publication forbidden: '+','.join(live))
        unknown=[name for name,r in self.state['children'].items() if r['actual_exit'] is None]
        if unknown:
            self.state.update(status='FAILED_UNKNOWN_PARENT_EXIT_NO_TRAINING',unobserved_actual_exits=unknown);self.save()

    def abort_descendants(self):
        """Abort known separate-session labelers, then their exact native tools."""
        owned={}
        commands=self.out/'labels/commands.json'
        if commands.exists():
            for record in json.loads(commands.read_bytes()):
                process=Path('/proc')/str(record['pid'])
                try:
                    argv=(process/'cmdline').read_bytes().split(b'\0')[:-1]
                    if argv != [str(value).encode() for value in record['argv']]:continue
                    owned[record['pid']]=(process/'stat').read_text().split()[21]
                except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        for process in Path('/proc').iterdir():
            if not process.name.isdigit():continue
            try:
                executable=(process/'exe').resolve(strict=True)
                if executable.is_relative_to(self.out/'build/bin'):
                    owned[int(process.name)]=(process/'stat').read_text().split()[21]
            except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        def matching(pid,ticks):
            try:
                fields=(Path('/proc')/str(pid)/'stat').read_text().split()
                return fields[21]==ticks and fields[2]!='Z'
            except (FileNotFoundError,PermissionError,ProcessLookupError):return False
        for pid,ticks in owned.items():
            if matching(pid,ticks):
                try:os.kill(pid,signal.SIGTERM);self.event('abort_owned_descendant',pid=pid,signal='SIGTERM')
                except ProcessLookupError:pass
        deadline=time.monotonic()+10
        while any(matching(pid,ticks) for pid,ticks in owned.items()) and time.monotonic()<deadline:time.sleep(.05)
        for pid,ticks in owned.items():
            if matching(pid,ticks):
                try:os.kill(pid,signal.SIGKILL);self.event('abort_owned_descendant',pid=pid,signal='SIGKILL')
                except ProcessLookupError:pass

    def close(self):
        for flag in (self.out/'games/STOP_GENERATION',self.out/'labels/STOP_LABELING'):
            flag.parent.mkdir(parents=True,exist_ok=True);flag.touch()
        for name,process in self.processes.items():
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    # Coordinator children have separate sessions. Abort those
                    # verified workers/tools before killing their supervisor.
                    self.abort_descendants()
                    try:process.wait(timeout=25)
                    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            self.record_exit(name)
        self.abort_descendants()
        for stream in self.streams:stream.close()


def self_test():
    class Tests(unittest.TestCase):
        def test_publication_batch_bound(self):
            self.assertEqual(batches([('a',80),('b',40),('c',20)],128),[[('a',80),('b',40)],[('c',20)]])
            with self.assertRaises(ValueError):batches([('oversize',129)],128)
        def test_streaming_checkpoint_excludes_external_payload(self):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);repo=root/'repo';out=root/'shard'
                (repo/'tools/nnue').mkdir(parents=True);(out/'build/bin').mkdir(parents=True)
                (out/'build/external').mkdir()
                (out/'build/bin/stockfish').write_bytes(b'EXTERNAL GPL PAYLOAD')
                (out/'build/external/stockfish-19.archive').write_bytes(b'EXTERNAL ARCHIVE')
                (out/'build/bin/probe').write_bytes(b'MIT native probe')
                runner=Runner(argparse.Namespace(repo=repo,out=out,shard=0))
                commits=[]
                runner.commit_files=lambda files,description:commits.append([name for name,_ in files])
                runner.publish()
                manifests=list((out/'publication').glob('*/RECOVERY-MANIFEST.json'))
                members=[m['path'] for path in manifests for m in json.loads(path.read_bytes())['members']]
                self.assertTrue(any(name.endswith('/build/bin/probe') for name in members))
                self.assertFalse(any('stockfish' in name for name in members))
                self.assertTrue(commits[-1]==['STATUS.json'])
                self.assertTrue(all(path.stat().st_size<=31*MIB for path in (out/'publication').rglob('dataset.zip.*')))
        def test_abort_separate_session_worker_before_parent_kill(self):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);runner=Runner(argparse.Namespace(repo=root,out=root/'shard',shard=0))
                argv=[sys.executable,'-c','import signal; signal.pause()']
                worker=subprocess.Popen(argv,start_new_session=True)
                atomic(runner.out/'labels/commands.json',[{'worker':0,'pid':worker.pid,'argv':argv}])
                try:
                    ready_deadline=time.monotonic()+5
                    while (Path('/proc')/str(worker.pid)/'cmdline').read_bytes().split(b'\0')[:-1] != [v.encode() for v in argv]:
                        if time.monotonic()>ready_deadline:self.fail('Synthetic worker did not finish exec')
                        time.sleep(.01)
                    runner.abort_descendants();worker.wait(timeout=5)
                    self.assertEqual(worker.returncode,-signal.SIGTERM)
                finally:
                    if worker.poll() is None:worker.kill();worker.wait()
        def test_started_child_identity_survives_reload(self):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);args=argparse.Namespace(repo=root,out=root/'shard',shard=0)
                runner=Runner(args)
                try:
                    process=runner.start([sys.executable,'-c','import signal; signal.pause()'],'identity-test')
                    self.assertIsNotNone(runner.state['children']['identity-test']['proc_start_ticks'])
                    reloaded=Runner(args)
                    with self.assertRaisesRegex(RuntimeError,'remain active'):reloaded.ensure_closed()
                finally:runner.close()
                self.assertIsNotNone(process.returncode)
                Runner(args).ensure_closed()
        def test_finalizer_rejects_live_unreaped_parent(self):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);runner=Runner(argparse.Namespace(repo=root,out=root/'shard',shard=0))
                runner.state['children']['live']={'pid':os.getpid(),'actual_exit':None,
                    'proc_start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().split()[21]}
                with self.assertRaisesRegex(RuntimeError,'remain active'):runner.ensure_closed()
        def test_actual_frames_union_and_hash(self):
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'labels.gz';ids=['a','b']
                fen='8/8/8/8/8/8/K7/7k w - - 0 1'
                frames=[{'game_id':identity,'samples':[{'game_id':identity,'fen':fen}]} for identity in ids]
                with gzip.open(path,'wt') as stream:
                    for frame in frames:stream.write(json.dumps(frame)+'\n')
                metadata={'sha256':sha(path),'game_ids':ids,'games':2,'accepted':2};positions=set();games=set()
                self.assertEqual(scan_chunk(path,metadata,positions,games),2);self.assertEqual(len(positions),1)
                self.assertEqual(games,set(ids))
                with self.assertRaisesRegex(ValueError,'SHA'):scan_chunk(path,{**metadata,'sha256':'0'*64},set(),set())
                with self.assertRaisesRegex(ValueError,'metadata'):scan_chunk(path,{**metadata,'accepted':3},set(),set())
    return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--stage',choices=('started','run','finalize'),default='run');parser.add_argument('--shard',type=int,choices=range(4))
    parser.add_argument('--out',type=Path);parser.add_argument('--repo',type=Path,default=Path('/workspace/dwqww'))
    parser.add_argument('--stop-at',default='2026-10-23T22:40:00Z');parser.add_argument('--job-status');args=parser.parse_args()
    if args.self_test:return self_test()
    if args.shard is None or args.out is None:parser.error('--shard and --out required')
    runner=Runner(args)
    if args.stage=='started':runner.publish();return 0
    if args.stage=='finalize':
        if args.job_status and args.job_status!='success':
            runner.state.update(status='FAILED_WORKFLOW_NO_TRAINING',workflow_job_status=args.job_status);runner.save()
        try:runner.ensure_closed()
        except BaseException as error:
            runner.state.update(status='FAILED_ACTIVE_PROCESSES_NO_CLOSED_RAW_PUBLICATION',error=repr(error));runner.save()
            runner.publish(final=False);raise
        runner.publish(final=True);return 0
    def interrupted(number, frame):raise RuntimeError('Owned CI runner received signal '+str(number))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    failed=False
    try:runner.run()
    except BaseException as error:
        failed=True;runner.state.update(status='FAILED_OR_INCOMPLETE_NO_TRAINING',error=repr(error));runner.save();runner.event('failure',error=repr(error))
    finally:
        runner.close();runner.ensure_closed();runner.publish(final=True)
    return 1 if failed else 0


if __name__=='__main__':raise SystemExit(main())
