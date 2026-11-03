param([string]$Kind)
function smp($n, $v) { $c = if ($null -ne $v) { [double]$v }; [pscustomobject]@{ InstanceName = $n; CookedValue = $c } }
switch ($Kind) {
  'throws'    { function global:Get-Counter { throw 'simulated counter failure' } }
  'nothing'   { function global:Get-Counter { } }
  'error'     { function global:Get-Counter { Write-Error 'simulated counter error' } }
  'nototal'   { function global:Get-Counter { [pscustomobject]@{ CounterSamples = @(smp '0' 5.0; smp '1' 5.0) } } }
  'nullvalue' { function global:Get-Counter { [pscustomobject]@{ CounterSamples = @(smp '_total' $null; smp '0' 5.0) } } }
  'good'      { function global:Get-Counter { [pscustomobject]@{ CounterSamples = @(smp '_total' 7.0; 0..15 | ForEach-Object { smp "$_" 7.0 }) } } }
  default     { throw "unknown kind $Kind" }
}
