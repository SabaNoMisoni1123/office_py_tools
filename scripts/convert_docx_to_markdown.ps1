param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

if ($CliArgs.Count -lt 1) {
    Write-Host "Usage:"
    Write-Host "  .\convert_docx_to_markdown.ps1 <docx_path> --output <markdown_path> [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  --markdown-format <gfm|markdown|commonmark>  Output Markdown flavor."
    Write-Host "  --media-dir <dir>                            Directory for extracted media."
    Write-Host "  --no-extract-media                           Do not extract media."
    Write-Host "  --config <path>                              Converter config JSON."
    Write-Host "  --dry-run                                    Show conversion plan without creating files."
    Write-Host "  --overwrite                                  Overwrite existing output file."
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\convert_docx_to_markdown.ps1 .\input.docx --output .\output.md"
    Write-Host "  .\convert_docx_to_markdown.ps1 .\input.docx --output .\output.md --media-dir .\media"
    Write-Host ""
    return
}

$InputPath = $CliArgs[0]
$RestArgs = if ($CliArgs.Count -ge 2) { $CliArgs[1..($CliArgs.Count - 1)] } else { @() }
$PythonArgs = @("--input", $InputPath)

$Index = 0
while ($Index -lt $RestArgs.Count) {
    $Arg = $RestArgs[$Index]
    if ($Arg -in @("--dry-run", "--overwrite", "--no-extract-media")) {
        $PythonArgs += $Arg
        $Index += 1
    }
    elseif ($Arg -in @("--output", "--markdown-format", "--media-dir", "--config")) {
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
        Write-Error "Specify exactly one docx path as the first argument. Unsupported argument: $Arg"
        return
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir = (Get-Location).Path

Push-Location $ProjectRoot
try {
    python -m mytools.convert_docx_to_markdown --cwd $CallDir @PythonArgs
}
finally {
    Pop-Location
}
