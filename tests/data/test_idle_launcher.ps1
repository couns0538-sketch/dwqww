#requires -Version 5.1
# IDEA_SOURCE: item 7A review; native stderr must remain data under Stop.
# Execute on Windows with an explicitly spare CPU. This is not a Linux/static test.
# Example: & .\tests\data\test_idle_launcher.ps1 -Python $Python -CpuList @($VerifiedSpareCpu)
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][int[]]$CpuList,
    [string]$EvidenceDirectory = (Join-Path ([IO.Path]::GetTempPath()) ('idle-launcher-test-' + [guid]::NewGuid().ToString('N')))
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:OS -ne 'Windows_NT') { throw 'Run this behavioral regression on Windows.' }
if (Test-Path -LiteralPath $EvidenceDirectory) { throw 'Use a NEW evidence directory.' }
$Launcher = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\tools\data\run_idle_spare.ps1')).Path
$Python = (Resolve-Path -LiteralPath $Python).Path
$null = New-Item -ItemType Directory -Path $EvidenceDirectory
$EvidenceDirectory = (Resolve-Path -LiteralPath $EvidenceDirectory).Path
$Fixture = Join-Path $EvidenceDirectory 'native stderr fixture.py'
@'
import ctypes
from ctypes import wintypes
import json
import msvcrt
import os
import sys

kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.GetCurrentProcess.restype = wintypes.HANDLE
kernel.GetPriorityClass.argtypes = [wintypes.HANDLE]
kernel.GetPriorityClass.restype = wintypes.DWORD
kernel.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
kernel.GetProcessAffinityMask.restype = wintypes.BOOL
handle = kernel.GetCurrentProcess()
affinity, system = ctypes.c_size_t(), ctypes.c_size_t()
if not kernel.GetProcessAffinityMask(handle, ctypes.byref(affinity), ctypes.byref(system)):
    raise ctypes.WinError(ctypes.get_last_error())
