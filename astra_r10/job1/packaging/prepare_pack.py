"""Prepare the Job 1 incomplete evidence pack after timing exits. UNPROVEN.

Task-specific collector. Run only after review, through the safety launcher.
It never starts an engine or seals a pack itself. Existing attempts are retained.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

ROOT = Path('D:/a10')
WT = ROOT/'wt'
JOB = WT/'astra_r10/job1'
PACK = JOB/'pack'
PRODUCTION = '775edea1d476a3a18c64af63f53c55d6e29a4571556aad2666e87f18a6ef4284'
LOCK = 'fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072'
PROTOCOL = 'c83ccb17d428069be129eaf4f1b253dbf299bb6d77ad0353a5667fa82ccb3245'
SEALER = WT/'skills/gate-handover-pack/scripts/seal_evidence.py'
sys.path.insert(0,str(SEALER.parent))
import seal_evidence as sealing
sys.path.insert(0, 'D:/a10/wt/astra_r10/job1')  # CR crfix 0e91e02e: shared lane guard (crfix_abcbb9c9 lane_guard.py 596ecbe6)
import lane_guard


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return sealing.decode(sealing.json_bytes(sealing.checked_path(path)))


def hash_file(path):
    return sealing.digests(sealing.checked_path(path))[0]


def write_new(path, value):
    data = value if isinstance(value,bytes) else (json.dumps(value,indent=2)+'\n').encode()
    sealing.write_new(path,data)


def timestamp(value):
    require(isinstance(value,str),'completion timestamp missing')
    result=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
    require(result.tzinfo is not None,'completion timestamp needs timezone')
    return result


def completed_timing():
    """The safe-launcher receipt is emitted only after its child exited/drained."""
    summary_path=JOB/'timing/run01/summary.json'
    receipt_path=JOB/'timing/run-launch02/result.json'
    require(summary_path.is_file() and receipt_path.is_file(),
            'timing summary AND completed launcher receipt required; do not seal active logs')
    summary=load(summary_path);receipt=load(receipt_path)
    launched_manifest_path=receipt_path.parent/'manifest.json'
    launched_manifest=load(launched_manifest_path)
    require(hash_file(launched_manifest_path)==receipt.get('manifest_sha256','').lower(),
            'completion receipt is not bound to the copied launcher manifest')
    launched_args=launched_manifest.get('arguments',[])
    for flag,expected_path in (('--protocol',JOB/'timing/protocol.json'),('--out',JOB/'timing/run01')):
        require(launched_args.count(flag)==1 and launched_args.index(flag)+1<len(launched_args),
                'unexpected timing launcher arguments')
        require(Path(launched_args[launched_args.index(flag)+1])==expected_path,'wrong timing launch target')
    require(hash_file(JOB/'timing/protocol.json')==hash_file(JOB/'timing/run01/PROTOCOL.json')==PROTOCOL
            and summary.get('protocol_sha256')==PROTOCOL,'timing protocol identity differs')
    require(summary.get('status') in ('CALIBRATION_FAIL','INCOMPLETE','BELOW_THRESHOLD','ADVISORY_THRESHOLD_MET'),
            'timing has not reached a recognized final status')
    require(type(receipt.get('native_exit_code')) is int,'launcher has not recorded native exit completion')
    require(timestamp(receipt.get('finished_utc'))>=timestamp(summary.get('finish_utc')),
            'launcher completion precedes timing summary')
    expected=0 if summary['status'] in ('BELOW_THRESHOLD','ADVISORY_THRESHOLD_MET') else 1
    require(receipt['native_exit_code']==expected,'timing status and native exit code disagree')
    # Preserve failure evidence but disclose incomplete capture/floor qualification.
    require(isinstance(receipt.get('capture_errors'),list) and type(receipt.get('disk_floor_breached')) is bool,
            'malformed launcher completion receipt')
    return summary,receipt


def prepare(destination, launcher_output):
    destination=sealing.checked_path(destination)
    launcher_output=sealing.checked_path(launcher_output)
    require(launcher_output.is_relative_to(JOB) and (launcher_output/'manifest.json').is_file(),
            'identify this active safe-launcher output under job1')
    require(destination.is_relative_to(JOB/'packaging'),'preparation output must be inside job1/packaging')
    require(not destination.exists() and not PACK.exists(),'preparation/pack output already exists; use a new attempt')
    summary,receipt=completed_timing()
    # Parent finishes this document before collecting, then holds inputs stable.
    require((JOB/'HANDOVER.md').is_file(),'root must finish job1/HANDOVER.md before preparation')
    require(hash_file(ROOT/'inputs/lock.exe')==LOCK,'wrong lock binary')
    candidates=[ROOT/f'b/{tag}/src_copy/forge_ltopgo_{tag}.exe' for tag in ('pc1-a','pc2-a')]
    require(all(hash_file(p)==PRODUCTION for p in candidates),'both production builds must be 775EDEA1')
    require(not os.path.samefile(*candidates),'independent production files required')
    require(load(JOB/'build-proof01/REPORT.json').get('status')=='PASS','native build proof did not PASS')

    # No bulk copies here: nominate originals directly, omit their archived twins.
    sources=set(); aliases={}; excluded=[]
    skip_trees={JOB/'build-proof01',JOB/'native-parity',PACK,destination,launcher_output}
    def add(path):
        path=sealing.checked_path(path)
        require(path.is_file(),'required artifact missing: '+str(path))
        sources.add(path)
    def tree(directory):
        directory=sealing.checked_path(directory)
        require(directory.is_dir(),'required evidence directory missing: '+str(directory))
        pending=[directory]
        while pending:
            current=pending.pop()
            with os.scandir(current) as entries:
                for entry in entries:
                    path=Path(entry.path)
                    require(not sealing.reparse(path),'reparse evidence refused: '+str(path))
                    if entry.is_dir(follow_symlinks=False):
                        if path in skip_trees or (current==JOB/'packaging' and path!=destination):
                            excluded.append({'path':str(path),'reason':
                                'current preparation launcher is still active; retained outside final input list' if path==launcher_output else
                                'archive duplicate or earlier preparation; original files retained'})
                        else:pending.append(path)
                    else:add(path)

    for directory in (ROOT/'b/pc1-a',ROOT/'b/pc2-a',ROOT/'c1',ROOT/'parity-negative',
                      ROOT/'parity-r1',ROOT/'parity-compiler-probe01',ROOT/'kit',ROOT/'inputs',JOB,WT/'skills'):
        tree(directory)
    add(JOB/'build-proof01/REPORT.json')
    archive_path=JOB/'native-parity/ARCHIVE.json';add(archive_path)
    archive=load(archive_path)
    require(archive.get('status')=='PASS' and isinstance(archive.get('files'),list),'native archive manifest incomplete')
    for entry in archive['files']:
        original=sealing.checked_path(entry['source']);add(original)
        # The preserved legacy archive uses Windows separators; the new manifest
        # uses slash-separated relative paths. Validate after separator conversion.
        alias=sealing.checked_path(JOB/'native-parity'/sealing.relative_name(entry['path'].replace('\\','/')))
        aliases[str(alias)]=original
    for tag in ('pc1-a','pc2-a'):
        for original in list(sources):
            for base,copybase in ((ROOT/'b'/tag,JOB/'build-proof01'/tag),
                                  (JOB/('build-'+tag),JOB/'build-proof01'/(tag+'-runner'))):
                if original.is_relative_to(base):aliases[str(copybase/original.relative_to(base))]=original
    recovered=ROOT/'inputs/r9.exe'
    if recovered in sources:
        require(hash_file(recovered)==PRODUCTION,'recovered R9 identity differs')
        sources.remove(recovered);aliases[str(recovered)]=candidates[0]
    for name in ('c1-source.json','auxiliary-build-provenance.json'):
        add(WT/'astra_r9/evidence'/name)
    for path in (WT/'AGENTS.md',WT/'astra_r10/RESULTS.md',WT/'astra_r10/RESUME.md',WT/'astra_r10/PLAN.md'):
        add(path)
    # Keep a licence/idea record if the branch supplies either conventional path.
    for path in (WT/'IDEA_SOURCE.md',WT/'astra_r10/IDEA_SOURCE.md'):
        if path.is_file():add(path)

    def role(path):
        if path in candidates:return 'production_candidate'
        if path==ROOT/'inputs/lock.exe':return 'baseline_binary'
        if path.suffix.lower() in ('.exe','.dll'):
            return 'auxiliary_fixture_binary' if any(x.endswith('-tests') for x in path.parts) else 'auxiliary_binary'
        if path.is_relative_to(ROOT/'parity-r1') or path.is_relative_to(ROOT/'parity-negative'):return 'auxiliary_parity_evidence'
        if path.is_relative_to(JOB/'timing'):return 'timing_evidence'
        return 'original_evidence'

    artifacts=[]
    for path in sorted(sources):
        artifacts.append({'role':role(path),'path':path.relative_to(ROOT).as_posix(),'sha256':hash_file(path)})
    by_path={str(ROOT/item['path']):item for item in artifacts}
    for entry in archive['files']:
        require(by_path[str(Path(entry['source']))]['sha256']==entry['sha256'].lower(),
                'original parity evidence differs from frozen archive manifest')
    blockers=['T4 UNVERIFIED: host loaded; no four-thread smoke executed.',
              'No fresh trusted active/archived gate seed inventory; live seed availability UNVERIFIED.',
              'Generic forge-lock-proof-set compiler -Werror witness contract differs from exact kit v2.3; reviewed native collector and original logs are supplied.']
    if summary['status']=='CALIBRATION_FAIL':
        blockers.append('A/A calibration FAIL; protocol stopped candidate comparison. No ABBA candidate gain was measured; do not relabel as below threshold.')
    elif summary['status']=='INCOMPLETE':blockers.append('Timing INCOMPLETE; no qualified speed conclusion.')
    elif summary['status']=='BELOW_THRESHOLD':blockers.append('Completed candidate ABBA result is below the preregistered 1.0% threshold.')
    if receipt['capture_errors'] or receipt['disk_floor_breached']:
        blockers.append('Timing launcher reported capture/disk errors; retain original receipt and treat affected native evidence as unqualified.')
    sealing.disk_budget(10_000_000)
    require(sealing.workspace_bytes()+10_000_000<=sealing.CAP,'insufficient workspace reservation for preparation')
    destination.mkdir(parents=True,exist_ok=False)
    mapping={'schema':1,'source_root':str(ROOT),'pack_root':str(PACK),
        'direct':[{'source':str(ROOT/a['path']),'packed':'artifacts/'+a['path'],'sha256':a['sha256'],'role':a['role']} for a in artifacts],
        'archive_aliases':[{'original_reference':alias,'packed':'artifacts/'+original.relative_to(ROOT).as_posix(),
                           'sha256':by_path[str(original)]['sha256']} for alias,original in sorted(aliases.items())],
        'omitted_duplicate_trees':excluded,
        'generated_metadata':[{'source':str(destination/name),'packed':'artifacts/'+(destination/name).relative_to(ROOT).as_posix()}
            for name in ('PATH_MAP.json','PACK_NOTES.json','seal-launch.json','verify-launch.json','COMMANDS.txt')],
        'request_copy':{'source':str(destination/'pack-request.json'),'packed':'REQUEST.json'},
        'note':'Generated metadata hashes are bound by REQUEST.json; PATH_MAP cannot contain its own hash.'}
    write_new(destination/'PATH_MAP.json',mapping)
    notes={'schema':1,'status':'UNPROVEN','pack_purpose':'incomplete-engine','production_sha256':PRODUCTION,
        'baseline_sha256':LOCK,'native_build_source_commit':'f43a26aeed2448379fc2916b25f31ead8707b0ec',
        'timing_status':summary['status'],'timing_phase_summaries':summary.get('phase_summaries'),
        'blockers':blockers,'auxiliary_policy':'Only production_candidate entries may be used as crew candidate engines; baseline_binary is the accepted FD3A5190 opponent. Every remaining exe/DLL is auxiliary evidence, never a gate variant.',
        'seed_record':{'parity_experiment_seed':3771096103,'gate_seeds':'NONE; availability UNVERIFIED'},
        'scope':'Preserved original evidence. Hashes/packing are not new native proof or Elo claims.'}
    write_new(destination/'PACK_NOTES.json',notes)
    manifest_path=destination/'pack-request.json'
    python=ROOT/'python/python.exe';python_hash=hash_file(python)
    def launch_manifest(name,args,reads,writes):
        launch_out=destination/('launch-'+name)
        return {'schema':1,'executable':str(python),'executable_sha256':python_hash,
            'arguments':['-B',*map(str,args),'--threads','1'],'working_directory':str(ROOT),
            'output_directory':str(launch_out),'read_paths':[str(python),str(ROOT/'python'),*map(str,reads)],
            'write_paths':[str(launch_out),*map(str,writes)],'logical_cpus':[2],'worker_threads':1,
            'minimum_free_mib':51200,'required_bytes':10_000_000}
    seal_launch=launch_manifest('seal',[SEALER,manifest_path,'--purpose','incomplete-engine','--out',PACK],
                                [ROOT],[PACK])
    # Launcher reservation includes full copied payload plus bounded metadata.
    seal_launch['required_bytes']=sum((ROOT/a['path']).stat().st_size for a in artifacts)+10_000_000
    write_new(destination/'seal-launch.json',seal_launch)
    verifier=Path(__file__).with_name('verify_pack.py')
    write_new(destination/'verify-launch.json',launch_manifest('verify',[verifier,'--pack',PACK],[verifier,PACK],[]))
    commands=(f'UNPROVEN — Job 1 evidence sealing, no gate or match commands\n\n'
        f'powershell -NoProfile -File D:\\a10\\wt\\astra_r10\\launch.ps1 -Manifest "{destination / "seal-launch.json"}"\n'
        f'powershell -NoProfile -File D:\\a10\\wt\\astra_r10\\launch.ps1 -Manifest "{destination / "verify-launch.json"}"\n\n'
        'Run sequentially after root review. Do not reuse output directories. The second command independently checks both checksum manifests and complete file coverage.\n'
        'For crew reproduction, restore/remap original absolute references using PATH_MAP.json. Original command, manifest, source, compiler and profile records are shipped unchanged; use NEW output paths and the full protected roots.\n'
        'A/A failure stops the registered experiment: no comparison or relaxed-noise retry is authorized by this pack. Crew official ABBA/SPRT requires its own reviewed protocol and fresh seed-availability check. UHO only.\n')
    write_new(destination/'COMMANDS.txt',commands.encode())
    for name in ('PATH_MAP.json','PACK_NOTES.json','seal-launch.json','verify-launch.json','COMMANDS.txt'):
        path=destination/name;artifacts.append({'role':'handoff_metadata','path':path.relative_to(ROOT).as_posix(),'sha256':hash_file(path)})
    write_new(manifest_path,{'schema':1,'source_root':str(ROOT),'artifacts':artifacts,'blockers':blockers})
    # Recheck completion records; do not produce a request over changing timing evidence.
    require(completed_timing()==(summary,receipt),'timing completion evidence changed during preparation')
    print(json.dumps({'status':'PREPARED_INCOMPLETE','strength':'UNPROVEN','manifest':str(manifest_path),
        'manifest_sha256':hash_file(manifest_path),'artifacts':len(artifacts),'blockers':blockers},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threads',type=int,choices=(1,),required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--launcher-output',type=Path,required=True)
    args=parser.parse_args()
    lane_guard.check_lane()  # before any output
    prepare(args.out,args.launcher_output)
