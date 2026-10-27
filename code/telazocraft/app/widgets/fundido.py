# -*- coding: utf-8 -*-
"""Las ventanas emergentes aparecen y se van con un fundido (petición del usuario, 30/09/2026).

- **Al abrirse**, TODAS: `instalar(app)` pone un filtro en la aplicación que, justo antes de que
  cualquier ventana emergente se muestre (diálogos, avisos, asistentes), le quita la opacidad y la
  hace aparecer de menos a más. No hay que tocar cada ventana.
- **Al cerrarse**, las que heredan `ConFundido` (todas las del programa, a través de `VentanaBase`
  o directamente): Aceptar, Cancelar, Cerrar o la X se desvanecen y DESPUÉS se cierran con su
  resultado.
- **Los avisos de Qt (`QMessageBox`)**, también los de `QMessageBox.question/warning/...`, que crea
  Qt por dentro: su clic no pasa por `done()` y no se puede retrasar, así que el filtro se engancha
  a `buttonClicked` (llega justo antes del cierre) y a la X, y espera allí al fundido con un bucle
  de eventos propio. Mientras se desvanecen no aceptan más clics ni teclas (petición del usuario,
  01/10/2026).

La ventana principal tiene su propio fundido (`gotas`) y la animación de carga no es una ventana
emergente: ninguna de las dos pasa por aquí. Sin pantalla (pruebas) o con la animación apagada en
Interfaz, nada cambia.
"""

from PySide6.QtCore import (QEasingCurve, QEvent, QEventLoop, QObject, Qt, QTimer,
                            QVariantAnimation)
from PySide6.QtWidgets import QDialog, QMessageBox, QWidget
from PySide6.QtGui import QGuiApplication
from .. import style
from ...common.infrastructure import ui_prefs

FUNDIDO_MS = 200
# Tipos de ventana que se funden: diálogos y ventanas normales. Fuera quedan menús, ayudas
# emergentes, el splash y las ventanas de herramienta (la animación de carga).
_TIPOS = (Qt.Dialog, Qt.Window, Qt.Sheet)


def activo():
    # Los diálogos no dependen de una escena de carga ni del logo de otra aplicación.
    return (QGuiApplication.platformName() not in ("offscreen", "minimal")
            and style.animaciones_activas()
            and bool(ui_prefs.cargar().get("animacion_inicio", True)))


def animar(ventana, desde, hasta, al_terminar=None, duracion_ms=FUNDIDO_MS):
    """Opacidad de `desde` a `hasta` sin bloquear; `al_terminar()` al acabar."""
    animacion = QVariantAnimation(ventana)
    animacion.setDuration(int(duracion_ms))
    animacion.setStartValue(float(desde))
    animacion.setEndValue(float(hasta))
    animacion.setEasingCurve(QEasingCurve.InOutQuad)
    animacion.valueChanged.connect(lambda valor: ventana.setWindowOpacity(float(valor)))
    if al_terminar is not None:
        animacion.finished.connect(al_terminar)
    animacion.start()
    return animacion


def _elegible(ventana):
    if not ventana.isWindow() or bool(ventana.property("sin_fundido")):
        return False
    return (ventana.windowFlags() & Qt.WindowType_Mask) in _TIPOS


# Avisos de Qt que se están desvaneciendo: la entrada que les llegue mientras tanto se descarta.
_DESVANECIENDO = []
_ENTRADA = (QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick,
            QEvent.KeyPress, QEvent.KeyRelease, QEvent.ShortcutOverride, QEvent.Shortcut,
            QEvent.Close)


def desvanecer_y_esperar(ventana):
    """Desvanece `ventana` y vuelve cuando ya no se ve; la interfaz sigue viva mientras tanto.

    Es para lo que Qt cierra justo después de avisar (los `QMessageBox`), donde no se puede
    retrasar el cierre. Sin pantalla, con la animación apagada o si ya se está yendo, vuelve
    enseguida.
    """
    if ventana in _DESVANECIENDO or not ventana.isVisible() or not activo():
        return
    _DESVANECIENDO.append(ventana)
    try:
        bucle = QEventLoop()
        animar(ventana, ventana.windowOpacity(), 0.0, bucle.quit)
        bucle.exec()
    finally:
        _DESVANECIENDO.remove(ventana)


