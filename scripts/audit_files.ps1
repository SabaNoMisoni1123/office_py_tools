param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

if ($CliArgs.Count -lt 1) {
    Write-Host "Usage:"
    Write-Host "  .\audit_files.ps1 <root_dir> [options]"
    return
}

$RootDir = $CliArgs[0]
$RestArgs = if ($CliArgs.Count -ge 2) { $CliArgs[1..($CliArgs.Count - 1)] } else { @() }
$PythonArgs = @("--root", $RootDir)

$Index = 0
while ($Index -lt $RestArgs.Count) {
    $Arg = $RestArgs[$Index]
    if ($Arg -in @("--dry-run", "--overwrite", "--create-dirs")) {
        $PythonArgs += $Arg
        $Index += 1
    }
    elseif ($Arg -in @("--glob", "--exclude-glob", "--summary-output", "--list-output", "--format", "--hash", "--max-size-mb", "--naming-regex", "--config")) {
        if (($Index + 1) -ge $RestArgs.Count) {
            Write-Error "$Arg requires a value."
            return
        }
        $PythonArgs += @($Arg, $RestArgs[$Index + 1])
        $Index += 2
    }
    else {
        Write-Error "Unsupported argument: $Arg"
        return
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir = (Get-Location).Path

Push-Location $ProjectRoot
try {
    python -m mytools.audit_files --cwd $CallDir @PythonArgs
}
finally {
    Pop-Location
}
