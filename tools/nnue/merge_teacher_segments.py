#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Merge closed RAW labeler segments without changing a metadata field or label.

The original global chunk names remain unchanged. Exact metadata, label gzip,
manifest and original UCI bytes are hardlinked into a new closed publication.
No engines are launched. The result is valid initial input to the unchanged
process coordinator, unlike a coordinator manifest with prefixed chunk paths.
"""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
import os
from pathlib import Path

import label_teacher_games as labeler
from coordinate_teacher_shards import SCIENCE_KEYS, TOTAL_KEYS, encoded


def read_json(path):
    raw=Path(path).read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()


def safe_relative(value):
    path=Path(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('unsafe relative artifact path: '+str(path))
    return path


def merge_segments(manifests,generation_manifest,output_dir):
    paths=[Path(path).resolve() for path in manifests]
    if not paths or len(set(paths))!=len(paths):raise ValueError('require distinct raw segment manifests')
    generation_path=Path(generation_manifest).resolve();output=Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):raise ValueError('merge output must be a fresh directory')
    generation_raw=generation_path.read_bytes();generation=json.loads(generation_raw)
    generation_sha=hashlib.sha256(generation_raw).hexdigest()
    gconfig=dict(generation['configuration']);config_sha=gconfig.pop('config_sha256')
    if hashlib.sha256(encoded(gconfig)).hexdigest()!=config_sha:raise ValueError('generation configuration hash mismatch')
    declared={}
    for record in generation['chunks']:
        source=(generation_path.parent/safe_relative(record['path'])).resolve()
        if str(source) in declared:raise ValueError('duplicate canonical generation chunk')
        declared[str(source)]=record
    bindings={}
    def bind(path,kind,expected=None):
        path=Path(path).resolve();key=str(path)
        digest=labeler.sha256(path) if expected is None else expected
        if key in bindings:
            if bindings[key]['sha256']!=digest:raise ValueError('conflicting artifact hash: '+key)
            return digest
        if not path.is_file() or labeler.sha256(path)!=digest:raise ValueError('artifact hash mismatch: '+key)
        bindings[key]={'path':key,'sha256':digest,'bytes':path.stat().st_size,'kind':kind}
        return digest
    # The generator may resume later. Bind its exact observed snapshot, never
    # claim that the appendable original manifest is an immutable artifact.
    prepared=[];chunks=[];seen_games=set();seen_sources=set();seen_paths=set();totals=Counter();base=None
    identities=[];network_messages=set();advertised=None
    # Authenticate every input before publishing any path in the new directory.
    for index,path in enumerate(paths):
        manifest,manifest_sha=read_json(path)
        if manifest.get('status')!='complete':raise ValueError('raw segment is not closed and complete')
        config=manifest['configuration']
        if base is None:base=dict(config)
        elif any(config.get(key)!=base.get(key) for key in SCIENCE_KEYS):
            raise ValueError('teacher science/source settings differ between raw segments')
        bind(path,'original_raw_segment_manifest',manifest_sha)
        own_totals=Counter();raw_chunks=[];raw_sessions=[]
        for metadata in manifest['chunks']:
            relative=safe_relative(metadata['path']);key=relative.as_posix()
            source=str(Path(metadata['source_path']).resolve())
            original=declared.get(source)
            if original is None or original['sha256']!=metadata['source_sha256']:
                raise ValueError('raw source is absent or changed in canonical generation manifest')
            if source in seen_sources:raise ValueError('duplicate canonical source chunk')
            if key in seen_paths:raise ValueError('duplicate raw metadata chunk path')
            seen_sources.add(source);seen_paths.add(key)
            bind(source,'canonical_generation_chunk',metadata['source_sha256'])
            data=path.parent/'chunks'/relative
            bind(data,'original_teacher_chunk',metadata['sha256'])
            metadata_path=data.parent/'metadata.json';raw_metadata,metadata_sha=read_json(metadata_path)
            if raw_metadata!=metadata:
                raise ValueError('raw chunk metadata differs from manifest; use original raw labeler segments')
            bind(metadata_path,'original_raw_chunk_metadata',metadata_sha)
            actual_ids=[];accepted=0
            with gzip.open(data,'rt') as stream:
                for line in stream:
                    if not line.endswith('\n'):raise ValueError('truncated raw game line')
                    game=json.loads(line);identity=game['game_id']
                    if identity in seen_games:raise ValueError('duplicate game ID across raw segments')
                    seen_games.add(identity);actual_ids.append(identity)
                    if any(row.get('game_id')!=identity for row in game['samples']):
                        raise ValueError('sample game identity differs from its complete game')
                    accepted+=len(game['samples'])
            if actual_ids!=metadata['game_ids'] or len(actual_ids)!=metadata['games'] or accepted!=metadata['accepted']:
                raise ValueError('actual raw game identities/counts differ from metadata')
            if metadata['teacher_depth']!=base['depth']:raise ValueError('raw chunk teacher depth changed')
            for key in TOTAL_KEYS:own_totals[key]+=metadata.get(key,0)
            raw_chunks.append((relative,data,metadata_path,metadata_sha,metadata))
            chunks.append(metadata)
        for key,value in manifest.get('totals',{}).items():
            if key in TOTAL_KEYS and not math.isclose(own_totals[key],value,rel_tol=1e-12,abs_tol=1e-6):
                raise ValueError('raw manifest counters differ from actual chunk counters: '+key)
        for session in manifest.get('transcript_sessions',[]):
            if not session.get('complete'):raise ValueError('raw UCI stream is not closed')
            directory=safe_relative(session['directory']);files=[]
            for record in session['segments']:
                filename=safe_relative(record['path']);raw=path.parent/directory/filename
                if not raw.is_file() or raw.stat().st_size!=record['bytes']:raise ValueError('raw UCI size/hash mismatch')
                bind(raw,'original_raw_uci_segment',record['sha256']);files.append((filename,raw,record))
            raw_sessions.append((directory,session,files))
        current_advertised=manifest.get('teacher_advertised_options',[])
        if advertised is None:advertised=current_advertised
        elif current_advertised!=advertised:raise ValueError('advertised teacher option set changed')
        identities.extend(manifest.get('teacher_identities',[]));network_messages.update(manifest.get('teacher_network_messages',[]))
        totals.update(own_totals)
        prepared.append((index,path,manifest,manifest_sha,raw_chunks,raw_sessions))
    if not chunks:raise ValueError('raw union is empty')
    bind(base['teacher_binary'],'pinned_independent_teacher_binary',base['teacher_sha256'])
    bind(Path(__file__).with_name('label_teacher_games.py'),'pinned_unchanged_labeler_source',base['tool_sha256'])
    merger_sha=bind(Path(__file__),'raw_segment_merger_source')
    if labeler.sha256(generation_path)!=generation_sha:
        raise ValueError('generation manifest changed during merge authentication')
    output.mkdir(parents=True,exist_ok=True)
    generation_snapshot=output/'generation-at-merge.json';generation_snapshot.write_bytes(generation_raw)
    bind(generation_snapshot,'generation_manifest_exact_observed_snapshot',generation_sha)
    def link(source,destination,kind,expected):
        destination.parent.mkdir(parents=True,exist_ok=True)
        os.link(source,destination)
        bind(destination,kind,expected)
    segments=[];sessions=[]
    for index,path,manifest,manifest_sha,raw_chunks,raw_sessions in prepared:
        name='segment%02d'%index;root=output/'raw-segments'/name
        link(path,root/'manifest.json','preserved_raw_segment_manifest',manifest_sha)
        for relative,data,metadata_path,metadata_sha,metadata in raw_chunks:
            # Global paths and metadata fields remain EXACTLY as originally emitted.
            link(data,output/'chunks'/relative,'merged_teacher_chunk',metadata['sha256'])
            link(metadata_path,(output/'chunks'/relative).parent/'metadata.json','merged_raw_chunk_metadata',metadata_sha)
            link(data,root/'chunks'/relative,'preserved_segment_teacher_chunk',metadata['sha256'])
            link(metadata_path,(root/'chunks'/relative).parent/'metadata.json','preserved_segment_raw_metadata',metadata_sha)
        for directory,session,files in raw_sessions:
            for filename,raw,record in files:
                link(raw,root/directory/filename,'preserved_raw_uci_segment',record['sha256'])
            sessions.append({**session,'directory':('raw-segments/'+name+'/'+directory.as_posix()),'segment':name})
        segments.append({'segment':name,'original_manifest_path':str(path),'manifest_sha256':manifest_sha,
            'preserved_manifest_path':str(root/'manifest.json'),'configuration':manifest['configuration'],
            'historical_workers':manifest['configuration']['workers'],'totals':manifest['totals']})
    # Verify all original AND preserved bytes again after the hardlinks exist.
    for record in bindings.values():
        if labeler.sha256(Path(record['path']))!=record['sha256']:
            raise ValueError('artifact hash changed during merge: '+record['path'])
    if labeler.sha256(generation_path)!=generation_sha:
        raise ValueError('generation manifest changed during merge publication')
    configuration={**base,'input_dir':str(generation_path.parent),'execution_model':'closed_raw_segment_union',
        'merge_tool_path':str(Path(__file__).resolve()),'merge_tool_sha256':merger_sha,
        'worker_count_scope':'historical configured teacher concurrency; no active workers in merger'}
    result={'schema':'forge-independent-teacher-games-v1','status':'complete','configuration':configuration,
        'execution_model':'closed_raw_segment_union','active_teacher_workers':0,'engines_launched':0,
        'chunks':sorted(chunks,key=lambda row:row['source_path']),'totals':dict(totals),
        'teacher_identities':identities,'teacher_identity_scope':'historical instances across closed raw segments',
        'teacher_advertised_options':advertised,'teacher_network_messages':sorted(network_messages),
        'transcript_sessions':sessions,'segments':segments,'artifact_bindings':list(bindings.values()),
        'generation_manifest_path':str(generation_path),'generation_manifest_sha256_observed':generation_sha,
        'generation_status_observed':generation.get('status'),
        'generation_snapshot_path':str(generation_snapshot),'generation_snapshot_sha256':generation_sha,
        'generation_observation_note':'Committed sources authenticated; generator status is preserved without claiming successful full generation. Original manifest may append after this merge.',
        'raw_metadata_policy':'exact original metadata bytes and fields; no path prefix or segment fields added to chunks',
        'stop_reason':'closed_raw_segment_union'}
    labeler.write_json_atomic(output/'manifest.json',result)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,action='append',required=True)
    parser.add_argument('--generation-manifest',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(argv)
    result=merge_segments(args.manifest,args.generation_manifest,args.output_dir)
    receipt={'status':'PASS_CLOSED_RAW_SEGMENT_UNION','output_manifest':str((args.output_dir/'manifest.json').resolve()),
        'manifest_sha256':labeler.sha256(args.output_dir/'manifest.json'),'segments':len(result['segments']),
        'games':result['totals']['games'],'accepted':result['totals']['accepted'],'chunks':len(result['chunks']),
        'metadata_fields_changed':0,'engines_launched':0,'artifact_bindings':len(result['artifact_bindings']),
        'merge_tool_sha256':result['configuration']['merge_tool_sha256'],
        'generation_status_observed':result['generation_status_observed']}
    labeler.write_json_atomic(args.output_dir/'merge-receipt.json',receipt)
    print(json.dumps(receipt,sort_keys=True),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
