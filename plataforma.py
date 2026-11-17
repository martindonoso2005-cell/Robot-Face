# Lo que cambia entre macOS y Windows, en un solo lugar: el puerto del Arduino, la cámara,
# cómo se cierran los programas, la voz y el sonido. seguir.py, hablar.py y servidor.py lo usan
# para que el mismo código corra en los dos sistemas.
# ROBOT_COMO_PC=1 fuerza en un Mac las piezas que usa Windows (para probarlas sin un PC).
import os, queue, subprocess, sys, tempfile, threading, time
from pathlib import Path

WINDOWS = sys.platform == "win32"
MAC = sys.platform == "darwin" and not os.environ.get("ROBOT_COMO_PC")


def puerto_arduino():
    """El puerto serie del Arduino (COM3 en Windows, /dev/cu.usbmodem... en Mac) o None.
    Se puede fijar a mano con la variable de entorno ROBOT_PUERTO."""
    if os.environ.get("ROBOT_PUERTO"):
        return os.environ["ROBOT_PUERTO"]
    from serial.tools import list_ports
    claves = ("arduino", "usbmodem", "usbserial", "ch340", "ch341", "wch", "usb serial", "usb-serial", "cp210")
    buenos = sorted(p.device for p in list_ports.comports()
                    if any(k in f"{p.device} {p.description} {p.manufacturer or ''}".lower() for k in claves))
    return buenos[0] if buenos else None


def abrir_captura(indice):
    """Abre una cámara con el motor de cada sistema. En Windows pide 1280x720 (si no, entrega 640x480)."""
    import cv2
    if sys.platform == "darwin":
        return cv2.VideoCapture(indice, cv2.CAP_AVFOUNDATION)
    if WINDOWS:
        cam = cv2.VideoCapture(indice, cv2.CAP_DSHOW)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        return cam
    return cv2.VideoCapture(indice)


ORDEN_CAMARAS = [0, 1, 2, 3] if WINDOWS else [1, 0, 2, 3]   # en el Mac la 0 a veces es la del iPhone


