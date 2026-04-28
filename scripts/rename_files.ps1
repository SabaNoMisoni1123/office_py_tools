param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs = @()
)

if ($CliArgs.Count -lt 1) {
    Write-Host "使い方:"
    Write-Host "  .\rename_files.ps1 basename <base_name> <file_path...> [options]"
    Write-Host "  .\rename_files.ps1 prefix <prefix> <file_path...> [options]"
    Write-Host "  .\rename_files.ps1 suffix <suffix> <file_path...> [options]"
    Write-Host ""
    Write-Host "例:"
    Write-Host "  .\rename_files.ps1 basename report .\a.txt .\b.txt --dry-run"
    Write-Host "  .\rename_files.ps1 prefix old_ .\a.txt"
    Write-Host "  .\rename_files.ps1 suffix _done .\a.txt"
    Write-Host ""
    return
}

$Operation = $CliArgs[0]
$RestArgs = if ($CliArgs.Count -ge 2) { $CliArgs[1..($CliArgs.Count - 1)] } else { @() }
$PythonArgs = @()

switch ($Operation) {
    "basename" {
        if ($RestArgs.Count -lt 2) {
            Write-Error "basename には <base_name> と <file_path...> が必要です。"
            return
        }
        $BaseName = $RestArgs[0]
        $RestArgs = $RestArgs[1..($RestArgs.Count - 1)]
        $PythonArgs += @("--operation", $Operation, "--base-name", $BaseName)
    }
    "prefix" {
        if ($RestArgs.Count -lt 2) {
            Write-Error "prefix には <prefix> と <file_path...> が必要です。"
            return
        }
        $Prefix = $RestArgs[0]
        $RestArgs = $RestArgs[1..($RestArgs.Count - 1)]
        $PythonArgs += @("--operation", $Operation, "--prefix", $Prefix)
    }
    "suffix" {
        if ($RestArgs.Count -lt 2) {
            Write-Error "suffix には <suffix> と <file_path...> が必要です。"
            return
        }
        $Suffix = $RestArgs[0]
        $RestArgs = $RestArgs[1..($RestArgs.Count - 1)]
        $PythonArgs += @("--operation", $Operation, "--suffix", $Suffix)
    }
    default {
        Write-Error "未対応の操作です: $Operation"
        return
    }
}

$Index = 0
while ($Index -lt $RestArgs.Count) {
    $Arg = $RestArgs[$Index]
    switch ($Arg) {
        { $_ -in @("--dry-run", "--overwrite") } {
            $PythonArgs += $Arg
            $Index += 1
        }
        { $_ -in @("--start", "--padding", "--separator") } {
            if (($Index + 1) -ge $RestArgs.Count) {
                Write-Error "$Arg には値が必要です。"
                return
            }
            $PythonArgs += @($Arg, $RestArgs[$Index + 1])
            $Index += 2
        }
        { $_.StartsWith("--") } {
            Write-Error "未対応のオプションです: $Arg"
            return
        }
        default {
            $PythonArgs += @("--path", $Arg)
            $Index += 1
        }
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$CallDir = (Get-Location).Path

Push-Location $ProjectRoot
try {
    python -m mytools.rename_files --cwd $CallDir @PythonArgs
}
finally {
    Pop-Location
}
