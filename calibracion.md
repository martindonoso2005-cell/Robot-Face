# Calibración del mecanismo de ojos

PCA9685 en I2C 0x40. Pulsos 600–2400 µs (0–180°), 50 Hz. Fuente V+ 5 V.
Valores en uso en `OjosAnimados.ino` (recalibrado en noviembre de 2026).

| Canal | Parte                     | Centro | Abierto | Cerrado | Sentido para abrir |
|-------|---------------------------|--------|---------|---------|--------------------|
| 0     | Párpado inferior derecho  | 90     | 55      | 138     | bajar ángulo       |
| 1     | Párpado superior derecho  | **115** | 165    | 70      | subir ángulo       |
| 2     | Ojos arriba/abajo         | **95** | abajo 0 | arriba 180 | bajar = abajo. Abajo: párp. sup. ≤90. Arriba: párp. inf. a 110/70 |
| 3     | Párpado inferior izquierdo| 90     | 140     | 30      | subir ángulo       |
| 4     | Párpado superior izquierdo| 90     | 40      | 135     | bajar ángulo       |
| 5     | Ojos izquierda/derecha    | 90     | der. 40 | izq. 130| bajar = su derecha |

- Los párpados superiores van en espejo: abren 50° y cierran 45° desde su centro.
- El servo del párpado superior izquierdo es más lento: el parpadeo dura ~330 ms (`PASO_PARPADO = 0.06`).
  Con ~220 ms ese párpado casi no se movía.
- Para mover servos sueltos se carga `OjosCalibracion` (órdenes `c` y `<canal> <ángulo>` por `serie.py`).
