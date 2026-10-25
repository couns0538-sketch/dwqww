# Pure-PGO build, correctness measurements and descriptive native timing.
# Native CTest is unverified because original tests conflict with kill-nothing.
# Native Windows, dedicated PowerShell 7 only.
# The reviewed Job 1 handoff must be closed before executing this separate job.
# One shared 3GiB/CPUs0-3/Idle job; 43-minute admission and 45-minute total budget.
[CmdletBinding()]
param(
    [string]$Source = (Join-Path $PSScriptRoot 'forge_sol_lock_source_20261025'),
    [string]$Recipe = (Join-Path $PSScriptRoot 'forge_sol_lock_pc_recipe_20261025.ps1'),
    [string]$Out = (Join-Path $PSScriptRoot ('forge_sol_pgo_run_20261025_' + [DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss'))),
    [string]$Gpp = 'C:\msys64\ucrt64\bin\g++.exe',
    [string]$Python = 'C:\Python314\python.exe',
    [string]$CMake = 'C:\msys64\ucrt64\bin\cmake.exe',
    [string]$Objdump = 'C:\msys64\ucrt64\bin\objdump.exe',
    [ValidateRange(8,16)][int]$Blocks = 8
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$clock = [Diagnostics.Stopwatch]::StartNew()
$beganUnix = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$controls = $null
$log = $null
$status = 'UNVERIFIED'
$invariant = [Globalization.CultureInfo]::InvariantCulture
$saved = @{}
$identity = @{}
$nodes = @{11=[long]308972;13=[long]745494;16=[long]2460422;20=[long]11901452;22=[long]31111774}
$script:ownRoot = [IO.Path]::GetFullPath($PSScriptRoot)

function Log([string]$Text) { $script:log.WriteLine($Text); $script:log.Flush(); Write-Host $Text }
function Resolve-OwnOutput([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { throw 'BAD_OUT: output path is empty' }
    $root = [IO.Path]::GetFullPath($script:ownRoot)
    $full = if ([IO.Path]::IsPathRooted($Path)) { [IO.Path]::GetFullPath($Path) } else { [IO.Path]::GetFullPath((Join-Path $root $Path)) }
    $prefix = $root.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    $comparison = if ([Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([Runtime.InteropServices.OSPlatform]::Windows)) { [StringComparison]::OrdinalIgnoreCase } else { [StringComparison]::Ordinal }
    if (-not $full.StartsWith($prefix,$comparison)) { throw 'BAD_OUT: output escapes the script own folder' }
    $rootItem = Get-Item -LiteralPath $root -Force -ErrorAction Stop
    if (-not $rootItem.PSIsContainer) { throw 'BAD_OUT: own root must be a directory' }
    # Inspect every existing ancestor, including the own root and its parents.
    # No directory or result file is created before this completes.
    $cursor = $full
    while ($null -ne $cursor) {
        $item = $null
        try { $item = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop } catch [Management.Automation.ItemNotFoundException] { }
        if ($null -ne $item) {
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'BAD_OUT: reparse point in output ancestry' }
            if (-not $item.PSIsContainer) { throw 'BAD_OUT: output ancestor is not a directory' }
        }
        $parent = [IO.Directory]::GetParent($cursor)
        $cursor = if ($null -eq $parent) { $null } else { $parent.FullName }
    }
    return $full
}
function Initialize-Result([string]$Path) {
    $folder = Resolve-OwnOutput $Path
    if (Test-Path -LiteralPath $folder) { throw 'BAD_OUT: output must be new; refusing evidence overwrite' }
    [void][IO.Directory]::CreateDirectory($folder)
    $null = Resolve-OwnOutput $folder
    $resultPath = Join-Path $folder 'forge_sol_pgo_results_20261025.txt'
    $stream = [IO.FileStream]::new($resultPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $script:log = [IO.StreamWriter]::new($stream,[Text.UTF8Encoding]::new($false))
    $script:runFolder = $folder
    $script:buildFolder = Join-Path $folder 'build'
}
function Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Median([double[]]$Values) {
    $a = @($Values | Sort-Object); $i = [int][Math]::Floor($a.Count/2)
    if ($a.Count % 2) { return $a[$i] }
    return ($a[$i-1]+$a[$i])/2.0
}
function Format([double]$Value) { $Value.ToString('0.000000',$script:invariant) }
function Admit {
    if ($script:clock.Elapsed.TotalSeconds -ge 2580) { throw 'INCOMPLETE_TIME_BUDGET: no new work after 43 minutes' }
}
function Run([string]$Exe,[string[]]$Arguments,[string[]]$InputLines,[string]$Tag,[bool]$Disassembly=$false) {
    Admit
    if (-not $script:identity.ContainsKey($Exe)) { $script:identity[$Exe] = Hash $Exe }
    if ((Hash $Exe) -ne $script:identity[$Exe]) { throw "IDENTITY_CHANGED: $Exe" }
    Log "RUN tag=$Tag exe=$Exe sha256=$($script:identity[$Exe]) arguments=$($Arguments -join ' ')"
    $child = $script:controls.Start($Exe,[string[]]$Arguments,$script:runFolder,$Disassembly)
    if ($InputLines.Count) {
        Log "STDIN tag=$Tag BEGIN"
        foreach ($line in $InputLines) { Log $line }
        Log "STDIN tag=$Tag END"
        $script:controls.Send($child,[string[]]$InputLines)
    } else { $script:controls.CloseInput($child) }
    while (-not $script:controls.Poll($child,100)) {
        if ($script:clock.Elapsed.TotalSeconds -ge 2580) {
            $script:controls.RequestStop($child)
            throw "INCOMPLETE_TIME_BUDGET: graceful stop/quit/EOF requested for owned PID $($child.Pid); no kill"
        }
    }
    $script:controls.CloseInput($child)
    if (-not $script:controls.Drain($child,3000)) { throw "OUTPUT_DRAIN_FAILED: $Tag" }
    Log "STDOUT tag=$Tag total_chars=$($child.Out.Characters) truncated=$($child.Out.Truncated) BEGIN"
    Log $child.Out.Text; Log "STDOUT tag=$Tag END"
    Log "STDERR tag=$Tag total_chars=$($child.Err.Characters) truncated=$($child.Err.Truncated) BEGIN"
    Log $child.Err.Text; Log "STDERR tag=$Tag END"
    Log "EXIT tag=$Tag code=$($child.ExitCode) pid=$($child.Pid)"
    if ($child.ExitCode -ne 0 -or $child.Err.Truncated -or ($child.Out.Truncated -and -not $Disassembly)) { throw "CHILD_FAILED: $Tag" }
    return $child
}
function Setup {
    return @('uci','setoption name Threads value 1','setoption name Hash value 16',
             'setoption name OwnBook value false','setoption name UseNNUE value true',
             'setoption name NnueInt16 value false','setoption name SingTtPv value false',
             'setoption name RefutLmr value false','isready')
}
function Bench([string]$Exe,[int[]]$Depths,[string]$Tag) {
    $commands = @(Setup) + @($Depths | ForEach-Object { "bench $_" }) + @('quit')
    $child = Run $Exe @() $commands $Tag
    if ($child.Err.Characters -ne 0) { throw "BENCH_STDERR: $Tag" }
    $rows = [regex]::Matches($child.Out.Text,'(?m)^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)\r?$')
    $starts = [regex]::Matches($child.Out.Text,'(?m)^info string bench depth ')
    if ($rows.Count -ne $Depths.Count -or $starts.Count -ne $Depths.Count) { throw "BAD_BENCH_ROWS: $Tag" }
    $answer = @()
    for ($i=0; $i -lt $Depths.Count; $i++) {
        $m = $rows[$i]; $d = $Depths[$i]
        if ([int]$m.Groups[1].Value -ne $d -or [long]$m.Groups[2].Value -ne $script:nodes[$d] -or [long]$m.Groups[4].Value -le 0) { throw "BAD_NODES: $Tag depth=$d" }
        $answer += [double]$m.Groups[4].Value
        Log "BENCH PASS tag=$Tag depth=$d nodes=$($m.Groups[2].Value) time_ms=$($m.Groups[3].Value) nps=$($m.Groups[4].Value)"
    }
    return $answer
}
function Worker([string]$Phase) {
    $arguments = @($script:worker,'--platform','pc-msys2','--phase',$Phase,'--source',$script:sourceFolder,
                   '--out',$script:buildFolder,'--recipe',$script:recipeFile,'--cxx',$Gpp,'--cmake',$CMake)
    $null = Run $Python $arguments @() "worker-$Phase"
}
function Load([string]$Tag) {
    Admit
    # Read-only load sample; availability is reported rather than guessed.
    try {
        $samples = @(Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop | ForEach-Object {
            if ($null -eq $_.LoadPercentage) { throw 'CPU load sample is unavailable' }
            $value = [double]$_.LoadPercentage
            if (-not [double]::IsFinite($value) -or $value -lt 0 -or $value -gt 100) { throw 'Invalid CPU load sample' }
            $value
        })
        if ($samples.Count -eq 0) { throw 'CPU load sample is empty' }
        Log "LOAD tag=$Tag machine_cpu_load_percent=$($samples -join ',') allowed_cpu_indices=0,1,2,3 priority=Idle"
    } catch { throw "LOAD_UNVERIFIED tag=$Tag error=$($_.Exception.Message); no native speed verdict" }
}
function Assert-Disassembly($Capture,[string]$Label) {
    if (-not $Capture.PeX64 -or $Capture.ParseError -or $Capture.UnknownFma -ne 0) { throw "BAD_DISASSEMBLY: $Label format/parser/unattributed FMA" }
    if ($Capture.DefinedNnueFunctions.Count -eq 0) { throw "BAD_DISASSEMBLY: $Label no defined NNUE functions in COFF inventory" }
    $apis = @{refresh=0;update=0;evaluate=0}
    foreach ($symbol in $Capture.DefinedNnueFunctions) {
        if (-not $Capture.Symbols.ContainsKey($symbol) -or $Capture.Symbols[$symbol].Instructions -le 0) { throw "BAD_DISASSEMBLY: $Label defined NNUE body missing: $symbol" }
        foreach ($api in @('refresh','update','evaluate')) {
            if ($symbol.StartsWith("forge::nnue::$api(",[StringComparison]::Ordinal)) { $apis[$api]++ }
        }
    }
    foreach ($api in @('refresh','update','evaluate')) { if ($apis[$api] -eq 0) { throw "BAD_DISASSEMBLY: $Label defined/parsed NNUE API missing: $api" } }
    $found=0; $nnueFma=[long]0; $externalFma=[long]0
    foreach ($entry in $Capture.Symbols.GetEnumerator()) {
        $symbol=$entry.Key; $stats=$entry.Value
        if ($symbol.Contains('forge::nnue::')) {
            if ($stats.Instructions -le 0 -or $stats.AllFma -ne 0) { throw "NNUE_FMA_FAIL: $Label empty/fused NNUE symbol: $symbol" }
            $found++; $nnueFma += $stats.AllFma
            Log "NNUE_SYMBOL build=$Label instructions=$($stats.Instructions) all_fma=$($stats.AllFma) symbol=$symbol"
        } elseif ($stats.AllFma -gt 0) { $externalFma += $stats.AllFma }
    }
    if ($found -eq 0 -or $nnueFma -ne 0) { throw "NNUE_FMA_FAIL: $Label no parsed NNUE functions or fused arithmetic" }
    Log "FMA PASS build=$Label defined_NNUE_functions=$($Capture.DefinedNnueFunctions.Count) parsed_NNUE_symbols=$found refresh=$($apis.refresh) update=$($apis.update) evaluate=$($apis.evaluate) all_nnue_fma=$nnueFma external_runtime_all_fma=$externalFma scope=emitted_named_functions_no_LTO"
}

try {
    Initialize-Result $Out
    Log 'STATUS RUNNING_PREFLIGHT native_measurements=UNVERIFIED'
    foreach ($name in @('TEMP','TMP','TMPDIR','PATH','PYTHONDONTWRITEBYTECODE','FORGE_PGO_REVIEWED_ENVELOPE','FORGE_PGO_ADMISSION_DEADLINE_UNIX','PSModuleAnalysisCachePath','DOTNET_BUNDLE_EXTRACT_BASE_DIR')) {
        $saved[$name] = [Environment]::GetEnvironmentVariable($name,'Process')
    }
    $env:PSModuleAnalysisCachePath = Join-Path $script:runFolder 'forge_sol_pgo_psmodule_cache_20261025.bin'
    $env:DOTNET_BUNDLE_EXTRACT_BASE_DIR = $script:runFolder
    if ($PSVersionTable.PSVersion.Major -lt 7 -or -not $IsWindows -or -not [Environment]::Is64BitProcess) { throw 'Native 64-bit Windows PowerShell 7 required' }
    $script:sourceFolder = (Resolve-Path -LiteralPath $Source).Path
    $script:recipeFile = (Resolve-Path -LiteralPath $Recipe).Path
    $script:worker = Join-Path $PSScriptRoot 'forge_sol_pgo_worker_20261025.py'
    $native = Join-Path $PSScriptRoot 'forge_sol_pgo_native_resource_20261025.cs'
    foreach ($file in @($Gpp,$Python,$Objdump,$script:worker,$native,$script:recipeFile)) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Required file missing: $file" }
    }
    if ((Hash $script:recipeFile) -ne 'a5c88c838ff91b778501d913de38dc1286e1958268b78810b0483cea5306bd23') { throw 'RECOVERED_RECIPE_HASH_MISMATCH' }
    [void](New-Item -ItemType Directory -Path (Join-Path $script:runFolder 'tmp'))
    foreach ($name in @('TEMP','TMP','TMPDIR')) { [Environment]::SetEnvironmentVariable($name,(Join-Path $script:runFolder 'tmp'),'Process') }
    $env:PATH = (Split-Path -Parent $Gpp) + ';' + (Split-Path -Parent $CMake) + ';' + $env:PATH
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:FORGE_PGO_REVIEWED_ENVELOPE = 'ACTIVE'
    $env:FORGE_PGO_ADMISSION_DEADLINE_UNIX = ($beganUnix+2580).ToString($invariant)
    Add-Type -TypeDefinition ([IO.File]::ReadAllText($native)) -Language CSharp
    if ([ForgeSolWinqual20261025.Session]::IsWine -or (Test-Path 'HKCU:\Software\Wine') -or (Test-Path 'HKLM:\SOFTWARE\Wine')) { throw 'Wine is not native Windows evidence' }
    $cpu = Get-ItemProperty -LiteralPath 'HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor\0'
    Log "CPU name=$($cpu.ProcessorNameString.Trim()) identifier=$($cpu.Identifier) vendor=$($cpu.VendorIdentifier)"
    if ($cpu.VendorIdentifier -ne 'AuthenticAMD' -or $cpu.Identifier -notmatch '\bFamily 26\b') { throw 'ZEN5_REQUIRED: AuthenticAMD family 0x1A (26) required; native verdict unavailable' }
    $script:controls = [ForgeSolWinqual20261025.Session]::new()
    Log 'RESOURCE CPUs=0,1,2,3 affinity=0xF priority=Idle total_job_private_commit_limit=3221225472 admission_seconds=2580 total_budget_seconds=2700 no_kill=true no_GPU=true'
    Log "MACHINE name=$env:COMPUTERNAME OS=$([Environment]::OSVersion.VersionString) processor=$env:PROCESSOR_IDENTIFIER"
    Log "HELPERS worker_sha256=$(Hash $script:worker) native_resource_sha256=$(Hash $native) recipe_sha256=$(Hash $script:recipeFile)"
    Worker 'baseline'
    $baseline = Join-Path $script:buildFolder 'bin\forge_sol_pgo_baseline_20261025.exe'
    # Validate each response before starting the next engine test. In
    # particular a bench11 mismatch admits no later depth or training work.
    foreach ($depth in @(11,13,16,20,22)) { $null = Bench $baseline @($depth) "baseline-lock-gate-$depth" }
    Worker 'generate'
    # Declared training is instrumented bench11, bench16 and six awaited FENs.
    # The worker freezes that dataset before any extra instrumented validation.
    Worker 'train'
    $instrumented = Join-Path $script:buildFolder 'bin\forge_sol_pgo_instrumented_20261025.exe'
    foreach ($depth in @(11,13,16,20,22)) { $null = Bench $instrumented @($depth) "instrumented-post-freeze-gate-$depth" }
    Worker 'use'
    $pgo = Join-Path $script:buildFolder 'bin\forge_sol_pgo_final_20261025.exe'
    foreach ($depth in @(11,13,16,20,22)) { $null = Bench $pgo @($depth) "pgo-lock-gate-$depth" }
    foreach ($entry in @(@('startpos','position startpos',[long]4865609),
                         @('kiwipete','position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',[long]193690690))) {
        $child = Run $pgo @() (@(Setup)+@($entry[1],'go perft 5','quit')) "perft-$($entry[0])"
        $matches = [regex]::Matches($child.Out.Text,'(?m)^nodes (\d+)\r?$')
        if ($child.Err.Characters -ne 0 -or $matches.Count -ne 1 -or [long]$matches[0].Groups[1].Value -ne $entry[2]) { throw "PERFT_FAIL: $($entry[0])" }
        Log "PERFT PASS position=$($entry[0]) depth=5 nodes=$($entry[2])"
    }
    $dis = Run $Objdump @('-d','-t','-C','--no-show-raw-insn',$pgo) @() 'pgo-disassembly' $true
    if ($dis.Err.Characters -ne 0) { throw 'DISASSEMBLY_STDERR' }
    Assert-Disassembly $dis.Out 'pgo'
    Log 'NATIVE_CTEST UNVERIFIED_NOT_RUN_KILL_NOTHING_CONTRACT reason=unchanged_uci_regression.py_may_process.kill_on_timeout original_tests_unchanged=true full_release_acceptance=UNVERIFIED'
    Load 'before-timing'
    $null = Bench $baseline @(20) 'baseline-warmup'
    $null = Bench $pgo @(20) 'pgo-warmup'
    $blockRatios = @(); $adjacentRatios = @()
    for ($i=1; $i -le $Blocks; $i++) {
        # Exactly ABAB; two adjacent A/B pairs and ONE four-launch block.
        $a1 = @(Bench $baseline @(20) "block-$i-A1")[0]
        $b1 = @(Bench $pgo @(20) "block-$i-B1")[0]
        $a2 = @(Bench $baseline @(20) "block-$i-A2")[0]
        $b2 = @(Bench $pgo @(20) "block-$i-B2")[0]
        $ratio = [Math]::Sqrt(($b1/$a1)*($b2/$a2))
        $blockRatios += $ratio; $adjacentRatios += ($b1/$a1); $adjacentRatios += ($b2/$a2)
        Log "ABAB block=$i A1_nps=$(Format $a1) B1_nps=$(Format $b1) A2_nps=$(Format $a2) B2_nps=$(Format $b2) block_geometric_ratio=$(Format $ratio) adjacent_1=$(Format ($b1/$a1)) adjacent_2=$(Format ($b2/$a2))"
    }
    Load 'after-timing'
    $median = Median $adjacentRatios
    $verdict = if ($median -ge 1.03) { 'DESCRIPTIVE_GE_3_PERCENT_RELEASE_UNVERIFIED' } else { 'DROP_BELOW_3_PERCENT' }
    Log "SUMMARY completed_ABAB_blocks=$Blocks timed_launches=$($Blocks*4) adjacent_AB_pairs=$($Blocks*2) median_block_geometric_ratio=$(Format (Median $blockRatios)) median_adjacent_ratio=$(Format $median) block_ratios=$($blockRatios.ForEach({Format $_}) -join ',') adjacent_ratios=$($adjacentRatios.ForEach({Format $_}) -join ',') comparison_statistic=median_adjacent_ratio threshold=1.03 verdict=$verdict full_release_acceptance=UNVERIFIED native_ctest=UNVERIFIED_NOT_RUN_KILL_NOTHING_CONTRACT Elo=UNPROVEN"
    $status = 'DONE_' + $verdict
} catch {
    $status = 'UNVERIFIED'
    $problem = $_.Exception.Message
    try { if ($null -ne $script:log) { Log "STOP UNVERIFIED $problem" } else { Write-Host "STOP UNVERIFIED $problem" } } catch {
        $status='UNVERIFIED_REPORT_ERROR'; Write-Host "STOP UNVERIFIED report unavailable; $problem"
    }
} finally {
    try {
        if ($null -ne $script:controls) {
            foreach ($child in $script:controls.Children) {
                try { $script:controls.RequestStop($child) } catch {
                    $status='UNVERIFIED_CLEANUP_ERROR'
                    Log "CLEANUP_REQUEST_ERROR pid=$($child.Pid) error=$($_.Exception.Message)"
                }
            }
            $living = @($script:controls.LivingPids())
            while ($living.Count -gt 0 -and $clock.Elapsed.TotalSeconds -lt 2700) {
                foreach ($child in $script:controls.Children) { [void]$script:controls.Poll($child,100) }
                [Threading.Thread]::Sleep(100)
                $living = @($script:controls.LivingPids())
            }
            foreach ($child in $script:controls.Children) {
                if ($child.Exited) { [void]$script:controls.Drain($child,100) }
                if (-not $child.Resumed -or -not $child.Exited -or -not $child.DrainComplete -or $null -ne $child.ControlError) {
                    Log "POST_CLEANUP_STDIN pid=$($child.Pid) sent=$($child.CommandsSent -join ' | ')"
                    Log "POST_CLEANUP_STDOUT_TAIL pid=$($child.Pid) BEGIN"; Log $child.Out.Tail; Log "POST_CLEANUP_STDOUT_TAIL END"
                    Log "POST_CLEANUP_STDERR_TAIL pid=$($child.Pid) BEGIN"; Log $child.Err.Tail; Log "POST_CLEANUP_STDERR_TAIL END"
                }
            }
            if ($living.Count -gt 0 -or $clock.Elapsed.TotalSeconds -ge 2700) { $status='UNVERIFIED_RESOURCE_OR_TIME_INCOMPLETE' }
            if ($null -ne $script:log) { Log "RESOURCE_RESULT peak_job_private_commit_bytes=$($script:controls.PeakCommittedBytes) remaining_child_pids=$($living -join ',') seconds=$(Format $clock.Elapsed.TotalSeconds) no_kill=true" }
        }
    } catch {
        $status='UNVERIFIED_CLEANUP_ERROR'
        try { Log "CLEANUP_ERROR $($_.Exception.Message) remaining_child_pids=UNKNOWN no_termination_attempted=true" } catch { Write-Host 'CLEANUP_ERROR report unavailable' }
    } finally {
        if ($null -ne $script:controls) {
            try { $script:controls.Dispose() } catch { $status='UNVERIFIED_CLEANUP_ERROR'; Write-Host "DISPOSE_ERROR $($_.Exception.Message)" }
        }
        try { foreach ($name in $saved.Keys) { [Environment]::SetEnvironmentVariable($name,$saved[$name],'Process') } } catch {
            $status='UNVERIFIED_ENVIRONMENT_RESTORE_ERROR'; Write-Host $_.Exception.Message
        }
        if ($clock.Elapsed.TotalSeconds -ge 2700 -and $status -like 'DONE_*') { $status='UNVERIFIED_TIME_INCOMPLETE' }
        if ($null -ne $script:log) {
            try { Log "STATUS $status"; $script:log.Dispose() } catch { $status='UNVERIFIED_REPORT_ERROR'; Write-Host "STATUS $status" }
        }
    }
}
if ($status -notlike 'DONE_*') { exit 1 }
