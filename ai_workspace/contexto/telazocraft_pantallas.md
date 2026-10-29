# Telazocraft — pantallas 0.3.1

Actualizado el 2026-10-27. Arquitectura: `telazocraft.md`; guía pública en docs/estilo del repo.

Tema oscuro gris y T rellena Arial Rounded, contorno incorporado con cinco variantes opcionales.
Misma marca en ventana, bandeja, accesos, EXE e instalador. Ventana centrada, sin pantalla completa;
emergentes centradas en el monitor de la app. Cinco vistas; no hay una sexta página de sistema.

## Armazón

Barra superior: logo, selector con estado, ＋, estado, Iniciar/Parar/Reiniciar en verde/rojo/ámbar.
Abrir nunca arranca servidores. Iniciar otro queda desactivado si hay uno activo.
Lateral: Inicio, Jugadores, Mods, Copias, Ajustes; bajo 1080 px solo iconos con tooltip.
Engranaje inferior abre VentanaBase con versión, actualizaciones, Playit/Syncthing/Java y biblioteca.
Consola inferior desplegable con búsqueda, seguimiento, historial y altura recordada; 5.000 líneas.
Avisos temporales y barra verde por fases o bytes; espera indeterminada si no es medible.

Botones y campos de una fila a 36 px; carpeta y ⋯ cuadrados. Mano en elementos interactivos,
incluidos los creados después; textos mantienen cursor de edición y cabeceras el de redimensionar.
Pestañas y tablas con contorno redondeado, combos/popups, menús, tooltips y campos coherentes.
Cambios con confirmación antes→después y Cancelar predeterminado; Iniciar no pregunta y Parar
solo con jugadores. La X oculta en bandeja; Salir guarda y copia antes de cerrar.

## Vistas

1. Inicio: ficha de servidor, acceso, dirección copiable, último uso y tamaño en caché. Conectados
   con cabeza; cifras de jugadores, horas jugadas globales, horas encendido, mods y última copia.
   Últimas partidas: las vivas primero, «jugando» y duración; actualización por eventos y minuto.
   CPU/RAM/TPS a tres anchos iguales, alto fijo, ejes y valor actual. Se miden desde el arranque;
   Inicio dibuja mientras es visible. Contenido desplazable para pantallas pequeñas.
2. Jugadores: Lista/Actividad en pestañas píldora, tablas de ancho completo. Horas de sesiones
   históricas y actuales, unidas por nick sin modificar UUID o personajes. Permisos en chips;
   acciones en ⋯ y añadir whitelist. Actividad filtrable, fecha legible y duración.
3. Mods: inventario automático e iconos, lado y actualización; ＋ Añadir mod y Paquete para amigos
   con carpeta. Búsqueda al escribir, 300 ms, compatibilidad MC/loader y marca Instalado.
   Texto «Resultados de Modrinth para <MC> <loader>». JAR manual y dependencias; cambios parados.
4. Copias: tarjetas por fecha/tipo/tamaño y menú para abrir/restaurar; Copia ahora. Restaurar
   confirma qué se pierde y archiva lo sustituido. Las pruebas nunca restauran la biblioteca real.
5. Ajustes: General, Mundo/Chunky, Acceso, Copias, Hardcore y Extras de cliente. Campos propios
   sin rueda; borrador por servidor y barra Descartar/Aplicar. Acceso advierte de la migración.

## Nuevo servidor

Cinco pasos: tipo/versión o copiar sin mundo; mods/compatibilidad; nombre/semilla/hardcore;
acceso/whitelist; resumen/EULA/Java y opción de crear paquete. Carga de versiones visible,
errores con Reintentar, sin edición libre; NeoForge estable más nuevo filtrado por MC.
Progreso dentro de la ventana; nunca arranca el servidor creado. Servidores nuevos sin extras
predefinidos. Servidor de prueba vanilla ofrecido únicamente al crear biblioteca vacía.

## Paquete y aceptación

Disponible en Mods y bandeja. ZIP con carpeta mods, extras, instalador NeoForge verificado,
Instalar.bat, ayudante PowerShell y LEEME para launcher oficial/TLauncher y vuelta atrás.
Conserva tres; anteriores archivados. Vanilla sin NeoForge. La biblioteca no se modifica.
Capturas reales de todas las vistas y asistente a 1400×900/1000×700 revisadas en TEMP;
las del README usan biblioteca ficticia, sin datos reales. 57 pruebas y smoke correctos.
