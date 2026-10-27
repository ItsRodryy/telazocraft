# -*- coding: utf-8 -*-
"""Tabla de datos de solo lectura con comportamiento común a toda la aplicación.

Reúne en un solo sitio lo que antes cada tabla resolvía a su manera (o no resolvía):

  - **Columnas de datos `Interactive`**: nacen con un ancho razonable y se arrastran. El cursor de
    redimensionar (`SplitHCursor`) sale solo sobre sus separadores, porque las demás columnas son
    `Fixed` y Qt no ofrece redimensionarlas.
  - **Columnas de acción `Fixed`** (p. ej. Copiar): un icono, no un dato. Ni se ensanchan ni se
    arrastran ni se persisten.
  - **Columna de relleno**: última columna vacía, `Fixed` y no arrastrable. Se queda el hueco
    sobrante para que la fila se pinte de lado a lado y no quede una franja de otro color a la
    derecha del header. Si los datos desbordan, el relleno se oculta y aparece el scrollbar
    horizontal `AsNeeded`, sin espacio muerto.
  - **Sin mover secciones**: el orden de columnas es fijo.
  - **Persistencia opcional** de los anchos de datos (nunca acción ni relleno), con un debounce para
    no escribir `ui.json` por cada píxel arrastrado, validando que la columna oculta no guarde 0.

El relleno se recalcula tras cada `sectionResized`, cada resize del viewport y cada aparición o
desaparición de scrollbars.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView,
                               QAbstractItemView)

from ...common.infrastructure import ui_prefs

_MINIMO_SECCION = 40
_DEBOUNCE_MS = 250


class TablaDatos(QTableWidget):
    def __init__(self, cabeceras, *, columna_relleno=None, columnas_accion=(),
                 anchos=None, minimo_relleno=0, clave=None, mostrar_rejilla=False,
                 columna_estirada=None, parent=None):
        super().__init__(0, len(cabeceras), parent)
        self.setHorizontalHeaderLabels(cabeceras)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Una línea por celda: lo que no cabe se recorta con «…» y se lee en el tooltip.
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideRight)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(bool(mostrar_rejilla))
        self.verticalHeader().setVisible(False)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._relleno = columna_relleno
        self._accion = set(columnas_accion)
        self._minimo_relleno = minimo_relleno
        self._clave = clave
        self._ajustando = False
        # Columnas de datos: todo lo que no sea acción ni relleno. Son las únicas Interactive y
        # las únicas que se persisten.
        self._cols_datos = [c for c in range(self.columnCount())
                            if c != self._relleno and c not in self._accion]

        cabecera = self.horizontalHeader()
        cabecera.setStretchLastSection(False)
        cabecera.setSectionResizeMode(QHeaderView.Interactive)
        cabecera.setSectionsMovable(False)
        cabecera.setMinimumSectionSize(_MINIMO_SECCION)
        # El cursor de redimensionar solo se actualiza si el header sigue el ratón.
        cabecera.viewport().setMouseTracking(True)

        if self._relleno is not None:
            cabecera.setSectionResizeMode(self._relleno, QHeaderView.Fixed)
        # Columna estirada: se queda el ancho sobrante para que la tabla ocupe todo el panel.
        if columna_estirada is not None:
            cabecera.setSectionResizeMode(columna_estirada, QHeaderView.Stretch)
        for columna in self._accion:
            cabecera.setSectionResizeMode(columna, QHeaderView.Fixed)

        # Debounce de guardado: arrastrar un separador dispara muchos sectionResized seguidos.
        self._timer_guardar = QTimer(self)
        self._timer_guardar.setSingleShot(True)
        self._timer_guardar.setInterval(_DEBOUNCE_MS)
        self._timer_guardar.timeout.connect(self._persistir_ahora)

        # Anchos iniciales, luego los guardados (si su longitud cuadra). Con `_ajustando` para que
        # estos cambios programáticos no se lean como "el usuario ha arrastrado".
        self._ajustando = True
        for columna, ancho in (anchos or {}).items():
            self.setColumnWidth(columna, ancho)
        guardados = self._leer_persistidos()
        if guardados is not None:
            for columna, ancho in zip(self._cols_datos, guardados):
                self.setColumnWidth(columna, ancho)
        self._ajustando = False

        cabecera.sectionResized.connect(self._seccion_movida)
        self.horizontalScrollBar().rangeChanged.connect(lambda *_: self._repartir())
        self.verticalScrollBar().rangeChanged.connect(lambda *_: self._repartir())

    # ------------------------------------------------------------------ persistencia
    def _leer_persistidos(self):
        if not self._clave:
            return None
        return ui_prefs.anchos_tabla(self._clave, len(self._cols_datos))

    def _persistir(self, anchos):
        if not self._clave:
            return
        ui_prefs.guardar_anchos_tabla(self._clave, anchos)

    def _persistir_ahora(self):
        previos = self._leer_persistidos() or []
        anchos = []
        for i, columna in enumerate(self._cols_datos):
            ancho = self.columnWidth(columna)
            # Una columna oculta (p. ej. «#» cuando no hay captura) mide 0: no se guarda ese 0,
            # se conserva el último ancho conocido para no perderlo al reaparecer.
            if self.isColumnHidden(columna) or ancho <= 0:
                ancho = previos[i] if i < len(previos) else _MINIMO_SECCION
            anchos.append(ancho)
        self._persistir(anchos)

    # ------------------------------------------------------------------ acciones/relleno
    def fijar_ancho(self, columna, ancho, redimensionable=True):
        """Fija el ancho de una columna. El modo PRIMERO y el ancho DESPUÉS: al pasar a `Fixed`,
        Qt le pone el ancho por defecto del header y se lleva por delante el recién asignado."""
        self._ajustando = True
        if not redimensionable:
            self.horizontalHeader().setSectionResizeMode(columna, QHeaderView.Fixed)
        self.setColumnWidth(columna, ancho)
        self._ajustando = False

    def _seccion_movida(self, indice, _viejo, _nuevo):
        if self._ajustando:
            return
        # El usuario ha arrastrado una columna de datos: reparte de nuevo el hueco y programa el
        # guardado. Un cambio en la de relleno o acción no se guarda ni cuenta como edición.
        self._repartir()
        if indice in self._cols_datos:
            self._timer_guardar.start()

    def _repartir(self):
        """La columna de relleno se queda el hueco sobrante; si no cabe, se oculta y aparece el
        scrollbar horizontal."""
        if self._relleno is None or self._ajustando:
            return
        ocupado = sum(self.columnWidth(c) for c in range(self.columnCount())
                      if c != self._relleno and not self.isColumnHidden(c))
        libre = self.viewport().width() - ocupado - 2
        self._ajustando = True
        if libre >= max(_MINIMO_SECCION, self._minimo_relleno):
            if self.isColumnHidden(self._relleno):
                self.showColumn(self._relleno)
            self.setColumnWidth(self._relleno, libre)
        elif not self.isColumnHidden(self._relleno):
            self.hideColumn(self._relleno)
        self._ajustando = False

    def hay_scroll_horizontal(self):
        """True si los datos desbordan el viewport (independiente del estado visible del scrollbar,
        que en modo offscreen no es fiable)."""
        ancho_cols = sum(self.columnWidth(c) for c in range(self.columnCount())
                         if not self.isColumnHidden(c))
        return ancho_cols > self.viewport().width()

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._repartir()

    # ------------------------------------------------------------------ contenido
    def llenar(self, filas):
        self.setRowCount(len(filas))
        for r, fila in enumerate(filas):
            for c, valor in enumerate(fila):
                item = QTableWidgetItem("" if valor is None else str(valor))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.setItem(r, c, item)
        self._repartir()
