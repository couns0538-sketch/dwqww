<#
.SYNOPSIS
  S49 PC speed check that works under gate load: interleaved ABBA bench pairs of two Forge exes on ONE free logical
  core at Idle priority, A/A control pairs for the noise floor, median ratio with a bootstrap 95% CI.

.DESCRIPTION
  PowerShell 7. Read-only except -OutDir (a new or empty directory; the exes are copied into it first).
  Core choice: every core used by a gate is excluded -- cores in the live fastchess processes' affinity (and their
  child engines'), in the 'affinity' field of recent gate RUN_INFO.json files, and in any per-gate affinity/cores
  field of the gate manifest -- and cores 0-3 are never used. With no free core the script REFUSES (exit 3).
  Each slot = one fresh engine process, priority Idle and affinity set before any command is sent, one "bench <d>"
  call; nodes and CPU time are read while the process is still alive. Per slot: whole-machine and chosen-core load,
  CPU temperature, free RAM. Aborts (exit 4) above -MaxTempC (default 90 C) or below -MinFreeRamGB.
  Running it on the PC (not -PlanOnly / -SelfTest) needs a separate crew vote; see README.md.

  Exit codes: 0 done; 2 bad arguments; 3 refused (no free core / unsafe setup); 4 aborted (temperature, RAM, engine
  failure); 5 self-test failure.

.EXAMPLE
  pwsh -NoProfile -File pc_speed_ci_20261027.ps1 -ExeA lock.exe -ExeB cand.exe -Depths 16,20 -Pairs 40 -OutDir F:\opus_scratch\s49\run1
.EXAMPLE
  pwsh -NoProfile -File pc_speed_ci_20261027.ps1 -PlanOnly -OutDir F:\opus_scratch\s49\plan   (prints the core decision only)
#>
[CmdletBinding()]
param(
    [string]$ExeA = '',
    [string]$ExeB = '',
    [string]$Depths = '16,20',
    [int]$Pairs = 40,
    [int]$ControlEvery = 4,
    [string]$OutDir = '',
    [string]$Manifest = 'C:\Users\Administrator\grok-pc\forge_push\autorestart\forge_gates.json',
    [string]$RunInfoRoot = 'D:\grok-pc-data\forge_push',
    [int]$RunInfoMaxAgeHours = 48,
    [string]$ReservedCores = '0,1,2,3',
    [int]$Core = -1,
    [string]$TempCsv = 'C:\Users\Administrator\grok-pc\nnue\tools\hwinfo\gpu_sensors.csv',
    [double]$MaxTempC = 90,
    [int]$TempMaxAgeSec = 120,
    [switch]$AllowNoTemperature,
    [double]$MinFreeRamGB = 6,
    [ValidateSet('cpu', 'wall')][string]$Metric = 'cpu',
    [double]$RuleLowerBound = 1.02,
    [int]$Bootstrap = 10000,
    [int]$Seed = 20261027,
    [int]$TimeoutSec = 900,
    [string]$Label = '',
    [switch]$PlanOnly,
    [switch]$BoxOnly,
    [switch]$SelfTest,
    [string]$FixtureLiveMask = '',
    [int]$FixtureCoreCount = 0
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[System.Threading.Thread]::CurrentThread.CurrentCulture = [Globalization.CultureInfo]::InvariantCulture
$script:Protected = @('forge_push', 'selfplay_out', 'forge_nnue_train', [IO.Path]::Combine('Administrator', 'grok-pc'))
$script:ChosenMask = [int64]0

# ------------------------------------------------------------------------------------------------ pure helpers

function ConvertTo-IntList([string]$Text) {
    # '16,20' / '16 20' / '16, 20' -> @(16, 20). Lists arrive as one string under 'pwsh -File' (an [int[]] parameter
    # would read '13,16' as 1316 through the invariant thousands separator), so they are split explicitly.
    if ([string]::IsNullOrWhiteSpace($Text)) { return , @() }
    return , @($Text -split '[,;\s]+' | Where-Object { $_ -ne '' } | ForEach-Object { [int]::Parse($_, [Globalization.CultureInfo]::InvariantCulture) })
}

function ConvertTo-CoreList([int64]$Mask) {
    $cores = New-Object System.Collections.Generic.List[int]
    for ($i = 0; $i -lt 64; $i++) { if ((($Mask -shr $i) -band 1) -eq 1) { $cores.Add($i) } }
    return , $cores.ToArray()
}

function ConvertFrom-AffinityText([string]$Text) {
    # "0xFFF0 (CPUs 4-15)", "0xFFF0", "4-15", "4,5,6" -> core list
    if ([string]::IsNullOrWhiteSpace($Text)) { return , @() }
    $m = [regex]::Match($Text, '0x([0-9A-Fa-f]+)')
    if ($m.Success) { return ConvertTo-CoreList ([Convert]::ToInt64($m.Groups[1].Value, 16)) }
    $cores = New-Object System.Collections.Generic.List[int]
    foreach ($part in ($Text -split '[,\s]+')) {
        if ($part -match '^(\d+)-(\d+)$') { for ($c = [int]$Matches[1]; $c -le [int]$Matches[2]; $c++) { $cores.Add($c) } }
        elseif ($part -match '^\d+$') { $cores.Add([int]$part) }
    }
    return , $cores.ToArray()
}

function Get-ManifestCores([string]$Path) {
    # Per-gate or top-level 'affinity' / 'cores' / 'cpu_affinity' fields (none in the 2026-10-27 manifest; the
    # driver hard-codes 0xFFF0 and records it in RUN_INFO.json, which Get-RunInfoCores reads).
    $cores = New-Object System.Collections.Generic.HashSet[int]
    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) { return , @() }
    $json = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 64
    $objects = @($json)
    if ($json.PSObject.Properties.Name -contains 'gates') { $objects += @($json.gates) }
    foreach ($o in $objects) {
        foreach ($f in 'affinity', 'cores', 'cpu_affinity') {
            if ($o.PSObject.Properties.Name -contains $f) {
                foreach ($c in (ConvertFrom-AffinityText ([string]($o.$f -join ',')))) { [void]$cores.Add($c) }
            }
        }
    }
    return , @($cores)
}

