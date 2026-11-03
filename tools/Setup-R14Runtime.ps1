#Requires -Version 7
param(
    [switch]$Fixture,
    [string]$FixtureScript,
    [ValidateRange(0,1000)][int]$FixtureFailGuardAfter=0,
    [ValidateRange(1,600)][int]$ChildTimeoutSeconds=600
)
$ErrorActionPreference='Stop'
$root='D:\a14'
$runtime=Join-Path $root 'runtime'
$downloads=Join-Path $runtime 'downloads'
$pythonRoot=Join-Path $runtime 'python'
$python=Join-Path $pythonRoot 'python.exe'
$utf8=New-Object System.Text.UTF8Encoding($false)
. (Join-Path $root 'tools\R14-OwnedJob.ps1')

function Assert-R14OwnedPath([string]$Value) {
    $full=[IO.Path]::GetFullPath($Value)
    if ($full -ne $root -and -not $full.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside owned root' }
    $walk=$full
    while ($walk) {
        if (Test-Path -LiteralPath $walk) {
            if ((Get-Item -Force -LiteralPath $walk).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Redirected path refused' }
        }
        $walk=[IO.Path]::GetDirectoryName($walk)
    }
    return $full
}

function Get-R14OwnedBytes {
    $pending=[Collections.Generic.Stack[IO.DirectoryInfo]]::new()
    $pending.Push([IO.DirectoryInfo]::new($root))
    [long]$total=0
    while ($pending.Count) {
        foreach ($entry in $pending.Pop().EnumerateFileSystemInfos()) {
            # Count owned files without traversing fixture links or junctions.
            if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
            if ($entry.Attributes -band [IO.FileAttributes]::Directory) { $pending.Push([IO.DirectoryInfo]$entry) }
            else { $total += ([IO.FileInfo]$entry).Length }
            if ($total -ge 5000000000) { return $total }
        }
    }
    return $total
}

function Assert-R14Resources([long]$RequiredBytes=0) {
    if ($RequiredBytes -lt 0) { throw 'Negative allocation' }
    if ((Get-PSDrive D).Free -lt (50GB+$RequiredBytes)) { throw 'D: disk admission refused' }
    if ((Get-PSDrive C).Free -lt 30GB) { throw 'C: disk floor breached' }
    if ((Get-R14OwnedBytes)+$RequiredBytes -ge 5000000000) { throw 'Owned 5 GB cap reached' }
}

$childEnvironment=@{
    TEMP=(Join-Path $root 'tmp'); TMP=(Join-Path $root 'tmp'); TMPDIR=(Join-Path $root 'tmp')
    PYTHONNOUSERSITE='1'; PYTHONDONTWRITEBYTECODE='1'; PYTHONPATH=(Join-Path $root 'tools')
    CUDA_VISIBLE_DEVICES='-1'; HIP_VISIBLE_DEVICES='-1'; ROCR_VISIBLE_DEVICES='-1'
    OMP_NUM_THREADS='1'; OPENBLAS_NUM_THREADS='1'; MKL_NUM_THREADS='1'; NUMEXPR_NUM_THREADS='1'
    PIP_CACHE_DIR=(Join-Path $runtime 'pip-cache'); PIP_CONFIG_FILE='NUL'
    PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
}

function Invoke-R14OwnedProcess([string]$Executable,[string[]]$Arguments) {
    Assert-R14Resources 16MB
    $run=Join-Path $root ('tmp\runtime-setup-'+[Guid]::NewGuid().ToString('N'))
    $null=Assert-R14OwnedPath $run
    New-Item -ItemType Directory -Path $run | Out-Null
    $child=[Diagnostics.Process]::new()
    $child.StartInfo=[Diagnostics.ProcessStartInfo]::new()
    $child.StartInfo.FileName=$Executable
    $child.StartInfo.WorkingDirectory=$root
    $child.StartInfo.UseShellExecute=$false
    $child.StartInfo.CreateNoWindow=$true
    $child.StartInfo.RedirectStandardOutput=$true
    $child.StartInfo.RedirectStandardError=$true
    foreach ($argument in $Arguments) { $child.StartInfo.ArgumentList.Add($argument) }
    foreach ($key in $childEnvironment.Keys) { $child.StartInfo.Environment[$key]=$childEnvironment[$key] }
    $job=Initialize-R14JobChild $child $run $Executable $Arguments
    $stdout=$stderr=$copyOut=$copyErr=$null
    $started=$false
    $polls=0
    try {
        $stdout=[IO.File]::Open((Join-Path $run 'stdout.log'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
        $stderr=[IO.File]::Open((Join-Path $run 'stderr.log'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
        if (-not $child.Start()) { throw 'Owned child creation failed' }
        $started=$true
        $copyOut=$child.StandardOutput.BaseStream.CopyToAsync($stdout)
        $copyErr=$child.StandardError.BaseStream.CopyToAsync($stderr)
        Release-R14JobChild $job $child
        $watch=[Diagnostics.Stopwatch]::StartNew()
        while (-not $child.WaitForExit(500)) {
            Assert-R14Resources
            $polls++
            if ($Fixture -and $FixtureFailGuardAfter -gt 0 -and $polls -ge $FixtureFailGuardAfter) { throw 'Fixture resource refusal' }
            if ($watch.Elapsed.TotalSeconds -ge $ChildTimeoutSeconds) { throw 'Owned child timeout' }
            if ($copyOut.IsFaulted -or $copyErr.IsFaulted) { throw 'Owned child capture failed' }
        }
        Complete-R14JobCapture $job $child @($copyOut,$copyErr) { Assert-R14Resources }
        Assert-R14Resources
        if ($child.ExitCode -ne 0) { throw "Owned child failed: exit $($child.ExitCode); logs $run" }
        Get-Content -LiteralPath (Join-Path $run 'stdout.log')
        Get-Content -LiteralPath (Join-Path $run 'stderr.log')
    } finally {
        # The handle belongs only to the process created above and its children.
        if ($started -and -not $child.HasExited) {
            Stop-R14JobChild $job $child $started
        }
        try { Complete-R14JobCapture $job $child @($copyOut,$copyErr) $null }
        finally {
        if ($stdout) { $stdout.Dispose() }
        if ($stderr) { $stderr.Dispose() }
        $child.Dispose()
        }
    }
}

function Get-R14Download([string]$Uri,[string]$Destination,[string]$ExpectedMD5) {
    $null=Assert-R14OwnedPath $Destination
    if (-not (Test-Path -LiteralPath $Destination)) {
        Assert-R14Resources 32MB
        $helper=Join-Path $root ('tmp\runtime-download-'+[Guid]::NewGuid().ToString('N')+'.ps1')
        [IO.File]::WriteAllText($helper, "param([string]`$Uri,[string]`$Destination)`n`$ErrorActionPreference='Stop'`nInvoke-WebRequest -Uri `$Uri -OutFile `$Destination`n", $utf8)
        Invoke-R14OwnedProcess (Join-Path $PSHOME 'pwsh.exe') @('-NoProfile','-File',$helper,'-Uri',$Uri,'-Destination',$Destination)
    }
    if ((Get-FileHash -Algorithm MD5 -LiteralPath $Destination).Hash.ToLowerInvariant() -ne $ExpectedMD5) { throw 'Runtime download MD5 mismatch' }
    Assert-R14Resources
}

$caller=[Diagnostics.Process]::GetCurrentProcess()
$oldPriority=$caller.PriorityClass
$oldEnvironment=@{}
$oldEnvironmentPresent=@{}
foreach ($key in $childEnvironment.Keys) {
    $oldEnvironmentPresent[$key]=Test-Path -LiteralPath ('Env:'+$key)
    $oldEnvironment[$key]=[Environment]::GetEnvironmentVariable($key,'Process')
}
try {
    $caller.PriorityClass='Idle'
    $null=Assert-R14OwnedPath $root
    if (-not $Fixture -and ($FixtureScript -or $FixtureFailGuardAfter)) { throw 'Fixture options require explicit -Fixture' }
    if ($Fixture) {
        if (-not $FixtureScript) { throw 'Fixture requires an owned Python script' }
        $fixtureFull=Assert-R14OwnedPath $FixtureScript
        if ([IO.Path]::GetExtension($fixtureFull) -ne '.py' -or -not (Test-Path -LiteralPath $fixtureFull -PathType Leaf)) { throw 'Invalid fixture script' }
        Invoke-R14OwnedProcess $python @('-I','-B',$fixtureFull)
    } else {
        Assert-R14Resources 512MB
        foreach ($path in @($downloads,$pythonRoot,(Join-Path $root 'tmp'))) {
            $null=Assert-R14OwnedPath $path
            New-Item -ItemType Directory -Force -Path $path | Out-Null
        }
        $archive=Join-Path $downloads 'python-3.12.10-embed-amd64.zip'
        Get-R14Download 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' $archive 'fe8ef205f2e9c3ba44d0cf9954e1abd3'
        if (-not (Test-Path -LiteralPath $python)) {
            Assert-R14Resources 64MB
            Expand-Archive -LiteralPath $archive -DestinationPath $pythonRoot
        }
        $null=Assert-R14OwnedPath $python
        if ((Get-FileHash -Algorithm MD5 -LiteralPath $python).Hash.ToLowerInvariant() -ne '0cfdf7db1b81d067d3dad75f6abb312b') { throw 'Runtime interpreter MD5 mismatch' }
        $pth=Assert-R14OwnedPath (Join-Path $pythonRoot 'python312._pth')
        [IO.File]::WriteAllText($pth, "python312.zip`n.`nLib\site-packages`nD:\a14\tools`nimport site`n",$utf8)
        $bootstrap=Join-Path $downloads 'get-pip.py'
        Get-R14Download 'https://bootstrap.pypa.io/get-pip.py' $bootstrap '8bae3e432175fb42da9d41cbe68217b0'
        $requirements=Assert-R14OwnedPath (Join-Path $root 'tools\requirements-r14.txt')
        $pins=Get-Content -LiteralPath $requirements
        $buildPins=@($pins | Where-Object { $_ -match '^(pip|setuptools|wheel)==[0-9][0-9.]*$' })
        if ($buildPins.Count -ne 3) { throw 'Pinned build dependencies missing' }
        Assert-R14Resources 128MB
        Invoke-R14OwnedProcess $python (@('-I','-B',$bootstrap,'--no-cache-dir','--disable-pip-version-check')+$buildPins)
        Assert-R14Resources 256MB
        Invoke-R14OwnedProcess $python @('-I','-B','-m','pip','install','--no-build-isolation','--no-cache-dir','--disable-pip-version-check','--no-deps','--requirement',$requirements)
        Invoke-R14OwnedProcess $python @('-I','-B','-m','pip','freeze','--all')
        Get-FileHash -Algorithm MD5 -LiteralPath $python,$archive,$bootstrap,$requirements | ConvertTo-Json
    }
} finally {
    foreach ($key in $oldEnvironment.Keys) {
        if ($oldEnvironmentPresent[$key]) { [Environment]::SetEnvironmentVariable($key,$oldEnvironment[$key],'Process') }
        else { Remove-Item -LiteralPath ('Env:'+$key) -ErrorAction SilentlyContinue }
    }
    $caller.PriorityClass=$oldPriority
}
