#!/bin/zsh
# Descarga los modelos de visión y la voz del robot a modelos/ (Whisper se descarga solo la primera vez que corre hablar.py)
cd "$(dirname "$0")"; mkdir -p modelos
curl -L -o modelos/yunet.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
curl -L -o modelos/sface.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
curl -L -o modelos/face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
# Voz del robot (Piper es_MX-claude-high, unos 60 MB): la misma en Mac y Windows
curl -L -o modelos/voz_es.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx
curl -L -o modelos/voz_es.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx.json
