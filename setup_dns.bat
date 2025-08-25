@echo off
SETLOCAL

:: Nome do script principal
SET SCRIPT_PRINCIPAL=resultado_dns.py

:: URL do instalador do Python (Windows x64)
SET PYTHON_URL=https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe
SET PYTHON_INSTALLER=python_installer.exe

:: Função para verificar Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python nao encontrado. Baixando instalador...
    powershell -Command "Invoke-WebRequest -Uri %PYTHON_URL% -OutFile %PYTHON_INSTALLER%"
    echo Instalando Python...
    start /wait "" %PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1
    IF %ERRORLEVEL% NEQ 0 (
        echo Erro ao instalar Python. Verifique manualmente.
        exit /b 1
    )
) ELSE (
    echo Python ja instalado.
)

:: Verifica se pip esta disponivel
python -m pip --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Pip nao encontrado. Instalando pip...
    python -m ensurepip --upgrade
)

:: Atualiza pip
echo Atualizando pip...
python -m pip install --upgrade pip

:: Instala bibliotecas necessárias
echo Instalando bibliotecas necessarias (requests e beautifulsoup4)...
python -m pip install --upgrade requests beautifulsoup4

:: Executa o script principal
IF EXIST "%SCRIPT_PRINCIPAL%" (
    echo Rodando script principal...
    python "%SCRIPT_PRINCIPAL%"
) ELSE (
    echo Script principal "%SCRIPT_PRINCIPAL%" nao encontrado.
)

ENDLOCAL
pause
