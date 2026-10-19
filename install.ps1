$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (Get-Command py -ErrorAction SilentlyContinue) { py -3 jarvis.py init }
elseif (Get-Command python -ErrorAction SilentlyContinue) { python jarvis.py init }
else { throw 'Install Python 3.10+ first: https://python.org/downloads/' }
if ($LASTEXITCODE -ne 0) { throw 'Initialization failed' }
Write-Host 'JARVIS initialized. Run .\start.ps1'