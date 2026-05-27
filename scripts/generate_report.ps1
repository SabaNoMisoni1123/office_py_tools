param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

if ($CliArgs.Count -lt 1) {
    Write-Host "Usage:"
    Write-Host "  .\generate_report.ps1 <input_path> --config <config_path> --output <output_path> [options]"
    return
}

$InputPath = $CliArgs[0]
$RestArgs = if ($CliArgs.Count -ge 2) { $CliArgs[1..($CliArgs.Count - 1)] } else { @() }
$PythonArgs = @("--input", $InputPath)

$Index = 0
while ($Index -lt $RestArgs.Count) {
    $Arg = $RestArgs[$Index]
    if ($Arg -in @("--dry-run", "--overwrite", "--create-dirs")) {
        $PythonArgs += $Arg
        $Index += 1
    }
    elseif ($Arg -in @("--config", "--output", "--sheet", "--encoding", "--summary-csv-output", "--title", "--template")) {
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
    python -m mytools.generate_report --cwd $CallDir @PythonArgs
}
finally {
    Pop-Location
}
