# cand_pack.ps1 - Opus R15: one command from a patch to a gate-ready candidate with its INDEX entry.
#   fresh LF lock copy (git d4f4312) -> patch -p1 -F0 (dry run first) -> cleanroom_lint -> kit v2.3 -Expose pc1 + pc2
#   with -CheckOpt 'Option=On' (OFF pins, plain = LTO+PGO per option run) -> pc1 sha256 = pc2 sha256 -> exe copied to
#   <Root>\cands\<Name>\ -> pin_check OFF (bench d11-d22 + perft = lock pins) and ON (live, perft = pins) -> smoke2m ON
#   (2 min self-play, 0 illegal / 0 crashes / 0 hangs / 0 time losses) -> RESULT.json -> make_index.py (INDEX.md).
# -NoPatch builds the unpatched lock source (the self-test: the exe must be FD3A5190 byte for byte, OFF checks only).
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File cand_pack.ps1 -Name c1_x -Tag c1x -Patch P.patch
#        -Option Name -On 1 [-Sides pc1,pc2] [-SmokeSeconds 120] [-SkipSmoke] [-NoPatch] [-Root D:\o15]
#        [-BranchDir D:\o15\wt\opus_r15] [-Idea 'one line']
# Exit: 0 all checks PASS, 1 a check failed (RESULT.json says which), 2 bad arguments, 3 source / build step failed,
# 76 disk below the R15 floor (D: 50 GB, C: 30 GB). Never overwrites: an existing <Name> RESULT.json or tag is refused.
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Patch = '',
    [string]$Option = '',
    [string]$On = '',
    [string]$Sides = 'pc1,pc2',
    [int]$SmokeSeconds = 120,
    [switch]$SkipSmoke,
    [switch]$NoPatch,
    [string]$Root = 'D:\o15',
    [string]$BranchDir = 'D:\o15\wt\opus_r15',
    [string]$Idea = ''
)
$ErrorActionPreference = 'Stop'
$Tools = $PSScriptRoot
$Bash = 'C:\Program Files\Git\bin\bash.exe'
$Py = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
$Lock = 'd4f43124dde1d1e37de90e18930e374f32ea7ffa'
$LockSha = 'fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072'
function Fail-Args([string]$m) { [Console]::Error.WriteLine("cand_pack: $m"); exit 2 }
function To-Msys([string]$p) { $q = $p -replace '\\', '/'; if ($q -match '^([A-Za-z]):/(.*)$') { return '/' + $Matches[1].ToLower() + '/' + $Matches[2] }; return $q }