print(json.dumps({"argv": sys.argv[2:], "priority": kernel.GetPriorityClass(handle),
                  "affinity": affinity.value, "threads": {name: os.environ.get(name) for name in
                  ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")}}), flush=True)
# Each stream exceeds a pipe buffer; sequential reads would deadlock here.
msvcrt.setmode(1, os.O_BINARY)
msvcrt.setmode(2, os.O_BINARY)
os.write(1, b"O" * 131072)
os.write(2, b"normal native stderr\n" + b"E" * 131072)
sys.exit(int(sys.argv[1]))
'@ | Set-Content -LiteralPath $Fixture -Encoding UTF8
$Values = @('', 'space value', 'embedded"quote', 'C:\space end\', 'slashes\\\"quote',
            '$HOME; & | > < `', "tab`tvalue", "line`nvalue", ([string][char]0x03bb))
$Self = [Diagnostics.Process]::GetCurrentProcess()
$OldAffinity = $Self.ProcessorAffinity
$OldPriority = $Self.PriorityClass
$OldThreadEnvironment = @{}
foreach ($Name in @('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')) {
    $OldThreadEnvironment[$Name] = [Environment]::GetEnvironmentVariable($Name, 'Process')
}
[int64]$ExpectedMask = 0
foreach ($Cpu in $CpuList) {
    if ($Cpu -lt 0 -or $Cpu -ge 63) { throw 'Use a supported spare CPU index.' }
    $ExpectedMask = $ExpectedMask -bor ([int64]1 -shl $Cpu)
}
try {
    foreach ($Code in @(0, 17)) {
        $Log = Join-Path $EvidenceDirectory ('exit ' + $Code)
        $Caught = $null
        try {
            & $Launcher -Python $Python -Script $Fixture -CpuList $CpuList `
                -LogDirectory $Log -ScriptArguments (@([string]$Code) + $Values)
        } catch { $Caught = $_ }
        if ($Code -eq 0 -and $null -ne $Caught) { throw "Benign stderr caused failure: $Caught" }
        if ($Code -ne 0 -and ($null -eq $Caught -or $Caught.Exception.Message -notmatch 'exit code 17')) {
            throw 'Nonzero exit did not retain the original failure contract.'
        }
        $ExitReceipt = Get-Content -Raw -LiteralPath (Join-Path $Log 'exit.json') | ConvertFrom-Json
        if ($ExitReceipt.exit_code -ne $Code) { throw 'Original native exit code lost.' }
        if ($LASTEXITCODE -ne $Code) { throw 'LASTEXITCODE does not retain the original native exit.' }
        $Receipt = Get-Content -Raw -LiteralPath (Join-Path $Log 'command.json') | ConvertFrom-Json
        if ($Receipt.script_sha256 -ne (Get-FileHash -Algorithm SHA256 -LiteralPath $Fixture).Hash) { throw 'Script provenance missing.' }
        if ($Receipt.verified_parent_affinity -ne $ExpectedMask -or $Receipt.verified_parent_priority -ne 'Idle') { throw 'Parent scheduling receipt differs.' }
        $Stdout = [IO.File]::ReadAllText((Join-Path $Log 'stdout.log'))
        $Stderr = [IO.File]::ReadAllText((Join-Path $Log 'stderr.log'))
        $Console = [IO.File]::ReadAllText((Join-Path $Log 'console.log'))
        if ($Stderr -cne ("normal native stderr`n" + ('E' * 131072))) { throw 'stderr capture was altered or truncated.' }
        if (-not $Stdout.EndsWith(('O' * 131072))) { throw 'stdout capture was truncated.' }
        if ($Console -cne ($Stdout + $Stderr)) { throw 'Compatibility console log lost output.' }
        $Child = ($Stdout -split "`n", 2)[0] | ConvertFrom-Json
        if ($Child.argv.Count -ne $Values.Count) { throw 'Argument count changed.' }
        for ($Index = 0; $Index -lt $Values.Count; $Index++) {
            if ($Child.argv[$Index] -cne $Values[$Index] -or $Receipt.argv[$Index + 1] -cne $Values[$Index]) { throw "Argument $Index changed." }
        }
        if ($Child.priority -ne 64 -or $Child.affinity -ne $ExpectedMask) { throw 'Child did not inherit Idle and explicit affinity.' }
        foreach ($Name in $OldThreadEnvironment.Keys) {
            if ($Child.threads.$Name -ne '1') { throw 'Child thread cap missing.' }
            if ([Environment]::GetEnvironmentVariable($Name, 'Process') -cne $OldThreadEnvironment[$Name]) { throw 'Parent thread environment was not restored.' }
        }
        $Self.Refresh()
        if ($Self.ProcessorAffinity -ne $OldAffinity -or $Self.PriorityClass -ne $OldPriority) { throw 'Parent scheduling was not restored.' }
        $Before = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Log 'console.log')).Hash
        $Refused = $false
        try {
            & $Launcher -Python $Python -Script $Fixture -CpuList $CpuList -LogDirectory $Log -ScriptArguments @('0')
        } catch { $Refused = $_.Exception.Message -match 'NEW log directory' }
        if (-not $Refused -or (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Log 'console.log')).Hash -ne $Before) { throw 'Existing evidence was not preserved.' }
    }
    # Exercise the exact production drain helper with a test-only failing sink.
    # The real child emits more than a pipe buffer on both streams. A sink fault
    # must not stop reading its pipe or change the child's natural native exit.
    if (-not ('IdleTestFailingSink' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
public sealed class IdleTestFailingSink : MemoryStream {
    public override Task WriteAsync(byte[] buffer, int offset, int count, CancellationToken cancellationToken) {
        throw new IOException("synthetic capture sink failure");
    }
}
'@
    }
    $Self.ProcessorAffinity = [IntPtr]$ExpectedMask
    $Self.PriorityClass = [Diagnostics.ProcessPriorityClass]::Idle
    foreach ($Name in $OldThreadEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($Name, '1', 'Process')
    }
    $FaultResults = @()
    foreach ($FailedStream in @('stdout', 'stderr')) {
        $Start = New-Object Diagnostics.ProcessStartInfo
        $Start.FileName = $Python
        $Start.Arguments = '"' + $Fixture + '" "17"'
        $Start.UseShellExecute = $false
        $Start.CreateNoWindow = $true
        $Start.RedirectStandardOutput = $true
        $Start.RedirectStandardError = $true
        $Process = New-Object Diagnostics.Process
        $Process.StartInfo = $Start
        $OutSink = New-Object IO.MemoryStream
        $ErrSink = New-Object IO.MemoryStream
        if ($FailedStream -eq 'stdout') { $OutSink.Dispose(); $OutSink = New-Object IdleTestFailingSink }
        else { $ErrSink.Dispose(); $ErrSink = New-Object IdleTestFailingSink }
        try {
            if (-not $Process.Start()) { throw 'Fault fixture failed to start.' }
            $OutTask = [ForgeIdlePipeCapture]::DrainAsync($Process.StandardOutput.BaseStream, $OutSink)
            $ErrTask = [ForgeIdlePipeCapture]::DrainAsync($Process.StandardError.BaseStream, $ErrSink)
            $Process.WaitForExit()
            $OutError = $OutTask.GetAwaiter().GetResult()
            $ErrError = $ErrTask.GetAwaiter().GetResult()
            if ($Process.ExitCode -ne 17) { throw 'Capture fault changed the natural native exit.' }
            if ($FailedStream -eq 'stdout') {
                if ($OutError -notmatch 'synthetic capture sink failure' -or $ErrError -or $ErrSink.Length -lt 131072) { throw 'stdout fault stopped draining or damaged stderr.' }
            } else {
                if ($ErrError -notmatch 'synthetic capture sink failure' -or $OutError -or $OutSink.Length -lt 131072) { throw 'stderr fault stopped draining or damaged stdout.' }
            }
            $FaultResults += [ordered]@{failed_stream=$FailedStream;exit_code=$Process.ExitCode;stdout_error=$OutError;stderr_error=$ErrError}
        } finally {
            $OutSink.Dispose()
            $ErrSink.Dispose()
            $Process.Dispose()
        }
    }
    $FaultResults | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $EvidenceDirectory 'capture_faults.json') -Encoding UTF8
    [ordered]@{
        result = 'PASS'
        windows_runtime_verified = $true
        powershell_version = [string]$PSVersionTable.PSVersion
        powershell_edition = $PSVersionTable.PSEdition
        launcher_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Launcher).Hash
        test_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash
        python = $Python
        python_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Python).Hash
        cpu_list = $CpuList
        checked_native_exit_codes = @(0, 17)
        checked_sink_faults = @('stdout', 'stderr')
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $EvidenceDirectory 'result.json') -Encoding UTF8
    "PASS: Windows $($PSVersionTable.PSVersion); stderr under Stop, exits, argv, logs, sink faults, scheduling/restoration. Evidence retained: $EvidenceDirectory"
} finally {
    # Only restore this test process. No fixture, evidence or external process is removed.
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
