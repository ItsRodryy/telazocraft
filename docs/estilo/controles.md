# Controles

| Necesidad | Se usa | Nunca |
|---|---|---|
| botón de texto | `AnimatedButton` | `QPushButton` (excepción: muestras de color) |
| acción principal | `AnimatedButton` con `capturar` (ancho), `pasada` o `aplicar` | colorear a mano |
| botón de icono | `IconButton(glifo, tooltip)`, 30 × 30 | `QIcon` de PNG |
| abrir carpeta | `BotonCarpeta(proveedor, tooltip)`, cuadrado del alto del botón vecino | `explorer`/`xdg-open` |
| número | `SpinBox`, `compactar()` (88 px) si el valor es corto | `QSpinBox`, `QDoubleSpinBox` |
| lista | `ComboSinRueda` (chevron propio) | `QComboBox` |
| casilla de formulario | `CheckBox` (tic vectorial) | `QCheckBox` |
| ajuste inmediato sí/no | `Toggle` (interruptor animado) | `CheckBox` |
| opción excluyente | `QRadioButton` (QSS, círculo) | — |
| deslizador | `SliderSinRueda` (carril 4 px, asa circular 14 px) | `QSlider` |
| texto que puede no caber | `EtiquetaElidida` | `QLabel` que empuja |
| fila de botones | `FilaFlexible` | `QHBoxLayout` que aplasta |
| rótulo lejos de su valor | `FilaGuiada`/`LineaGuia` | hueco vacío |
| buscar en una lista | `QLineEdit` **sin rótulo al lado**: lo que busca va dentro, como texto de ayuda; mismo ancho y alto que el control de encima; el contador de coincidencias fuera de la caja | «Buscar:» delante |
| rutas | `PathPanel(entradas, descripcion)` | rutas sueltas |
| tabla de solo lectura | `TablaDatos` | `QTableWidget` a mano |
| estado | `PuntoEstado`/`StatusBadge` (operativa, simulación, trabajando, fallo, inactiva, desconectada) | colores sueltos |
| trabajo largo | `DialogoProceso` | consola embebida |
| ayuda de un ajuste | `AyudaFlotante` o tooltip | párrafos bajo el campo |
| menú de selección | `CameraSelector`/`DomainSelector` | `QMenu` sin estilo |
| botones sobre un visor | `AnclaEsquina` + agrupador | `move()` a mano |
| pantalla que no puede trabajar | `CapaBloqueo` (`superficies.md`) | apagar control a control sin decir por qué |

Todos los controles de valor ignoran la rueda del ratón. `test_controles_numericos.py` falla si una
pantalla monta `QSpinBox`, `QDoubleSpinBox`, `QComboBox`, `QSlider`, `QCheckBox` o `QPushButton`.

## Estados

- Entradas: planas (`superficie_alta`); borde `borde` al pasar; borde `acento` con foco; texto tenue
  deshabilitadas.
- Botones: al pasar, fondo `acento_hover` y texto `sobre_acento`; deshabilitados, `borde_sutil`.
- Casillas y radios marcados: `acento`.
- Pestañas: píldora; la activa en `acento`.
- Scroll: sin pista ni flechas; asa de 4 px que pasa a 8 al pasar y a `acento` al arrastrar.
- Slider: sin fondo; carril `borde`, recorrido `acento`, asa `texto_fuerte`.
- Menús: `superficie_opaca`, radio `R_PANEL`, elegido en `acento`.
- Variantes por propiedad dinámica (`[pendiente]`, `[compacto]`), repolish tras cambiarlas.
- Un aviso que no impide seguir (la medida vale, pero ojo): un párrafo al final en `aviso` (ámbar),
  sin pastilla ni icono.

## Editar y aplicar (13/10/2026)

Patrón para cualquier lista de ajustes que cambia algo de fuera (un dispositivo, una configuración):

- **Nada se aplica al tocarlo.** Lo cambiado queda pendiente y su rótulo pasa a `acento` y negrita
  (`QLabel#rotuloParametro[pendiente="true"]`). Mientras está pendiente, el refresco no lo pisa.
- Botones: «Valores originales» (deja pendiente lo que había la primera vez, pregunta antes),
  «Restablecer» (vuelve a lo aplicado) y «Aplicar» (`aplicar` con `[pendiente]`: tenue sin cambios,
  acento con cambios). En una fila si hay ancho; en un lateral estrecho, «Valores originales» a todo
  el ancho y los otros dos debajo.
- «Aplicar» manda todo junto, en un orden que funcione (primero lo que habilita a lo demás, como un
  modo automático); el valor pedido se enseña hasta que se confirma o pasan unos segundos.
- Un valor por cosa: lo aplicado en un sitio es lo que enseñan todos los demás, y se recuerda.
- **Salir con cambios sin aplicar** (cambiar de pantalla, cerrar): ventanita con «Aplicar» /
  «Descartar» / «Cancelar»; al cambiar de elemento (otra cámara), sin «Cancelar». Si no se puede
  aplicar (sin conexión), no se ofrece «Aplicar». Gancho `resolver_pendientes` de
  `app/panel_protocol.py`; modelo en `app/editor_pendiente.py` o `volumen/widgets/panel_camara.py`.
- Lo protegido (lo que nunca se debe cambiar) sale en solo lectura y con su aviso.

## Preguntas y ventanas

- **Nada encima de nada** en flujos de varias páginas (versiones, SDK): una sola ventana que cambia
  de página sin moverse de su centro; «Volver» y Escape regresan. Las confirmaciones de esos flujos
  van en un recuadro dentro de la ventana (`widgets/confirmacion.py::Confirmacion`): texto y dos
  botones; el de sí dice la acción («Instalar la 7.0.1», «Reiniciar ahora»); en lo destructivo o
  hacia atrás, el foco va a «Cancelar».
- Una pregunta que interrumpe otra acción (salir con cambios sin aplicar) sí es una ventanita
  (`QMessageBox`), con el fundido de siempre.
- **Ventanas emergentes centradas:** toda ventana emergente sale en el centro de su monitor (el de
  la ventana de la que sale; sin ella, el principal), por el filtro de `widgets/fundido.py`. Una que
  no deba centrarse lleva la propiedad `sin_centrar`.
- **Final de un trabajo largo:** la barra de `DialogoProceso` se para siempre (llena si salió bien) y
  el mensaje final va en la misma ventana: bien → `QLabel#mensajeOk` (verde `ok_claro`, negrita) con
  el resultado y, debajo, qué hacer ahora; mal → `QLabel#avisoPeligro` y el detalle abierto.
- **Lo que se perderá si se sigue:** `QLabel#avisoPeligro` (color `peligro`, sin relleno, negrita)
  debajo de la casilla que lo provoca.
- **Idioma:** `ComboSinRueda` «Idioma» con cada idioma en su idioma. No pasa por «Aplicar»: al
  cambiarlo, un `Confirmacion` («Reiniciar ahora» / «Ahora no»). «Ahora no» devuelve el desplegable
  al idioma en uso y no guarda nada.

Lo concreto de cada pantalla de Vision Driver (asistente de SDK, desinstalador, versiones, cámaras):
`vision_driver.md`.
