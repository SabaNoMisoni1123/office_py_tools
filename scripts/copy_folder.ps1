param(
    [string]$SourceDir,
    [string]$DestinationDir,
    [string[]]$SkipFolderContaining = @(),
    [switch]$Force,
    [switch]$DryRun,
    [Alias("h")]
    [switch]$Help
)

function Show-Help {
    Write-Host "使用方法:"
    Write-Host "  .\copy_folder.ps1 -SourceDir <コピー元> -DestinationDir <コピー先> [-SkipFolderContaining <文字列>] [-Force] [-DryRun]"
    Write-Host ""
    Write-Host "例:"
    Write-Host "  .\copy_folder.ps1 -SourceDir .\source -DestinationDir .\destination -SkipFolderContaining .git -DryRun"
}

if ($Help -or [string]::IsNullOrWhiteSpace($SourceDir) -or [string]::IsNullOrWhiteSpace($DestinationDir)) {
    Show-Help
    return
}

$PythonArgs = @("--source-dir", $SourceDir, "--destination-dir", $DestinationDir)
foreach ($SkipString in $SkipFolderContaining) {
    $PythonArgs += @("--skip-folder-containing", $SkipString)
}
if ($Force) {
    $PythonArgs += "--force"
}
if ($DryRun) {
    $PythonArgs += "--dry-run"
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir = (Get-Location).Path

Push-Location $ProjectRoot
try {
    python -m mytools.copy_folder --cwd $CallDir @PythonArgs
}
finally {
    Pop-Location
}

