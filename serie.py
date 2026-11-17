# Envía órdenes al Arduino por serie y muestra las respuestas (funciona en Mac y Windows).
# Uso: python serie.py "orden1" "orden2" ...     Ejemplos: "E 7" (feliz), "M 50 0" (mirar), "D" (diagnóstico),
#      "espera 2" (pausa de 2 segundos entre órdenes)
import sys, time
import serial
import plataforma

PUERTO = plataforma.puerto_arduino()
if PUERTO is None:
    sys.exit("No encuentro el Arduino: revisa el cable USB")
arduino = serial.Serial(PUERTO, 115200, timeout=0.05)


def leer(segundos, hasta_linea=False):
    # Con hasta_linea, vuelve en cuanto llega una respuesta completa
    fin, datos = time.time() + segundos, b""
    while time.time() < fin:
        datos += arduino.read(1024)
        if hasta_linea and datos.endswith(b"\n"):
            break
    return datos.decode(errors="replace")


print(leer(2.5), end="")  # al abrir el puerto el Uno se reinicia
for orden in sys.argv[1:]:
    if orden.startswith("espera"):
        time.sleep(float(orden.split()[1]))
        continue
    arduino.write((orden + "\n").encode())
    print(leer(0.6, hasta_linea=orden != "c"), end="")
arduino.close()