function Get-RunInfoCores([string]$Root, [int]$MaxAgeHours) {
    $cores = New-Object System.Collections.Generic.HashSet[int]
    if (-not $Root -or -not (Test-Path -LiteralPath $Root)) { return , @() }
    $cut = (Get-Date).AddHours(-$MaxAgeHours)
    foreach ($dir in Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue) {
        $ri = Join-Path $dir.FullName 'RUN_INFO.json'
        if (-not (Test-Path -LiteralPath $ri)) { continue }
        if ((Get-Item -LiteralPath $ri).LastWriteTime -lt $cut) { continue }
        try { $j = Get-Content -LiteralPath $ri -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 32 } catch { continue }
        if ($j.PSObject.Properties.Name -contains 'affinity') {
            foreach ($c in (ConvertFrom-AffinityText ([string]$j.affinity))) { [void]$cores.Add($c) }
        }
    }
    return , @($cores)
}

function Get-LiveGateCores {
    # fastchess processes and their direct children (the engines fastchess starts); read-only queries.
    $cores = New-Object System.Collections.Generic.HashSet[int]
    $gates = @(Get-Process -Name 'fastchess' -ErrorAction SilentlyContinue)
    foreach ($p in $gates) { try { foreach ($c in (ConvertTo-CoreList ([int64]$p.ProcessorAffinity))) { [void]$cores.Add($c) } } catch {} }
    if ($gates.Count -gt 0 -and $IsWindows) {
        $ids = @($gates | ForEach-Object { $_.Id })
        foreach ($child in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $ids -contains $_.ParentProcessId })) {
            try {
                $cp = Get-Process -Id $child.ProcessId -ErrorAction Stop
                foreach ($c in (ConvertTo-CoreList ([int64]$cp.ProcessorAffinity))) { [void]$cores.Add($c) }
            } catch {}
        }
    }
    return [pscustomobject]@{ Cores = @($cores); GateProcesses = $gates.Count }
}

function Select-SafeCore([int]$CoreCount, [int[]]$Used, [int[]]$Reserved, [int]$Requested) {
    # Returns @{ Core; Free; Reason }. Never returns a core in $Used or $Reserved.
    $blocked = New-Object System.Collections.Generic.HashSet[int]
    foreach ($c in $Used) { [void]$blocked.Add($c) }
    foreach ($c in $Reserved) { [void]$blocked.Add($c) }
    $free = @(0..($CoreCount - 1) | Where-Object { -not $blocked.Contains($_) })
    if ($Requested -ge 0) {
        if ($free -contains $Requested) { return @{ Core = $Requested; Free = $free; Reason = "requested core $Requested is free" } }
        return @{ Core = -1; Free = $free; Reason = "requested core $Requested is used by a gate or reserved" }
    }
    if ($free.Count -eq 0) { return @{ Core = -1; Free = $free; Reason = 'no logical core is free of gates and outside the reserved cores' } }
    $pick = ($free | Measure-Object -Maximum).Maximum
    return @{ Core = [int]$pick; Free = $free; Reason = "highest free core" }
}

