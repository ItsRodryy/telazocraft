# Animaciones

**Norma:** toda ventana emergente aparece y se va con un fundido. Un diálogo nuevo hereda de
`VentanaBase` (o de `ConFundido` delante de `QDialog`); no se crea un `QDialog` pelado. Todo se
apaga con Interfaz → «Animación» y con `style.animaciones_activas()` en falso, y nada se anima sin
pantalla (pruebas).

**Antes de animar algo nuevo, se parte de lo que ya hay.** No se rehace de cero lo que está hecho
y validado con el usuario:

| Qué | Dónde | Para qué sirve |
|---|---|---|
| Pasar el ratón, fundidos cortos | `app/widgets/anim.py` | 120 ms al pasar, 150 ms en fundidos, interpolando propiedades |
| Ventanas emergentes | `app/widgets/fundido.py` | Filtro de la aplicación que funde la aparición de todas (200 ms); `ConFundido` desvanece antes de cerrar; `animar(ventana, desde, hasta)` |
| Avisos de Qt (`QMessageBox`) | `app/widgets/fundido.py` (`desvanecer_y_esperar`) | Se van también con fundido, incluidos los de `QMessageBox.question/warning/…`: el filtro se engancha a `buttonClicked` y a la X sin tocar cada llamada; mientras se desvanecen no aceptan clics ni teclas |
| Espera corta sin porcentaje | `app/widgets/cargando.py::IndicadorCarga` | Arco de acento que gira sobre su pista `borde` (una vuelta por segundo) mientras se pregunta a GitHub en el inicio; se ve al menos 0,6 s, y en la instalada oculta el botón hasta tener respuesta (06/10/2026) |
| Ventana principal | `app/widgets/gotas.py::fundido_ventana` | Aparece de menos a más al terminar la carga; se desvanece al cerrar |
| Carga del programa | `app/widgets/gotas.py::Escena` + `tools/escena_carga.py` | Contorno del logo que se rellena con olas según el progreso real, **en un proceso aparte** (`Ayudante`) para que vaya fluido aunque el programa esté construyendo |
| Propuestas de estilo | `animaciones/propuestas_carga.html` | Galería vectorial de 12 animaciones (remolino con gotas con forma de gota, llenado, burbujas, tinta), en el navegador. El usuario eligió «Llenado 2» sin chorro |

Lecciones que ya costaron:

- **Algo que se anima mientras el programa construye su interfaz va a trompicones**: el hilo de Qt
  no puede pintar. Se pinta en otro proceso (como la carga) o después de construir.
- **El logo final lo dibuja la propia animación**, nunca se cambia a una imagen del logo: el cambio
  se nota como un corte.
- **Nada de chorros, rayas o líneas encima del logo**: se ven como un fallo. Tampoco nada que se
  mueva de lado a lado sin sentido.
- Un control sin padre al que se le hace `show()` aparece como ventana suelta un instante:
  parpadeo. Se enseña cuando ya está en su pantalla.
- **El clic de un `QMessageBox` no pasa por `done()`**: Qt lo cierra por dentro, así que
  `ConFundido` no le sirve. Se espera al fundido dentro de `buttonClicked`, que llega justo antes
  del cierre. Comprobado en pantalla el 01/10/2026: ~210 ms hasta opacidad 0, con botón y con la X.
- Se mide antes de decir que va fluido: `VISION_DRIVER_MEDIR_ESCENA=<fichero>` guarda los
  intervalos entre fotogramas de la carga (objetivo: ninguno por encima de 33 ms).
