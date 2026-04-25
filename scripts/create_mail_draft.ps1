param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

if ($CliArgs.Count -lt 1) {
    Write-Host "égÇ¢ï˚:"
    Write-Host "  .\create_mail_draft.ps1 <yaml_path> [ÇªÇÃëºÇÃà¯êî]"
    Write-Host ""
    Write-Host "ó·:"
    Write-Host "  .\create_mail_draft.ps1 .\config.yaml "
    Write-Host ""
    return
}

$YamlPath  = $CliArgs[0]
$OtherArgs = if ($CliArgs.Count -ge 2) { $CliArgs[1..($CliArgs.Count - 1)] } else { @() }

$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir     = (Get-Location).Path

Push-Location $ProjectRoot
try {
    python -m mytools.create_mail_draft --yaml-path $YamlPath @OtherArgs --cwd $CallDir
}
finally {
    Pop-Location
}