function Test-OutDirAllowed([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    foreach ($p in $script:Protected) { if ($full.ToLowerInvariant().Contains($p.ToLowerInvariant())) { return $false } }
    return $true
}

function Get-Median([double[]]$Values) {
    $s = @($Values | Sort-Object)
    $n = $s.Count
    if ($n -eq 0) { return [double]::NaN }
    if ($n % 2 -eq 1) { return [double]$s[($n - 1) / 2] }
    return ([double]$s[$n / 2 - 1] + [double]$s[$n / 2]) / 2.0
}

function Get-BootstrapMedianCI([double[]]$Values, [int]$Reps, [int]$SeedValue) {
    $rng = [System.Random]::new($SeedValue)
    $n = $Values.Count
    $meds = New-Object double[] $Reps
    $buf = New-Object double[] $n
    for ($r = 0; $r -lt $Reps; $r++) {
        for ($i = 0; $i -lt $n; $i++) { $buf[$i] = $Values[$rng.Next($n)] }
        [Array]::Sort($buf)
        $meds[$r] = if ($n % 2 -eq 1) { $buf[($n - 1) / 2] } else { ($buf[$n / 2 - 1] + $buf[$n / 2]) / 2.0 }
    }
    [Array]::Sort($meds)
    $lo = $meds[[int][Math]::Floor(0.025 * ($Reps - 1))]
    $hi = $meds[[int][Math]::Ceiling(0.975 * ($Reps - 1))]
    return @($lo, $hi)
}

function Get-SlotOrder([int]$PairCount, [int]$Every) {
    # Test pairs alternate A,B / B,A (ABBA); after every $Every test pairs one control pair A,A2 / A2,A.
    $order = New-Object System.Collections.Generic.List[object]
    $control = 0
    for ($i = 0; $i -lt $PairCount; $i++) {
        $first, $second = if ($i % 2 -eq 0) { 'A', 'B' } else { 'B', 'A' }
        $order.Add([pscustomobject]@{ Kind = 'test'; Pair = $i; First = $first; Second = $second })
        if ($Every -gt 0 -and (($i + 1) % $Every) -eq 0) {
            $f2, $s2 = if ($control % 2 -eq 0) { 'A', 'A2' } else { 'A2', 'A' }
            $order.Add([pscustomobject]@{ Kind = 'control'; Pair = $control; First = $f2; Second = $s2 })
            $control++
        }
    }
    return , $order.ToArray()
}

function Get-PairRatio($Rows, [string]$Num, [string]$Den, [string]$MetricName) {
    # Rows of one pair: ratio = metric(Num) / metric(Den)
    $n = @($Rows | Where-Object { $_.Exe -eq $Num })[0]
    $d = @($Rows | Where-Object { $_.Exe -eq $Den })[0]
    $field = if ($MetricName -eq 'cpu') { 'NpsCpu' } else { 'NpsWall' }
    return [double]$n.$field / [double]$d.$field
}

# ------------------------------------------------------------------------------------------------ machine probes

function Get-CoreCount { if ($FixtureCoreCount -gt 0) { return $FixtureCoreCount }; return [Environment]::ProcessorCount }

function ConvertFrom-MemInfo([string[]]$Lines) {
    # /proc/meminfo text -> MemAvailable in GB (kB / 1MB)
    $line = @($Lines | Where-Object { $_ -like 'MemAvailable:*' })[0]
    return [Math]::Round(([double](($line.Trim() -split '\s+')[1])) / 1MB, 2)
}

function Get-FreeRamGB {
    if ($IsWindows) { return [Math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2) }
    return ConvertFrom-MemInfo @(Get-Content /proc/meminfo)
}

function Get-CpuTempC {
    # 1. HWiNFO sensor CSV (read with sharing; last row; 'CPU (Tctl/Tdie)'); 2. ACPI thermal zone; 3. Linux sysfs.
    if ($IsWindows -and $TempCsv -and (Test-Path -LiteralPath $TempCsv)) {
        try {
            $fs = [IO.File]::Open($TempCsv, 'Open', 'Read', 'ReadWrite')
            try {
                $sr = [IO.StreamReader]::new($fs)
                $header = $sr.ReadLine() -split ','
                $col = -1
                for ($i = 0; $i -lt $header.Count; $i++) { if ($header[$i] -match 'CPU \(Tctl/Tdie\)') { $col = $i; break } }
                $len = $fs.Length
                [void]$fs.Seek([Math]::Max(0, $len - 16384), 'Begin')
                $sr.DiscardBufferedData()
                $rows = @($sr.ReadToEnd() -split "`n" | Where-Object { $_.Trim() })
                $last = $rows[-1] -split ','
                $age = [double]::PositiveInfinity
                try {
                    # HWiNFO writes unpadded fields, e.g. '27.10.2026 15:2:30.941'.
                    $stamp = [datetime]::ParseExact("$($last[0]) $($last[1])".Trim(), [string[]]@('d.M.yyyy H:m:s.fff', 'd.M.yyyy H:m:s'),
                        [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None)
                    $age = ((Get-Date) - $stamp).TotalSeconds
                } catch {}
                if ($col -ge 0 -and $age -le $TempMaxAgeSec) {
                    return [pscustomobject]@{ C = [double]::Parse($last[$col], [Globalization.CultureInfo]::InvariantCulture); Source = 'hwinfo_csv' }
                }
            } finally { $fs.Dispose() }
        } catch {}
    }
    if ($IsWindows) {
        try {
            $z = @(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction Stop)
            if ($z.Count) { return [pscustomobject]@{ C = (($z | ForEach-Object { $_.CurrentTemperature / 10 - 273.15 }) | Measure-Object -Maximum).Maximum; Source = 'acpi' } }
        } catch {}
    }
    if ($IsLinux) {
        $vals = @()
        foreach ($f in @(Get-ChildItem -Path '/sys/class/thermal/thermal_zone*/temp', '/sys/class/hwmon/hwmon*/temp*_input' -ErrorAction SilentlyContinue)) {
            try { $vals += [double](Get-Content -LiteralPath $f.FullName -Raw) / 1000.0 } catch {}
        }
        if ($vals.Count) { return [pscustomobject]@{ C = ($vals | Measure-Object -Maximum).Maximum; Source = 'sysfs' } }
    }
    return $null
}

function ConvertFrom-ProcStat([string[]]$Lines) {
    # /proc/stat text -> @{ 'cpu' = @(busy, all); 'cpuN' = @(busy, all) } in jiffies (idle = idle + iowait).
    # Note: PowerShell's comma binds tighter than '-', hence the parentheses in @(($all - $idle), $all).
    $t = @{}
    foreach ($l in $Lines) {
        if ($l -notlike 'cpu*') { continue }
        $f = $l.Trim() -split '\s+'
        $nums = @($f[1..($f.Count - 1)] | ForEach-Object { [double]$_ })
        $all = ($nums | Measure-Object -Sum).Sum
        $idle = $nums[3] + $nums[4]
        $t[$f[0]] = @(($all - $idle), $all)
    }
    return $t
}

function Get-LoadFromTimes($Before, $After, [string]$Key) {
    if (-not $Before -or -not $After) { return [double]::NaN }
    $b = $Before[$Key]; $a = $After[$Key]
    if ($null -eq $a -or $null -eq $b) { return [double]::NaN }
    $den = $a[1] - $b[1]
    if ($den -le 0) { return [double]::NaN }
    return 100.0 * ($a[0] - $b[0]) / $den
}

function Get-CpuTimes {
    # Linux: /proc/stat snapshot. Windows: $null (CIM formatted counters are used instead).
    if (-not $IsLinux) { return $null }
    return ConvertFrom-ProcStat @(Get-Content /proc/stat)
}

function Get-LoadPercent($Before, [int]$CoreIndex) {
    if ($IsWindows) {
        try {
            $rows = @(Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -ErrorAction Stop)
            $tot = @($rows | Where-Object { $_.Name -eq '_Total' })[0].PercentProcessorTime
            $one = @($rows | Where-Object { $_.Name -eq "$CoreIndex" })[0].PercentProcessorTime
            return @([double]$tot, [double]$one)
        } catch { return @([double]::NaN, [double]::NaN) }
    }
    if ($IsLinux -and $Before) {
        $after = Get-CpuTimes
        return @((Get-LoadFromTimes $Before $after 'cpu'), (Get-LoadFromTimes $Before $after "cpu$CoreIndex"))
    }
    return @([double]::NaN, [double]::NaN)
}

# ------------------------------------------------------------------------------------------------ one slot

function Invoke-BenchSlot([string]$Exe, [int]$Depth) {
    $psi = [System.Diagnostics.ProcessStartInfo]::new($Exe)
    $psi.UseShellExecute = $false
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    try {
        # Priority and the single chosen core are applied before any command is sent.
        $p.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::Idle
        $p.ProcessorAffinity = [IntPtr]$script:ChosenMask
        $p.StandardInput.WriteLine("bench $Depth")
        $p.StandardInput.Flush()
        $deadline = (Get-Date).AddSeconds($TimeoutSec)
        $m = $null
        while ($true) {
            $task = $p.StandardOutput.ReadLineAsync()
            while (-not $task.Wait(500)) { if ((Get-Date) -gt $deadline) { throw "bench timeout ($TimeoutSec s): $Exe" } }
            $line = $task.Result
            if ($null -eq $line) { throw "engine exited before the bench line: $Exe" }
            $m = [regex]::Match($line, 'bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)')
            if ($m.Success) { break }
        }
        $p.Refresh()
        $cpu = $p.TotalProcessorTime.TotalSeconds      # read while the process is alive (portable)
        $affinityUsed = [int64]$p.ProcessorAffinity
        $p.StandardInput.WriteLine('quit')
        $p.StandardInput.Flush()
        if (-not $p.WaitForExit(60000)) { throw "engine did not quit: $Exe" }
        $nodes = [int64]$m.Groups[2].Value
        $ms = [double]$m.Groups[3].Value
        return [pscustomobject]@{
            Nodes = $nodes; WallMs = $ms; NpsWall = [double]$m.Groups[4].Value
            CpuS = $cpu; NpsCpu = if ($cpu -gt 0) { $nodes / $cpu } else { [double]::NaN }; AffinityUsed = $affinityUsed
        }
    } finally {
        if (-not $p.HasExited) { try { $p.StandardInput.Close() } catch {}; [void]$p.WaitForExit(10000) }
        $p.Dispose()
    }
}

# ------------------------------------------------------------------------------------------------ self test

function Invoke-SelfTest {
    function Check([bool]$ok, [string]$label) { $script:stChecks++; if (-not $ok) { $script:stFails++; Write-Host "FAIL $label" } else { Write-Host "PASS $label" } }
    $script:stChecks = 0; $script:stFails = 0
    Check ((ConvertTo-IntList '13,16') -join '|' -eq '13|16') "list '13,16' -> 13, 16 (not 1316)"
    Check ((ConvertTo-IntList '13 16') -join '|' -eq '13|16' -and (ConvertTo-IntList '0') -join '|' -eq '0') "list '13 16' and '0'"
    Check ((ConvertFrom-AffinityText '0xFFF0 (CPUs 4-15)') -join ',' -eq (4..15 -join ',')) 'affinity text 0xFFF0 -> cores 4-15'
    Check ((ConvertFrom-AffinityText '4-6, 9') -join ',' -eq '4,5,6,9') 'affinity text ranges'
    Check ((ConvertTo-CoreList 0xF000) -join ',' -eq '12,13,14,15') 'mask 0xF000 -> 12-15'
    $r = Select-SafeCore 16 (4..15) @(0, 1, 2, 3) -1
    Check ($r.Core -eq -1) 'PC case: gate on 4-15 + reserved 0-3 -> refuse'
    $r = Select-SafeCore 16 (4..13) @(0, 1, 2, 3) -1
    Check ($r.Core -eq 15) 'gate on 4-13 -> highest free core 15'
    $r = Select-SafeCore 16 (4..13) @(0, 1, 2, 3) 14
    Check ($r.Core -eq 14) 'requested free core 14 accepted'
    $r = Select-SafeCore 16 (4..13) @(0, 1, 2, 3) 5
    Check ($r.Core -eq -1) 'requested gate core 5 refused'
    $r = Select-SafeCore 16 @() @(0, 1, 2, 3) 2
    Check ($r.Core -eq -1) 'requested reserved core 2 refused'
    $all = $true
    foreach ($used in @(@(), @(4), @(15), (4..14), (5..15), @(4, 6, 8, 10, 12, 14))) {
        foreach ($req in -1..15) {
            $x = Select-SafeCore 16 $used @(0, 1, 2, 3) $req
            if ($x.Core -ge 0 -and (($used -contains $x.Core) -or $x.Core -lt 4)) { $all = $false }
        }
    }
    Check $all 'exhaustive: no selection ever returns a gate core or core 0-3'
    $order = Get-SlotOrder 8 4
    Check (@($order | Where-Object Kind -eq 'test').Count -eq 8 -and @($order | Where-Object Kind -eq 'control').Count -eq 2) 'slot order: 8 test + 2 control pairs'
    Check ((@($order | Where-Object Kind -eq 'test') | ForEach-Object { $_.First }) -join '' -eq 'ABABABAB') 'ABBA alternation of the first exe'
    Check (-not (Test-OutDirAllowed 'D:\grok-pc-data\forge_push\x')) 'refuses forge_push'
    Check (-not (Test-OutDirAllowed 'D:\grok-pc-data\selfplay_out\x')) 'refuses selfplay_out'
    Check (-not (Test-OutDirAllowed 'F:\forge_nnue_train\x')) 'refuses forge_nnue_train'
    Check (Test-OutDirAllowed ([IO.Path]::Combine([IO.Path]::GetTempPath(), 's49'))) 'temp dir allowed'
    # Statistics: A/A noise -> CI contains 1; a 5% slower B -> CI excludes 1 (synthetic ratios, fixed seed).
    $rng = [System.Random]::new(7)
    $aa = @(1..40 | ForEach-Object { 1.0 + 0.01 * ($rng.NextDouble() - 0.5) })
    $ci = Get-BootstrapMedianCI $aa 4000 1
    Check ($ci[0] -le 1.0 -and $ci[1] -ge 1.0) "synthetic A/A CI $([Math]::Round($ci[0],4))-$([Math]::Round($ci[1],4)) contains 1"
    $slow = @(1..40 | ForEach-Object { 0.95 + 0.01 * ($rng.NextDouble() - 0.5) })
    $ci = Get-BootstrapMedianCI $slow 4000 1
    Check ($ci[1] -lt 1.0) "synthetic 5% slowdown CI $([Math]::Round($ci[0],4))-$([Math]::Round($ci[1],4)) excludes 1"
    Check ((Get-Median @(3.0, 1.0, 2.0)) -eq 2.0 -and (Get-Median @(4.0, 1.0, 2.0, 3.0)) -eq 2.5) 'median'
    # Linux probes, parsed from fixture text (so they are tested on every OS).
    $t0 = ConvertFrom-ProcStat @('cpu  100 0 100 700 100 0 0 0 0 0', 'cpu3 10 0 10 70 10 0 0 0 0 0', 'intr 1 2 3')
    $t1 = ConvertFrom-ProcStat @('cpu  400 0 100 1300 200 0 0 0 0 0', 'cpu3 110 0 10 70 10 0 0 0 0 0')
    Check ($t0['cpu'][0] -eq 200 -and $t0['cpu'][1] -eq 1000 -and $t0['cpu3'][0] -eq 20) '/proc/stat parse: busy and total jiffies'
    Check ([Math]::Abs((Get-LoadFromTimes $t0 $t1 'cpu') - 300.0 / 1000.0 * 100.0) -lt 1e-9) '/proc/stat load: 300 busy of 1000 jiffies = 30%'
    Check ((Get-LoadFromTimes $t0 $t1 'cpu3') -eq 100.0) '/proc/stat load of one core: 100%'
    Check ([double]::IsNaN((Get-LoadFromTimes $t0 $t1 'cpu9'))) '/proc/stat load of a missing core: NaN'
    Check ((ConvertFrom-MemInfo @('MemTotal:       16777216 kB', 'MemAvailable:    8388608 kB')) -eq 8.0) '/proc/meminfo MemAvailable 8388608 kB = 8 GB'
    # Static check on this file: the only affinity assignment uses $script:ChosenMask, set only from Select-SafeCore.
    $src = Get-Content -LiteralPath $PSCommandPath -Raw
    $assign = [regex]::Matches($src, 'ProcessorAffinity\s*=\s*([^\r\n;]+)')
    Check ($assign.Count -eq 1 -and $assign[0].Groups[1].Value.Trim() -eq '[IntPtr]$script:ChosenMask') 'one ProcessorAffinity assignment, from $script:ChosenMask'
    $maskSet = [regex]::Matches($src, '\$script:ChosenMask\s*=\s*([^\r\n;]+)')
    Check ($maskSet.Count -eq 2 -and $maskSet[1].Groups[1].Value.Trim() -eq '[int64]1 -shl $sel.Core') '$script:ChosenMask set once (besides the 0 initialiser), from the Select-SafeCore result'
    Write-Host "SELFTEST checks=$($script:stChecks) failures=$($script:stFails)"
}

# ------------------------------------------------------------------------------------------------ main

if ($SelfTest) {
    Invoke-SelfTest
    exit ($(if ($script:stFails -eq 0) { 0 } else { 5 }))
}
try { $DepthList = ConvertTo-IntList $Depths; $ReservedList = ConvertTo-IntList $ReservedCores } catch { Write-Output "ERROR: bad -Depths / -ReservedCores list: $_"; exit 2 }
if (@($DepthList).Count -eq 0 -or @($DepthList | Where-Object { $_ -lt 1 -or $_ -gt 24 }).Count -gt 0) {
    # bench cannot be interrupted once started, so an absurd depth is refused before any engine runs
    Write-Output "ERROR: -Depths must be 1..24 (got '$Depths')"; exit 2
}
if (-not $OutDir) { Write-Output 'ERROR: -OutDir is required'; exit 2 }
if (-not (Test-OutDirAllowed $OutDir)) { Write-Output "REFUSED: -OutDir $OutDir is under a protected PC data directory"; exit 3 }
if ((Test-Path -LiteralPath $OutDir) -and @(Get-ChildItem -LiteralPath $OutDir -Force).Count -gt 0) { Write-Output "ERROR: -OutDir $OutDir must be new or empty"; exit 2 }
if (($FixtureLiveMask -or $FixtureCoreCount -gt 0) -and -not $PlanOnly) { Write-Output 'ERROR: fixtures are allowed with -PlanOnly only'; exit 2 }
if (-not $BoxOnly) {
    foreach ($c in 0, 1, 2, 3) { if ($ReservedList -notcontains $c) { Write-Output 'REFUSED: cores 0-3 must stay reserved (use -BoxOnly only on a machine without gates)'; exit 3 } }
}
$live = if ($FixtureLiveMask) { [pscustomobject]@{ Cores = (ConvertFrom-AffinityText $FixtureLiveMask); GateProcesses = 1 } } else { Get-LiveGateCores }
$runInfo = Get-RunInfoCores $RunInfoRoot $RunInfoMaxAgeHours
$manifestCores = Get-ManifestCores $Manifest
if ($BoxOnly -and ($live.GateProcesses -gt 0 -or $runInfo.Count -gt 0)) {
    Write-Output "REFUSED: -BoxOnly but this machine runs gates (fastchess processes $($live.GateProcesses), recent RUN_INFO cores $($runInfo -join ','))"
    exit 3
}
$used = @(@($live.Cores) + @($runInfo) + @($manifestCores) | Sort-Object -Unique)
$coreCount = Get-CoreCount
$sel = Select-SafeCore $coreCount $used $ReservedList $Core
$plan = [ordered]@{
    tool = 'pc_speed_ci_20261027.ps1'; label = $Label; box_only = [bool]$BoxOnly; host = [Environment]::MachineName
    logical_cores = $coreCount; live_gate_processes = $live.GateProcesses; live_gate_cores = @($live.Cores)
    runinfo_cores = @($runInfo); manifest_cores = @($manifestCores); reserved = @($ReservedList); used = $used
    free = @($sel.Free); chosen_core = $sel.Core; reason = $sel.Reason
}
$probeTemp = Get-CpuTempC
$probeLoad = Get-LoadPercent (Get-CpuTimes) $(if ($sel.Core -ge 0) { $sel.Core } else { 0 })
$plan.temp_c = $(if ($probeTemp) { $probeTemp.C } else { $null }); $plan.temp_source = $(if ($probeTemp) { $probeTemp.Source } else { 'none' })
$plan.free_ram_gb = Get-FreeRamGB; $plan.load_total_pct = $probeLoad[0]
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$plan | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutDir 'plan.json') -Encoding utf8
Write-Output ("PLAN: cores {0}, gate-used [{1}], reserved [{2}], free [{3}] -> {4}" -f $coreCount, ($used -join ','), ($ReservedList -join ','), (@($sel.Free) -join ','), $(if ($sel.Core -ge 0) { "core $($sel.Core) ($($sel.Reason))" } else { "REFUSED: $($sel.Reason)" }))
Write-Output ("PROBES: CPU temperature {0} C ({1}), free RAM {2} GB, machine load {3}%" -f $plan.temp_c, $plan.temp_source, $plan.free_ram_gb, $plan.load_total_pct)
if ($sel.Core -lt 0) { exit 3 }
$script:ChosenMask = [int64]1 -shl $sel.Core
if ($PlanOnly) { exit 0 }

# ---- run
if (-not $ExeA -or -not $ExeB) { Write-Output 'ERROR: -ExeA and -ExeB are required'; exit 2 }
if ($Pairs -lt 40) { Write-Output 'ERROR: -Pairs must be >= 40'; exit 2 }
$temp0 = Get-CpuTempC
if (-not $temp0 -and -not $AllowNoTemperature) { Write-Output 'REFUSED: no CPU temperature source (use -AllowNoTemperature only on a box)'; exit 3 }
$bin = Join-Path $OutDir 'bin'
New-Item -ItemType Directory -Path $bin -Force | Out-Null
$ext = [IO.Path]::GetExtension($ExeA)
$exes = [ordered]@{ A = (Join-Path $bin "A$ext"); A2 = (Join-Path $bin "A2$ext"); B = (Join-Path $bin "B$ext") }
Copy-Item -LiteralPath $ExeA -Destination $exes.A
Copy-Item -LiteralPath $ExeA -Destination $exes.A2
Copy-Item -LiteralPath $ExeB -Destination $exes.B
if (-not $IsWindows) { foreach ($e in $exes.Values) { & chmod +x $e } }
$hashes = [ordered]@{}
foreach ($k in $exes.Keys) { $hashes[$k] = (Get-FileHash -Algorithm SHA256 -LiteralPath $exes[$k]).Hash }
$order = Get-SlotOrder $Pairs $ControlEvery
$rows = New-Object System.Collections.Generic.List[object]
$csv = Join-Path $OutDir 'slots.csv'
$slot = 0
$aborted = ''
Write-Output ("RUN: {0} pairs + {1} control pairs x depths {2}; core {3}; metric {4}; A {5} B {6}" -f $Pairs, @($order | Where-Object Kind -eq 'control').Count, ($DepthList -join ','), $sel.Core, $Metric, $hashes.A.Substring(0, 12), $hashes.B.Substring(0, 12))
foreach ($pair in $order) {
    foreach ($d in $DepthList) {
        foreach ($tag in @($pair.First, $pair.Second)) {
            $ram = Get-FreeRamGB
            if ($ram -lt $MinFreeRamGB) { $aborted = "free RAM $ram GB < $MinFreeRamGB"; break }
            $t = Get-CpuTempC
            if ($t -and $t.C -gt $MaxTempC) { $aborted = "CPU temperature $($t.C) C > $MaxTempC"; break }
            $before = Get-CpuTimes
            $start = Get-Date
            try { $res = Invoke-BenchSlot $exes[$tag] $d } catch { $aborted = "slot failed: $_"; break }
            $load = Get-LoadPercent $before $sel.Core
            $row = [pscustomobject]@{
                Slot = $slot; Kind = $pair.Kind; Pair = $pair.Pair; Exe = $tag; Depth = $d; Nodes = $res.Nodes; WallMs = $res.WallMs
                NpsWall = $res.NpsWall; CpuS = [Math]::Round($res.CpuS, 4); NpsCpu = [Math]::Round($res.NpsCpu, 1); Core = $sel.Core
                AffinityUsed = ('0x{0:X}' -f $res.AffinityUsed); LoadTotalPct = [Math]::Round($load[0], 1); LoadCorePct = [Math]::Round($load[1], 1)
                TempC = $(if ($t) { $t.C } else { '' }); TempSource = $(if ($t) { $t.Source } else { 'none' }); FreeRamGB = $ram
                Start = $start.ToString('yyyy-MM-ddTHH:mm:ss.fff')
            }
            if ($row.AffinityUsed -ne ('0x{0:X}' -f $script:ChosenMask)) { $aborted = "affinity check failed: $($row.AffinityUsed)"; break }
            $rows.Add($row)
            $row | Export-Csv -LiteralPath $csv -Append -NoTypeInformation -Encoding utf8
            $slot++
        }
        if ($aborted) { break }
    }
    if ($aborted) { break }
}

# ---- statistics
$summary = [ordered]@{ plan = $plan; label = $Label; metric = $Metric; pairs = $Pairs; control_every = $ControlEvery; depths = @($DepthList)
    exe_sha256 = $hashes; bootstrap = $Bootstrap; seed = $Seed; slots = $rows.Count; aborted = $aborted; per_depth = [ordered]@{} }
$allPass = $true
foreach ($d in $DepthList) {
    $dr = @($rows | Where-Object Depth -eq $d)
    $nodesA = @($dr | Where-Object { $_.Exe -in 'A', 'A2' } | ForEach-Object Nodes | Sort-Object -Unique)
    $nodesB = @($dr | Where-Object Exe -eq 'B' | ForEach-Object Nodes | Sort-Object -Unique)
    $test = @(); $ctrl = @()
    foreach ($g in ($dr | Group-Object Kind, Pair)) {
        $k = $g.Group[0].Kind
        if ($g.Count -ne 2) { continue }
        if ($k -eq 'test') { $test += Get-PairRatio $g.Group 'B' 'A' $Metric } else { $ctrl += Get-PairRatio $g.Group 'A2' 'A' $Metric }
    }
    $res = [ordered]@{ nodes_A = $nodesA; nodes_B = $nodesB; node_exact = ($nodesA.Count -eq 1 -and $nodesB.Count -eq 1 -and $nodesA[0] -eq $nodesB[0])
        test_pairs = $test.Count; control_pairs = $ctrl.Count }
    if ($test.Count -ge 2) {
        $ci = Get-BootstrapMedianCI ([double[]]$test) $Bootstrap $Seed
        $res.median_ratio = Get-Median ([double[]]$test); $res.ci95 = $ci
        $res.ci_excludes_1 = ($ci[0] -gt 1.0 -or $ci[1] -lt 1.0)
        $res.rule_pass = ($ci[0] -ge $RuleLowerBound)
        if (-not $res.rule_pass) { $allPass = $false }
    } else { $allPass = $false }
    if ($ctrl.Count -ge 2) {
        $cc = Get-BootstrapMedianCI ([double[]]$ctrl) $Bootstrap ($Seed + 1)
        $res.control_median = Get-Median ([double[]]$ctrl); $res.control_ci95 = $cc
        $res.control_ci_contains_1 = ($cc[0] -le 1.0 -and $cc[1] -ge 1.0)
    }
    $summary.per_depth["d$d"] = $res
}
$summary.rule = "PC speed rule: CI lower bound >= $RuleLowerBound at every depth"
$summary.rule_pass_all_depths = $allPass -and -not $aborted
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutDir 'summary.json') -Encoding utf8
$md = New-Object System.Collections.Generic.List[string]
$md.Add("# pc_speed_ci $Label ($(if ($BoxOnly) { 'box-only' } else { 'PC' }); metric $Metric NPS; core $($sel.Core); Idle)")
$md.Add('')
$md.Add('| depth | test pairs | median B/A | 95% CI | CI excludes 1 | A/A pairs | A/A median | A/A 95% CI | A/A contains 1 | nodes A = B |')
$md.Add('|---|---:|---:|---|---|---:|---:|---|---|---|')
foreach ($d in $DepthList) {
    $r = $summary.per_depth["d$d"]
    $f = { param($v) if ($null -eq $v) { '-' } else { ([double]$v).ToString('F4', [Globalization.CultureInfo]::InvariantCulture) } }
    $ci = if ($r.Contains('ci95')) { "$(& $f $r.ci95[0])-$(& $f $r.ci95[1])" } else { '-' }
    $cc = if ($r.Contains('control_ci95')) { "$(& $f $r.control_ci95[0])-$(& $f $r.control_ci95[1])" } else { '-' }
    $md.Add("| d$d | $($r.test_pairs) | $(& $f $(if ($r.Contains('median_ratio')) { $r.median_ratio })) | $ci | $(if ($r.Contains('ci_excludes_1')) { $r.ci_excludes_1 } else { '-' }) | $($r.control_pairs) | $(& $f $(if ($r.Contains('control_median')) { $r.control_median })) | $cc | $(if ($r.Contains('control_ci_contains_1')) { $r.control_ci_contains_1 } else { '-' }) | $($r.node_exact) |")
}
$md.Add('')
$md.Add("Speed rule (CI lower bound >= $RuleLowerBound at every depth): $(if ($summary.rule_pass_all_depths) { 'PASS' } else { 'not met' })$(if ($aborted) { " -- ABORTED: $aborted" })")
$md | Set-Content -LiteralPath (Join-Path $OutDir 'summary.md') -Encoding utf8
$md | ForEach-Object { Write-Output $_ }
if ($aborted) { exit 4 }
exit 0
