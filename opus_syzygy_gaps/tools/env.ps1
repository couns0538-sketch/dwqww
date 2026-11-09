# env.ps1 - dot-source at the top of every job script (PowerShell 5.1).
# Job-only environment: TEMP/TMP/caches inside the job root, this process at
# Idle on CPUs 12-15 (mask 0xF000). Child processes inherit both.
$JobRoot = 'D:\forge_jobs_20261107\opus1'
$JobRepo = Join-Path $JobRoot 'repo'
$JobOut  = Join-Path $JobRoot 'out'
$JobTmp  = Join-Path $JobRoot 'tmp'
foreach ($d in @($JobRoot, $JobOut, $JobTmp)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}
$env:TEMP = $JobTmp
$env:TMP = $JobTmp
$env:TMPDIR = $JobTmp
$env:PYTHONPYCACHEPREFIX = Join-Path $JobTmp 'pycache'
$env:PIP_CACHE_DIR = Join-Path $JobTmp 'pipcache'
$env:GIT_TERMINAL_PROMPT = '0'
$me = [Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]0xF000
$me.PriorityClass = [Diagnostics.ProcessPriorityClass]::Idle

function Get-JobPinLine {
    $x = [Diagnostics.Process]::GetCurrentProcess()
    return ('pin mask=0x{0:X} priority={1} pid={2}' -f [int64]$x.ProcessorAffinity, $x.PriorityClass, $x.Id)
}

# The PC clock is wrong (about 7 h fast on 2026-11-09). Vienna time comes from the
# Date header of an HTTPS server, converted with the Windows time zone database.
function Get-ViennaNow {
    $tz = [TimeZoneInfo]::FindSystemTimeZoneById('W. Europe Standard Time')
    foreach ($u in 'https://www.google.com', 'https://www.cloudflare.com') {
        try {
            $r = [Net.WebRequest]::Create($u)
            $r.Method = 'HEAD'
            $r.Timeout = 15000
            $r.AllowAutoRedirect = $false
            $resp = $null
            try { $resp = $r.GetResponse() } catch [Net.WebException] { $resp = $_.Exception.Response }
            if ($resp) {
                $d = $resp.Headers['Date']
                $resp.Close()
                if ($d) {
                    $n = [DateTimeOffset]::Parse($d)
                    $v = [TimeZoneInfo]::ConvertTime($n, $tz)
                    return ('{0} Vienna (net:{1})' -f $v.ToString('yyyy-MM-dd HH:mm:ss zzz'), ([Uri]$u).Host)
                }
            }
        } catch { }
    }
    return 'UNKNOWN Vienna (no network time source reached)'
}
