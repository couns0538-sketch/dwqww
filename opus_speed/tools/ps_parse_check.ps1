# ps_parse_check.ps1 - parse every .ps1 in a folder with the Windows PowerShell 5.1 parser (the version the tools run
# under) and print the errors; exit 1 if any file has one. usage: powershell -NoProfile -File ps_parse_check.ps1 [-Dir <folder>]
param([string]$Dir = $PSScriptRoot)
$bad = 0
foreach ($f in (Get-ChildItem -Path $Dir -Filter *.ps1 -Recurse | Sort-Object FullName)) {
  $errs = $null; $tokens = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tokens, [ref]$errs)
  if ($errs.Count -gt 0) {
    $bad++
    foreach ($e in $errs) { Write-Output ("{0}:{1}: {2}" -f $f.Name, $e.Extent.StartLineNumber, $e.Message) }
  } else { Write-Output ("{0}: ok" -f $f.Name) }
}
Write-Output "PowerShell $($PSVersionTable.PSVersion): $bad file(s) with parse errors"
if ($bad) { exit 1 } else { exit 0 }
