$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]8
$env:TEMP='D:\a10\tmp';$env:TMP=$env:TEMP
$protected=@('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
. 'D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1' -ProtectedRoots $protected
$base='C:\Users\Administrator\grok-pc\nnue\pythons\cpython-3.10.22-windows-x86_64-none'
$packages='C:\Users\Administrator\grok-pc\nnue\.venv\Lib\site-packages'
$out='D:\a10\job3\runtime'
if(Test-Path -LiteralPath $out){throw 'Fresh runtime destination required'}
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
$manifest=@()
foreach($file in $files){
    if($file.FullName.StartsWith($base+'\')){$destination=Join-Path (Join-Path $out 'python') $file.FullName.Substring($base.Length+1)}else{$destination=Join-Path $target $file.FullName.Substring($packages.Length+1)}
    $before=(Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
    $after=(Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash
    if($before -ne $after){throw 'Runtime copy mismatch'}
    $manifest+=@{source=$file.FullName;copy=$destination;bytes=$file.Length;sha256=$after.ToLowerInvariant()}
}
@{classification='UNPROVEN';scope='External CPU execution dependencies only; no external trainer source vendored into Forge. CPU torch2.4.1+cpu; DirectML and torchvision excluded.';bytes=$bytes;files=$manifest} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'RUNTIME_INPUTS.json') -Encoding UTF8
Assert-SafeDisk -MinimumMiB 51200 -RequiredBytes 0 -FreshWorkspace
"Runtime bytes=$bytes files=$($files.Count)"
