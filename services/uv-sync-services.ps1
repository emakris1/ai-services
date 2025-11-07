if (-not (Get-Command uv -ErrorAction SilentlyContinue))
{
    Write-Error "The 'uv' command was not found on PATH. Please install it or add it to PATH."
    exit 127
}

$Services = Get-ChildItem -Path $PSScriptRoot -Directory
foreach ($Service in $Services)
{
    Push-Location $Service.FullName
    Write-Host "Syncing packages for $($Service.Name)" -ForegroundColor Cyan
    uv sync --reinstall-package cgt-ai-core
    Pop-Location
}
