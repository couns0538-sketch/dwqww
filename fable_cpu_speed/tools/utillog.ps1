# utillog.ps1 - one line every -EveryMin minutes into UTILIZATION.log (PowerShell 5.1, ASCII only).
# Read-only on other processes. Pins itself to one CPU of the lane at BelowNormal. Ends at -Hours after start
# or when the stop file exists. The lines are observations at those moments, not continuous monitoring.
param(
    [string]$LogFile = 'D:\forge_jobs_20261110\fable4cpu\repo\fable_cpu_speed\UTILIZATION.log',
    [string]$StopFile = 'D:\forge_jobs_20261110\fable4cpu\out\utillog.stop',
    [int]$EveryMin = 15,
    [double]$Hours = 3.9,
    [long]$Mask = 0x2,
    [switch]$Once,
    [string]$Note = ''
)
$ErrorActionPreference = 'Continue'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]$Mask
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
$me.Refresh()
$Lane = 0x707F
$MyCpus = @(0, 1, 2, 3, 4, 5, 6, 12, 13, 14)
$JobRoot = 'D:\forge_jobs_20261110\fable4cpu'
$T0utc = [DateTime]::Parse('2026-11-10T21:49:27Z').ToUniversalTime()
function NowV { ([DateTime]::UtcNow.AddSeconds(-25159.3).AddHours(1)).ToString('yyyy-MM-dd HH:mm:ss') + ' Vienna' }
$n = [Environment]::ProcessorCount
$pcs = @()
for ($i = 0; $i -lt $n; $i++) { $pcs += New-Object System.Diagnostics.PerformanceCounter('Processor', '% Processor Time', "$i") }
function One([string]$note) {
    foreach ($c in $pcs) { [void]$c.NextValue() }
    $a = @{}
    foreach ($p in [System.Diagnostics.Process]::GetProcesses()) { try { $a[$p.Id] = $p.TotalProcessorTime.TotalSeconds } catch { } }
    Start-Sleep -Seconds 5
    $v = @(); foreach ($c in $pcs) { $v += [int][Math]::Round($c.NextValue()) }
    $mineTxt = @(); $foreign = @(); $viol = @()
    foreach ($p in [System.Diagnostics.Process]::GetProcesses()) {
        if ($p.Id -eq $me.Id) { continue }
        $cpu = $null; try { $cpu = $p.TotalProcessorTime.TotalSeconds } catch { }
        $d = 0.0; if ($cpu -ne $null -and $a.ContainsKey($p.Id)) { $d = ($cpu - $a[$p.Id]) / 5.0 }
        $aff = 0; try { $aff = [int64]$p.ProcessorAffinity } catch { }
        $st = $null; try { $st = $p.StartTime.ToUniversalTime() } catch { }
        $path = ''; try { $path = $p.MainModule.FileName } catch { }
        $inJob = ($path -like "$JobRoot\*")
        $isMine = $inJob -or ($st -ne $null -and $st -ge $T0utc -and $aff -ne 0 -and ($aff -band (-bnot $Lane)) -eq 0 -and
            $p.ProcessName -match '^(python|powershell|cmd|clang\+\+|clang|ld\.lld|lld|git|git-remote-https|llvm-.*|conhost)$')
        if ($isMine) {
            if ($aff -ne 0 -and ($aff -band (-bnot $Lane)) -ne 0) { $viol += ('{0}({1}) mask 0x{2:X}' -f $p.ProcessName, $p.Id, $aff) }
            if ($d -ge 0.05) { $mineTxt += ('{0}({1}) 0x{2:X} {3:N2}cpu' -f $p.ProcessName, $p.Id, $aff, $d) }
        } elseif ($d -ge 0.05) {
            $m = 'UNREADABLE'; if ($aff -ne 0) { $m = ('0x{0:X}' -f $aff) }
            if ($aff -eq 0 -or ($aff -band $Lane) -ne 0) { $foreign += ('{0}({1}) {2} {3:N2}cpu' -f $p.ProcessName, $p.Id, $m, $d) }
        }
    }
    $load = @(); foreach ($i in $MyCpus) { $load += ('{0}:{1}' -f $i, $v[$i]) }
    $other = @(); foreach ($i in 7, 8, 9, 10, 11, 15) { $other += ('{0}:{1}' -f $i, $v[$i]) }
    $free = (New-Object System.IO.DriveInfo('D')).AvailableFreeSpace / 1GB
    $line = (NowV) + ' | my CPUs load % ' + ($load -join ' ') + ' | others ' + ($other -join ' ') +
        ' | mine: ' + $(if ($mineTxt.Count) { $mineTxt -join ', ' } else { 'nothing using CPU' }) +
        ' | foreign with CPU use, mask overlapping or unreadable: ' + $(if ($foreign.Count) { $foreign -join ', ' } else { 'none seen' }) +
        ' | VIOLATIONS (mine outside 0x707F): ' + $(if ($viol.Count) { $viol -join ', ' } else { 'none' }) +
        (' | D: free {0:N2} GiB' -f $free) + $(if ($note) { ' | ' + $note } else { '' })
    [System.IO.File]::AppendAllText($LogFile, $line + "`n", [System.Text.Encoding]::ASCII)
    [Console]::Out.WriteLine($line)
}
if ($Once) { One $Note; exit 0 }
$end = [DateTime]::UtcNow.AddHours($Hours)
while ([DateTime]::UtcNow -lt $end -and -not (Test-Path -LiteralPath $StopFile)) {
    One 'logger'
    $next = [DateTime]::UtcNow.AddMinutes($EveryMin).AddSeconds(-5)
    while ([DateTime]::UtcNow -lt $next -and -not (Test-Path -LiteralPath $StopFile)) { Start-Sleep -Seconds 20 }
}
