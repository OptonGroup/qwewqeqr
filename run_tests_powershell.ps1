# Script for running tests in PowerShell with correct encoding handling
# Author: AI Assistant
# Date: 26.04.2025

<#
.SYNOPSIS
    Runs tests with correct encoding handling in PowerShell.

.DESCRIPTION
    This script sets up the environment for correct work with Cyrillic in PowerShell,
    activates Python virtual environment and runs tests with specified parameters.

.PARAMETER Config
    Configuration for running tests (e.g., "formal", "sport", "default").

.PARAMETER TestFile
    Test file to run.

.PARAMETER VenvPath
    Path to Python virtual environment. Default is "./venv".

.PARAMETER NoValidation
    Skip result validation.

.PARAMETER Debug
    Enable debug mode.

.PARAMETER OutputFile
    File to save output.

.EXAMPLE
    .\run_tests_powershell.ps1 -Config formal -TestFile test_assistant_wildberries_sync.py

.EXAMPLE
    .\run_tests_powershell.ps1 -VenvPath C:\path\to\venv -TestFile test_assistant_wildberries.py -NoValidation
#>

param (
    [string]$Config = "formal",
    [Parameter(Mandatory=$true)]
    [string]$TestFile,
    [string]$VenvPath = "./venv",
    [switch]$NoValidation,
    [switch]$Debug,
    [string]$OutputFile
)

# Setting encoding for PowerShell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Function to check Python availability
function Test-Python {
    try {
        $pythonVersion = python --version
        Write-Host "Python found: $pythonVersion" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
        return $false
    }
}

# Function to activate virtual environment
function Activate-Venv {
    param (
        [string]$VenvPath
    )
    
    # Check if virtual environment exists
    if (-not (Test-Path $VenvPath)) {
        Write-Host "Virtual environment not found at path: $VenvPath" -ForegroundColor Yellow
        Write-Host "Creating new virtual environment..." -ForegroundColor Yellow
        
        try {
            python -m venv $VenvPath
            Write-Host "Virtual environment created successfully." -ForegroundColor Green
        }
        catch {
            Write-Host "Error creating virtual environment: $_" -ForegroundColor Red
            return $false
        }
    }
    
    # Determine path to activation script depending on OS
    $activateScript = if ($IsWindows -or $PSVersionTable.PSVersion.Major -lt 6) {
        Join-Path $VenvPath "Scripts\Activate.ps1"
    } else {
        Join-Path $VenvPath "bin/activate.ps1"
    }
    
    # Check if activation script exists
    if (-not (Test-Path $activateScript)) {
        Write-Host "Activation script not found: $activateScript" -ForegroundColor Red
        return $false
    }
    
    # Activate virtual environment
    try {
        & $activateScript
        Write-Host "Virtual environment activated: $VenvPath" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Error activating virtual environment: $_" -ForegroundColor Red
        return $false
    }
}

# Function to check and install dependencies
function Install-Dependencies {
    Write-Host "Checking dependencies..." -ForegroundColor Yellow
    
    # Check if requirements.txt exists
    if (Test-Path "requirements.txt") {
        Write-Host "Found requirements.txt. Installing dependencies..." -ForegroundColor Yellow
        
        try {
            python -m pip install -r requirements.txt
            Write-Host "Dependencies installed successfully." -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "Error installing dependencies: $_" -ForegroundColor Red
            return $false
        }
    }
    else {
        Write-Host "requirements.txt not found. Skipping dependency installation." -ForegroundColor Yellow
        return $true
    }
}

# Function to run tests
function Run-Tests {
    param (
        [string]$Config,
        [string]$TestFile,
        [switch]$NoValidation,
        [bool]$DebugMode,
        [string]$OutputFile
    )
    
    # Form command
    $cmd = "python $TestFile"
    
    if ($Config) {
        $cmd += " -c `"$Config`""
    }
    
    if ($NoValidation) {
        $cmd += " --no-validation"
    }
    
    if ($DebugMode) {
        $cmd += " --debug"
    }
    
    # Set environment variables for correct encoding
    $env:PYTHONIOENCODING = "utf-8"
    
    # Run tests
    Write-Host "Running tests: $cmd" -ForegroundColor Yellow
    
    if ($OutputFile) {
        # Run with output to file
        try {
            Invoke-Expression "$cmd" | Out-File -FilePath $OutputFile -Encoding utf8
            Write-Host "Results saved to file: $OutputFile" -ForegroundColor Green
        }
        catch {
            Write-Host "Error running tests: $_" -ForegroundColor Red
            return $false
        }
    }
    else {
        # Run with output to console
        try {
            Invoke-Expression "$cmd"
        }
        catch {
            Write-Host "Error running tests: $_" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Main script logic
Write-Host "Running tests with parameters:" -ForegroundColor Cyan
Write-Host "  Configuration: $Config" -ForegroundColor Cyan
Write-Host "  Test file: $TestFile" -ForegroundColor Cyan
Write-Host "  Venv path: $VenvPath" -ForegroundColor Cyan
Write-Host "  Skip validation: $NoValidation" -ForegroundColor Cyan
Write-Host "  Debug mode: $Debug" -ForegroundColor Cyan
Write-Host "  Output file: $($OutputFile -or 'Not specified')" -ForegroundColor Cyan

# Check Python availability
if (-not (Test-Python)) {
    exit 1
}

# Activate virtual environment
if (-not (Activate-Venv -VenvPath $VenvPath)) {
    exit 1
}

# Check and install dependencies
if (-not (Install-Dependencies)) {
    exit 1
}

# Run tests
if (-not (Run-Tests -Config $Config -TestFile $TestFile -NoValidation:$NoValidation -DebugMode:$Debug -OutputFile $OutputFile)) {
    exit 1
}

Write-Host "Tests completed successfully." -ForegroundColor Green
exit 0 