---
name: cerrar
description: Cierra o pausa el trabajo. Verifica, compacta la documentación, actualiza el estado y archiva el plan si terminó, o deja el traspaso si no.
---

Si el usuario solo pausa o cambia de agente, salta los pasos 1 y 6.

1. Si cambió código, ejecuta todos los comandos de verificación de `AGENTS.md`. Si fallan, no
   cierres: deja el plan `EN CURSO` o `BLOQUEADO` e informa del fallo.
2. Si cambió código y Graphify está activo: `graphify update .`
3. Sustituye `ai_workspace/ESTADO.md` (no añadas al final): qué se hizo, qué se verificó con sus
   resultados, qué queda y el siguiente paso. Pon al día `ai_workspace/progreso.md` (secciones de
   la orden `progreso`) y añade la fila de la tarea a `ai_workspace/registro_trabajo.md`, con las
   horas «por confirmar».
4. En `ai_workspace/archivo/CHANGELOG.md`, una línea arriba por hito que explique una decisión o una
   regresión. Nada más.
5. Mide: `powershell -NoProfile -File ai_workspace/tools/planes.ps1 -Accion Medir`
   - `EXCEDE`: compacta ese documento dejando solo lo vigente. CHANGELOG: funde lo antiguo en un
     resumen corto. Plan: bloques hechos en una línea. AGENTS.md: mueve el detalle a
     `ai_workspace/contexto/` con su fila en la tabla de documentación.
   - `REVISAR`: borra los temporales que creaste tú; si no sabes de dónde vienen, pregunta.
6. Plan terminado y verificado:
   `powershell -NoProfile -File ai_workspace/tools/planes.ps1 -Accion Archivar -Estado COMPLETADO`
   (se guardan los tres últimos). Si queda trabajo, marca los bloques, escribe el siguiente paso y no
   lo archives.
7. Informa en pocas líneas: hecho, verificado y pendiente.
