$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess(); $self.PriorityClass='Idle'; $self.ProcessorAffinity=[IntPtr]12
$python='D:\a10\python\python.exe'
$pythonHash=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash
$adapter=Join-Path $PSScriptRoot 'parity_adapter.py'
$skill='D:\a10\wt\skills\eval-exact-simd-port'
$commonReads=@($python,$PSScriptRoot,$skill,'D:\a10\c1','D:\a10\inputs\fens_12k.txt')
$jobs=@(
 @{name='red02';args=@('-B',(Join-Path $skill 'scripts\test_components.py'),'--threads','1','--baseline',(Join-Path $PSScriptRoot 'check_eval_parity_original.py'));read=@();write=@()},
 @{name='green02';args=@('-B',(Join-Path $skill 'scripts\test_components.py'),'--threads','1');read=@();write=@()},
 @{name='adapter-green01';args=@('-B',(Join-Path $PSScriptRoot 'test_adapter.py'),'--threads','1');read=@();write=@()},
 @{name='prepare-launch01';args=@('-B',$adapter,'--threads','1','prepare','--source','D:\a10\c1','--negative-source','D:\a10\parity-negative','--fens','D:\a10\inputs\fens_12k.txt','--out','D:\a10\parity-r1','--seed','3771096103');read=@();write=@('D:\a10\parity-r1','D:\a10\parity-negative')},
 @{name='build-launch01';args=@('-B',$adapter,'--threads','1','build','--prepared','D:\a10\parity-r1\prepared.json','--compiler-config',(Join-Path $PSScriptRoot 'compiler.json'));read=@('D:\a10\parity-r1','D:\a10\parity-negative');write=@('D:\a10\parity-r1')},
 @{name='run-launch01';args=@('-B',$adapter,'--threads','1','run','--prepared','D:\a10\parity-r1\prepared.json');read=@('D:\a10\parity-r1','D:\a10\parity-negative');write=@('D:\a10\parity-r1')},
 @{name='check-launch01';args=@('-B',(Join-Path $skill 'scripts\check_eval_parity.py'),'D:\a10\parity-r1\eval-parity.json','--threads','1');read=@('D:\a10\parity-r1','D:\a10\parity-negative');write=@()}
)
foreach ($job in $jobs) {
  $out=Join-Path $PSScriptRoot $job.name
  $manifest=Join-Path $PSScriptRoot ($job.name+'-manifest.json')
  if (Test-Path -LiteralPath $manifest) { throw 'Manifest already exists' }
  $m=@{schema=1;executable=$python;executable_sha256=$pythonHash;arguments=$job.args;working_directory=$PSScriptRoot;output_directory=$out;read_paths=@($commonReads)+@($job.read);write_paths=@($out)+@($job.write);logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=209715200}
  $m | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifest -Encoding UTF8
}