def python_del_proyecto(raiz):
    return str(Path(raiz) / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python"))


def reemplazar(origen, destino):
    """os.replace que no se cae en Windows cuando otro programa está leyendo el archivo de destino
    justo en ese momento: reintenta un par de veces y, si no puede, lo deja para la próxima."""
    for _ in range(3):
        try:
            os.replace(origen, destino)
            return True
        except PermissionError:
            time.sleep(0.01)
    return False


def matar_programa(archivo, suave=False):
    """Cierra todos los Python que estén corriendo ese archivo (por ejemplo "seguir.py")."""
    if WINDOWS:
        orden = ("Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
                 f"Where-Object {{ $_.CommandLine -like '*{archivo}*' }} | "
                 "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }")
        subprocess.run(["powershell", "-NoProfile", "-Command", orden], capture_output=True)
    else:
        patron = f"[{archivo[0]}]{archivo[1:]}"   # así pkill no se encuentra a sí mismo
        subprocess.run(["pkill", "-INT" if suave else "-9", "-f", patron])


def programa_corriendo(archivo):
    """¿Hay algún Python corriendo ese archivo? (En Windows es lento: usar solo de vez en cuando.)"""
    if WINDOWS:
        orden = ("(Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
                 f"Where-Object {{ $_.CommandLine -like '*{archivo}*' }} | Measure-Object).Count")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", orden], capture_output=True, text=True)
        return r.stdout.strip() not in ("", "0")
    return subprocess.run(["pgrep", "-f", f"[{archivo[0]}]{archivo[1:]}"], capture_output=True).returncode == 0


# ---------------------------------------------------------------------------------------------
# Voz del robot en los dos sistemas: Piper, una voz neuronal que corre en el computador, sin
# internet. Usa modelos/voz_es.onnx (es_MX-claude-high, licencia Apache 2.0), que descargan
# instalar_windows.bat y descargar_modelos.sh. No depende de las voces que traiga el sistema.
# ---------------------------------------------------------------------------------------------
class VozPiper:
    def __init__(self, modelo, velocidad=1.0):
        from piper import PiperVoice, SynthesisConfig
        if not Path(modelo).exists():
            raise FileNotFoundError(f"no está el modelo de voz {modelo}")
        self.voz = PiperVoice.load(str(modelo))
        self.config = SynthesisConfig(length_scale=1.0 / velocidad)   # length_scale menor = más rápido
        self.nombre = f"Piper {Path(modelo).stem}"

    def generar(self, texto):
        """Devuelve (audio float32 mono, tasa) con la voz de `texto`."""
        import numpy as np
        trozos = list(self.voz.synthesize(texto, self.config))
        if not trozos:
            return np.zeros(2205, dtype="float32"), 22050
        return np.concatenate([t.audio_float_array for t in trozos]).astype("float32"), trozos[0].sample_rate


# ---------------------------------------------------------------------------------------------
# Sonido fuera del Mac: se reproduce con sounddevice (en el Mac se usa afplay). Tiene la misma
# forma que un proceso (poll / terminate / wait) para que hablar.py lo use igual.
# ---------------------------------------------------------------------------------------------
class Sonido:
    def __init__(self, datos, tasa):
        import numpy as np
        import sounddevice as sd
        self.sd = sd
        try:
            tasa_salida = int(sd.query_devices(kind="output")["default_samplerate"])
        except Exception:
            tasa_salida = 48000
        if tasa_salida != tasa:   # a la tasa del parlante: algunas tarjetas no aceptan 22050 Hz
            n = int(len(datos) * tasa_salida / tasa)
            datos = np.interp(np.linspace(0, len(datos) - 1, n), np.arange(len(datos)), datos).astype("float32")
        sd.play(datos, tasa_salida)
        self.fin = time.time() + len(datos) / tasa_salida + 0.05

    def poll(self):
        return None if time.time() < self.fin else 0

    def terminate(self):
        self.sd.stop()
        self.fin = 0

    def wait(self):
        pass


# ---------------------------------------------------------------------------------------------
# Entender la voz fuera del Mac: faster-whisper. Con tarjeta NVIDIA usa el modelo grande; sin ella,
# uno chico en el procesador (más rápido, se equivoca un poco más).
# ---------------------------------------------------------------------------------------------
def preparar_cuda():
    """¿Están las bibliotecas de NVIDIA que necesita Whisper (cuBLAS y cuDNN)? En Windows las instala
    instalar_windows.bat como paquetes de Python (nvidia-cublas-cu12, nvidia-cudnn-cu12) solo si hay
    una tarjeta NVIDIA; aquí se agregan sus carpetas a la búsqueda de DLL y se prueba cargarlas."""
    if not WINDOWS:
        return True   # en Linux se prueba directamente al cargar el modelo
    import ctypes, importlib.util
    for paquete in ("nvidia.cublas", "nvidia.cudnn"):
        try:
            spec = importlib.util.find_spec(paquete)
        except ModuleNotFoundError:
            spec = None
        for base in (spec.submodule_search_locations or []) if spec else []:
            carpeta = Path(base) / "bin"
            if carpeta.is_dir():
                os.add_dll_directory(str(carpeta))
                os.environ["PATH"] = str(carpeta) + os.pathsep + os.environ.get("PATH", "")
    try:
        for dll in ("cublas64_12.dll", "cublasLt64_12.dll", "cudnn_ops64_9.dll"):
            ctypes.WinDLL(dll)   # quedan cargadas: Whisper las encuentra después
        return True
    except OSError:
        return False


def cargar_whisper_pc(modelo_gpu="large-v3-turbo", modelo_cpu="small"):
    from faster_whisper import WhisperModel
    import numpy as np
    elegido = os.environ.get("ROBOT_WHISPER")   # para forzar otro: tiny, base, small, medium, large-v3-turbo
    try:
        if os.environ.get("ROBOT_SIN_GPU"):
            raise RuntimeError("tarjeta desactivada con ROBOT_SIN_GPU")
        # Antes de descargar el modelo grande (~1,6 GB), revisa que la tarjeta NVIDIA lo pueda usar
        import ctranslate2
        if ctranslate2.get_cuda_device_count() == 0:
            raise RuntimeError("no hay tarjeta NVIDIA")
        if not preparar_cuda():
            raise RuntimeError("faltan las bibliotecas de NVIDIA (cuBLAS/cuDNN): vuelve a abrir instalar_windows.bat")
        modelo = WhisperModel(elegido or modelo_gpu, device="cuda", compute_type="float16")
        list(modelo.transcribe(np.zeros(16000, dtype="float32"), language="es")[0])   # falla aquí si CUDA no sirve
        print(f"Whisper {elegido or modelo_gpu} en la tarjeta de video (NVIDIA)")
        return modelo, 5
    except Exception as e:
        modelo = WhisperModel(elegido or modelo_cpu, device="cpu", compute_type="int8")
        print(f"Whisper {elegido or modelo_cpu} en el procesador ({e})")
        return modelo, 1


# ---------------------------------------------------------------------------------------------
# Detección de caras en la tarjeta de video: el mismo modelo YuNet que usa OpenCV, corrido con
# ONNX Runtime + DirectML (cualquier tarjeta con DirectX 12, sin depender de la versión de CUDA).
# Hace lo mismo que cv2.FaceDetectorYN (rellena a múltiplos de 32, decodifica las cajas y los 5
# puntos de cada cara, y filtra con NMS) y se usa igual: detect(imagen) -> (1, filas Nx15 o None).
# instalar_windows.bat instala onnxruntime-directml y onnx solo si hay tarjeta NVIDIA.
# ---------------------------------------------------------------------------------------------
class DetectorCarasGPU:
    PASOS = (8, 16, 32)

    def __init__(self, modelo, confianza, nms=0.3, top_k=5000):
        import onnx
        import onnxruntime as ort
        if "DmlExecutionProvider" not in ort.get_available_providers():
            raise RuntimeError("ONNX Runtime no tiene DirectML")
        self.ort = ort
        self.modelo = onnx.load(str(modelo))
        # El modelo guarda los tamaños internos de una imagen de 640x640. El procesador los ignora,
        # pero DirectML los usaría y entregaría solo un pedazo de la imagen: se borran
        del self.modelo.graph.value_info[:]
        for salida in self.modelo.graph.output:
            salida.type.tensor_type.shape.dim[1].dim_param = "celdas"
        self.confianza, self.nms, self.top_k = confianza, nms, top_k
        self.sesiones, self.rejillas = {}, {}

    def _sesion(self, alto_pad, ancho_pad):
        """Una sesión por tamaño de imagen: el modelo viene marcado 640x640 y DirectML necesita el
        tamaño real fijo. La cámara entrega siempre el mismo tamaño, así que se prepara una vez."""
        clave = (alto_pad, ancho_pad)
        if clave not in self.sesiones:
            dims = self.modelo.graph.input[0].type.tensor_type.shape.dim
            dims[2].dim_value, dims[3].dim_value = alto_pad, ancho_pad
            opciones = self.ort.SessionOptions()
            opciones.log_severity_level = 3
            opciones.enable_mem_pattern = False                  # lo pide DirectML
            opciones.execution_mode = self.ort.ExecutionMode.ORT_SEQUENTIAL
            sesion = self.ort.InferenceSession(self.modelo.SerializeToString(), opciones,
                                               providers=["DmlExecutionProvider", "CPUExecutionProvider"])
            if sesion.get_providers()[0] != "DmlExecutionProvider":
                raise RuntimeError("DirectML no pudo usar la tarjeta")
            self.sesiones[clave] = (sesion, [s.name for s in sesion.get_outputs()])
        return self.sesiones[clave]

    def _rejilla(self, alto_pad, ancho_pad):
        """Columna y fila de cada celda de cada paso (se calcula una vez por tamaño de imagen)."""
        import numpy as np
        clave = (alto_pad, ancho_pad)
        if clave not in self.rejillas:
            r = {}
            for paso in self.PASOS:
                filas, cols = alto_pad // paso, ancho_pad // paso
                f, c = np.divmod(np.arange(filas * cols, dtype=np.float32), cols)
                r[paso] = (c, f)
            self.rejillas[clave] = r
        return self.rejillas[clave]

    def detect(self, imagen):
        import cv2
        import numpy as np
        alto, ancho = imagen.shape[:2]
        alto_pad, ancho_pad = (alto - 1) // 32 * 32 + 32, (ancho - 1) // 32 * 32 + 32
        blob = np.zeros((1, 3, alto_pad, ancho_pad), dtype=np.float32)
        blob[0, :, :alto, :ancho] = imagen.transpose(2, 0, 1)   # BGR, sin escalar (igual que OpenCV)
        sesion, nombres = self._sesion(alto_pad, ancho_pad)
        salida = dict(zip(nombres, sesion.run(None, {"input": blob})))
        rejilla = self._rejilla(alto_pad, ancho_pad)
        cajas, puntajes, filas = [], [], []
        for paso in self.PASOS:
            cls = np.clip(salida[f"cls_{paso}"][0, :, 0], 0, 1)
            obj = np.clip(salida[f"obj_{paso}"][0, :, 0], 0, 1)
            puntaje = np.sqrt(cls * obj)
            sel = np.nonzero(puntaje >= self.confianza)[0]
            if not len(sel):
                continue
            c, f = rejilla[paso][0][sel], rejilla[paso][1][sel]
            b = salida[f"bbox_{paso}"][0, sel]
            k = salida[f"kps_{paso}"][0, sel]
            cx, cy = (c + b[:, 0]) * paso, (f + b[:, 1]) * paso
            w, h = np.exp(b[:, 2]) * paso, np.exp(b[:, 3]) * paso
            puntos = np.empty((len(sel), 10), dtype=np.float32)
            puntos[:, 0::2] = (k[:, 0::2] + c[:, None]) * paso
            puntos[:, 1::2] = (k[:, 1::2] + f[:, None]) * paso
            caja = np.stack([cx - w / 2, cy - h / 2, w, h], axis=1)
            filas.append(np.hstack([caja, puntos, puntaje[sel, None]]).astype(np.float32))
            cajas += caja.tolist()
            puntajes += puntaje[sel].tolist()
        if not filas:
            return 1, None
        todas = np.vstack(filas)
        quedan = cv2.dnn.NMSBoxes(cajas, puntajes, self.confianza, self.nms, top_k=self.top_k)
        return 1, (todas[np.array(quedan).reshape(-1)] if len(quedan) else None)


def detector_caras_gpu(modelo, confianza):
    """El detector de caras en la tarjeta de video, o None si no se puede (entonces se usa OpenCV)."""
    if os.environ.get("ROBOT_SIN_GPU"):
        return None
    try:
        import numpy as np
        d = DetectorCarasGPU(modelo, confianza)
        d.detect(np.zeros((720, 1280, 3), dtype=np.uint8))   # la primera vez prepara la tarjeta
        print("Detección de caras en la tarjeta de video (DirectML)")
        return d
    except Exception as e:
        print(f"Detección de caras en el procesador ({e})")
        return None


def asegurar_utf8():
    """En Windows los archivos de texto se leen por defecto en la codificación antigua del sistema y
    los nombres con tilde se rompen. Si el programa no partió en modo UTF-8, se relanza a sí mismo
    con ese modo activado (los .bat y el servidor ya lo activan, así que normalmente no hace nada)."""
    if WINDOWS and not sys.flags.utf8_mode:
        os.environ["PYTHONUTF8"] = "1"
        sys.exit(subprocess.call([sys.executable, *sys.argv]))
