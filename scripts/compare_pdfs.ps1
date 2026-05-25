param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

if ($CliArgs.Count -lt 2) {
    Write-Host "Usage:"
    Write-Host "  .\compare_pdfs.ps1 <left_pdf_path> <right_pdf_path> [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  --quality <low|medium|high>  Compare quality. low=150DPI, medium=300DPI, high=600DPI"
    Write-Host "  --threshold <0-255>          Ignore small RGB channel differences"
    Write-Host "  --output-dir <dir_path>      Output directory for diff images"
    Write-Host "  --overwrite                  Overwrite existing output files"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\compare_pdfs.ps1 .\old.pdf .\new.pdf"
    Write-Host "  .\compare_pdfs.ps1 .\old.pdf .\new.pdf --quality high"
    Write-Host "  .\compare_pdfs.ps1 .\old.pdf .\new.pdf --threshold 5 --output-dir .\pdf_diff"
    Write-Host ""
    return
}

$LeftPdf = $CliArgs[0]
$RightPdf = $CliArgs[1]
$RestArgs = if ($CliArgs.Count -ge 3) { $CliArgs[2..($CliArgs.Count - 1)] } else { @() }
$PythonArgs = @("--left-pdf", $LeftPdf, "--right-pdf", $RightPdf)

$Index = 0
while ($Index -lt $RestArgs.Count) {
    $Arg = $RestArgs[$Index]

    if ($Arg -eq "--overwrite") {
        $PythonArgs += $Arg
        $Index += 1
    }
    elseif ($Arg -in @("--quality", "--threshold", "--output-dir")) {
        if (($Index + 1) -ge $RestArgs.Count) {
            Write-Error "$Arg requires a value."
            return
        }
        $PythonArgs += @($Arg, $RestArgs[$Index + 1])
        $Index += 2
    }
    elseif ($Arg.StartsWith("--")) {
        Write-Error "Unsupported option: $Arg"
        return
    }
    else {
        Write-Error "Specify exactly two PDF paths first. Unsupported argument: $Arg"
        return
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir = (Get-Location).Path
$ExitCode = 0

Push-Location $ProjectRoot
try {
    python -m mytools.compare_pdfs --cwd $CallDir @PythonArgs
    $ExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

exit $ExitCode
