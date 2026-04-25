param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir = Get-Location

Push-Location $ProjectRoot
try {
    python -m mytools.test @CliArgs --cwd $CallDir
}
finally {
    Pop-Location
}