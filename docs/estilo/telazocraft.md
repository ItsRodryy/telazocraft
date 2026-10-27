# Telazocraft 0.3.1

Tema oscuro gris. T rellena de Arial Rounded MT Bold con contorno vectorial incorporado, trazo
suavizado y degradado del acento; mismo dibujo en ventana, bandeja, ejecutable, ICO multirresolución
e instalador. AppUserModelID ItsRodryy.Telazocraft. Cinco vistas: Inicio, Jugadores, Mods, Copias y Ajustes; engranaje Telazocraft
al pie. Bajo 1080 px, navegación con iconos y tooltip. Consola inferior desplegable, altura y estado
recordados. El engranaje abre una VentanaBase; no es una sexta página.

Botones semánticos por propiedad QSS: ok, peligro, aviso, principal. Todo cambio de servidor tiene
confirmación antes→después y Cancelar predeterminado; Iniciar no pregunta, Parar solo con jugadores.
Los ajustes conservan borradores y una barra de cambios sin aplicar. Listas por eventos y watcher
con antirrebote sin vigilar logs. Lecturas pesadas en trabajadores, caché por servidor y solo la
vista visible se repinta. Acciones secundarias en menús por fila. Cachés locales
para iconos y cabezas, con sustitutos si falla la red. El historial se importa sin editar identidades.

Paneles y controles genéricos de esta guía, ventanas VentanaBase con fundido y progreso en
DialogoProceso. Interfaz en español por tr(); nombres de jugadores, mods y servidores son datos.
Controles de una fila a 36 px; iconos de carpeta y ⋯ cuadrados. Cursores de mano también en
controles creados después. Tablas y emergentes recortan su contorno redondeado; pestañas sin
fondo rectangular. Gráficas a tres partes iguales, con ejes, valor y altura fija. Progreso verde
por bytes, archivos o fases conocidas; indeterminado solo durante trabajo no medible.
Sesiones vivas arriba y contador por minuto. Horas por unión de intervalos de diario y logs,
sin duplicados. Búsqueda Modrinth con 300 ms de antirrebote y descarte de respuestas antiguas.
Operaciones de edición y red fuera del hilo de interfaz. La X oculta en bandeja; Salir guarda y
copia antes de liberar el bloqueo. Capturas a 1400×900 y 1000×700 y pruebas de regresión.
