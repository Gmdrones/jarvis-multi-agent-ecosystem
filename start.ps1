Set-Location $PSScriptRoot
if (Get-Command py -ErrorAction SilentlyContinue) { py -3 jarvis.py serve }
else { python jarvis.py serve }