# IDEA_SOURCE: user spare-core/Idle constraint; Windows Process scheduling APIs.
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
    $Receipt = [ordered]@{
        started_utc = [DateTime]::UtcNow.ToString('o')
        python = (Resolve-Path -LiteralPath $Python).Path
        script = (Resolve-Path -LiteralPath $Script).Path
        script_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Script).Hash
        argv = $ScriptArguments
        requested_cpus = $CpuList
        verified_parent_affinity = $Self.ProcessorAffinity.ToInt64()
        verified_parent_priority = [string]$Self.PriorityClass
        note = 'Only owned workload; no external processes changed. Single processor group.'
    }
    $Receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $LogDirectory 'command.json') -Encoding UTF8
    & $Python $Script @ScriptArguments *> (Join-Path $LogDirectory 'console.log')
    $ExitCode = $LASTEXITCODE
    [ordered]@{exit_code=$ExitCode;finished_utc=[DateTime]::UtcNow.ToString('o')} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $LogDirectory 'exit.json') -Encoding UTF8
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
if ($ExitCode -ne 0) { throw "Data job failed with exit code $ExitCode; evidence is in $LogDirectory" }
