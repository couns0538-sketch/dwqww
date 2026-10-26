"""One CPU-only RAM-loader probe; real archive execution requires root's BUILD window.

No disk restoration, package edits, installation or GPU operation. Ordinary
private-environment import remains unready outside this one owning process.
"""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

PRIVATE_ENV=Path('/workspace/.cloud-setup/nnue-pipeline-20261023-venv')
ARCHIVE=Path('/workspace/forge-pack24-20261025/forge_sol_S00_space_recovery_20261025/payloads/third_party/libtorch_cpu.so.gz')
COMPRESSED_SIZE=129931554
COMPRESSED_SHA256='a889e666c7922e02fc51569518a2742b5f74556840c45266fb2245fd78d81b9b'
RAW_SIZE=488851697
RAW_SHA256='0aae29741806982c5778f7863e53711edc5c4afb829595d7296f729ac176cfe3'
CHUNK=1024*1024
# Linux UAPI /usr/include/linux/fcntl.h: base1024 +9/+10 and bits1/2/4/8.
# Some Python builds omit the symbolic constants while the kernel supports them.
F_ADD_SEALS=getattr(fcntl,'F_ADD_SEALS',1033)
F_GET_SEALS=getattr(fcntl,'F_GET_SEALS',1034)
IMMUTABLE_SEALS=0x0001|0x0002|0x0004|0x0008


def verified_file_hash(path,expected):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(CHUNK):digest.update(block)
    value=digest.hexdigest()
    if value!=expected:raise ValueError('pinned file hash mismatch: '+str(path))
    return value


def preserve_evidence(source,destination):
    """Keep exact unique proof bytes as deterministic new gzip, then rehash."""
    raw=hashlib.sha256();size=0
    with Path(source).open('rb') as src,Path(destination).open('xb') as dst:
        with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as compressed:
            while block:=src.read(CHUNK):raw.update(block);size+=len(block);compressed.write(block)
    check=hashlib.sha256();count=0
    with gzip.open(destination,'rb') as decoded:
        while block:=decoded.read(CHUNK):check.update(block);count+=len(block)
    if count!=size or check.digest()!=raw.digest():raise ValueError('evidence archive roundtrip failed')
    packed=hashlib.sha256()
    with Path(destination).open('rb') as stream:
        while block:=stream.read(CHUNK):packed.update(block)
    return {'file':Path(destination).name,'raw_size':size,'raw_sha256':raw.hexdigest(),
            'compressed_size':Path(destination).stat().st_size,'compressed_sha256':packed.hexdigest()}


def sealed_memfd_from_gzip(path,*,compressed_size,compressed_sha256,raw_size,raw_sha256):
    """Validate compressed/raw bytes, then return an immutable anonymous fd."""
    if type(compressed_size) is not int or type(raw_size) is not int or compressed_size<0 or raw_size<0:
        raise ValueError('compressed/raw sizes must be nonnegative integers')
    fd=None
    try:
        with Path(path).open('rb') as source:
            if os.fstat(source.fileno()).st_size!=compressed_size:raise ValueError('compressed size mismatch')
            outer=hashlib.sha256();count=0
            while block:=source.read(CHUNK):
                outer.update(block);count+=len(block)
                if count>compressed_size:raise ValueError('compressed size changed')
            if count!=compressed_size or outer.hexdigest()!=compressed_sha256:raise ValueError('compressed hash/size mismatch')
            source.seek(0)
            fd=os.memfd_create('forge_s09_verified_libtorch_cpu',os.MFD_ALLOW_SEALING|os.MFD_CLOEXEC)
            inner=hashlib.sha256();count=0
            with gzip.GzipFile(fileobj=source,mode='rb') as decoded:
                while block:=decoded.read(min(CHUNK,raw_size-count+1)):
                    count+=len(block)
                    if count>raw_size:raise ValueError('raw decompression exceeds pinned size')
                    inner.update(block);view=memoryview(block)
                    while view:
                        written=os.write(fd,view)
                        if written<=0:raise ValueError('raw memfd write failed')
                        view=view[written:]
            if count!=raw_size or inner.hexdigest()!=raw_sha256:raise ValueError('raw hash/size mismatch')
            if os.fstat(fd).st_size!=raw_size:raise ValueError('raw memfd size mismatch')
            seals=IMMUTABLE_SEALS
            fcntl.fcntl(fd,F_ADD_SEALS,seals)
            if fcntl.fcntl(fd,F_GET_SEALS)&seals!=seals:raise ValueError('raw memfd immutable sealing failed')
            os.lseek(fd,0,os.SEEK_SET)
            result=fd;fd=None;return result
    except (OSError,EOFError) as error:
        raise ValueError('gzip/raw decode or memfd operation failed: '+str(error)) from error
    finally:
        if fd is not None:os.close(fd)


