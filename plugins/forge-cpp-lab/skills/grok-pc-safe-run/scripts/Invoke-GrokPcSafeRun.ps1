#requires -Version 5.1
# IDEA_SOURCE: crew D-only / spare-core policy; .NET process pipes and Windows CRT argv rules.
# Policy preflight for a reviewed job, not an OS sandbox or arbitrary native thread limiter.
[CmdletBinding()]
param([string]$Manifest, [string[]]$ProtectedRoots = @())

function Assert-DPath([string]$Path, [string[]]$ProtectedRoots = @()) {
    if ([string]::IsNullOrWhiteSpace($Path) -or $Path -notmatch '^[dD]:[\\/]' -or $Path -match '[*?]' -or $Path.IndexOf([char]0) -ge 0) { throw 'Absolute D: path required, without wildcard or NUL' }
    if (@($Path -split '[\\/]' | Where-Object {$_ -eq '.' -or $_ -eq '..'}).Count -ne 0) { throw 'Dot path components are refused before normalization' }
    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    if ($full -notmatch '^[dD]:\\' -or $full.Substring(2).Contains(':')) { throw 'D: root and alternate data streams are not allowed' }
    # Lexical checks precede filesystem inspection; queue.txt and queue_state.json are never opened.
    if ($full -match '(?i)(?:^|\\)(?:npt|nnue-pytorch|gate|gates|gate-queue|gate_queue)(?:\\|$)' -or [IO.Path]::GetFileName($full) -match '(?i)^(?:queue(?:_state)?\.(?:txt|json)|STOP(?:\..*)?|PAUSE(?:\..*)?)$') { throw 'Protected production path' }
    foreach ($root in $ProtectedRoots) {
        if ([string]::IsNullOrWhiteSpace($root) -or $root -notmatch '^[dD]:[\\/]' -or $root -match '[*?]' -or $root.IndexOf([char]0) -ge 0 -or $root.Substring(2).Contains(':') -or @($root -split '[\\/]' | Where-Object {$_ -eq '.' -or $_ -eq '..'}).Count -ne 0) { throw 'Protected roots must be explicit absolute D: paths without wildcard, stream or dot components' }
        $blocked = [IO.Path]::GetFullPath($root).TrimEnd('\')
        if ($full.Equals($blocked,[StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith($blocked+'\',[StringComparison]::OrdinalIgnoreCase) -or $blocked.StartsWith($full+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Protected production root or its ancestor' }
    }
    $parent = $full
    while ($parent) {
        if (Test-Path -LiteralPath $parent) {
            if ((Get-Item -LiteralPath $parent -Force -ErrorAction Stop).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse points are not approved D: paths' }
        }
        $parent = [IO.Path]::GetDirectoryName($parent)
    }
    return $full
}
function Quote-SafeArgument([AllowEmptyString()][string]$Value) {
    if ($Value.IndexOf([char]0) -ge 0) { throw 'NUL in argument' }
    $quoted = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $quoted = [regex]::Replace($quoted, '(\\+)$', '$1$1')
    return '"' + $quoted + '"'
}
function Assert-SafeDisk([long]$MinimumMiB, [long]$RequiredBytes) {
    if ($MinimumMiB -lt 32768 -or $RequiredBytes -lt 0) { throw 'Disk floor is at least 32768 MiB; required bytes must be nonnegative' }
    [decimal]$need = [decimal]$MinimumMiB * 1048576 + $RequiredBytes
    if ([decimal]([IO.DriveInfo]::new('D:\').AvailableFreeSpace) -lt $need) { throw 'Insufficient D: space for the job budget plus reserve' }
}
function Test-SafeJob([object]$j, [string[]]$ProtectedRoots) {
    $fields = @('schema','executable','executable_sha256','arguments','working_directory','output_directory','read_paths','write_paths','logical_cpus','worker_threads','minimum_free_mib','required_bytes')
    if ($null -eq $j -or @($j.PSObject.Properties.Name).Count -ne $fields.Count) { throw 'Unexpected or missing manifest fields' }
    foreach ($name in $fields) { if ($null -eq $j.PSObject.Properties[$name]) { throw "Missing manifest field: $name" } }
    if (($j.schema -isnot [int] -and $j.schema -isnot [long]) -or $j.schema -ne 1) { throw 'Manifest schema must be integer 1' }
    if (($j.worker_threads -isnot [int] -and $j.worker_threads -isnot [long]) -or $j.worker_threads -lt 1 -or $j.worker_threads -gt 2) { throw 'worker_threads must be 1 or 2; T4 needs a separate authorized host' }
    if (($j.minimum_free_mib -isnot [int] -and $j.minimum_free_mib -isnot [long]) -or $j.minimum_free_mib -lt 32768) { throw 'minimum_free_mib must be integer >=32768' }
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
            foreach ($path in @($j.read_paths)+@($j.write_paths)) {
                $allowed = Assert-DPath $path $ProtectedRoots
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
    $cwd = Assert-DPath $j.working_directory $ProtectedRoots
    $out = Assert-DPath $j.output_directory $ProtectedRoots
    foreach ($path in @($j.read_paths)+@($j.write_paths)) { $null = Assert-DPath $path $ProtectedRoots }
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf) -or -not (Test-Path -LiteralPath $cwd -PathType Container)) { throw 'Executable and working directory must already exist on D:' }
    foreach ($path in $j.read_paths) { if (-not (Test-Path -LiteralPath $path)) { throw 'Declared input is missing' } }
    if ($exe -notin @($j.read_paths | ForEach-Object {[IO.Path]::GetFullPath($_).TrimEnd('\')})) { throw 'Executable must be a declared read path' }
    if ($out -notin @($j.write_paths | ForEach-Object {[IO.Path]::GetFullPath($_).TrimEnd('\')})) { throw 'output_directory must be a declared write path' }
    if (Test-Path -LiteralPath $out) { throw 'output_directory must be NEW; evidence is never overwritten' }
    if ($j.executable_sha256 -notmatch '^[0-9a-fA-F]{64}$' -or (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash -ine $j.executable_sha256) { throw 'Executable SHA256 mismatch' }
    Assert-SafeDisk $j.minimum_free_mib $j.required_bytes
    return [pscustomobject]@{Mask=$mask;Exe=$exe;Cwd=$cwd;Out=$out}
}
function Invoke-GrokPcSafeJob([string]$Manifest, [string[]]$ProtectedRoots) {
    if ($env:OS -ne 'Windows_NT') { throw 'Windows runtime required' }
    if ($ProtectedRoots.Count -lt 1) { throw 'Supply the complete production ProtectedRoots before reading the manifest' }
    $manifestPath = Assert-DPath $Manifest $ProtectedRoots
    # ReadOnly manifest: review the complete command and I/O declarations before invoking.
    $raw = Get-Content -LiteralPath $manifestPath -Raw -ErrorAction Stop
    $keys = @([regex]::Matches($raw, '(?<!\\)"(?<key>[^"\\]*)"\s*:') | ForEach-Object {$_.Groups['key'].Value})
    if ($keys.Count -ne @($keys | Select-Object -Unique).Count) { throw 'Duplicate manifest fields refused' }
    $j = $raw | ConvertFrom-Json -ErrorAction Stop
    if ($keys.Count -ne @($j.PSObject.Properties.Name).Count) { throw 'Manifest requires plain top-level property names only' }
    $checked = Test-SafeJob $j $ProtectedRoots
    $self = [Diagnostics.Process]::GetCurrentProcess()
    $oldAffinity=$self.ProcessorAffinity; $oldPriority=$self.PriorityClass
    $envNames=@('TEMP','TMP','TMPDIR','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')
    $saved=@{}; foreach ($name in $envNames) { $saved[$name]=[Environment]::GetEnvironmentVariable($name,'Process') }
    $resultCode=70; $nativeCode=$null; $captureErrors=@(); $diskBreach=$false
    $null=New-Item -ItemType Directory -Path $checked.Out -ErrorAction Stop
    $temp=Join-Path $checked.Out 'temp'; $null=New-Item -ItemType Directory -Path $temp -ErrorAction Stop
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
        try { Assert-SafeDisk $j.minimum_free_mib 0 } catch { $diskBreach=$true }
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $checked.Exe).Hash -ine $j.executable_sha256) { $captureErrors+='Executable changed during run' }
        $receipt=[ordered]@{native_exit_code=$nativeCode;capture_errors=@($captureErrors);disk_floor_breached=$diskBreach;affinity=$checked.Mask;priority='Idle';worker_threads=$j.worker_threads;manifest_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $checked.Out 'manifest.json')).Hash;finished_utc=[DateTime]::UtcNow.ToString('o')}
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
    try { if (-not $Manifest) { throw 'Manifest is required' }; $code=Invoke-GrokPcSafeJob $Manifest $ProtectedRoots; exit $code }
    catch { [Console]::Error.WriteLine('REFUSED/FAILED: '+$_.Exception.Message); exit 76 }
}
