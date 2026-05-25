param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

if ($CliArgs.Count -lt 1) {
    Write-Host "Usage:"
    Write-Host "  .\pdf2png.ps1 <pdf_path> [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  --quality <low|medium|high>  Output quality. low=150DPI, medium=300DPI, high=600DPI"
    Write-Host "  --output-dir <dir_path>      Output directory for PNG images"
    Write-Host "  --dry-run                    Show planned output files without creating them"
    Write-Host "  --overwrite                  Overwrite existing PNG files"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\pdf2png.ps1 .\sample.pdf"
    Write-Host "  .\pdf2png.ps1 .\sample.pdf --quality high"
    Write-Host "  .\pdf2png.ps1 .\sample.pdf --output-dir .\images --dry-run"
    Write-Host ""
    return
}

$PdfPath = $CliArgs[0]
$RestArgs = if ($CliArgs.Count -ge 2) { $CliArgs[1..($CliArgs.Count - 1)] } else { @() }
$PythonArgs = @("--pdf-path", $PdfPath)

$Index = 0
while ($Index -lt $RestArgs.Count) {
    $Arg = $RestArgs[$Index]

    if ($Arg -in @("--dry-run", "--overwrite")) {
        $PythonArgs += $Arg
        $Index += 1
    }
    elseif ($Arg -in @("--quality", "--output-dir")) {
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
        Write-Error "Specify exactly one PDF path as the first argument. Unsupported argument: $Arg"
        return
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir = (Get-Location).Path

Push-Location $ProjectRoot
try {
    python -m mytools.pdf_to_png --cwd $CallDir @PythonArgs
}
finally {
    Pop-Location
}
