param
(
    [ValidateSet("pwsh","powershell")]
    [string]$Shell
)

if (-not $Shell)
{
    $Shell = "powershell"
}

Write-Host "Launching new terminal window with shell $Shell" -ForegroundColor DarkGray

if (-not (Get-Command uv -ErrorAction SilentlyContinue))
{
    Write-Error "The 'uv' command was not found on PATH. Please install it or add it to PATH."
    exit 127
}

$WtArgs = @()

# List service folder names you want to skip
$ExcludedServices = @(
    "test_services"
)

# Get all directories, then filter out excluded ones
$Services = Get-ChildItem -Path $PSScriptRoot -Directory | Where-Object { $ExcludedServices -notcontains $_.Name }

foreach ($Service in $Services)
{
    $ServicePath = $Service.FullName
    Write-Host "Creating new tab for $($Service.Name)" -ForegroundColor Cyan

    $TabArgs = @()

    # Put a semicolon (with backtick for powershell escaping) between every tab's argument list
    # Windows Terminal interprets a semicolon as a new tab command to execute with provided arguments
    # This equates to prepending the backtick and semicolon to the args for every service except the first
    if ($Service -ne $Services[0])
    {
        $TabArgs += "`;"
    }

    $TabArgs += @(
        "--title", $Service.Name,
        "--startingDirectory", $ServicePath,
        $Shell,
        "-NoExit",
        "-Command",
        "uv run $($Service.Name).py"
    )

    $WtArgs += $TabArgs
}

Start-Process wt -ArgumentList $WtArgs
Write-Host "Launch complete!" -ForegroundColor Green
