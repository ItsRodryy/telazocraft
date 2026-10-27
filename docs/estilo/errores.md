# Errores ya vistos

| Síntoma | Causa | Se evita con |
|---|---|---|
| rectángulo oscuro dentro de un panel o la barra | `QWidget` sin nombre hereda el fondo | `style.agrupador()`; `test_agrupadores` |
| panel que no se ve como panel | `QWidget` llamado `panel` | `QFrame` o `style.tarjeta()` |
| controles sueltos; esquina curva dentro de una recta | contenido fuera de paneles; caja de pestañas | regla de los paneles; `test_paneles` |
| asa o esquina cuadrada | radio mayor que medio lado | radios derivados; `test_aspecto_paneles` |
| franja negra como separador | `QFrame.VLine` nativo | `#separadorFormulario` / `#sep` |
| casilla gris sin tic, flechas de Windows | control de Qt pelado | controles propios; `test_controles_numericos` |
| un valor cambia al desplazar la página | rueda sobre un control | controles `SinRueda` |
| texto cortado | fila sin plan B o barra demasiado llena | `FilaFlexible`, elidir, compactar; `test_sin_recortes` |
| lateral cortado por la derecha | ancho a ojo menor que el contenido | ancho = mínimo del contenido + scroll |
| el dominio salta o no está centrado | anchos variables a los lados | zonas iguales, huecos reservados; `test_barra_estable` |
| icono gris sobre blanco tras cambiar de tema | `QIcon` ya pintado | `IconButton` + glifos |
| esquina rayada | máscara de 1 bit | QSS con radio |
| tarjeta cortada en seco sobre otro bloque | scroll sin transición | `DifuminadoInferior` |
| «Preparando…» asomando entre paneles | vista perezosa lo borraba tarde | se oculta al sustituirlo |
| bloque oscuro en un grupo con título | `QGroupBox` con fondo | QSS sin caja |
| bloque oscuro de esquinas rectas dentro de un panel con scroll | el viewport y el contenido del scroll pintan fondo | `QScrollArea#scrollEnPanel` y contenido `agrupador` |
| casillas que desaparecen, cajas de números cortadas en un lateral | las filas piden más ancho del que hay (rótulo largo + caja) y Qt aprieta | ancho del lateral suficiente y rótulos cortos cuando el subtítulo ya da contexto |
| títulos que no se distinguen del resto | `tituloPanel` sin regla de estilo | jerarquía de `tema.md` |
| barra recortada al poner un lateral de arriba abajo | a 1080 px la barra no cabe al lado | recolocar: la barra a todo el ancho y el lateral debajo |
| vídeo congelado sin explicación | la última imagen se queda y nadie avisa | velo «Sin imagen» mirando si la imagen cambia (`superficies.md`) |
