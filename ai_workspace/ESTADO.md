# Estado

Actualizado el 29 de octubre de 2026. Versión 0.3.1 publicada (Release v0.3.1, commit 0a653ef).

## Hecho

- **Biblioteca dentro de la app (29/10):** movida del Escritorio a `biblioteca/` (excluida de
  Git). Copia comprobada (3.145 archivos, 13,55 GB; lista, tamaño y fecha iguales; `servidores/`
  byte a byte) y carpeta antigua borrada. `ajustes.json` y Syncthing (`lepazo-vice-server`)
  apuntan aquí; los servidores nuevos se crean en `biblioteca/servidores/`.
- Workspace único en la app (AI Workspace 2.3.0); el de la biblioteca quedó en
  `biblioteca/archivo/workspace_biblioteca_antiguo/` y su contexto, en `ai_workspace/contexto/`.
- Verificado el 29/10: 57 pruebas OK, smoke con la biblioteca nueva, Syncthing en reposo sin error.
  Ningún servidor arrancado ni parado.

## Pendiente

- **Portátil:** conectado y sin pausa en Syncthing desde el 29/10 09:46 (no lo cambió la IA); 95 %
  sincronizado. Comprobar que su `.stignore` es solo `#include stignore_comun.txt` (si no, baja
  las copias locales) y, si se quiere la misma estructura, apuntar su carpeta a
  `D:\Proyectos\personal\telazocraft\biblioteca` e instalar Telazocraft desde Releases.
- Comprobar el túnel real de Playit con un amigo (las pruebas usaron `GESTOR_NO_PLAYIT=1`).
- Equipo: BSOD previos por RAM/XMP; revisar BIOS y pasar MemTest86.
- Copias antiguas fuera de la biblioteca, a decidir (mover a `biblioteca/archivo/` o borrar):
  `Escritorio/LepazoVice_respaldo_pre_app_2026-10-26_223850` (1,8 GB, vuelta atrás previa a la
  app), `Escritorio/minecraft_server_neoforge_1_21_1_backup` (41 MB) y
  `D:/Proyectos/personal/backups_server_minecraft` (1,3 GB).

## Siguiente paso

Revisar el `.stignore` del portátil.
