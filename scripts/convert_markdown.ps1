param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

if ($CliArgs.Count -lt 1) {
    Write-Host "Usage:"
    Write-Host "  .\convert_markdown.ps1 <markdown_path_or_dir> [-f <html|pdf|docx>] [--out-dir <output_dir>] [--recursive] [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  --out-dir <path>          Output directory. Defaults to the input file directory."
    Write-Host "  --recursive               When the input is a directory, include Markdown files in subdirectories."
    Write-Host "  --skip-containing <text>  When the input is a directory, skip files whose name or subdirectory name contains text. Can be specified multiple times."
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
    Write-Host "  .\convert_markdown.ps1 .\markdowns -f html --recursive --out-dir .\out"
    Write-Host "  .\convert_markdown.ps1 .\markdowns -f html --skip-containing draft --skip-containing archive"
    Write-Host ""
    return
}

$InputPath = $CliArgs[0]
$RestArgs = if ($CliArgs.Count -ge 2) { $CliArgs[1..($CliArgs.Count - 1)] } else { @() }
$PythonArgs = @()
$OutputDir = $null
$Recursive = $null
$OutputFormat = $null
$SkipContaining = @()
$ConfigPath = $null

$Index = 0
while ($Index -lt $RestArgs.Count) {
    $Arg = $RestArgs[$Index]
    if ($Arg -in @("--dry-run", "--overwrite", "--standalone", "--no-standalone", "--no-default-css", "--no-default-template")) {
        $PythonArgs += $Arg
        $Index += 1
    }
    elseif ($Arg -eq "--recursive") {
        $Recursive = $true
        $Index += 1
    }
    elseif ($Arg -eq "--out-dir") {
        if (($Index + 1) -ge $RestArgs.Count) {
            Write-Error "$Arg requires a value."
            return
        }
        if ($null -ne $OutputDir) {
            Write-Error "--out-dir can only be specified once."
            return
        }
        $OutputDir = $RestArgs[$Index + 1]
        $Index += 2
    }
    elseif ($Arg -eq "--skip-containing") {
        if (($Index + 1) -ge $RestArgs.Count) {
            Write-Error "$Arg requires a value."
            return
        }
        $SkipText = $RestArgs[$Index + 1]
        if ([string]::IsNullOrWhiteSpace($SkipText)) {
            Write-Error "--skip-containing requires a non-empty value."
            return
        }
        $SkipContaining += $SkipText
        $Index += 2
    }
    elseif ($Arg -in @("-f", "--format", "--css", "--template", "--config")) {
        if (($Index + 1) -ge $RestArgs.Count) {
            Write-Error "$Arg requires a value."
            return
        }
        $PythonArgs += @($Arg, $RestArgs[$Index + 1])
        if ($Arg -in @("-f", "--format")) {
            $OutputFormat = $RestArgs[$Index + 1]
        }
        if ($Arg -eq "--config") {
            $ConfigPath = $RestArgs[$Index + 1]
        }
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

if (-not (Test-Path -LiteralPath $InputPath)) {
    Write-Error "Input path does not exist: $InputPath"
    return
}

$InputItem = Get-Item -LiteralPath $InputPath
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir = (Get-Location).Path
$ConfigDefaultFormat = "html"
$ConfigRecursive = $false
$ConfigDryRun = $false
$ConfigOverwrite = $false
$ConfigUseDefaultCss = $true
$ConfigUseDefaultTemplate = $true

if ($null -ne $ConfigPath) {
    if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
        Write-Error "Config file does not exist or is not a file: $ConfigPath"
        return
    }
    $EffectiveConfigPath = (Get-Item -LiteralPath $ConfigPath).FullName
}
else {
    $InvocationConfigPath = Join-Path $CallDir "config\markdown_converter.json"
    $UserConfigPath = Join-Path ([Environment]::GetFolderPath("UserProfile")) ".config\markdown_converter.json"
    $ProjectConfigPath = Join-Path $ProjectRoot "config\markdown_converter.json"
    if (Test-Path -LiteralPath $InvocationConfigPath -PathType Leaf) {
        $EffectiveConfigPath = $InvocationConfigPath
    }
    elseif (Test-Path -LiteralPath $UserConfigPath -PathType Leaf) {
        $EffectiveConfigPath = $UserConfigPath
    }
    else {
        $EffectiveConfigPath = $ProjectConfigPath
    }
}

if (Test-Path -LiteralPath $EffectiveConfigPath -PathType Leaf) {
    try {
        $Config = Get-Content -LiteralPath $EffectiveConfigPath -Raw | ConvertFrom-Json
        if ($Config -is [System.Array]) {
            throw "The config must be a JSON object."
        }

        $ConfigFormatProperty = $Config.PSObject.Properties["default_format"]
        if ($null -ne $ConfigFormatProperty) {
            if ($ConfigFormatProperty.Value -isnot [string] -or $ConfigFormatProperty.Value -notin @("html", "pdf", "docx")) {
                throw "default_format must be html, pdf, or docx."
            }
            $ConfigDefaultFormat = $ConfigFormatProperty.Value
        }

        foreach ($ConfigBool in @(
            @{ Name = "recursive"; Default = $false },
            @{ Name = "dry_run"; Default = $false },
            @{ Name = "overwrite"; Default = $false },
            @{ Name = "use_default_css"; Default = $true },
            @{ Name = "use_default_template"; Default = $true }
        )) {
            $ConfigBoolProperty = $Config.PSObject.Properties[$ConfigBool.Name]
            $ConfigBoolValue = $ConfigBool.Default
            if ($null -ne $ConfigBoolProperty) {
                if ($ConfigBoolProperty.Value -isnot [bool]) {
                    throw "$($ConfigBool.Name) must be true or false."
                }
                $ConfigBoolValue = $ConfigBoolProperty.Value
            }
            switch ($ConfigBool.Name) {
                "recursive" { $ConfigRecursive = $ConfigBoolValue }
                "dry_run" { $ConfigDryRun = $ConfigBoolValue }
                "overwrite" { $ConfigOverwrite = $ConfigBoolValue }
                "use_default_css" { $ConfigUseDefaultCss = $ConfigBoolValue }
                "use_default_template" { $ConfigUseDefaultTemplate = $ConfigBoolValue }
            }
        }

        $ConfigSkipProperty = $Config.PSObject.Properties["skip_containing"]
        if ($null -ne $ConfigSkipProperty) {
            $ConfigSkipValues = $ConfigSkipProperty.Value
            if ($ConfigSkipValues -is [string] -or $ConfigSkipValues -isnot [System.Collections.IEnumerable]) {
                throw "skip_containing must be an array of non-empty strings."
            }
            foreach ($ConfigSkipValue in $ConfigSkipValues) {
                if ($ConfigSkipValue -isnot [string] -or [string]::IsNullOrWhiteSpace($ConfigSkipValue)) {
                    throw "skip_containing must be an array of non-empty strings."
                }
                $SkipContaining += $ConfigSkipValue
            }
        }
    }
    catch {
        Write-Error "Failed to read skip_containing from config: $EffectiveConfigPath. $($_.Exception.Message)"
        return
    }
}

if ($null -eq $OutputFormat) {
    $OutputFormat = $ConfigDefaultFormat
    $PythonArgs += @("--format", $OutputFormat)
}
if ($null -eq $Recursive) {
    $Recursive = $ConfigRecursive
}
if ($ConfigDryRun -and $PythonArgs -notcontains "--dry-run") {
    $PythonArgs += "--dry-run"
}
if ($ConfigOverwrite -and $PythonArgs -notcontains "--overwrite") {
    $PythonArgs += "--overwrite"
}
if (-not $ConfigUseDefaultCss -and $PythonArgs -notcontains "--no-default-css") {
    $PythonArgs += "--no-default-css"
}
if (-not $ConfigUseDefaultTemplate -and $PythonArgs -notcontains "--no-default-template") {
    $PythonArgs += "--no-default-template"
}

if (-not $InputItem.PSIsContainer) {
    if ($Recursive) {
        Write-Error "--recursive can only be used when the input path is a directory."
        return
    }

    $SingleFileArgs = @("--input", $InputPath) + $PythonArgs
    if ($null -ne $OutputDir) {
        $SingleFileArgs += @("--out-dir", $OutputDir)
    }

    Push-Location $ProjectRoot
    try {
        python -m mytools.convert_markdown --cwd $CallDir @SingleFileArgs
    }
    finally {
        Pop-Location
    }
    return
}

$InputDir = $InputItem.FullName
$EffectiveOutputDir = if ($null -ne $OutputDir) {
    (Get-Item -LiteralPath $OutputDir).FullName
}
else {
    $InputDir
}

if (-not (Test-Path -LiteralPath $EffectiveOutputDir -PathType Container)) {
    Write-Error "Output directory does not exist or is not a directory: $EffectiveOutputDir"
    return
}

$MarkdownFiles = if ($Recursive) {
    Get-ChildItem -LiteralPath $InputDir -File -Recurse
}
else {
    Get-ChildItem -LiteralPath $InputDir -File
}
$MarkdownFiles = @($MarkdownFiles | Where-Object { $_.Extension -in @(".md", ".markdown") })

if ($SkipContaining.Count -gt 0) {
    $FilteredMarkdownFiles = @()
    foreach ($MarkdownFile in $MarkdownFiles) {
        $RelativePath = $MarkdownFile.FullName.Substring($InputDir.Length).TrimStart('\', '/')
        $PathParts = $RelativePath -split '[\\/]'
        $MatchedSkipText = $null
        foreach ($SkipText in $SkipContaining) {
            if ($PathParts | Where-Object { $_.IndexOf($SkipText, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 }) {
                $MatchedSkipText = $SkipText
                break
            }
        }
        if ($null -ne $MatchedSkipText) {
            Write-Host "Skip: $RelativePath (matches: $MatchedSkipText)"
            continue
        }
        $FilteredMarkdownFiles += $MarkdownFile
    }
    $MarkdownFiles = $FilteredMarkdownFiles
}

if ($MarkdownFiles.Count -eq 0) {
    Write-Host "No Markdown files were found: $InputDir"
    return
}

$OutputNames = @{}
foreach ($MarkdownFile in $MarkdownFiles) {
    $RelativePath = $MarkdownFile.FullName.Substring($InputDir.Length).TrimStart('\', '/')
    $RelativeBaseName = $RelativePath.Substring(0, $RelativePath.Length - $MarkdownFile.Extension.Length)
    $OutputName = "$($RelativeBaseName -replace '[\\/]', '_').$OutputFormat"
    if ($OutputNames.ContainsKey($OutputName)) {
        Write-Error "Multiple input files would produce the same output file: $OutputName"
        return
    }
    $OutputNames[$OutputName] = $MarkdownFile
}

Push-Location $ProjectRoot
try {
    foreach ($MarkdownFile in $MarkdownFiles) {
        $RelativePath = $MarkdownFile.FullName.Substring($InputDir.Length).TrimStart('\', '/')
        $RelativeBaseName = $RelativePath.Substring(0, $RelativePath.Length - $MarkdownFile.Extension.Length)
        $OutputName = "$($RelativeBaseName -replace '[\\/]', '_').$OutputFormat"
        $FileArgs = @("--input", $MarkdownFile.FullName, "--out-dir", $EffectiveOutputDir, "--output-name", $OutputName) + $PythonArgs
        python -m mytools.convert_markdown --cwd $CallDir @FileArgs
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
}
finally {
    Pop-Location
}
