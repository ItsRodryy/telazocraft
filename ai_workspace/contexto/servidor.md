# Servidor Lepazo Vice

Hechos comprobados el 2026-10-27. Biblioteca migrada y Telazocraft 0.3.1 instalado.

- Biblioteca: `biblioteca/` dentro de la app (rutas de abajo, relativas a ella). Servidor normal: servidores/lepazo/ (NeoForge 21.1.233, Minecraft 1.21.1, 96 mods, Java 21, heap 10 GB).
- Metadatos: telazocraft.json y servidores/lepazo/servidor.json. El modo.ini anterior está archivado.
- Arranque: acceso directo Telazocraft. Consola instalada: %LOCALAPPDATA%/Programs/Telazocraft/python/python.exe -m telazocraft --biblioteca RUTA --consola lepazo. stop guarda, detiene y crea copia de sesión; Ctrl+C solicita parada segura. Gestor antiguo archivado en archivo/pre_app/emergencia/. Reinicio cada 2 h y apagado tras 10 min vacío después de la primera entrada.
- Copias: copias/lepazo/locales/ (4), compartidas/ (sesión 3, diarias 5). Rotadas a archivo/copias_rotadas/; no se destruyen los ZIP anteriores.
- Hardware, testigo, lock, Playit y guardia: compartido/. Clave local en sync_guardia.local.ini: nunca imprimirla ni copiarla al repo.
- Identidad: online-mode=false, whitelist activa con 7 UUID offline, ops vacío. Conservada.
- Hardcore vanilla 1.21.1 retirado a archivo/hardcore_1.21.1/. Nuevo servidores/hardcore/: Minecraft 26.3, NeoForge 26.3.0.99, JDK 25; JEI, Jade, AppleSkin, Sophisticated Backpacks, Lithium, FerriteCore, Chunky, Terralith y tres dependencias. Acceso abierto, whitelist de Lepazo, ops vacío.
- Syncthing: carpeta `lepazo-vice-server` = `biblioteca/`; .stignore incluye stignore_comun.txt. Portátil conectado desde el 29/10: pendiente comprobar su .stignore (ver ESTADO.md). No pausar ni reanudar dispositivos sin orden del dueño.
- Prueba bloque 1 sobre copia: Done/list/stop y dos ZIP verificados. Originales apartados y devueltos por traslado; level.dat y personaje conservan hashes del manifiesto. La ejecución de prueba quedó en archivo/pruebas_app/ejecucion_bloque1/.
- Ryzen 7 5800X, 32 GB, RTX 3060. BSOD RAM/XMP previos: pendiente BIOS/MemTest86.

- Telazocraft: motor sin Qt, cinco pantallas y engranaje, bandeja y actualizador; licencia MIT. Instalador 0.3.1 fabricado con Inno Setup 6.7.3; aceptación de servidores de la 0.1.0 superada en copias; TLS nativo con truststore. Git y publicación de Releases autorizados en ItsRodryy/telazocraft con identidad local del dueño. README del repo y LEEME de la biblioteca contienen los arranques vigentes.
- Aceptación Hardcore real: cliente 26.3 aislado, salud 20→20 al recibir daño durante gracia; daño mortal después, ZIP de partida y semilla nueva. La gracia no protege /kill ni el vacío (decisión del dueño: probar daño normal). Sin Playit en todas las pruebas.

Historial Lepazo importado de logs: seis jugadores con horas y la persona de whitelist sin entradas a cero; sin modificar identidades ni mundos. Rediseño 0.3.1 comprobado sin arrancar servidores reales.
