# Prepare exact command/bindings, review them, then use -Action Run.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('fixtures','assemble','preflight','suite')][string]$Mode,
      [Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9-]+$')][string]$Tag,
      [ValidateSet('Prepare','Run')][string]$Action='Prepare')
$ErrorActionPreference='Stop'
$repo='D:\a11\wt';$runtime='D:\a11\runtime';$here="$repo\astra_r11\runtime"
$helper="$repo\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1"
$jobRoot='D:\a11\runtime-runs'
$r11Protected=@('D:\a10','D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
$r11Runtime=@();$r11Toolchain=@()
if($Mode -in @('preflight','suite')){
    $r11Runtime=@('D:\grok-pc-data\npt\nnue-pytorch-amd')
    $r11Toolchain=@('C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.51.36231','C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0','C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0')
}
function Owned-Path([string]$Path) {
    if([string]::IsNullOrWhiteSpace($Path) -or $Path -notmatch '^[dD]:[\\/]' -or $Path -match '[*?]' -or $Path.IndexOf([char]0) -ge 0 -or $Path.Substring(2).Contains(':')){throw 'Explicit owned D:a11 path required'}
    if(@($Path -split '[\\/]'|Where-Object{$_ -in @('.','..') -or $_ -match '[. ]$'}).Count){throw 'Windows path aliases refused before inspection'}
    $full=[IO.Path]::GetFullPath($Path).TrimEnd('\')
    if(-not $full.StartsWith('D:\a11\',[StringComparison]::OrdinalIgnoreCase) -or $full -match '(?i)\.nnue$' -or [IO.Path]::GetFileName($full) -match '(?i)^(forge_queue_state\.json|STOP(?:\..*)?|PAUSE(?:\..*)?)$'){throw 'Forbidden/outside owned path'}
    $pending=[Collections.Generic.Stack[string]]::new();$parent=$full
    while($parent){$pending.Push($parent);$parent=[IO.Path]::GetDirectoryName($parent)}
    while($pending.Count){
        $component=$pending.Pop()
        try{$entry=Get-Item -LiteralPath $component -Force -ErrorAction Stop}catch [Management.Automation.ItemNotFoundException]{break}
        if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Owned path reparse refused before descendant inspection'}
    }
    return $full
}
function Hash([string]$Path){(Get-FileHash -LiteralPath (Owned-Path $Path) -Algorithm SHA256).Hash.ToLowerInvariant()}
function Checked-Input([string]$Path) {
    return (Owned-Path $Path)
}
function Candidate-Snapshot {
    $paths=@();$pending=[Collections.Generic.Stack[string]]::new();$pending.Push($here)
    if($Mode -eq 'fixtures'){$pending.Push("$repo\astra_r11\gameprov")}
    while($pending.Count){
        $directory=Checked-Input $pending.Pop()
        foreach($entry in Get-ChildItem -LiteralPath $directory -Force){
            $checked=Checked-Input $entry.FullName
            if($entry.PSIsContainer){$pending.Push($checked)}else{$paths+=$checked}
        }
    }
    $paths+=@($helper,"$runtime\BOOTSTRAP.json")
    if($Mode -ne 'fixtures'){$paths+=@("$runtime\WHEEL_LOCK.json","$runtime\CHESS_SOURCE.json")}
    if($Mode -in @('preflight','suite')){$paths+="$runtime\RUNTIME_FILES.json"}
    $rows=@()
    foreach($path in @($paths|Sort-Object -Unique)){
        $checked=Checked-Input $path
        $rows+=[ordered]@{path=$checked;bytes=(Get-Item -LiteralPath $checked).Length;sha256=(Hash $checked)}
    }
    $sourceCopy=Get-Content -Raw -LiteralPath (Checked-Input "$here\regression\SOURCE_COPY.json")|ConvertFrom-Json
    foreach($item in $sourceCopy.final_files){
        $checked=Checked-Input $item.path
        if((Hash $checked) -ine $item.sha256){throw 'Pinned copied regression source differs'}
        if($checked -notin $rows.path){throw 'Copied regression input escaped complete candidate tree'}
    }
    return [ordered]@{schema=1;files=$rows;scope='complete R11 runtime script/fixture tree, source-copy manifests, launcher helper and bootstrap/wheel/chess/runtime manifests'}
}
function Assert-Candidate([object]$Expected) {
    $actual=Candidate-Snapshot
    if(($actual|ConvertTo-Json -Compress -Depth 8) -cne ($Expected|ConvertTo-Json -Compress -Depth 8)) {throw 'Complete reviewed runtime candidate changed'}
}
function New-Json([string]$Path,[object]$Value){
    $Path=Owned-Path $Path
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 10)+"`n")
    $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
$jobRoot=Owned-Path $jobRoot
$manifest=Owned-Path "$jobRoot\$Tag.manifest.json";$binding=Owned-Path "$jobRoot\$Tag.binding.json"
. (Checked-Input "$here\verify_bootstrap.ps1")
if($Action -eq 'Prepare'){
    if(Test-Path -LiteralPath $manifest){throw 'Fresh preparation tag required'}
    if([IO.DriveInfo]::new('C:\').AvailableFreeSpace -lt 30GB -or [IO.DriveInfo]::new('D:\').AvailableFreeSpace -lt 50GB){throw 'Storage floor'}
    [IO.Directory]::CreateDirectory((Owned-Path $jobRoot))|Out-Null
    $exe="$runtime\python\python.exe";$reads=@($exe,$runtime,$here);$writes=@("$jobRoot\$Tag-launch")
    if($Mode -eq 'fixtures'){
        $runner="$here\run_fixtures.py";$threads=1;$cpus=@(3);$reservation=268435456L
        $out="D:\a11\fixture-runs\$Tag"
        $argv=@('-I','-B',$runner,'--threads','1','--out',$out)
        $reads+="$repo\astra_r11\gameprov";$writes+=$out
    }elseif($Mode -eq 'assemble'){
        $runner="$here\assemble_runtime.py";$threads=1;$cpus=@(3);$reservation=2500000000L
        $argv=@('-I','-B',$runner,'--threads','1','--lock-sha256',(Hash "$runtime\WHEEL_LOCK.json"))
        $writes+=@("$runtime\packages","$runtime\RUNTIME_FILES.json")
    }else{
        $runner="$here\regression\run_regression.py";$threads=2;$cpus=@(2,3);$reservation=536870912L
        $out="D:\a11\regression-runs\$Tag"
        $argv=@('-B',$runner,'--threads','2','--out',$out,'--runtime-manifest-sha256',(Hash "$runtime\RUNTIME_FILES.json"))
        if($Mode -eq 'preflight'){$argv+='--preflight-only'}
        $reads+=$r11Runtime;$reads+=$r11Toolchain;$writes+=$out
    }
    $job=[ordered]@{schema=1;executable=$exe;executable_sha256=(Hash $exe);arguments=$argv;working_directory='D:\a11';output_directory="$jobRoot\$Tag-launch";read_paths=$reads;write_paths=$writes;logical_cpus=$cpus;worker_threads=$threads;minimum_free_mib=51200;required_bytes=$reservation}
    $bootstrap=Get-BootstrapSnapshot
    New-Json $manifest $job
    New-Json $binding ([ordered]@{mode=$Mode;manifest_sha256=(Hash $manifest);runner=$runner;runner_sha256=(Hash $runner);helper_sha256=(Hash $helper);admission_sha256=(Hash "$here\lane_admission.ps1");candidate=(Candidate-Snapshot);bootstrap=$bootstrap;status='PREPARED_NOT_RUN';classification='UNPROVEN'})
    Write-Output $manifest;return
}
$bound=Get-Content -Raw -LiteralPath (Owned-Path $binding)|ConvertFrom-Json
if($bound.mode -ne $Mode -or (Hash $manifest) -ne $bound.manifest_sha256 -or (Hash $bound.runner) -ne $bound.runner_sha256 -or (Hash $helper) -ne $bound.helper_sha256 -or (Hash "$here\lane_admission.ps1") -ne $bound.admission_sha256){throw 'Reviewed command/runner/helper/admission binding changed'}
Assert-Candidate $bound.candidate
Assert-BootstrapSnapshot $bound.bootstrap
. (Checked-Input "$here\lane_admission.ps1")
$admission=Get-R11LaneAdmission
$stamp=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ')
$admissionPath=Owned-Path "$jobRoot\$Tag-admission-$stamp.json"
New-Json $admissionPath $admission
if($admission.status -ne 'ADMITTED'){throw 'R11 CPU2/3 lane unavailable; no child launched; receipt retained'}
$pythonNames=@(Get-ChildItem Env:|Where-Object Name -like 'PYTHON*'|ForEach-Object Name)
$cleanNames=@($pythonNames+@('PYTHONHOME','PYTHONPATH','PYTHONNOUSERSITE','PYTHONDONTWRITEBYTECODE','PYTEST_ADDOPTS','PYTEST_PLUGINS','PYTEST_DISABLE_PLUGIN_AUTOLOAD','CUDA_VISIBLE_DEVICES','HIP_VISIBLE_DEVICES','ROCR_VISIBLE_DEVICES')|Sort-Object -Unique)
$saved=@{};foreach($name in $cleanNames){$saved[$name]=[Environment]::GetEnvironmentVariable($name,'Process')}
try {
    foreach($name in $pythonNames){[Environment]::SetEnvironmentVariable($name,$null,'Process')}
    foreach($name in @('PYTHONHOME','PYTEST_ADDOPTS','PYTEST_PLUGINS')){[Environment]::SetEnvironmentVariable($name,$null,'Process')}
    $env:PYTHONNOUSERSITE='1';$env:PYTHONDONTWRITEBYTECODE='1';$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
    $env:PYTHONPATH="$here\regression"
    foreach($name in @('CUDA_VISIBLE_DEVICES','HIP_VISIBLE_DEVICES','ROCR_VISIBLE_DEVICES')){[Environment]::SetEnvironmentVariable($name,'','Process')}
    Assert-Candidate $bound.candidate
    try {& $helper -Manifest $manifest -ProtectedRoots $r11Protected -ReadOnlyRuntimeRoots $r11Runtime -ReadOnlyToolchainRoots $r11Toolchain}
    finally {Assert-Candidate $bound.candidate;Assert-BootstrapSnapshot $bound.bootstrap}
    if($LASTEXITCODE -ne 0){throw "Native launcher returned $LASTEXITCODE"}
} finally {foreach($name in $cleanNames){[Environment]::SetEnvironmentVariable($name,$saved[$name],'Process')}}
