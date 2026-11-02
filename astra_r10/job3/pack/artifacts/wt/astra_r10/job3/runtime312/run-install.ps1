#requires -Version 5.1
param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Fa-f0-9]{64}$')][string]$WheelLockSHA256)
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]8
$python='D:\a10\python\python.exe'
$lockFile=Join-Path $PSScriptRoot 'WHEEL_LOCK.json'
if((Get-FileHash -LiteralPath $lockFile -Algorithm SHA256).Hash -ne $WheelLockSHA256){throw 'Wheel lock differs'}
$wheelSpec=Get-Content -LiteralPath $lockFile -Raw|ConvertFrom-Json
$reservation=[long]$wheelSpec.expanded_bytes*2+100000000
if($reservation -gt 4000000000){throw 'Measured reservation exceeds reviewed ceiling'}
$file=Join-Path $PSScriptRoot 'install.manifest.json'
$launch=Join-Path $PSScriptRoot 'install-launch'
if((Test-Path -LiteralPath $file) -or (Test-Path -LiteralPath $launch)){throw 'Preserve install attempt'}
$installSpec=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;
 arguments=@('-B',(Join-Path $PSScriptRoot 'install_runtime.py'),'--lock-sha256',$WheelLockSHA256.ToLowerInvariant(),'--threads','1');working_directory='D:\a10';output_directory=$launch;
 read_paths=@($python,'D:\a10');write_paths=@($launch,$PSScriptRoot,'D:\a10\job3\runtime312');
 logical_cpus=@(3);worker_threads=1;minimum_free_mib=51200;required_bytes=$reservation}
$installSpec|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $file -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $file
exit $LASTEXITCODE
