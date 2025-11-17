if (-not (Get-Command uv -ErrorAction SilentlyContinue))
{
    Write-Error "The command 'uv' was not found on PATH. Please install it and/or add it to PATH."
    exit 127
}

$ServiceDirs = Get-ChildItem -Path $PSScriptRoot -Directory
foreach ($ServiceDir in $ServiceDirs)
{
    Write-Host "Syncing packages for $($ServiceDir.Name)" -ForegroundColor Cyan
    uv sync --directory $ServiceDir.FullName --reinstall-package cgt-ai-core
}
