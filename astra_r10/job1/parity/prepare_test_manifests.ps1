$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess(); $self.PriorityClass='Idle'; $self.ProcessorAffinity=[IntPtr]12
$python='D:\a10\python\python.exe'
foreach ($tag in @('red01','green01')) {
  $arguments=@('-B','D:\a10\wt\skills\eval-exact-simd-port\scripts\test_components.py','--threads','1')
  if ($tag -eq 'red01') { $arguments+=@('--baseline','D:\a10\wt\astra_r10\job1\parity\check_eval_parity_original.py') }
  $out=Join-Path $PSScriptRoot $tag
  $m=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;arguments=$arguments;working_directory=$PSScriptRoot;output_directory=$out;read_paths=@($python,'D:\a10\wt\skills\eval-exact-simd-port',$PSScriptRoot);write_paths=@($out);logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=10485760}
  $path=Join-Path $PSScriptRoot ($tag+'-manifest.json')
  if (Test-Path -LiteralPath $path) { throw 'Manifest already exists' }
  $m | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $path -Encoding UTF8
}
