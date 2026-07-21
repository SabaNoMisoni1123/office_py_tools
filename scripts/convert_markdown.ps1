param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

if ($CliArgs.Count -lt 1) {
    Write-Host "Usage:"
    Write-Host "  .\convert_markdown.ps1 <markdown_path> -f <html|pdf|docx> [--out-dir <output_dir>] [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  --out-dir <path>          Output directory. Defaults to the input file directory."
    Write-Host "  --css <path-or-url>       CSS for HTML / PDF. Can be specified multiple times."
    Write-Host "  --template <path>         Word template or reference doc for docx."
    Write-Host "  --config <path>           Converter config JSON. Defaults to invocation, ~/.config, then project config."
    Write-Host "  --no-default-css          Do not use CSS from config."
    Write-Host "  --no-default-template     Do not use Word template from config."
    Write-Host "  --standalone              Write standalone HTML."
    Write-Host "  --no-standalone           Write HTML fragment."
    Write-Host "  --dry-run                 Show conversion plan without creating files."
    Write-Host "  --overwrite               Overwrite existing output file."
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\convert_markdown.ps1 .\input.md -f html --css .\style.css"
    Write-Host "  .\convert_markdown.ps1 .\input.md -f pdf --out-dir .\out --css https://example.com/style.css"
    Write-Host "  .\convert_markdown.ps1 .\input.md -f docx --out-dir .\out --template .\template.dotx"
    Write-Host ""
    return
}

$InputPath = $CliArgs[0]
$RestArgs = if ($CliArgs.Count -ge 2) { $CliArgs[1..($CliArgs.Count - 1)] } else { @() }
$PythonArgs = @("--input", $InputPath)

$Index = 0
while ($Index -lt $RestArgs.Count) {
    $Arg = $RestArgs[$Index]
    if ($Arg -in @("--dry-run", "--overwrite", "--standalone", "--no-standalone", "--no-default-css", "--no-default-template")) {
        $PythonArgs += $Arg
        $Index += 1
    }
    elseif ($Arg -in @("-f", "--format", "--out-dir", "--css", "--template", "--config")) {
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
        Write-Error "Specify exactly one Markdown path as the first argument. Unsupported argument: $Arg"
        return
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir = (Get-Location).Path

Push-Location $ProjectRoot
try {
    python -m mytools.convert_markdown --cwd $CallDir @PythonArgs
}
finally {
    Pop-Location
}