if ($Name -notmatch '^[a-z0-9_]{2,40}$') { Fail-Args "-Name '$Name' must be 2-40 of [a-z0-9_]" }
if ($Tag -notmatch '^[a-z0-9]{2,8}$') { Fail-Args "-Tag '$Tag' must be 2-8 of [a-z0-9] (short .gcda paths)" }
$sideList = @($Sides.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
foreach ($s in $sideList) { if ($s -notin @('pc1', 'pc2')) { Fail-Args "-Sides must list pc1 and/or pc2, not '$s'" } }
if (-not $NoPatch) {
    if (-not $Patch -or -not (Test-Path -LiteralPath $Patch -PathType Leaf)) { Fail-Args "patch not found: '$Patch'" }
    if (-not $Option -or -not $On) { Fail-Args '-Option and -On are required (the ON line)' }
    if ($Option -match '[;=\s]' -or $On -match '[;=\s]') { Fail-Args 'one option per candidate: -Option / -On without ; = or spaces' }
} elseif ($Patch -or $Option) { Fail-Args '-NoPatch takes no -Patch / -Option' }
$Out = Join-Path $Root "cands\$Name"
if (Test-Path -LiteralPath (Join-Path $Out 'RESULT.json')) { Fail-Args "$Out\RESULT.json exists (never overwritten: use a new -Name)" }
$SrcRepo = Join-Path $Root "src_pack\$Tag"
if (Test-Path -LiteralPath $SrcRepo) { Fail-Args "$SrcRepo exists (tag used before: use a new -Tag)" }
# The kit's work dir is fixed by kit_build_r15.sh (D:\o15\w), whatever -Root says (bug check 2026-11-03 12:36: -Root
# used to move only the record folders, so a test root looked for the kit outputs in the wrong place).
$KitWork = 'D:\o15\w'
foreach ($s in $sideList) { if (Test-Path -LiteralPath (Join-Path $KitWork "${Tag}_$s")) { Fail-Args "kit work dir $KitWork\${Tag}_$s exists (use a new -Tag)" } }
$dFree = [math]::Round((Get-PSDrive D).Free / 1GB, 1); $cFree = [math]::Round((Get-PSDrive C).Free / 1GB, 1)
if ($dFree -lt 51 -or $cFree -lt 30) { [Console]::Error.WriteLine("cand_pack: STOP - D: $dFree GB / C: $cFree GB (floor D: 50 + 1, C: 30)"); exit 76 }

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$LogFile = Join-Path $Out 'pack.log'
function Say([string]$m) { $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m"; $line; Add-Content -LiteralPath $LogFile -Value $line }
# Native calls: output captured as text and appended with ONE encoding (PS 5.1 `>>` writes UTF-16 and mixes it with
# Add-Content's ANSI), and stderr never turned into a terminating error (5.1 + 2>&1 + 'Stop' throws on any stderr line).
function Invoke-Logged([string]$exe, [string[]]$argv, [string]$log) {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $lines = @(& $exe @argv 2>&1 | ForEach-Object { "$_" }); $rc = $LASTEXITCODE } finally { $ErrorActionPreference = $old }
    if ($lines.Count) { Add-Content -LiteralPath $log -Value $lines }
    return $rc
}
# No MSYS_NO_PATHCONV here: bash must translate /d/... for native programs (git.exe inside fresh_lock.sh failed with
# "cannot change to '/d/grok-pc-data/dwqww'" when it was set, 2026-11-03 11:49).
function Run-Bash([string]$cmd, [string]$log) { return (Invoke-Logged $Bash @('-c', $cmd) $log) }
$t0 = Get-Date
$res = [ordered]@{ tool = 'cand_pack.ps1'; name = $Name; tag = $Tag; lock_source = $Lock; option = $Option; on = $On
    idea = $Idea; patch = ''; patch_sha256 = ''; checks = [ordered]@{}; problems = @(); started = $t0.ToString('yyyy-MM-dd HH:mm:ss') }
$problems = New-Object System.Collections.Generic.List[string]
function Check([string]$key, [bool]$ok, [string]$detail) {
    $res.checks[$key] = [ordered]@{ ok = $ok; detail = $detail }
    if (-not $ok) { $problems.Add("${key}: $detail") }
    Say ("check {0,-22} {1}  {2}" -f $key, $(if ($ok) { 'PASS' } else { 'FAIL' }), $detail)
}
function Finish([int]$code) {
    $res.problems = @($problems); $res.ended = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $res.verdict = if ($code -eq 0 -and $problems.Count -eq 0) { 'PASS' } else { 'FAIL' }
    $text = ($res | ConvertTo-Json -Depth 6).Replace("`r`n", "`n") + "`n"
    [System.IO.File]::WriteAllText((Join-Path $Out 'RESULT.json'), $text)
    $bdr = Join-Path $BranchDir "cands\$Name\logs"
    New-Item -ItemType Directory -Force -Path $bdr | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $bdr 'RESULT.json'), $text)
    $irc = Invoke-Logged $Py @('-I', '-B', (Join-Path $Tools 'make_index.py'), '--root', (Join-Path $Root 'cands'), '--copy-to', (Join-Path $BranchDir 'cands')) $LogFile
    if ($irc -ne 0) { Say "make_index.py failed ($irc, see pack.log)" }
    Say "cand_pack $($res.verdict) $Name ($([int]((Get-Date) - $t0).TotalMinutes) min)"
    if ($code -ne 0) { exit $code }
    if ($problems.Count) { exit 1 }
    exit 0
}

