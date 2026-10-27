# Llevarse el diseño a otro programa

El diseño de Vision Driver es un sistema, no una colección de pantallas: un tema que genera una sola
hoja de estilo, controles propios que sustituyen a los de Qt, un armazón de ventana y unas pruebas que
lo vigilan. Para que otro programa PySide6 se vea y se comporte igual, se copian esas piezas y se
siguen las reglas de esta guía (todo salvo `vision_driver.md`).

## Qué se copia tal cual (genérico)

| Pieza | Fichero | Qué da |
|---|---|---|
| Tema | `app/style.py` | 12 tonos × claro/oscuro, roles de color, medidas, radios, la hoja de estilo entera (`qss`), `tarjeta`, `agrupador`, `margen_panel`, el bus de cambio de tema |
| Iconos | `app/icons.py` | glifos vectoriales recoloreables y el dibujo del logo (cambiar el logo) |
| Interacción | `app/interaction.py` | cursores de mano, centrado de ventanas en su monitor |
| Controles | `app/widgets/`: `animated_button`, `icon_button`, `spin_box` (`SpinBox`, `ComboSinRueda`), `check_box`, `toggle`, `linea_guia`, `etiqueta_elidida`, `fila_flexible`, `scroll`, `difuminado`, `mascara`, `anclaje`, `estado_punto`, `status_badge`, `tabla_datos`, `path_panel`, `boton_carpeta`, `ayuda_flotante`, `confirmacion`, `capa_bloqueo`, `cargando`, `busy_indicator`, `log_view`, `image_viewer`, `viewer_grid` | los controles de `controles.md` |
| Ventanas y animación | `app/widgets/anim.py`, `fundido.py`, `dialogo_proceso.py` (`VentanaBase`, `DialogoProceso`), `gotas.py` | fundidos, ventanas emergentes, trabajos largos, aparición y cierre de la ventana |
| Armazón | `app/main_window.py` (barra lateral + pila de vistas), `app/vista_perezosa.py`, `app/panel_protocol.py`, `app/dominio_registry.py`, `app/editor_pendiente.py`, `app/qt_app.py` | navegación por dominios, vistas que se construyen al usarlas, avisos a las vistas (`set_worker`, `detener`, `resolver_pendientes`…), editar y aplicar |
| Textos | `common/i18n.py` + un `i18n_en.py` propio | `tr`, `marcar`, `tr_mensaje`; interfaz en español o inglés |
| Pruebas de diseño | `tests/comun/test_paneles.py`, `test_agrupadores.py`, `test_controles_numericos.py`, `test_aspecto_paneles.py`, `test_sin_recortes.py`, `test_barra_estable.py`, `test_traduccion.py` | que nada quede suelto, recortado, con controles de Qt pelados o sin traducir |

## Qué NO se copia (propio de Vision Driver)

Cámaras y dominios (`lectoras/`, `volumen/`, `camera_pool`, `camera_selector`, `domain_selector`,
`asistente_camaras`, `roi_viewer`, `rate_indicator`), instalador y versiones (`setup_wizard`,
`start_dialog`, `update_dialog`, `versiones`, `sesion_github`, `desinstalador`, `crear_instalador`) y
las decisiones de `vision_driver.md`. Sirven de ejemplo de cómo se aplica la guía, no de base.

## Pasos

1. Copiar las piezas genéricas en el paquete del programa nuevo (`<paquete>/app/…`,
   `<paquete>/common/i18n.py`) y ajustar los imports relativos.
2. Cambiar el logo en `icons.py` y, si se quiere, el tono por defecto en `style.py`.
3. Crear la aplicación con `qt_app.crear_app()` y la ventana con el armazón; cada área del programa es
   un «dominio» que registra sus vistas (como `lectoras/dominio.py` y `volumen/dominio.py`).
4. Construir cada pantalla con paneles (`style.tarjeta`), agrupadores, títulos `tituloPanel` y los
   controles propios; nunca `QPushButton`, `QSpinBox`, `QComboBox`, `QCheckBox` ni `QSlider` pelados.
5. Pasar todo texto de pantalla por `tr()` y mantener su catálogo inglés.
6. Copiar las pruebas de diseño y tenerlas en verde.
7. Llevar la guía: copiar esta carpeta `estilo/` sin `vision_driver.md` y escribir el anexo del
   programa nuevo con sus decisiones.

## Para que siga siendo reutilizable

- Una pieza genérica no importa nada de un dominio ni nombra cámaras.
- Lo que valdría en cualquier programa se escribe en la guía general; lo concreto, en el anexo.
- Si en el futuro se quiere compartir sin copiar, el paso siguiente es mover las piezas genéricas a un
  paquete propio (p. ej. `code/vd_ui/`) que importen los dos programas. Hoy no está hecho
  (decisión del usuario, 13/10/2026: primero la guía).
