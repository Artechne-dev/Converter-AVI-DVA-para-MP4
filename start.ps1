# Script de inicialização do Conversor AVI para MP4
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $ScriptDir

# Verifica se o FFmpeg está instalado localmente, senão tenta baixar
$FFmpegDir = Join-Path -Path $ScriptDir -ChildPath "ffmpeg"
$FFmpegExe = Join-Path -Path $FFmpegDir -ChildPath "ffmpeg.exe"

if (-not (Test-Path -Path $FFmpegExe)) {
    Write-Host "FFmpeg nao encontrado. Baixando ffmpeg via release oficial..." -ForegroundColor Yellow
    $FFmpegZip = Join-Path -Path $ScriptDir -ChildPath "ffmpeg.zip"
    
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip" -OutFile $FFmpegZip
    
    Write-Host "Extraindo FFmpeg (isso pode demorar um pouco)..." -ForegroundColor Yellow
    Expand-Archive -Path $FFmpegZip -DestinationPath $ScriptDir -Force
    
    $ExtractedFolder = Get-ChildItem -Path $ScriptDir -Filter "ffmpeg-master-latest-win64-gpl" -Directory
    if ($ExtractedFolder) {
        $BinFolder = Join-Path -Path $ExtractedFolder.FullName -ChildPath "bin"
        New-Item -ItemType Directory -Force -Path $FFmpegDir | Out-Null
        Copy-Item -Path "$BinFolder\*" -Destination $FFmpegDir -Force -Recurse
        Remove-Item -Path $ExtractedFolder.FullName -Recurse -Force
    }
    Remove-Item -Path $FFmpegZip -Force
}

# Adiciona o diretório local do FFmpeg ao PATH apenas para a sessão atual
$env:PATH = "$FFmpegDir;" + $env:PATH

# Configura o ambiente virtual Python
$VenvDir = Join-Path -Path $ScriptDir -ChildPath ".venv"

if (-not (Test-Path -Path $VenvDir)) {
    Write-Host "Criando ambiente virtual Python..." -ForegroundColor Yellow
    python -m venv .venv
}

# Ativa o ambiente e instala as dependencias
Write-Host "Instalando dependencias (CustomTkinter)..." -ForegroundColor Yellow
& "$VenvDir\Scripts\pip.exe" install -r requirements.txt --quiet

# Executa a aplicacao
Write-Host "Iniciando o conversor..." -ForegroundColor Green
& "$VenvDir\Scripts\python.exe" main.py
