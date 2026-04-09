@echo off
:: Initialize a new project with pretext support
:: Usage: init-project.bat <project-name>

if "%~1"=="" (
    echo Usage: init-project.bat ^<project-name^>
    exit /b 1
)

set PROJECT_NAME=%~1
set PROJECT_PATH=..\%PROJECT_NAME%

echo Creating new project: %PROJECT_NAME%

:: Create project directory
if not exist %PROJECT_PATH% mkdir %PROJECT_PATH%

:: Create package.json with pretext
cd %PROJECT_PATH%

echo {> package.json
echo   "name": "%PROJECT_NAME%",>> package.json
echo   "version": "1.0.0",>> package.json
echo   "type": "module",>> package.json
echo   "dependencies": {>> package.json
echo     "@chenglou/pretext": "latest">> package.json
echo   }>> package.json
echo }>> package.json

echo Project %PROJECT_NAME% created with pretext support!
echo Run 'npm install' in the project directory to install dependencies.
