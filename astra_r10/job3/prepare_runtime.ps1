$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]8
$env:TEMP='D:\a10\tmp';$env:TMP=$env:TEMP
$protected=@('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
. 'D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1' -ProtectedRoots $protected
$base='C:\Users\Administrator\grok-pc\nnue\pythons\cpython-3.10.22-windows-x86_64-none'
$packages='C:\Users\Administrator\grok-pc\nnue\.venv\Lib\site-packages'
$out='D:\a10\job3\runtime'
if(Test-Path -LiteralPath $out){throw 'Fresh runtime destination required'}
$receiptPath=Join-Path $PSScriptRoot 'RUNTIME_INPUTS.json'
if(Test-Path -LiteralPath $receiptPath){throw 'Preserve existing RUNTIME_INPUTS.json'}
# CR crfix 0e91e02e: shared CPU2-3 lane guard (child inherits Idle + CPU3 affinity; parent pwsh is skipped by the guard).
$python='D:\a10\python\python.exe'
& $python -B -c "import sys;sys.path.insert(0,'D:/a10/wt/astra_r10/job1');import lane_guard;lane_guard.check_lane()"
if($LASTEXITCODE){throw 'CPU2-3 lane guard refused'}
$selected=@(Get-ChildItem -LiteralPath $packages | Where-Object {$_.Name -notmatch '^(torch_directml|torchvision|PIL$|pillow-|__pycache__$)' -and $_.Extension -ne '.whl'})
$files=@(Get-ChildItem -LiteralPath $base -Recurse -File)
foreach($item in $selected){if($item.PSIsContainer){$files+=@(Get-ChildItem -LiteralPath $item.FullName -Recurse -File)}else{$files+=@($item)}}
$links=@(Get-ChildItem -LiteralPath $base -Recurse -Attributes ReparsePoint)
foreach($item in $selected){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse runtime input'};if($item.PSIsContainer){$links+=@(Get-ChildItem -LiteralPath $item.FullName -Recurse -Attributes ReparsePoint)}}
if($links.Count){throw 'Reparse runtime input'}
[long]$bytes=($files|Measure-Object -Property Length -Sum).Sum
Assert-SafeDisk -MinimumMiB 51200 -RequiredBytes ($bytes+10000000) -FreshWorkspace
New-Item -ItemType Directory -Path $out | Out-Null
Copy-Item -LiteralPath $base -Destination (Join-Path $out 'python') -Recurse
$target=Join-Path $out 'packages';New-Item -ItemType Directory -Path $target | Out-Null
foreach($item in $selected){Copy-Item -LiteralPath $item.FullName -Destination $target -Recurse}
$records=New-Object 'System.Collections.Generic.List[object]'  # not $manifest: dot-sourced [string]$Manifest would coerce it
foreach($file in $files){
    if($file.FullName.StartsWith($base+'\')){$destination=Join-Path (Join-Path $out 'python') $file.FullName.Substring($base.Length+1)}else{$destination=Join-Path $target $file.FullName.Substring($packages.Length+1)}
    $before=(Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
    $after=(Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash
    if($before -ne $after){throw 'Runtime copy mismatch'}
    $records.Add([ordered]@{source=$file.FullName;copy=$destination;bytes=$file.Length;sha256=$after.ToLowerInvariant()})
}
if($records.Count -ne $files.Count){throw 'Runtime manifest incomplete'}
$json=[ordered]@{classification='UNPROVEN';scope='External CPU execution dependencies only; no external trainer source vendored into Forge. CPU torch2.4.1+cpu; DirectML and torchvision excluded.';bytes=$bytes;files=$records.ToArray()} | ConvertTo-Json -Depth 5
$check=$json | ConvertFrom-Json
if(@($check.files).Count -ne $files.Count -or @($check.files | Where-Object {$_.sha256 -notmatch '^[0-9a-f]{64}$'}).Count){throw 'Runtime manifest malformed; not written'}
$stream=[IO.File]::Open($receiptPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{$bytesOut=(New-Object Text.UTF8Encoding($false)).GetBytes($json);$stream.Write($bytesOut,0,$bytesOut.Length)}finally{$stream.Dispose()}
Assert-SafeDisk -MinimumMiB 51200 -RequiredBytes 0 -FreshWorkspace
"Runtime bytes=$bytes files=$($files.Count)"
