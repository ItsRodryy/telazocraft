# -*- coding: utf-8 -*-
"""Modelo común de valores aplicados y ediciones todavía no confirmadas."""

import copy
from ..common.i18n import tr


class EditorPendiente:
    """Mantiene dos estados y permite aplicar por clave sin perder los fallos parciales."""

    def __init__(self, aplicados=None):
        self._aplicados = copy.deepcopy(aplicados or {})
        self._editados = copy.deepcopy(self._aplicados)
        self._validadores = {}

    def registrar(self, clave, valor, validador=None, reemplazar=False):
        if reemplazar or clave not in self._aplicados:
            self._aplicados[clave] = copy.deepcopy(valor)
            if reemplazar or clave not in self._editados:
                self._editados[clave] = copy.deepcopy(valor)
        if validador is not None:
            self._validadores[clave] = validador

    def editar(self, clave, valor):
        if clave not in self._aplicados:
            self.registrar(clave, valor)
        self._editados[clave] = copy.deepcopy(valor)

    def valor(self, clave, editado=True, por_defecto=None):
        origen = self._editados if editado else self._aplicados
        return copy.deepcopy(origen.get(clave, por_defecto))

    def aplicados(self):
        return copy.deepcopy(self._aplicados)

    def editados(self):
        return copy.deepcopy(self._editados)

    def pendientes(self):
        return {clave: copy.deepcopy(valor) for clave, valor in self._editados.items()
                if clave not in self._aplicados or valor != self._aplicados[clave]}

    def hay_cambios(self):
        return bool(self.pendientes())

    def validar(self, claves=None):
        errores = {}
        seleccion = self.pendientes() if claves is None else {
            clave: self._editados[clave] for clave in claves if clave in self._editados}
        for clave, valor in seleccion.items():
            validador = self._validadores.get(clave)
            if validador is None:
                continue
            try:
                resultado = validador(copy.deepcopy(valor))
            except Exception as exc:  # el mensaje del validador es el que necesita la interfaz
                resultado = str(exc)
            if resultado not in (None, True, ""):
                errores[clave] = tr("Valor no válido.") if resultado is False else str(resultado)
        return errores

    def aplicar(self, aplicador, conectado=None):
        """Aplica cada pendiente; devuelve ``(correctos, errores)``.

        Un aplicador puede devolver ``False`` o un texto para rechazar solo esa clave. Si la
        conexión cae, las claves aún no aplicadas se conservan como pendientes.
        """
        correctos, errores = [], self.validar()
        for clave, valor in self.pendientes().items():
            if clave in errores:
                continue
            if conectado is not None and not conectado():
                errores[clave] = tr("Se perdió la conexión antes de aplicar el cambio.")
                continue
            try:
                resultado = aplicador(clave, copy.deepcopy(valor))
            except Exception as exc:
                resultado = str(exc)
            if resultado not in (None, True, ""):
                errores[clave] = tr("No se pudo aplicar.") if resultado is False else str(resultado)
                continue
            self._aplicados[clave] = copy.deepcopy(valor)
            correctos.append(clave)
        return correctos, errores

    def confirmar(self, claves=None):
        for clave in list(claves if claves is not None else self._editados):
            if clave in self._editados:
                self._aplicados[clave] = copy.deepcopy(self._editados[clave])

    def rechazar(self, clave, aplicado_anterior, editado):
        """Revierte la confirmación optimista y deja el valor rechazado pendiente."""
        self._aplicados[clave] = copy.deepcopy(aplicado_anterior)
        self._editados[clave] = copy.deepcopy(editado)

    def restablecer(self, claves=None):
        seleccion = list(claves if claves is not None else self._aplicados)
        for clave in seleccion:
            if clave in self._aplicados:
                self._editados[clave] = copy.deepcopy(self._aplicados[clave])
        return self.editados()
