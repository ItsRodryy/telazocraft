# -*- coding: utf-8 -*-
"""Avisos a los paneles sin que la ventana sepa cuáles son.

Cada vista decide qué avisos entiende implementando el método correspondiente; la ventana solo
recorre los paneles registrados y llama al que exista. Antes había listas de widgets escritas a
mano en `main_window`, así que añadir una pestaña obligaba a acordarse de apuntarla en tres sitios
distintos —y olvidarlo no rompía nada de forma visible, simplemente esa pestaña dejaba de
enterarse—.

Ganchos reconocidos, todos opcionales:

- ``set_worker(worker)``            la cámara con el foco ha cambiado
- ``set_modo_trabajo(modo)`` /
  ``set_modo(modo)``               el modo de trabajo del dominio ha cambiado
- ``aplicar_preferencias(prefs)``   el usuario ha tocado la apariencia
- ``detener()``                     la ventana se cierra
- ``resolver_pendientes(cancelable)`` se sale de la vista o se cierra con cambios sin aplicar:
                                    pregunta Aplicar / Descartar (/ Cancelar) y devuelve True
                                    para seguir o False si se canceló
"""

import logging


_LOGGER = logging.getLogger(__name__)


def avisar(paneles, gancho, *args):
    """Llama a `gancho` en los paneles que lo implementen. Devuelve a cuántos llegó."""
    llamados = 0
    for panel in paneles:
        funcion = getattr(panel, gancho, None)
        if callable(funcion):
            try:
                funcion(*args)
                llamados += 1
            except Exception:
                _LOGGER.exception("Falló el gancho %s de %s", gancho,
                                  type(panel).__name__)
                ventana=panel.window() if hasattr(panel,'window') else None
                if hasattr(ventana,'mostrar_error'):ventana.mostrar_error('No se pudo actualizar este panel')
    return llamados


def avisar_alguno(paneles, ganchos, *args):
    """Como `avisar`, pero por panel se usa **el primer** gancho de la lista que exista.

    Hace falta donde el mismo aviso tiene dos nombres históricos (`set_modo_trabajo` y `set_modo`):
    llamar a los dos en un panel que tenga ambos aplicaría el cambio dos veces.
    """
    llamados = 0
    for panel in paneles:
        for gancho in ganchos:
            funcion = getattr(panel, gancho, None)
            if callable(funcion):
                llamados += avisar([panel],gancho,*args)
                break
    return llamados
