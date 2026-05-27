param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

if ($CliArgs.Count -lt 1) {
    Write-Host "Usage:"
    Write-Host "  .\batch_convert.ps1 <input_dir> --kind <markdown|docx|pdf> -f <format> --output-dir <dir> [options]"
    return
}

$InputDir = $CliArgs[0]
$RestArgs = if ($CliArgs.Count -ge 2) { $CliArgs[1..($CliArgs.Count - 1)] } else { @() }
$PythonArgs = @("--input-dir", $InputDir)

$Index = 0
while ($Index -lt $RestArgs.Count) {
    $Arg = $RestArgs[$Index]
    if ($Arg -in @("--dry-run", "--overwrite", "--create-dirs", "--continue-on-error", "--allow-partial-success", "--no-default-css", "--no-default-template", "--no-extract-media", "--recursive", "--no-recursive", "--standalone", "--no-standalone")) {
        $PythonArgs += $Arg
        $Index += 1
    }
    elseif ($Arg -in @("--output-dir", "--kind", "-f", "--format", "--glob", "--config", "--css", "--template", "--markdown-format", "--media-dir", "--quality", "--summary-output", "--summary-format")) {
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
    python -m mytools.batch_convert --cwd $CallDir @PythonArgs
}
finally {
    Pop-Location
}
