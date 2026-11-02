#requires -Version 5.1
# IDEA_SOURCE: crew D-only / spare-core policy; .NET process pipes and Windows CRT argv rules.
# Policy preflight for a reviewed job, not an OS sandbox or arbitrary native thread limiter.
[CmdletBinding()]
param([string]$Manifest, [string[]]$ProtectedRoots = @(), [string[]]$ReadOnlyRuntimeRoots = @())

# R10 policy: kept in this branch-local skill; never changes installed settings.
$script:R10WorkspaceCache = $null

function Get-DPathLexical([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path) -or $Path -notmatch '^[dD]:[\\/]' -or $Path -match '[*?]' -or $Path.IndexOf([char]0) -ge 0) { throw 'Absolute D: path required, without wildcard or NUL' }
    if (@($Path -split '[\\/]' | Where-Object {$_ -eq '.' -or $_ -eq '..'}).Count -ne 0) { throw 'Dot path components are refused before normalization' }
    if ($Path.Substring(2).Contains(':')) { throw 'D: root and alternate data streams are not allowed' }
    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    if ($full -notmatch '^[dD]:\\' -or $full.Substring(2).Contains(':')) { throw 'D: root and alternate data streams are not allowed' }
    return $full
}
function Get-ProtectedRootLexical([string]$Root) {
    if ([string]::IsNullOrWhiteSpace($Root) -or $Root -notmatch '^[a-zA-Z]:[\\/]' -or $Root -match '[*?]' -or $Root.IndexOf([char]0) -ge 0 -or $Root.Substring(2).Contains(':') -or @($Root -split '[\\/]' | Where-Object {$_ -eq '.' -or $_ -eq '..'}).Count -ne 0) { throw 'Protected roots must be explicit absolute drive paths without wildcard, stream or dot components' }
    return [IO.Path]::GetFullPath($Root).TrimEnd('\')
}
function Assert-NoReparsePath([string]$Full) {
    $parent = $Full
    while ($parent) {
        if (Test-Path -LiteralPath $parent) {
            if ((Get-Item -LiteralPath $parent -Force -ErrorAction Stop).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse points are not approved D: paths' }
        }
        $parent = [IO.Path]::GetDirectoryName($parent)
    }
}
function Assert-DPath([string]$Path, [string[]]$ProtectedRoots = @()) {
    $full = Get-DPathLexical $Path
    # Lexical checks precede filesystem inspection; queue.txt and queue_state.json are never opened.
    if ($full -match '(?i)(?:^|\\)(?:npt|nnue-pytorch|gate|gates|gate-queue|gate_queue)(?:\\|$)' -or [IO.Path]::GetFileName($full) -match '(?i)^(?:queue(?:_state)?\.(?:txt|json)|STOP(?:\..*)?|PAUSE(?:\..*)?)$') { throw 'Protected production path' }
    foreach ($root in $ProtectedRoots) {
        # Protected roots are lexical exclusions and may name any drive. Never
        # inspect these roots (especially forbidden F:) or relax D-only job I/O.
        $blocked = Get-ProtectedRootLexical $root
        if ($full.Equals($blocked,[StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith($blocked+'\',[StringComparison]::OrdinalIgnoreCase) -or $blocked.StartsWith($full+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Protected production root or its ancestor' }
    }
    Assert-NoReparsePath $full
    return $full
}
function Assert-ReadOnlyRuntimeRoots([string[]]$Roots, [string[]]$ProtectedRoots) {
    # Couns explicitly authorized reads of this external CPU runtime. This is
    # not a general production-root override, and never applies to a write role.
    if ($Roots.Count -gt 1) { throw 'Only the exact authorized NPT runtime may be opted in' }
    $protected = @($ProtectedRoots | ForEach-Object { Get-ProtectedRootLexical $_ })
    foreach ($root in $Roots) {
        $full = Get-DPathLexical $root
        if (-not $full.Equals('D:\grok-pc-data\npt\nnue-pytorch-amd',[StringComparison]::OrdinalIgnoreCase)) { throw 'Read-only runtime root is not explicitly authorized' }
        if ('D:\grok-pc-data\npt' -notin $protected) { throw 'The complete protected NPT root must remain declared' }
        Assert-NoReparsePath $full
    }
}
function Assert-ReadPath([string]$Path, [string[]]$ProtectedRoots, [string[]]$ReadOnlyRuntimeRoots = @()) {
    Assert-ReadOnlyRuntimeRoots $ReadOnlyRuntimeRoots $ProtectedRoots
    if ($ReadOnlyRuntimeRoots.Count -eq 0) { return (Assert-DPath $Path $ProtectedRoots) }
    $full = Get-DPathLexical $Path
    $runtime = 'D:\grok-pc-data\npt\nnue-pytorch-amd'
    if (-not ($full.Equals($runtime,[StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith($runtime+'\',[StringComparison]::OrdinalIgnoreCase))) {
        return (Assert-DPath $Path $ProtectedRoots)
    }
    $relative = $full.Substring($runtime.Length).TrimStart('\')
    if ($relative -match '(?i)(?:^|\\)(?:npt|nnue-pytorch|gate|gates|gate-queue|gate_queue|locks)(?:\\|$)' -or
        [IO.Path]::GetFileName($full) -match '(?i)^(?:queue(?:_state)?(?:\.[^\\]+)?|forge_queue(?:_state)?(?:\.[^\\]+)?|forge_gates\.json|CURRENT_LOCK\.json|STOP(?:\..*)?|PAUSE(?:\..*)?)$') { throw 'Production queue/lock/control path remains protected' }
    foreach ($root in $ProtectedRoots) {
        $blocked = Get-ProtectedRootLexical $root
        # Only this exact enclosing protected root gets a read-role exception.
        # Any extra protected ancestor or nested protected root still wins.
        if ($blocked.Equals('D:\grok-pc-data\npt',[StringComparison]::OrdinalIgnoreCase)) { continue }
        if ($full.Equals($blocked,[StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith($blocked+'\',[StringComparison]::OrdinalIgnoreCase) -or $blocked.StartsWith($full+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Protected production root or its ancestor' }
    }
    Assert-NoReparsePath $full
    return $full
}
function Quote-SafeArgument([AllowEmptyString()][string]$Value) {
    if ($Value.IndexOf([char]0) -ge 0) { throw 'NUL in argument' }
    $quoted = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $quoted = [regex]::Replace($quoted, '(\\+)$', '$1$1')
    return '"' + $quoted + '"'
}
function Assert-R10WritePath([string]$Path, [string[]]$ProtectedRoots) {
    $full = Assert-DPath $Path $ProtectedRoots
    if (-not ($full.Equals('D:\a10',[StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith('D:\a10\',[StringComparison]::OrdinalIgnoreCase))) { throw 'R10 write root must be D:\a10' }
    return $full
}
function Get-R10WorkspaceBytes([string]$Root = 'D:\a10') {
    $full = Assert-R10WritePath $Root @()
    [long]$bytes = 0
    $pending = New-Object 'System.Collections.Generic.Stack[System.IO.DirectoryInfo]'
    $pending.Push([IO.DirectoryInfo]::new($full))
    while ($pending.Count -gt 0) {
        $directory = $pending.Pop()
        if ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse point in R10 workspace' }
        foreach ($entry in $directory.EnumerateFileSystemInfos()) {
            if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse point in R10 workspace' }
            if ($entry -is [IO.DirectoryInfo]) { $pending.Push($entry) }
            else { $bytes += $entry.Length }
        }
    }
    return $bytes
}
function Assert-R10StorageBudget([long]$CFreeBytes, [long]$DFreeBytes, [long]$WorkspaceBytes, [long]$RequiredBytes, [long]$MinimumMiB) {
    if ($MinimumMiB -lt 51200 -or $RequiredBytes -lt 0 -or $WorkspaceBytes -lt 0) { throw 'Disk floor is at least 51200 MiB; byte budgets must be nonnegative' }
    if ($CFreeBytes -lt 30GB) { throw 'C: free-space floor is 30 GiB' }
    [decimal]$need = [decimal]$MinimumMiB * 1048576 + $RequiredBytes
    if ([decimal]$DFreeBytes -lt $need) { throw 'Insufficient D: space for the job budget plus reserve' }
    if ([decimal]$WorkspaceBytes + $RequiredBytes -gt 15000000000) { throw 'R10 workspace exceeds 15 GB cap including next reservation' }
}
function Assert-SafeDisk([long]$MinimumMiB, [long]$RequiredBytes, [switch]$FreshWorkspace) {
    # Inspect disk floors each second but enumerate the workspace only at bounded
    # job boundaries or once per minute. Native adapters must honor required_bytes.
    if ($MinimumMiB -lt 51200 -or $RequiredBytes -lt 0) { throw 'Disk floor is at least 51200 MiB; required bytes must be nonnegative' }
    $now = [DateTime]::UtcNow
    if ($FreshWorkspace -or $null -eq $script:R10WorkspaceCache -or ($now - $script:R10WorkspaceCache.utc).TotalSeconds -ge 60 -or $now -lt $script:R10WorkspaceCache.utc) {
        $script:R10WorkspaceCache = @{bytes=(Get-R10WorkspaceBytes);utc=$now}
    }
    Assert-R10StorageBudget -CFreeBytes ([IO.DriveInfo]::new('C:\').AvailableFreeSpace) -DFreeBytes ([IO.DriveInfo]::new('D:\').AvailableFreeSpace) -WorkspaceBytes $script:R10WorkspaceCache.bytes -RequiredBytes $RequiredBytes -MinimumMiB $MinimumMiB
}
function Test-SafeJob([object]$j, [string[]]$ProtectedRoots, [string[]]$ReadOnlyRuntimeRoots = @()) {
    Assert-ReadOnlyRuntimeRoots $ReadOnlyRuntimeRoots $ProtectedRoots
    $fields = @('schema','executable','executable_sha256','arguments','working_directory','output_directory','read_paths','write_paths','logical_cpus','worker_threads','minimum_free_mib','required_bytes')
    if ($null -eq $j -or @($j.PSObject.Properties.Name).Count -ne $fields.Count) { throw 'Unexpected or missing manifest fields' }
    foreach ($name in $fields) { if ($null -eq $j.PSObject.Properties[$name]) { throw "Missing manifest field: $name" } }
    if (($j.schema -isnot [int] -and $j.schema -isnot [long]) -or $j.schema -ne 1) { throw 'Manifest schema must be integer 1' }
    if (($j.worker_threads -isnot [int] -and $j.worker_threads -isnot [long]) -or $j.worker_threads -lt 1 -or $j.worker_threads -gt 2) { throw 'worker_threads must be 1 or 2; T4 needs a separate authorized host' }
    if (($j.minimum_free_mib -isnot [int] -and $j.minimum_free_mib -isnot [long]) -or $j.minimum_free_mib -lt 51200) { throw 'minimum_free_mib must be integer >=51200' }
    if (($j.required_bytes -isnot [int] -and $j.required_bytes -isnot [long]) -or $j.required_bytes -lt 0) { throw 'required_bytes must be a nonnegative integer' }
    if ($j.logical_cpus -isnot [array] -or $j.logical_cpus.Count -lt 1) { throw 'Explicit logical_cpus array required' }
    $cpus = @($j.logical_cpus | Select-Object -Unique)
    if ($cpus.Count -ne $j.logical_cpus.Count -or $cpus.Count -gt 2) { throw 'Select one or two unique spare logical CPUs' }
    [int64]$mask = 0
    [int64]$available = [Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity.ToInt64()
    foreach ($cpu in $cpus) {
        if (($cpu -isnot [int] -and $cpu -isnot [long]) -or $cpu -lt 0 -or $cpu -ge 63) { throw 'CPU must be integer 0..62 in one processor group' }
        [int64]$bit = [int64]1 -shl $cpu
        if (($available -band $bit) -eq 0) { throw 'Requested CPU is unavailable to the launcher' }
        $mask = $mask -bor $bit
    }
    if ($j.arguments -isnot [array] -or $j.arguments.Count -lt 1) { throw 'Explicit argument vector required' }
    $threadBindings = 0
    for ($i=0; $i -lt $j.arguments.Count; $i++) {
        $arg = $j.arguments[$i]
        if ($arg -isnot [string] -or $arg.IndexOf([char]0) -ge 0) { throw 'Arguments must be NUL-free strings' }
        $pathArgument = $null; $responseFile = $false
        if ($arg.StartsWith('@')) {
            $responseFile=$true; $pathArgument=$arg.Substring(1)
        } elseif ($arg -match '^[^=]+=(?<path>[a-zA-Z]:.*)$') {
            $pathArgument=$Matches.path
        } elseif ($arg -match '^[a-zA-Z]:') {
            $pathArgument=$arg
        } elseif ($arg.Contains('..') -or $arg -match '[\\/]') {
            throw 'Relative path-like argument refused; use a declared absolute D: path'
        }
        if ($null -ne $pathArgument) {
            $checkedPath = Assert-DPath $pathArgument $ProtectedRoots
            $declared = $false
            foreach ($path in @($j.read_paths)) {
                $allowed = Assert-ReadPath $path $ProtectedRoots $ReadOnlyRuntimeRoots
                if ($checkedPath.Equals($allowed,[StringComparison]::OrdinalIgnoreCase) -or $checkedPath.StartsWith($allowed+'\',[StringComparison]::OrdinalIgnoreCase)) {$declared=$true}
            }
            foreach ($path in @($j.write_paths)) {
                $allowed = Assert-R10WritePath $path $ProtectedRoots
                if ($checkedPath.Equals($allowed,[StringComparison]::OrdinalIgnoreCase) -or $checkedPath.StartsWith($allowed+'\',[StringComparison]::OrdinalIgnoreCase)) {$declared=$true}
            }
            if (-not $declared) {throw 'Argument path is not within declared read_paths/write_paths'}
            if ($responseFile -and ($checkedPath -notin @($j.read_paths | ForEach-Object {[IO.Path]::GetFullPath($_).TrimEnd('\')}) -or -not (Test-Path -LiteralPath $checkedPath -PathType Leaf))) {throw 'Response file requires an explicitly declared existing read path and prior content review'}
        }
        if ($arg -match '(?i)(?:queue(?:_state)?\.(?:txt|json)|(?:^|[\\/])(?:npt|nnue-pytorch|gate|gates)(?:[\\/]|$))') { throw 'Production argument refused' }
        if ($arg -match '^(?:--threads|--jobs|--parallel|-j)$') {
            $i++; if ($i -ge $j.arguments.Count -or $j.arguments[$i] -cne [string]$j.worker_threads) { throw 'Thread argument must match worker_threads' }; $threadBindings++
        } elseif ($arg -match '^(?:(?:--threads|--jobs|--parallel)=|-j)(\d+)$') {
            if ([int]$Matches[1] -ne $j.worker_threads) { throw 'Thread argument must match worker_threads' }; $threadBindings++
        } elseif ($arg -match '(?i)(?:threads\s*(?:=|value)|^/MP)') { throw 'Use one explicit supported thread argument or reviewed adapter' }
    }
    if ($threadBindings -ne 1) { throw 'Exactly one explicit thread argument (--threads/--jobs/--parallel/-j) is required' }
    foreach ($name in @('read_paths','write_paths')) { if ($j.$name -isnot [array] -or $j.$name.Count -lt 1) { throw "Nonempty $name array required" } }
    $exe = Assert-DPath $j.executable $ProtectedRoots
    $cwd = Assert-R10WritePath $j.working_directory $ProtectedRoots
    $out = Assert-R10WritePath $j.output_directory $ProtectedRoots
    foreach ($path in $j.read_paths) { $null = Assert-ReadPath $path $ProtectedRoots $ReadOnlyRuntimeRoots }
    foreach ($path in $j.write_paths) { $null = Assert-R10WritePath $path $ProtectedRoots }
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf) -or -not (Test-Path -LiteralPath $cwd -PathType Container)) { throw 'Executable and working directory must already exist on D:' }
    foreach ($path in $j.read_paths) { if (-not (Test-Path -LiteralPath $path)) { throw 'Declared input is missing' } }
    if ($exe -notin @($j.read_paths | ForEach-Object {[IO.Path]::GetFullPath($_).TrimEnd('\')})) { throw 'Executable must be a declared read path' }
    if ($out -notin @($j.write_paths | ForEach-Object {[IO.Path]::GetFullPath($_).TrimEnd('\')})) { throw 'output_directory must be a declared write path' }
    if (Test-Path -LiteralPath $out) { throw 'output_directory must be NEW; evidence is never overwritten' }
    if ($j.executable_sha256 -notmatch '^[0-9a-fA-F]{64}$' -or (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash -ine $j.executable_sha256) { throw 'Executable SHA256 mismatch' }
    Assert-SafeDisk $j.minimum_free_mib $j.required_bytes -FreshWorkspace
    return [pscustomobject]@{Mask=$mask;Exe=$exe;Cwd=$cwd;Out=$out}
}
function Invoke-GrokPcSafeJob([string]$Manifest, [string[]]$ProtectedRoots, [string[]]$ReadOnlyRuntimeRoots = @()) {
    if ($env:OS -ne 'Windows_NT') { throw 'Windows runtime required' }
    if ($ProtectedRoots.Count -lt 1) { throw 'Supply the complete production ProtectedRoots before reading the manifest' }
    $manifestPath = Assert-DPath $Manifest $ProtectedRoots
    # ReadOnly manifest: review the complete command and I/O declarations before invoking.
    $raw = Get-Content -LiteralPath $manifestPath -Raw -ErrorAction Stop
    $keys = @([regex]::Matches($raw, '(?<!\\)"(?<key>[^"\\]*)"\s*:') | ForEach-Object {$_.Groups['key'].Value})
    if ($keys.Count -ne @($keys | Select-Object -Unique).Count) { throw 'Duplicate manifest fields refused' }
    $j = $raw | ConvertFrom-Json -ErrorAction Stop
    if ($keys.Count -ne @($j.PSObject.Properties.Name).Count) { throw 'Manifest requires plain top-level property names only' }
    $checked = Test-SafeJob $j $ProtectedRoots $ReadOnlyRuntimeRoots
    $self = [Diagnostics.Process]::GetCurrentProcess()
    $oldAffinity=$self.ProcessorAffinity; $oldPriority=$self.PriorityClass
    $envNames=@('TEMP','TMP','TMPDIR','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')
    $saved=@{}; foreach ($name in $envNames) { $saved[$name]=[Environment]::GetEnvironmentVariable($name,'Process') }
    $resultCode=70; $nativeCode=$null; $captureErrors=@(); $diskBreach=$false
    $null=New-Item -ItemType Directory -Path $checked.Out -ErrorAction Stop
    $temp=Join-Path $checked.Out 'temp'; $null=New-Item -ItemType Directory -Path $temp -ErrorAction Stop
    if ($ReadOnlyRuntimeRoots.Count -gt 0) {
        [ordered]@{read_only_runtime_roots=@($ReadOnlyRuntimeRoots);declared_read_paths=@($j.read_paths);write_exception=$false;scope='explicit external CPU runtime reads only; full protected roots retained'} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $checked.Out 'readonly-runtime-policy.json') -Encoding UTF8
    }
    try {
        $self.ProcessorAffinity=[IntPtr]$checked.Mask
        $self.PriorityClass = [Diagnostics.ProcessPriorityClass]::Idle
        $self.Refresh()
        if ($self.PriorityClass -ne 'Idle' -or $self.ProcessorAffinity.ToInt64() -ne $checked.Mask) { throw 'Scheduling verification failed' }
        foreach ($name in @('TEMP','TMP','TMPDIR')) { [Environment]::SetEnvironmentVariable($name,$temp,'Process') }
        foreach ($name in @('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')) { [Environment]::SetEnvironmentVariable($name,[string]$j.worker_threads,'Process') }
        if (-not ('ForgeCrewSafeDrain' -as [type])) {
            Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Threading.Tasks;
public static class ForgeCrewSafeDrain {
  public static async Task<string> CopyAsync(Stream source, Stream destination) {
    byte[] buffer=new byte[81920]; string failure=null; int count;
    while ((count=await source.ReadAsync(buffer,0,buffer.Length).ConfigureAwait(false))!=0) {
      if (failure == null) {
        try { await destination.WriteAsync(buffer,0,count).ConfigureAwait(false); }
        catch(Exception error) { failure=error.ToString(); }
      }
    }
    if (failure==null) { try { await destination.FlushAsync().ConfigureAwait(false); } catch(Exception error) { failure=error.ToString(); } }
    return failure;
  }
}
'@
        }
        [IO.File]::WriteAllText((Join-Path $checked.Out 'manifest.json'),$raw)
        $info=New-Object Diagnostics.ProcessStartInfo
        $info.FileName=$checked.Exe; $info.Arguments=($j.arguments | ForEach-Object {Quote-SafeArgument $_}) -join ' '
        $info.WorkingDirectory=$checked.Cwd; $info.UseShellExecute=$false; $info.CreateNoWindow=$true
        $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
        $child=New-Object Diagnostics.Process; $child.StartInfo=$info
        $stdout=$null; $stderr=$null
        try {
            $stdout=[IO.File]::Open((Join-Path $checked.Out 'stdout.log'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
            $stderr=[IO.File]::Open((Join-Path $checked.Out 'stderr.log'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
            if ((Get-FileHash -Algorithm SHA256 -LiteralPath $checked.Exe).Hash -ine $j.executable_sha256) { throw 'Executable changed before launch' }
            if (-not $child.Start()) { throw 'Owned child failed to start' }
            $outTask=[ForgeCrewSafeDrain]::CopyAsync($child.StandardOutput.BaseStream,$stdout)
            $errTask=[ForgeCrewSafeDrain]::CopyAsync($child.StandardError.BaseStream,$stderr)
            while (-not $child.WaitForExit(1000)) {
                if (-not $diskBreach) {
                    try { Assert-SafeDisk $j.minimum_free_mib 0 }
                    catch { $diskBreach=$true; [Console]::Error.WriteLine('D: floor breached; no new work should start; child is not terminated') }
                }
            }
            $nativeCode=$child.ExitCode; $global:LASTEXITCODE=$nativeCode
            foreach ($task in @($outTask,$errTask)) { $failure=$task.GetAwaiter().GetResult(); if ($failure) { $captureErrors+=$failure } }
        } finally {
            foreach ($stream in @($stdout,$stderr)) { if ($null -ne $stream) { try {$stream.Dispose()} catch {$captureErrors+=$_.Exception.Message} } }
            $child.Dispose()
        }
        try { Assert-SafeDisk $j.minimum_free_mib 0 -FreshWorkspace } catch { $diskBreach=$true }
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $checked.Exe).Hash -ine $j.executable_sha256) { $captureErrors+='Executable changed during run' }
        $receipt=[ordered]@{native_exit_code=$nativeCode;capture_errors=@($captureErrors);disk_floor_breached=$diskBreach;affinity=$checked.Mask;priority='Idle';worker_threads=$j.worker_threads;manifest_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $checked.Out 'manifest.json')).Hash;finished_utc=[DateTime]::UtcNow.ToString('o')}
        if ($ReadOnlyRuntimeRoots.Count -gt 0) { $receipt['read_only_runtime_roots']=@($ReadOnlyRuntimeRoots); $receipt['write_exception']=$false }
        $receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $checked.Out 'result.json') -Encoding UTF8
        if ($captureErrors.Count -eq 0 -and -not $diskBreach) { $resultCode=$nativeCode }
    } finally {
        try {$self.ProcessorAffinity=$oldAffinity} finally {
            try {$self.PriorityClass=$oldPriority} finally {foreach($name in $envNames){[Environment]::SetEnvironmentVariable($name,$saved[$name],'Process')}}
        }
    }
    return $resultCode
}
if ($MyInvocation.InvocationName -ne '.') {
    $ErrorActionPreference='Stop'
    try { if (-not $Manifest) { throw 'Manifest is required' }; $code=Invoke-GrokPcSafeJob $Manifest $ProtectedRoots $ReadOnlyRuntimeRoots; exit $code }
    catch { [Console]::Error.WriteLine('REFUSED/FAILED: '+$_.Exception.Message); exit 76 }
}
