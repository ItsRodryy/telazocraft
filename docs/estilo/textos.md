# Textos e idioma

Decisión del usuario (07/10/2026): interfaz en español (por defecto) o inglés. Código en
`common/i18n.py` y catálogo en `common/i18n_en.py`.

- Todo texto que llega a pantalla pasa por `tr("frase en español")`; los datos se formatean después:
  `tr("Falta su SDK: %s") % nombre`. Nunca f-strings para textos de pantalla.
- **Los datos no se traducen**: carpetas, archivos, claves, valores guardados, nombres GenICam,
  códigos del motor, alias y nombres de perfiles. Un desplegable guarda su valor (`itemData`) y
  enseña `tr(texto)`; ninguna lógica compara texto de pantalla.
- Texto que se guarda en español y además se enseña (avisos de calibración, motivos de cámara,
  registros): `marcar("…")` donde nace (no cambia nada) y `tr_mensaje(texto)` al pintarlo, que
  reconoce la plantilla aunque ya lleve números.
- Si en inglés un rótulo no cabe a 1080 × 720, se acorta la traducción («Max:», «Turn 90°»),
  no se ensancha la interfaz. `test_sin_recortes` se pasa en los dos idiomas.
- Registros, manual `.docx` e informe `.docx`: en español.
- `test_traduccion` falla si un texto llega a un control sin `tr()`, si a una clave le falta su
  inglés, si cambian los marcadores o si sobra una entrada.

- Rótulos cortos cuando el contexto ya lo dice: bajo el subtítulo «Profundidad», «Exposición» y no
  «Exposición de profundidad». El nombre completo y el técnico, en la ayuda flotante.
- Nada en MAYÚSCULAS para destacar (ver `tema.md`).

El glosario de este programa (bulto, arco, pasada…) está en `vision_driver.md`.
