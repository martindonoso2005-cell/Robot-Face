@echo off
rem Doble clic UNA vez: prepara el robot en este PC (crea el entorno de Python e instala lo necesario).
rem Necesita Python 3.12 de 64 bits instalado desde python.org (con la casilla "Add python.exe to PATH").
chcp 65001 >nul
cd /d "%~dp0"
echo === RobotFace: instalacion en Windows ===
where py >nul 2>nul
if %errorlevel%==0 (
  py -3.12 -m venv .venv
) else (
  python -m venv .venv
)
if not exist .venv\Scripts\python.exe (
  echo.
  echo No pude crear el entorno de Python. Instala Python 3.12 de 64 bits desde https://www.python.org/downloads/
  echo y marca la casilla "Add python.exe to PATH". Despues vuelve a abrir este archivo.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requisitos_windows.txt
if errorlevel 1 (
  echo.
  echo Algo fallo al instalar. Copia el texto de arriba y revisa la guia INSTALAR_WINDOWS.md
  pause
  exit /b 1
)
rem Con tarjeta NVIDIA: bibliotecas para que Whisper la use (mas rapido y entiende mejor; ~1,5 GB)
where nvidia-smi >nul 2>nul
if %errorlevel%==0 (
  echo Tarjeta NVIDIA encontrada: instalando sus bibliotecas para Whisper...
  .venv\Scripts\python.exe -m pip install -r requisitos_nvidia.txt
  rem Deteccion de caras en la tarjeta: ONNX Runtime con DirectML en vez del normal (es el mismo modulo)
  .venv\Scripts\python.exe -m pip uninstall -y onnxruntime
  .venv\Scripts\python.exe -m pip install --force-reinstall --no-deps onnxruntime-directml==1.24.4
)
rem Modelos de vision y de voz (si no vienen en la carpeta, se descargan: unos 100 MB)
if not exist modelos mkdir modelos
if not exist modelos\yunet.onnx curl -L -o modelos\yunet.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
if not exist modelos\sface.onnx curl -L -o modelos\sface.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
if not exist modelos\face_landmarker.task curl -L -o modelos\face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
rem Voz del robot (Piper es_MX-claude-high, unos 60 MB): la misma en Mac y Windows
if not exist modelos\voz_es.onnx curl -L -o modelos\voz_es.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx
if not exist modelos\voz_es.onnx.json curl -L -o modelos\voz_es.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx.json
if not exist clave_anthropic.txt (
  echo.
  echo FALTA LA CLAVE: crea el archivo clave_anthropic.txt en esta carpeta con tu clave de la API de Anthropic.
)
echo.
echo Listo. Ahora abre pagina.bat para encender el robot.
pause
