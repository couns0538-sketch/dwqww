#requires -Version 5.1
# Prepare reviewable input files only. This never launches the native job.
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9-]+$')][string]$Tag,
      [Parameter(Mandatory=$true)][ValidateSet('preflight','suite')][string]$Mode,
      [ValidateSet(2,3)][int]$PreflightCpu=2)
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]4
$root='D:\a10\wt\astra_r10\job3\regression'
$runtime='D:\a10\job3\runtime312'
$runtimeManifest=Join-Path $runtime 'RUNTIME_FILES.json'
$runner=Join-Path $root 'run_regression.py'
$helper='D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1'
$helperSha='17205767AE3EA35A5CCB5A7965BC4988BAE26B4F2260C821411A657C9979C787'
if((Get-FileHash -LiteralPath $helper -Algorithm SHA256).Hash -ne $helperSha){throw 'Reviewed helper changed'}
$out='D:\a10\job3\regression-runs\'+$Tag
$launch=Join-Path $root ($Tag+'-launch')
$manifest=Join-Path $root ($Tag+'.manifest.json')
$wrapper=Join-Path $root ('launch_'+$Tag+'.ps1')
foreach($path in @($out,$launch,$manifest,$wrapper)){if(Test-Path -LiteralPath $path){throw ('Attempt must be fresh: '+$path)}}
$runtimeSha=(Get-FileHash -LiteralPath $runtimeManifest -Algorithm SHA256).Hash
$runtimeRecord=Get-Content -LiteralPath $runtimeManifest -Raw|ConvertFrom-Json
if($runtimeRecord.schema -ne 1 -or $runtimeRecord.status -ne 'RUNTIME_ASSEMBLED'){throw 'Private CPU runtime is not assembled'}
$exe=Join-Path $runtime 'python\python.exe'
$nativeArgs=@('-B',$runner,'--threads','2','--out',$out,'--runtime-manifest-sha256',$runtimeSha)
if($Mode -eq 'preflight'){$nativeArgs+=@('--preflight-only');$cpus=@($PreflightCpu)}else{$cpus=@(2,3)}
$toolRoots=@('C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.51.36231','C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0','C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0')
$job=[ordered]@{schema=1;executable=$exe;executable_sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash;arguments=$nativeArgs;working_directory='D:\a10';output_directory=$launch;read_paths=@($exe,$runtime,$root,'D:\grok-pc-data\npt\nnue-pytorch-amd')+$toolRoots;write_paths=@($out,$launch);logical_cpus=$cpus;worker_threads=2;minimum_free_mib=51200;required_bytes=536870912}
[IO.File]::WriteAllText($manifest,($job|ConvertTo-Json -Depth 8),(New-Object Text.UTF8Encoding($false)))
$template=@'
#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$env:PYTHONDONTWRITEBYTECODE='1';$env:PYTHONNOUSERSITE='1'
$env:CUDA_VISIBLE_DEVICES='';$env:HIP_VISIBLE_DEVICES='';$env:ROCR_VISIBLE_DEVICES=''
$helper='D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1'
$helperSha='__HELPER_SHA__'
$manifest='__MANIFEST__'
$runner='__RUNNER__'
if((Get-FileHash -LiteralPath $helper -Algorithm SHA256).Hash -ne $helperSha){throw 'Reviewed helper changed'}
if((Get-FileHash -LiteralPath $runner -Algorithm SHA256).Hash -ne '__RUNNER_SHA__'){throw 'Reviewed runner changed'}
if((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ne '__MANIFEST_SHA__'){throw 'Manifest changed after preparation'}
$roots=@('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
$runtimeRoots=@('D:\grok-pc-data\npt\nnue-pytorch-amd')
$toolRoots=@('C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.51.36231','C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0','C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0')
$binding='__BINDING__'
if(Test-Path -LiteralPath $binding){throw 'No evidence overwrite'}
[ordered]@{start_utc=[DateTime]::UtcNow.ToString('o');helper_sha256=$helperSha;runner_sha256='__RUNNER_SHA__';manifest_sha256='__MANIFEST_SHA__';wrapper_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash}|ConvertTo-Json|Set-Content -LiteralPath $binding -Encoding UTF8
& $helper -Manifest $manifest -ProtectedRoots $roots -ReadOnlyRuntimeRoots $runtimeRoots -ReadOnlyToolchainRoots $toolRoots
exit $LASTEXITCODE
'@
$template=$template.Replace('__HELPER_SHA__',$helperSha).Replace('__MANIFEST__',$manifest).Replace('__RUNNER__',$runner).Replace('__RUNNER_SHA__',(Get-FileHash -LiteralPath $runner -Algorithm SHA256).Hash).Replace('__MANIFEST_SHA__',(Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash).Replace('__BINDING__',(Join-Path $root ($Tag+'-command.json')))
[IO.File]::WriteAllText($wrapper,$template,(New-Object Text.UTF8Encoding($false)))
[ordered]@{manifest=$manifest;wrapper=$wrapper;runtime_manifest_sha256=$runtimeSha;mode=$Mode;logical_cpus=$cpus;output=$out;status='PREPARED_ONLY_NOT_EXECUTED'}|ConvertTo-Json
