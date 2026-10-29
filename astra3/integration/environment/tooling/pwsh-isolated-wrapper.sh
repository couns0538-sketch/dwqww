#!/bin/sh
export XDG_CACHE_HOME=/tmp/astra3-tools/pwsh-cache
export XDG_CONFIG_HOME=/tmp/astra3-tools/pwsh-config
export XDG_DATA_HOME=/tmp/astra3-tools/pwsh-data
export DOTNET_CLI_HOME=/tmp/astra3-tools/pwsh-home
export POWERSHELL_TELEMETRY_OPTOUT=1
exec /tmp/astra3-tools/powershell-7.5.2/opt/microsoft/powershell/7/pwsh "$@"
