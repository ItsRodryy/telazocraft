# Superficies

**Regla de los paneles:** todo el contenido de una pantalla va dentro de un panel redondeado, con
`SEPARACION_PANELES` de aire hasta el borde y hasta los vecinos. Nada suelto sobre el fondo, ningún
panel pegado a un borde ni dentro de una caja recta. Las barras de herramientas de una pantalla son un
panel más, no una franja de lado a lado. Lo vigila `test_paneles.py`.

| Pieza | Cómo |
|---|---|
| página | `#page`, `#central`, `#stack`: color `fondo` |
| panel | `QFrame#panel` (nunca `QWidget`: no se pinta). `style.tarjeta(*widgets)` |
| página con scroll sin paneles propios | `desplazable(widget, tarjeta=True)` |
| **scroll dentro de un panel** | `QScrollArea#scrollEnPanel`: ni el viewport ni su contenido pintan fondo; se ve el del panel, sin bloque oscuro de esquinas rectas. Su contenido, `agrupador`. La barra vertical lleva su pista en `fondo` con las esquinas redondeadas (`r_pista_scroll`, medio ancho) y el contenedor de Qt transparente: sin eso se veía una franja oscura recta (decisión del usuario, 14/10/2026) |
| grupo dentro de un panel | subtítulo `grupoParametros` y sus filas, sin caja; o `QFrame#panelSuave` (fondo `superficie_alta`, sin borde) si de verdad hace falta separarlo. Nunca panel dentro de panel |
| `QGroupBox` | sin caja ni fondo, título en negrita |
| pestañas | sin caja (`QTabWidget::pane` transparente); píldoras sueltas |
| barra superior | `QFrame#topbar` en tres zonas (ver `composicion.md`) |
| agrupador de layout | `style.agrupador()`: transparente. **Todo** `QWidget` contenedor dentro de un panel (filas, grupos, el contenido de un scroll) lleva ese nombre; sin él pinta un rectángulo oscuro |
| separador horizontal | `QFrame#sep` (1 px, `borde_sutil`) |
| separador vertical entre grupos o columnas | `QFrame#separadorFormulario` (2 px, primer plano al 32 %) |
| tabla, consola, visor | son su propia caja: van fuera de los paneles, no dentro. Una tabla o gráfica que pinta su propio fondo va en un `QFrame#panel` con `instalar_mascara`: si no, asoman picos por las esquinas redondeadas |
| final de lista con scroll sobre otro bloque | `DifuminadoInferior(area)` |
| lateral de datos junto a un visor | ancho fijo y suficiente para que sus filas quepan enteras; lo largo, a un scroll dentro del panel |

Nunca `QFrame.VLine/HLine` sin nombre: usa colores nativos.

## Velos: «aquí no se puede trabajar» y «no llegan datos» (13/10/2026)

Mismo aspecto en los dos: negro al `ALFA_VELO` y el texto centrado en blanco, título 18 px y negrita,
detalle debajo en tamaño normal.

- **Pantalla que no puede trabajar** (le falta el recurso del que depende: una cámara, una conexión…):
  `app/widgets/capa_bloqueo.py::CapaBloqueo`, hija de la pantalla o de la página que tapa. Deja pasar
  el ratón: se puede seguir mirando y desplazándose; quien la usa bloquea sus propias acciones. Lo que
  no necesita el recurso (un comparador, datos guardados) no lleva velo.
- **Visor que deja de recibir imagen** (3 s sin imagen nueva): `ImageViewer.velo` oscurece la última
  imagen y pone «Sin imagen · reintentando» con el motivo debajo; en un visor 3D, `CapaBloqueo` sobre
  la celda. Se quita solo al volver la imagen. Se decide mirando si la imagen cambia, no esperando a
  que el proceso que la produce avise: si ese proceso se cuelga, no avisa.
- **Recurso desconectado a mano** no lleva velo: enchufe y motivo en naranja (`desconectada`) en el
  propio visor, sobre su fondo.
