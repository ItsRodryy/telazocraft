# Telazocraft 0.2.1

Tema oscuro gris. Marca T con dos trazos redondeados y el degradado del acento; mismo dibujo en
ventana, bandeja e ICO. Cinco vistas: Inicio, Jugadores, Mods, Copias y Ajustes; engranaje Telazocraft
al pie. Bajo 1080 px, navegación con iconos y tooltip. Consola inferior desplegable, altura y estado
recordados. No hay pantallas separadas de consola, rendimiento, diario o sistema.

Botones semánticos por propiedad QSS: ok, peligro, aviso, principal. Todo cambio de servidor tiene
confirmación antes→después y Cancelar predeterminado; Iniciar no pregunta, Parar solo con jugadores.
Los ajustes conservan borradores y una barra de cambios sin aplicar. Listas por eventos y watcher
con antirrebote; sin actualización manual. Acciones secundarias en menús por fila. Caches locales
para iconos y cabezas, con sustitutos si falla la red. El historial se importa sin editar identidades.

Paneles y controles genéricos de esta guía, ventanas VentanaBase con fundido y progreso en
DialogoProceso. Interfaz en español por tr(); nombres de jugadores, mods y servidores son datos.
Operaciones de edición y red fuera del hilo de interfaz. La X oculta en bandeja; Salir guarda y
copia antes de liberar el bloqueo. Capturas a 1400×900 y 1000×700 y pruebas de regresión.
