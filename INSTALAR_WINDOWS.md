# RobotFace en Windows

Guía para instalar y usar el robot en un PC con Windows 10 u 11. El mismo código corre en Mac y en
Windows; lo que cambia entre los dos sistemas está en `plataforma.py`.

> **Estado:** esta versión se adaptó y se revisó en un Mac. La transcripción y el sonido que usa
> Windows se probaron ahí, pero **el conjunto todavía no se ha corrido en un PC con Windows**. Si algo
> falla en el primer arranque, la sección "Si algo falla" dice qué mirar y qué texto copiar.

## Qué necesitas

- Un PC con Windows 10 u 11 de 64 bits, con cámara y micrófono (los del notebook sirven).
- **Python 3.12 de 64 bits**, desde <https://www.python.org/downloads/>. Al instalarlo marca la casilla
  **"Add python.exe to PATH"**.
- Una **clave de la API de Anthropic** propia (<https://console.anthropic.com>). Cada persona usa la suya.
- El robot (Arduino UNO) conectado por USB. Sin él también funciona: cámara, voz y boca en pantalla,
  solo que los ojos físicos no se mueven.
- Internet: para conversar con Claude y, la primera vez, para bajar el modelo que entiende la voz (~500 MB).

## Instalación (una sola vez)

1. Descomprime `RobotFace_windows.zip` en una carpeta **sin tildes ni espacios raros**, por ejemplo `C:\RobotFace`.
2. Crea en esa carpeta el archivo `clave_anthropic.txt` y pega dentro tu clave (una sola línea).
   Ese archivo es secreto: no lo compartas ni lo subas a ninguna parte.
3. Haz doble clic en **`instalar_windows.bat`**. Tarda varios minutos: crea el entorno de Python, instala
   las bibliotecas y descarga la voz del robot (unos 60 MB). No hay que instalar voces en Windows.
   Si el PC tiene tarjeta NVIDIA, además instala las bibliotecas de NVIDIA para Whisper (~1,5 GB), así
   entiende mejor y más rápido con el modelo grande, y ONNX Runtime con DirectML para detectar caras
   en la tarjeta a resolución completa. Si Windows pregunta por el antivirus o SmartScreen, elige "Más información → Ejecutar de todas formas".
4. (Opcional) Si tienes el robot conectado, abre **`probar_ojos.bat`**: los ojos deben hacer "feliz" y
   después "sorpresa".

## Uso

1. Doble clic en **`pagina.bat`**. Se abre el navegador en `http://localhost:8730`.
2. En la sección **Panel**, aprieta **Encender robot**. La primera vez Windows pide permiso para la
   cámara y el micrófono, y se descarga el modelo de voz (unos minutos).
3. Párate frente a la cámara: el robot despierta, saluda y conversa. Para apagarlo, **Apagar** en el panel.
4. Para cerrar todo, cierra la ventana negra de `pagina.bat`.

## Diferencias con la versión de Mac

| Qué | Mac | Windows |
|---|---|---|
| Voz del robot | Piper (`es_MX-claude-high`) | La misma: Piper (`es_MX-claude-high`) |
| Entender la voz | Whisper grande en la GPU de Apple | Whisper "small" en el procesador; con tarjeta NVIDIA usa el grande en la tarjeta |
| Detectar caras | Procesador, a 960 px | Procesador a 960 px; con tarjeta NVIDIA, en la tarjeta (DirectML) a 1280 px |
| Prioridad de los programas | Normal | "Por encima de lo normal" (no se traban si abres otras cosas) |
| Velocidad de respuesta | 2,5 a 3,3 s | Depende del PC; sin NVIDIA puede ser 1 a 2 s más lenta |
| Lanzadores | archivos `.command` | archivos `.bat` |

Ajustes útiles (variables de entorno, antes de abrir `pagina.bat`, o editando el `.bat` con `set NOMBRE=valor`):

- `ROBOT_PUERTO=COM5`: fija el puerto del Arduino si no lo encuentra solo.
- `ROBOT_WHISPER=base`: usa un modelo de voz más liviano (más rápido, se equivoca más). Otros: `tiny`, `small`, `medium`.
- `ROBOT_SIN_GPU=1`: no usa la tarjeta de video (ni para Whisper ni para detectar caras).
- Para la máxima potencia: el notebook **enchufado** y el plan de energía en **Alto rendimiento**
  (Configuración → Sistema → Energía). Con batería Windows frena el procesador y la tarjeta.
- En `hablar.py`, `VELOCIDAD_VOZ = 1.1` hace que hable más rápido y `TONO = 0.9` más grave.
- En `seguir.py`, `CAMARA = 1` elige otra cámara si toma la equivocada.

## El Arduino

El robot ya trae cargado el programa `OjosAnimados`. Solo hay que volver a cargarlo si se cambia el
Arduino o el código: abre `OjosAnimados/OjosAnimados.ino` con **Arduino IDE**, instala la biblioteca
"Adafruit PWM Servo Driver Library", elige la placa **Arduino UNO** y el puerto COM, y aprieta **Subir**.
Si Windows no ve el Arduino (clones con chip CH340), instala el driver CH340.

## Privacidad

- Las caras y la ropa que el robot aprende quedan **solo en este PC** (`caras_conocidas.json`,
  `personas.json`, `memoria_robot.json`). Este paquete viene vacío: no trae a nadie memorizado.
- Solo escanea una cara con permiso de la persona, y se le puede pedir que la olvide.
- No subas a GitHub ni compartas esos archivos, la clave, ni las fotos de la cámara.

## Si algo falla

- **La página dice "sin servidor":** la ventana de `pagina.bat` se cerró. Ábrela de nuevo.
- **No ve la cámara o no oye:** Configuración → Privacidad y seguridad → Cámara / Micrófono → permite las
  aplicaciones de escritorio. Cierra otros programas que usen la cámara (Teams, Zoom).
- **Los ojos no se mueven:** revisa el cable USB y prueba `probar_ojos.bat`. Si no encuentra el puerto,
  usa `ROBOT_PUERTO`.
- **No habla:** falta `modelos\voz_es.onnx` (se descarga al instalar): vuelve a abrir `instalar_windows.bat`.
  Mira `registro_hablar.txt`.
- **Cualquier otro error:** los archivos `registro_seguir.txt` y `registro_hablar.txt` de la carpeta
  guardan lo que pasó. Copia las últimas líneas (sin la clave) y mándaselas a quien te pasó el proyecto.
