# IDEA_SOURCE: user spare-core/Idle constraint; Windows Process scheduling APIs.
# IDEA_SOURCE: item 7A review; .NET Process stream capture / Windows CRT quoting,
# also used by tools/bullet/run_hip_smoke.ps1 in the Astra bullet-export branch.
# Runtime qualification on grok-pc is still required. No external process is touched.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$Script,
    [Parameter(Mandatory=$true)][int[]]$CpuList,
    [Parameter(Mandatory=$true)][string]$LogDirectory,
    [string[]]$ScriptArguments = @()
)
$ErrorActionPreference = 'Stop'
function ConvertTo-IdleNativeArgument([AllowEmptyString()][string]$Value) {
    if ($Value.IndexOf([char]0) -ge 0) { throw 'Native arguments cannot contain NUL.' }
    # Quote every argument, including empty strings; escape quotes and trailing
    # backslashes according to Windows CRT argv parsing. No shell is involved.
    $Quoted = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $Quoted = [regex]::Replace($Quoted, '(\\+)$', '$1$1')
    return '"' + $Quoted + '"'
}
if ($env:OS -ne 'Windows_NT') { throw 'This launcher requires Windows.' }
if (!(Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Missing Python: $Python" }
if (!(Test-Path -LiteralPath $Script -PathType Leaf)) { throw "Missing script: $Script" }
if (Test-Path -LiteralPath $LogDirectory) { throw "Use a NEW log directory: $LogDirectory" }
if ($CpuList.Count -eq 0) { throw 'Explicit spare logical CPUs are required.' }
$Self = [Diagnostics.Process]::GetCurrentProcess()
$OldAffinity = $Self.ProcessorAffinity
$OldPriority = $Self.PriorityClass
$OldThreadEnvironment = @{}
foreach ($Name in @('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')) {
    $OldThreadEnvironment[$Name] = [Environment]::GetEnvironmentVariable($Name, 'Process')
}
[int64]$Mask = 0
foreach ($Cpu in ($CpuList | Select-Object -Unique)) {
    # This tool deliberately supports a single Windows processor group only.
    if ($Cpu -lt 0 -or $Cpu -ge 63) { throw "CPU index outside supported single-group range: $Cpu" }
    [int64]$Bit = [int64]1 -shl $Cpu
    if (($OldAffinity.ToInt64() -band $Bit) -eq 0) { throw "CPU $Cpu is unavailable to this process." }
    $Mask = $Mask -bor $Bit
}
$null = New-Item -ItemType Directory -Path $LogDirectory
$LogDirectory = (Resolve-Path -LiteralPath $LogDirectory).Path
$ExitCode = 1
$CaptureErrors = @()
try {
    # Set the parent BEFORE creating Python; children inherit this affinity.
    # Idle parents create Idle children; native Forge clients explicitly request Idle too.
    $Self.ProcessorAffinity = [IntPtr]$Mask
    $Self.PriorityClass = [Diagnostics.ProcessPriorityClass]::Idle
    $Self.Refresh()
    if ($Self.ProcessorAffinity.ToInt64() -ne $Mask -or $Self.PriorityClass -ne 'Idle') {
        throw 'Requested scheduling could not be verified; no workload started.'
    }
    $env:OMP_NUM_THREADS = '1'
    $env:MKL_NUM_THREADS = '1'
    $env:OPENBLAS_NUM_THREADS = '1'
    if (-not ('ForgeIdlePipeCapture' -as [type])) {
        # C#5/.NET 4.5 compatible; no PowerShell callback runs on a worker thread.
        # A failed disk sink must not stop draining a verbose child's pipe.
        Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Threading.Tasks;
public static class ForgeIdlePipeCapture {
    public static async Task<string> DrainAsync(Stream source, Stream destination) {
        byte[] buffer = new byte[81920];
        string captureError = null;
        int count;
        while ((count = await source.ReadAsync(buffer, 0, buffer.Length).ConfigureAwait(false)) != 0) {
            if (captureError == null) {
                try { await destination.WriteAsync(buffer, 0, count).ConfigureAwait(false); }
                catch (Exception error) { captureError = error.ToString(); }
            }
            // After a sink failure, discard bytes until EOF so the child can exit.
        }
        if (captureError == null) {
            try { await destination.FlushAsync().ConfigureAwait(false); }
            catch (Exception error) { captureError = error.ToString(); }
        }
        return captureError;
    }
}
'@
    }
    $Receipt = [ordered]@{
        started_utc = [DateTime]::UtcNow.ToString('o')
        python = (Resolve-Path -LiteralPath $Python).Path
        script = (Resolve-Path -LiteralPath $Script).Path
        script_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Script).Hash
        argv = $ScriptArguments
        requested_cpus = $CpuList
        verified_parent_affinity = $Self.ProcessorAffinity.ToInt64()
        verified_parent_priority = [string]$Self.PriorityClass
        stdout_log = 'stdout.log'
        stderr_log = 'stderr.log'
        console_log_layout = 'stdout followed by stderr after exit; no inter-stream ordering claim'
        note = 'Only owned workload; no external processes changed. Single processor group.'
    }
    $Receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $LogDirectory 'command.json') -Encoding UTF8
    $StartInfo = New-Object Diagnostics.ProcessStartInfo
    $StartInfo.FileName = $Receipt.python
    $StartInfo.Arguments = ((@($Receipt.script) + $ScriptArguments | ForEach-Object { ConvertTo-IdleNativeArgument $_ }) -join ' ')
    $StartInfo.WorkingDirectory = $ExecutionContext.SessionState.Path.CurrentFileSystemLocation.Path
    $StartInfo.UseShellExecute = $false
    $StartInfo.CreateNoWindow = $true
    $StartInfo.RedirectStandardOutput = $true
    $StartInfo.RedirectStandardError = $true
    $Child = New-Object Diagnostics.Process
    $Child.StartInfo = $StartInfo
    $Stdout = $null
    $Stderr = $null
    $Console = $null
    try {
        # Claim logs before starting the owned child. Both pipes drain at once,
        # without PS5.1 converting normal native stderr into NativeCommandError.
        $Stdout = [IO.File]::Open((Join-Path $LogDirectory 'stdout.log'), [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::Read)
        $Stderr = [IO.File]::Open((Join-Path $LogDirectory 'stderr.log'), [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::Read)
        $Console = [IO.File]::Open((Join-Path $LogDirectory 'console.log'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
        if (-not $Child.Start()) { throw 'Native process failed to start.' }
        $StdoutCopy = [ForgeIdlePipeCapture]::DrainAsync($Child.StandardOutput.BaseStream, $Stdout)
        $StderrCopy = [ForgeIdlePipeCapture]::DrainAsync($Child.StandardError.BaseStream, $Stderr)
        $Child.WaitForExit()
        $ExitCode = $Child.ExitCode
        $global:LASTEXITCODE = $ExitCode
        $StdoutError = $StdoutCopy.GetAwaiter().GetResult()
        $StderrError = $StderrCopy.GetAwaiter().GetResult()
        if ($StdoutError) { $CaptureErrors += 'stdout: ' + $StdoutError }
        if ($StderrError) { $CaptureErrors += 'stderr: ' + $StderrError }
        # Keep the existing console.log API as a byte-preserving concatenation.
        # The separate logs retain stream identity and can be read during the run.
        try {
            foreach ($Stream in @($Stdout, $Stderr)) {
                $Stream.Position = 0
                $Stream.CopyTo($Console)
            }
            $Console.Flush()
        } catch { $CaptureErrors += 'console.log: ' + $_.Exception.Message }
    } finally {
        foreach ($Stream in @($Stdout, $Stderr, $Console)) {
            if ($null -ne $Stream) {
                try { $Stream.Dispose() }
                catch { $CaptureErrors += 'log close: ' + $_.Exception.Message }
            }
        }
        $Child.Dispose()
    }
    try {
        [ordered]@{exit_code=$ExitCode;capture_errors=@($CaptureErrors);finished_utc=[DateTime]::UtcNow.ToString('o')} |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $LogDirectory 'exit.json') -Encoding UTF8
    } catch {
        # A full disk can also prevent the receipt itself; retain the native
        # exit and capture error in the thrown error as well as LASTEXITCODE.
        throw "Data job exit code $ExitCode; capture errors: $($CaptureErrors -join '; '); exit receipt failed: $($_.Exception.Message)"
    }
} finally {
    try { $Self.ProcessorAffinity = $OldAffinity }
    finally {
        try { $Self.PriorityClass = $OldPriority }
        finally {
            foreach ($Name in $OldThreadEnvironment.Keys) {
                [Environment]::SetEnvironmentVariable($Name, $OldThreadEnvironment[$Name], 'Process')
            }
        }
    }
}
if ($CaptureErrors.Count -ne 0) { throw "Data job capture failed after native exit code $ExitCode; $($CaptureErrors -join '; '); evidence is in $LogDirectory" }
if ($ExitCode -ne 0) { throw "Data job failed with exit code $ExitCode; evidence is in $LogDirectory" }
