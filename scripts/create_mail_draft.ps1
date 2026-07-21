param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

# Parse user arguments and pass only named arguments to the Python CLI.
if ($CliArgs.Count -lt 1) {
    Write-Host "Usage: .\create_mail_draft.ps1 <yaml-path> [--no-show] [--mode <new|reply>] [--reply-all]"
    return
}

$YamlPath = $CliArgs[0]
$PythonArgs = @("--yaml-path", $YamlPath)
$Index = 1

while ($Index -lt $CliArgs.Count) {
    $Argument = $CliArgs[$Index]
    if ($Argument -in @("--no-show", "--reply-all")) {
        $PythonArgs += $Argument
        $Index += 1
    }
    elseif ($Argument -eq "--mode") {
        if (($Index + 1) -ge $CliArgs.Count -or $CliArgs[$Index + 1] -notin @("new", "reply")) {
            Write-Error "--mode must be new or reply."
            return
        }
        $PythonArgs += @("--mode", $CliArgs[$Index + 1])
        $Index += 2
    }
    else {
        Write-Error "Unsupported argument: $Argument"
        return
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir = (Get-Location).Path
$ExitCode = 0

Push-Location $ProjectRoot
try {
    python -m mytools.create_mail_draft --cwd $CallDir @PythonArgs
    $ExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

exit $ExitCode
