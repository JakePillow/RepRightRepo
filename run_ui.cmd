@echo off
setlocal

set "REPO_ROOT=%~dp0"
set "PYTHON_EXE=%REPO_ROOT%.venv\Scripts\python.exe"
set "APP_PATH=%REPO_ROOT%ui\streamlit_app.py"

if not exist "%PYTHON_EXE%" (
  echo Repo virtualenv not found:
  echo   "%PYTHON_EXE%"
  echo.
  echo Create or restore .venv for this repo, then try again.
  exit /b 1
)

if not exist "%APP_PATH%" (
  echo Streamlit entrypoint not found:
  echo   "%APP_PATH%"
  exit /b 1
)

pushd "%REPO_ROOT%" >nul
"%PYTHON_EXE%" -m streamlit run "%APP_PATH%" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul

exit /b %EXIT_CODE%