def _enganchar_aviso(aviso):
    if aviso.property("_fundido_aviso"):
        return
    aviso.setProperty("_fundido_aviso", True)
    aviso.buttonClicked.connect(lambda _boton, a=aviso: desvanecer_y_esperar(a))


class _Filtro(QObject):
    def eventFilter(self, objeto, evento):
        tipo = evento.type()
        if (_DESVANECIENDO and tipo in _ENTRADA and isinstance(objeto, QWidget)
                and (tipo != QEvent.Close or evento.spontaneous())
                and objeto.window() in _DESVANECIENDO):
            return True
        # `Show` llega justo ANTES de que la ventana salga en pantalla: aquí se le quita la opacidad
        # sin que llegue a verse entera ni un fotograma.
        # Toda ventana emergente sale centrada en su monitor (petición del usuario, 06/10/2026).
        # Se centra al mostrarse y otra vez cuando Qt ya le ha dado su tamaño final.
        if (tipo == QEvent.Show and not evento.spontaneous() and isinstance(objeto, QDialog)
                and objeto.isWindow() and not objeto.property("sin_centrar")):
            from ..interaction import centrar_en_monitor
            centrar_en_monitor(objeto)
            QTimer.singleShot(0, lambda o=objeto: o.isVisible() and centrar_en_monitor(o))
        # Si el programa le cambia el tamaño (otra página del asistente, detalle desplegado), vuelve
        # al centro. Lo que arrastra el usuario llega como espontáneo y se respeta.
        if (tipo == QEvent.Resize and not evento.spontaneous() and isinstance(objeto, QDialog)
                and objeto.isWindow() and objeto.isVisible() and not objeto.property("sin_centrar")):
            from ..interaction import centrar_en_monitor
            QTimer.singleShot(0, lambda o=objeto: o.isVisible() and centrar_en_monitor(o))
        if (tipo == QEvent.Show and not evento.spontaneous()
                and hasattr(objeto, "isWindow") and _elegible(objeto) and activo()):
            objeto.setWindowOpacity(0.0)
            QTimer.singleShot(0, lambda o=objeto: animar(o, 0.0, 1.0))
            if isinstance(objeto, QMessageBox):
                _enganchar_aviso(objeto)
        elif isinstance(objeto, QMessageBox) and objeto.property("_fundido_aviso"):
            if tipo == QEvent.Close and evento.spontaneous():
                # La X o Alt+F4: se va con fundido y Qt decide después. Si Qt no la cierra (un
                # aviso sin botón de escape), vuelve a verse.
                desvanecer_y_esperar(objeto)
                QTimer.singleShot(0, lambda o=objeto: o.isVisible() and o.setWindowOpacity(1.0))
            elif tipo == QEvent.Hide:
                # Un aviso que se reutiliza no puede volver a salir transparente.
                objeto.setWindowOpacity(1.0)
        return False


_FILTRO = None


def instalar(app):
    global _FILTRO
    if _FILTRO is None:
        _FILTRO = _Filtro(app)
        app.installEventFilter(_FILTRO)


class ConFundido:
    """Mezcla para diálogos: se desvanecen antes de cerrarse con su resultado.

    Va delante de `QDialog` en la herencia. Un segundo clic mientras se va no cuenta. Si la
    ventana se borra al cerrarse (`WA_DeleteOnClose`), se borra al acabar el fundido.
    """

    def done(self, resultado):
        if getattr(self, "_fundido_resultado", None) is not None:
            return
        if not self.isVisible() or not activo():
            super().done(resultado)
            return
        self._fundido_resultado = resultado

        def cerrar():
            resultado_final, self._fundido_resultado = self._fundido_resultado, None
            QDialog.done(self, resultado_final)
            self.setWindowOpacity(1.0)
            if self.testAttribute(Qt.WA_DeleteOnClose):
                self.deleteLater()

        animar(self, self.windowOpacity(), 0.0, cerrar)
