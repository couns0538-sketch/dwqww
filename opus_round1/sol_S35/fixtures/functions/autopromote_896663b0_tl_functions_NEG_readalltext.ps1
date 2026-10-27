# S35 function extract: verbatim FunctionDefinitionAst text from autopromote.ps1.staged_ZH sha256 896663b0307402a7285ba8446c8b486db168075761c2dfbd7832f0a0fcdd7b12
# Read-Shared: source lines 83-83
function Read-Shared($p){ try{ return [IO.File]::ReadAllText($p) }catch{ return '' } }
# Log-TLCrash: source lines 84-85
function Log-TLCrash($tag){ $lp="$D\$tag\$tag.log"; if(-not (Test-Path $lp)){ return @(0,0) }; $tx=Read-Shared $lp
  $tl=@([regex]::Matches($tx,'Finished game .*\{.*loses on time')).Count; $cr=@([regex]::Matches($tx,'(?i)(disconnect|stalls|crash|illegal|abandon)')).Count; return @($tl,$cr) }