Say "cand_pack $Name tag $Tag option [$Option=$On] patch [$Patch] sides $($sideList -join ' ') smoke $SmokeSeconds s"
# 1 source: fresh lock copy + patch (dry run first)
$rc = Run-Bash "bash '$(To-Msys (Join-Path $Tools 'fresh_lock.sh'))' '$(To-Msys $SrcRepo)'" $LogFile
if ($rc -ne 0) { Say "fresh_lock.sh failed ($rc)"; Finish 3 }
if (-not $NoPatch) {
    $pm = To-Msys ((Resolve-Path -LiteralPath $Patch).Path)
    $res.patch = (Resolve-Path -LiteralPath $Patch).Path
    $res.patch_sha256 = (Get-FileHash -LiteralPath $Patch -Algorithm SHA256).Hash.ToLower()
    $rc = Run-Bash "cd '$(To-Msys $SrcRepo)' && patch -p1 -F0 --dry-run < '$pm' && patch -p1 -F0 < '$pm' && git add -A && git commit -q -m 'candidate $Name' && git diff --stat HEAD~1 HEAD" $LogFile
    Check 'patch_applies' ($rc -eq 0) "patch -p1 -F0 on a fresh d4f4312 copy (exit $rc)"
    if ($rc -ne 0) { Finish 3 }
    $lintJson = Join-Path $Out 'cleanroom.json'
    $lrc = Invoke-Logged $Py @('-I', '-B', (Join-Path $Tools 'cleanroom_lint.py'), '--patch', $Patch, '--json', $lintJson) $LogFile
    Check 'cleanroom_lint' ($lrc -eq 0) "no names / licence headers / protected files in the patch (exit $lrc)"
    if ($lrc -ne 0) { Finish 1 }
}
# 2 kit builds (one -CheckOpt = the ON line)
$kitArgs = "KIT_SIDES='$($sideList -join ' ')' bash '$(To-Msys (Join-Path $Tools 'kit_build_r15.sh'))' '$(To-Msys $SrcRepo)' $Tag"
if (-not $NoPatch) { $kitArgs += " '$Option=$On'" }
$kitLog = Join-Path $Out 'kit_build.log'
Say "kit: $kitArgs"
$rc = Run-Bash $kitArgs $kitLog
if ($rc -eq 76) { Say 'kit wrapper: disk floor reached - STOP'; Finish 76 }
Check 'kit_build' ($rc -eq 0) "kit_build_r15.sh exit $rc ($((Select-String -LiteralPath $kitLog -Pattern 'RESULT' | Select-Object -Last 1).Line))"
if ($rc -ne 0) { Finish 3 }
$shas = [ordered]@{}
foreach ($s in $sideList) {
    $e = Join-Path $KitWork "${Tag}_$s\src_copy\forge_ltopgo_${Tag}_$s.exe"
    $shas[$s] = (Get-FileHash -LiteralPath $e -Algorithm SHA256).Hash.ToLower()
}
$res.kit_exe_sha256 = $shas
if ($sideList.Count -eq 2) { Check 'pc1_equals_pc2' ($shas['pc1'] -eq $shas['pc2']) "pc1 $($shas['pc1']) pc2 $($shas['pc2'])" }
$first = $sideList[0]
$kitDir = Join-Path $KitWork "${Tag}_$first"
$summary = Get-Content -LiteralPath (Join-Path $kitDir 'SUMMARY.txt')
# plain strings only: PS 5.1 ConvertTo-Json writes every Get-Content line with its PSPath / PSDrive / PSProvider
# properties (bug check 2026-11-03 12:38: 20 MB of the 35 MB RESULT.json files were these properties)
$res.kit_summary = [string[]]@($summary | ForEach-Object { [string]$_ })
$wantIdent = if ($NoPatch) { 'node identity OFF: ALL OK' } else { 'node identity OFF + 1 option run(s): ALL OK' }
Check 'kit_identity' ([bool]($summary -contains $wantIdent)) "SUMMARY: '$wantIdent'"
Check 'kit_vfmadd0' ([bool](($summary | Where-Object { $_ -match '^forge_ltopgo_.* vfmadd 0$' }).Count -eq 1)) 'LTO+PGO exe has no vfmadd'
$mp = Select-String -LiteralPath (Join-Path $kitDir 'build_log.txt') -Pattern 'real missing-profile/coverage warnings: (\d+)' | Select-Object -Last 1
$mpn = if ($mp) { [int]$mp.Matches[0].Groups[1].Value } else { -1 }
Check 'kit_missing_profile0' ($mpn -eq 0) "kit build_log.txt: real missing-profile/coverage warnings: $mpn (must be 0)"
if (-not $NoPatch) {
    $cmp = Get-Content -LiteralPath (Join-Path $kitDir 'ident\opt1.compare.txt') -Raw
    Check 'kit_on_live' ($cmp -match 'differs from OFF \(live\)') 'ident\opt1.compare.txt: option run differs from OFF'
}
New-Item -ItemType Directory -Force -Path (Join-Path $Out 'kit') | Out-Null
Copy-Item -LiteralPath (Join-Path $kitDir 'SUMMARY.txt') -Destination (Join-Path $Out "kit\SUMMARY_$first.txt")
Get-ChildItem -LiteralPath (Join-Path $kitDir 'ident') -Filter '*.compare.txt' | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $Out "kit\$($_.Name)") }
if ($sideList.Count -eq 2) { Copy-Item -LiteralPath (Join-Path $KitWork "${Tag}_pc2\SUMMARY.txt") -Destination (Join-Path $Out 'kit\SUMMARY_pc2.txt') }
# 3 the exe for the gate
$exe = Join-Path $Out "forge_ltopgo_$Tag.exe"
Copy-Item -LiteralPath (Join-Path $kitDir "src_copy\forge_ltopgo_${Tag}_$first.exe") -Destination $exe
$res.exe = $exe
$res.exe_sha256 = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLower()
$res.exe_md5 = (Get-FileHash -LiteralPath $exe -Algorithm MD5).Hash.ToLower()
Check 'exe_copy_sha256' ($res.exe_sha256 -eq $shas[$first]) "copy = kit $first exe"
if ($NoPatch) { Check 'nopatch_is_lock' ($res.exe_sha256 -eq $LockSha) "unpatched lock source -> $($res.exe_sha256) (lock $LockSha)" }
# 4 pin checks
$pin = Join-Path $Tools 'pin_check.ps1'
$prc = Invoke-Logged 'powershell' @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $pin, '-Exe', $exe, '-Full', '-Json', (Join-Path $Out 'pin_off.json')) $LogFile
Check 'pin_off' ($prc -eq 0) 'bench d11/13/16/20/22 + perft startpos/kiwipete = lock pins (pin_check -Full)'
$res.pin_off = (Get-Content -LiteralPath (Join-Path $Out 'pin_off.json') -Raw | ConvertFrom-Json).bench
if (-not $NoPatch) {
    $prc = Invoke-Logged 'powershell' @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $pin, '-Exe', $exe, '-Full', '-Options', "$Option=$On", '-Json', (Join-Path $Out 'pin_on.json')) $LogFile
    Check 'pin_on_live' ($prc -eq 0) "ON line $Option=$On advertised, accepted, live, perft = pins"
    $onJson = Get-Content -LiteralPath (Join-Path $Out 'pin_on.json') -Raw | ConvertFrom-Json   # not $on: names ignore case ($On!)
    $res.pin_on = $onJson.bench; $res.advertised = $onJson.advertised
}
# 5 smoke
if (-not $SkipSmoke) {
    # PS 5.1 drops an empty-string argument to a native program: give --line only when there is an ON line
    $sargs = @('-I', '-B', (Join-Path $Tools 'smoke2m.py'), $exe)
    if (-not $NoPatch) { $sargs += @('--line', "$Option=$On") }
    $sargs += @('--seconds', "$SmokeSeconds", '--threads', '2', '--mask', '0x3', '--idle', '--out', (Join-Path $Out 'smoke_on'))
    $smrc = Invoke-Logged $Py $sargs $LogFile
    if (-not (Test-Path -LiteralPath (Join-Path $Out 'smoke_on.json'))) { Check 'smoke' $false "smoke2m.py wrote no summary (exit $smrc)"; Finish 1 }
    $smoke = Get-Content -LiteralPath (Join-Path $Out 'smoke_on.json') -Raw | ConvertFrom-Json
    $res.smoke = [ordered]@{ verdict = $smoke.verdict; seconds = $smoke.seconds; threads = $smoke.threads; tc = $smoke.tc
        games = $smoke.games; finished = $smoke.finished_games; plies = $smoke.plies; illegal = $smoke.illegal
        crashes = $smoke.crashes; hangs = $smoke.hangs; time_losses = $smoke.time_losses; overruns = $smoke.overruns }
    Check 'smoke' ($smoke.verdict -eq 'PASS') "$($smoke.games) games, $($smoke.plies) plies, illegal $($smoke.illegal), crashes $($smoke.crashes), hangs $($smoke.hangs), time losses $($smoke.time_losses) ($SmokeSeconds s, Threads 2, $($smoke.tc))"
}
# 6 evidence into the branch
$bd = Join-Path $BranchDir "cands\$Name\logs"
New-Item -ItemType Directory -Force -Path $bd | Out-Null
foreach ($f in @('pack.log', 'kit_build.log', 'cleanroom.json', 'pin_off.json', 'pin_on.json', 'smoke_on.json', 'smoke_on.stderr.txt')) {
    $src = Join-Path $Out $f; if (Test-Path -LiteralPath $src) { Copy-Item -LiteralPath $src -Destination (Join-Path $bd $f) -Force }
}
Copy-Item -LiteralPath (Join-Path $Out 'kit') -Destination $bd -Recurse -Force
Finish 0