def _s09_cpu_proof(torch,out):
    import importlib.util
    import tempfile
    import shutil
    import numpy as np
    staged=Path('/workspace/forge-pack24-20261026/S09')
    before=json.loads((staged/'forge_sol_S09_source_before_20261026.json').read_text())
    legacy=Path(before['legacy_trainer']['path']);candidate=staged/'forge_sol_S09_train_resid_v3b_20261026.py'
    receipt=json.loads((staged/'forge_sol_S09_receipt_20261026.json').read_text())
    legacy_hash=verified_file_hash(legacy,before['legacy_trainer']['sha256_before'])
    candidate_hash=verified_file_hash(candidate,receipt['implementation_sha256'][candidate.name])
    def module(path,name):
        spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
        sys.modules[name]=value;spec.loader.exec_module(value);return value
    old=module(legacy,'forge_s09_actual_legacy');new=module(candidate,'forge_s09_actual_candidate')
    torch.manual_seed(25);baseline=old.NNUE(256,qat=True,residual=True).cpu()
    torch.manual_seed(25);one=new.NNUE(256,qat=True,residual=True,buckets=1).cpu()
    if not all(torch.equal(value,one.state_dict()[key]) for key,value in baseline.state_dict().items()):
        raise ValueError('actual bucket1 initialization differs from v3b')
    with torch.no_grad():
        baseline.out.weight.uniform_(-0.025,0.025);baseline.out.bias.fill_(0.01)
    one.load_state_dict(baseline.state_dict())
    eight=new.NNUE(256,qat=True,residual=True,buckets=8).cpu()
    eight.ft.load_state_dict(baseline.ft.state_dict())
    with torch.no_grad():
        eight.out.weight.copy_(baseline.out.weight.repeat(8,1));eight.out.bias.copy_(baseline.out.bias.repeat(8))
    state_before={key:value.detach().cpu().numpy().copy() for key,value in eight.state_dict().items()}
    folder=Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/06_jobD/data32_sample/data32_sample_50k')
    paths=[folder/name for name in ['t00000.pos','t00000.hce','h000.pos','h000.hce']]
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    training=old.load_set_mmap([str(folder/'t00000.pos')],str(folder),limit=192)
    held=old.load_set_mmap([str(folder/'h000.pos')],str(folder),limit=512)
    def batch(data,indices):
        codes,stm,wres,score,hce=old.make_batch(data,np.asarray(indices,dtype=np.int64))
        return (torch.from_numpy(codes.astype(np.int64)),torch.from_numpy(stm.astype(np.int64)),
                torch.from_numpy(wres.astype(np.float32)),torch.from_numpy(score.astype(np.float32)),
                torch.from_numpy(hce.astype(np.float32))*(2.25/400.0))
    codes,stm,wres,score,hce=batch(held,range(512));target=old.targets(score,stm,wres,2.25,0.6)[2]
    with torch.no_grad():
        a=baseline(codes,stm,hce);b=one(codes,stm,hce);c=eight(codes,stm,hce)
        if not torch.equal(a,b):raise ValueError('actual bucket1 forward differs from v3b')
        maximum=float(torch.max(torch.abs(a-c)))
        if maximum>1e-5:raise ValueError('replicated bucket8 Torch forward exceeds declared float tolerance')
        loss_before=float(torch.nn.functional.mse_loss(torch.sigmoid(c),target))
    temporary=Path(tempfile.mkdtemp(prefix='forge_sol_S09_actual_exports_',dir=out))
    try:
        old.export_forge(baseline,temporary/'legacy',2.25,True);new.export_forge(one,temporary/'one',2.25,True)
        export_hashes={};archives=[]
        for suffix in ['.inc','.bin']:
            left=(temporary/'legacy').with_suffix(suffix);right=(temporary/'one').with_suffix(suffix)
            if left.read_bytes()!=right.read_bytes():raise ValueError('actual bucket1 export differs from v3b')
            export_hashes[suffix]=hashlib.sha256(right.read_bytes()).hexdigest()
            archives.append(preserve_evidence(left,out/('legacy'+suffix+'.gz')))
            archives.append(preserve_evidence(right,out/('one'+suffix+'.gz')))
        optimizer=torch.optim.Adam(eight.parameters(),lr=0.000707,foreach=False);losses=[]
        for step in range(3):
            tc,ts,tw,sc,hc=batch(training,range(step*64,(step+1)*64));tg=old.targets(sc,ts,tw,2.25,0.6)[2]
            optimizer.zero_grad();loss=torch.nn.functional.mse_loss(torch.sigmoid(eight(tc,ts,hc)),tg)
            loss.backward()
            if not all(p.grad is not None and torch.isfinite(p.grad).all().item() for p in eight.parameters()):
                raise ValueError('actual bucket8 gradient missing/nonfinite')
            optimizer.step();eight.project_weights();losses.append(float(loss.detach()))
        with torch.no_grad():loss_after=float(torch.nn.functional.mse_loss(torch.sigmoid(eight(codes,stm,hce)),target))
        new.export_forge(eight,temporary/'eight_trained3steps',2.25,True)
        exported=hashlib.sha256((temporary/'eight_trained3steps.inc').read_bytes()).hexdigest()
        for suffix in ['.inc','.bin']:
            archives.append(preserve_evidence((temporary/'eight_trained3steps').with_suffix(suffix),out/('eight_trained3steps'+suffix+'.gz')))
        state_after={key:value.detach().cpu().numpy().copy() for key,value in eight.state_dict().items()}
        checkpoint=out/'forge_sol_S09_CPU_before_after3steps_20261026.npz'
        np.savez_compressed(checkpoint,**{'before.'+k:v for k,v in state_before.items()},**{'after.'+k:v for k,v in state_after.items()})
        with np.load(checkpoint,allow_pickle=False) as checked:
            for phase,values in [('before',state_before),('after',state_after)]:
                for key,value in values.items():
                    if not np.array_equal(checked[phase+'.'+key],value):raise ValueError('CPU state checkpoint roundtrip failed')
        checkpoint_hash=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    finally:shutil.rmtree(temporary)
    if any(hashlib.sha256(p.read_bytes()).hexdigest()!=hashes[p.name] for p in paths):raise ValueError('sample input changed')
    verified_file_hash(legacy,legacy_hash);verified_file_hash(candidate,candidate_hash)
    if not all(p.device.type=='cpu' for p in eight.parameters()):raise ValueError('non-CPU model parameter')
    return {'bucket1_actual_initialization_forward_export_bitexact':True,'actual_bucket1_export_sha256':export_hashes,
            'replicated8_Torch_max_abs_logit_difference':maximum,'replicated8_Torch_tolerance':1e-5,
            'three_actual_bucket8_CPU_training_losses':losses,'optimizer':'torch Adam foreachFalse CPU smoke; default DML optimizer runtime pending',
            'holdout_rows':512,'holdout_scope':'synthetic h000 prefix; real013014 absent; no strength or improvement claim',
            'holdout_blend':0.6,'holdout_MSE_before':loss_before,'holdout_MSE_after3steps':loss_after,
            'trained3step_export_sha256':exported,'training_rows':192,'source_input_sha256':hashes,
            'source_inputs_unchanged':True,'candidate_trainer_sha256':receipt['implementation_sha256'][candidate.name],
            'legacy_trainer_sha256':legacy_hash,'reversible_export_archives':archives,
            'before_after_checkpoint':{'file':checkpoint.name,'sha256':checkpoint_hash,'bytes':checkpoint.stat().st_size},
            'parity_state':'seed25 initialization, then shared nonzero output weights for nontrivial forward/export parity; not a trained f006 checkpoint',
            'native1M_parity':'UNVERIFIED_NOT_RUN','Std_null_regression':'UNVERIFIED_NOT_RUN'}


