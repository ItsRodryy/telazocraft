# Composición de pantallas

- **Formularios:** dos columnas iguales en un panel, separadas por `#separadorFormulario`.
  `QSizePolicy.Ignored` en horizontal y el mínimo común para que sean iguales. `QFormLayout`: rótulo a
  la izquierda, valor a la derecha.
- Un desplegable en una columna de `SpinBox` termina donde la caja de las cifras: reserva a su derecha
  `SEPARACION_BOTONES + ANCHO_BOTON`.
- Una casilla que desbloquea un campo va justo debajo de ese campo, en la columna del valor.
- Cada formulario enseña solo lo que se usa en él; lo que explica qué hace una pestaña va en su ayuda
  (al pasar el ratón), no en la pantalla. Pestañas con nombre de una palabra, en el orden de uso.
- Parejas que se leen juntas (rango mín/máx, ancho/alto) en **rejilla**: mínimo encima del ancho,
  máximo encima del alto.
- Un control suelto junto a una rejilla de dos filas va a la altura de la primera fila.
- Grupos distintos de una misma barra se separan con `#separadorFormulario`.
- Paneles hermanos en una fila miden lo mismo. Las acciones de un bloque van juntas y bajo su rótulo.

## Pantalla de trabajo con visor (13/10/2026)

- **Dos columnas:** a la izquierda, la barra de herramientas (un panel, lo más bajo posible para dejar
  alto al visor) y debajo los visores; a la derecha, el **panel lateral de arriba abajo**, desde la
  altura de la barra hasta abajo, con `SEPARACION_PANELES` de hueco. El lateral tiene ancho fijo,
  suficiente para que sus filas quepan enteras; lo pierden los visores.
- Si la pantalla tiene pestañas (vivo / 3D…), cada una trae su lateral y la columna derecha enseña el
  de la pestaña activa: la barra no cambia de ancho al cambiar de pestaña.
- **Si no cabe, se recoloca, no se recorta:** con la ventana estrecha, la barra vuelve a ocupar todo el
  ancho y el lateral empieza debajo. Las acciones de la barra (capturar, carpeta, cancelar) van arriba a
  la derecha, en la fila de los controles; solo bajan a una fila propia si no caben.
- Dentro del lateral: título del panel, los datos, un `#sep`, el título del siguiente bloque y lo
  largo en un `scrollEnPanel` que es lo primero que cede alto; los botones de ese bloque, fijos al
  pie, fuera del scroll.

## Ventanas

- **Barra superior global:** tres zonas; estado a la izquierda, lo que se gestiona en el eje real de
  la ventana (laterales igualados) y las acciones globales pegadas al margen derecho. Lo que aparece o
  desaparece reserva su hueco; lo que cambia de texto tiene ancho fijo.
- **Ventana emergente de trabajo** (ver un resultado, marcar sobre una imagen): `VentanaBase` con
  `cabecera_app`, el visor a la izquierda y un lateral con scroll a la derecha (tarjeta con rótulo,
  controles y resultados), acciones en el pie y al 80 % de la pantalla. Los grises de texto
  enriquecido salen de `tema_actual().texto_tenue`, no de un color fijo.
- **Asistente** (varios requisitos que preparar): `VentanaBase`, una tarjeta por elemento con su
  `CheckBox` en negrita y, debajo, cada requisito con `PuntoEstado`; pie con la acción secundaria a la
  izquierda y «Ahora no» + la acción principal (`aplicar`) a la derecha; el trabajo en un
  `DialogoProceso`.
- **Tamaños:** todo cabe sin recortes a 1080 × 720 (`test_sin_recortes`); las pantallas de trabajo,
  sin scroll a 1920 × 1080.
- Estilos en código: solo en `style.qss()`. Un `setStyleSheet` suelto solo para anular algo puntual,
  nunca para poner un color.
