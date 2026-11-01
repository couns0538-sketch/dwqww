#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PluginRoot)
$ErrorActionPreference = 'Stop'
$Rows = @()
$Bad = $false
foreach ($File in Get-ChildItem -LiteralPath $PluginRoot -Recurse -Filter '*.ps1' -File) {
    $Tokens = $null
    $ParseErrors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($File.FullName, [ref]$Tokens, [ref]$ParseErrors)
    $Messages = @($ParseErrors | ForEach-Object { $_.Message })
    if ($Messages.Count -gt 0) { $Bad = $true }
    $Rows += [pscustomobject]@{ path=$File.FullName; errors=$Messages; status=$(if ($Messages.Count -eq 0) {'PASS'} else {'FAIL'}) }
}
[pscustomobject]@{ parser_version=$PSVersionTable.PSVersion.ToString(); scope='Syntax parsing only; scripts not executed'; files=$Rows } | ConvertTo-Json -Depth 6
if ($Bad -or $Rows.Count -eq 0) { exit 1 }
