# Logo, iconos y glifos

- **Logo:** vectorial, dibujado por código (`icons.py`) a cualquier tamaño (`logo_pixmap`,
  `splash_pixmap`, `app_icon`). Nunca un PNG suelto. El de Vision Driver, en `vision_driver.md`.
- **Glifos** (`icons._GLIFOS`): recarga, codigo, cubo, copiar, mas, menos, regla, segmentar,
  arriba/abajo, izquierda/derecha, pantalla_completa, encuadrar, volver, rotar, guardar, servidor,
  info, carpeta, candado/candado_abierto, enchufe_conectado/enchufe_desconectado. Se dibujan con
  `QPainterPath` y se recolorean con el tema: `IconButton`, `dibujar_glifo`, `glifo_pixmap`. Un glifo
  nuevo se añade ahí, no como imagen.
- Chevrons de desplegables y botones con menú: `ANCHO_CHEVRON` y `LADO_CHEVRON` de `style.py`.
- **Animación** (`anim.py`): 120 ms al pasar y 150 ms en fundidos, interpolando propiedades. Nunca
  `QGraphicsOpacityEffect` ni `QGraphicsDropShadowEffect`. Ninguna mientras
  `style.animaciones_activas()` sea falso.
- **Ventanas al abrir:** nada se abre como ventana suelta: un control sin padre no se hace visible
  (`show()` lo abriría un instante como ventana), y ningún programa externo abre consola.
- Esquinas por máscara (`mascara.py`) en visores 3D y en tablas o gráficas que pintan su propio
  fondo; en el resto, QSS.
- **Gráficas (pyqtgraph):** sin la «A» de autoajuste (`hideButtons()`); se ajustan con un
  `IconButton` `encuadrar` de 34 px anclado abajo a la izquierda con 14 px de margen, el mismo icono
  que en los visores.
- **Animaciones de apertura, carga, cierre y ventanas emergentes:** `animaciones.md`.
