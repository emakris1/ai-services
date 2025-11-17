if (-not (Get-Command flutter -ErrorAction SilentlyContinue))
{
    Write-Error "The command 'flutter' was not found on PATH. Please install it and/or add it to PATH."
    exit 127
}

$UIDir = $(Get-Item -Path $PSScriptRoot)
Write-Host "Building $($UIDir.Name)" -ForegroundColor Blue
Push-Location $UIDir.FullName
flutter build windows --release
Pop-Location
