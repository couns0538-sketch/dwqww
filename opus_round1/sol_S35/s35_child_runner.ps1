# s35_child_runner.ps1 - child process of the S35 harness (opus, 2026-10-27).
# Defines stubs for every side-effect command the conc watchers use, then dot-sources ONE patched watcher COPY
# (live paths already rewritten to a scratch sandbox by the harness). The watcher's own `while($true)` loop ends
# each pass with `Start-Sleep 30`; the Start-Sleep stub turns that into a tick handshake with the harness
# (writes ctl\tick<N>.done, then waits for ctl\tick<N+1>.go, or exits after the last tick).
param(
  [Parameter(Mandatory = $true)][string]$Ctl,
  [Parameter(Mandatory = $true)][string]$Patched,
  [Parameter(Mandatory = $true)][int]$Ticks,
  [int]$Timeout = 90,
  [int]$FakeOurPid = 999999
)
$ErrorActionPreference = 'Continue'
$script:__S35 = @{ ctl = $Ctl; ticks = $Ticks; tick = 0; timeout = $Timeout; state = 'watcher_returned' }
function __S35Stub { param([string]$Name, [object[]]$A)
  Add-Content -LiteralPath (Join-Path $script:__S35.ctl 'stub_calls.log') -Encoding utf8 -Value ('{0} {1}' -f $Name, (@($A | ForEach-Object { "$_" }) -join ' ')) }
# side effects: never executed, only recorded
function taskkill.exe { __S35Stub 'taskkill.exe' $args }
function taskkill { __S35Stub 'taskkill' $args }
function Stop-Process { __S35Stub 'Stop-Process' $args }
function Start-Process { __S35Stub 'Start-Process' $args }
function Stop-Computer { __S35Stub 'Stop-Computer' $args }
function Restart-Computer { __S35Stub 'Restart-Computer' $args }
# environment probes: deterministic fakes (64 GB free RAM, no "our" worker process, 12.5 % CPU)
function Get-Counter { __S35Stub 'Get-Counter' $args; [pscustomobject]@{ CounterSamples = @([pscustomobject]@{ CookedValue = 12.5 }) } }
function Get-CimInstance {
  [CmdletBinding()] param([Parameter(Position = 0)][string]$ClassName, [string]$Filter)
  __S35Stub 'Get-CimInstance' @($ClassName, $Filter)
  if ($ClassName -eq 'Win32_OperatingSystem') { return [pscustomobject]@{ FreePhysicalMemory = 67108864 } }
  if ($ClassName -eq 'Win32_Process') { return $null }
  throw "S35 stub: Get-CimInstance $ClassName is not modelled"
}
# tick handshake
function Start-Sleep {
  param([Parameter(Position = 0)]$Seconds, $Milliseconds)
  $s = $script:__S35; $s.tick++
  Set-Content -LiteralPath (Join-Path $s.ctl ('tick{0}.done' -f $s.tick)) -Value 'done' -Encoding ascii
  # `exit` here unwinds the dot-sourced watcher script only; the runner maps $s.state to the process exit code below
  if ($s.tick -ge $s.ticks) { $s.state = 'all_ticks_done'; exit }
  $go = Join-Path $s.ctl ('tick{0}.go' -f ($s.tick + 1)); $sw = [Diagnostics.Stopwatch]::StartNew()
  while (-not (Test-Path -LiteralPath $go)) { if ($sw.Elapsed.TotalSeconds -gt $s.timeout) { $s.state = 'timeout'; exit }; [Threading.Thread]::Sleep(50) }
}
# second safety net (the harness already refused any copy that still names a live root)
if ((Get-Content -LiteralPath $Patched -Raw) -match '(?i)(grok-pc\\forge_push|\\Users\\Administrator\\grok-pc|D:\\grok-pc-data|F:\\forge_nnue_train|F:\\forge_out|Global\\)') {
  Set-Content -LiteralPath (Join-Path $Ctl 'REFUSED.txt') -Value "live root in patched copy: $($Matches[0])"; exit 5
}
. $Patched -OurPid $FakeOurPid
# 0 = all ticks done; 3 = timeout waiting for the harness; 4 = the watcher returned/exited by itself (e.g. its mutex)
exit $(switch ($script:__S35.state) { 'all_ticks_done' { 0 } 'timeout' { 3 } default { 4 } })