def _real_probe(out,state):
    """Deferred real operation: invoke only after explicit root authorization."""
    if Path(sys.prefix).resolve()!=PRIVATE_ENV.resolve():raise ValueError('use the exact private-environment interpreter')
    libdirs=list((PRIVATE_ENV/'lib').glob('python*/site-packages/torch/lib'))
    if len(libdirs)!=1:raise ValueError('private Torch library directory is ambiguous/missing')
    libdir=libdirs[0]
    if (libdir/'libtorch_cpu.so').exists():raise ValueError('ordinary library state changed; re-review before using RAM probe')
    for name in ('libgomp-a34b3233.so.1','libc10.so','libtorch_python.so'):
        if not (libdir/name).is_file():raise ValueError('required existing dependency missing: '+name)
    available=os.sysconf('SC_AVPHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')
    if available<RAW_SIZE+512*1024*1024:raise ValueError('insufficient free RAM for one owning CPU probe')
    for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[name]='1'
    os.environ['CUDA_VISIBLE_DEVICES']=''
    fd=sealed_memfd_from_gzip(ARCHIVE,compressed_size=COMPRESSED_SIZE,compressed_sha256=COMPRESSED_SHA256,
                              raw_size=RAW_SIZE,raw_sha256=RAW_SHA256)
    state.update(verified_raw_memfd=True,raw_size=RAW_SIZE,raw_sha256=RAW_SHA256,
                 compressed_size=COMPRESSED_SIZE,compressed_sha256=COMPRESSED_SHA256,
                 immutable_seals=fcntl.fcntl(fd,F_GET_SEALS))
    try:
        import ctypes
        mode=ctypes.RTLD_GLOBAL|os.RTLD_NOW
        handles=[ctypes.CDLL(str(libdir/'libgomp-a34b3233.so.1'),mode=mode),
                 ctypes.CDLL(str(libdir/'libc10.so'),mode=mode)]
        handles.append(ctypes.CDLL('/proc/self/fd/'+str(fd),mode=mode))
        import torch
        torch.set_num_threads(1);torch.set_num_interop_threads(1)
        state.update(Torch_import='PASS_IN_OWNING_PROCESS_ONLY',torch_version=torch.__version__)
        # Concrete CPU-only arithmetic/autograd check; no package-global changes.
        torch.manual_seed(25)
        layer=torch.nn.Linear(4,1,device='cpu');optimizer=torch.optim.SGD(layer.parameters(),lr=0.01)
        x=torch.arange(32,dtype=torch.float32,device='cpu').reshape(8,4)/32
        target=torch.zeros((8,1),device='cpu');losses=[]
        for _ in range(3):
            optimizer.zero_grad();loss=(layer(x)-target).square().mean();loss.backward();optimizer.step()
            losses.append(float(loss.detach()))
        if not all(torch.isfinite(p).all().item() for p in layer.parameters()):raise ValueError('nonfinite CPU toy parameters')
        state['S09_actual_CPU_proof']=_s09_cpu_proof(torch,out)
        state.update({'status':'PASS_CPU_MEMFD_S09_PROCESS_ONLY','torch_version':torch.__version__,
                'ordinary_environment_ready':False,'raw_size':RAW_SIZE,'raw_sha256':RAW_SHA256,
                'compressed_size':COMPRESSED_SIZE,'compressed_sha256':COMPRESSED_SHA256,
                'immutable_seals':fcntl.fcntl(fd,F_GET_SEALS),'cpu_only':True,
                'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES'],'cpu_threads':torch.get_num_threads(),
                'three_CPU_toy_losses':losses,
                'package_edits':False,'disk_restore':False,'GPU_execution':False})
        return state
    finally:os.close(fd)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorized-build-window',choices=['f022-BUILD'],required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.out.exists():
        print('output folder must be new',file=sys.stderr);return 2
    args.out.mkdir(parents=False,exist_ok=False)
    # This flag records the root coordinator's explicit authorization; it is
    # not a substitute for obtaining that authorization before invocation.
    result={'ordinary_environment_ready':False,'disk_restore':False,'package_edits':False,'root_build_window':args.authorized_build_window}
    try:
        result=_real_probe(args.out,result)
    except Exception as error:
        result.update(status='FAILED_UNVERIFIED',error_type=type(error).__name__,error=str(error))
        code=1
    else:code=0
    (args.out/'forge_sol_S09_torchram_result_20261026.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True));return code


if __name__=='__main__':sys.exit(main())
