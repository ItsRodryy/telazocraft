# -*- coding: utf-8 -*-
"""La ventana con la que el programa enseña un trabajo largo: pasos, barra y detalle plegado.

Este era el molde de la actualización y solo lo usaba ella. El resto de procesos largos —preparar el
entorno de Caliscope, procesar una calibración ChArUco— enseñaban su salida cruda en un recuadro
negro embebido en la pestaña, que es una consola con otro nombre: pared de texto técnico, sin decir
en qué punto va ni cuánto queda, y con el aspecto de algo que se ha escapado de la aplicación.

Aquí el trabajo se cuenta en pasos (✓ hecho, ▶ en marcha, ○ pendiente) con su barra. El texto crudo
sigue estando, porque cuando algo falla es lo único que sirve, pero **plegado**: se abre con «Ver
detalle» y solo si hace falta.

Un proceso que no puede anunciar sus pasos —los hay— se abre sin lista: barra indeterminada y la
última línea de salida como estado. Sigue sin haber consola.

Cómo se anuncian los pasos: al arrancar, el proceso escribe `@@PASOS uno|dos|tres` y luego, según
avanza, `@@PASO n/total texto`. La lista se declara **donde se ejecuta el trabajo**, que es quien
sabe cuántos pasos son y en qué orden; aquí solo se lee. Así no hay dos listas que mantener a la vez,
que es como acaban desincronizadas.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar,
                               QVBoxLayout)

from ...common.infrastructure import ui_prefs
from .. import icons, style
from .animated_button import AnimatedButton
from .fundido import ConFundido
from ...common.i18n import tr

# Prefijos con los que un subproceso declara sus pasos y anuncia en cuál va. Ver el docstring.
MARCA_PASOS = "@@PASOS "
MARCA_PASO = "@@PASO "


def cabecera_app(layout, subtitulo=""):
    """Logo, nombre del programa y una línea de qué se está haciendo. Igual en todos los diálogos."""
    cab = QHBoxLayout()
    logo = QLabel()
    logo.setPixmap(icons.logo_pixmap(56, con_fondo=True))
    cab.addWidget(logo)
    textos = QVBoxLayout()
    titulo = QLabel(tr("Telazocraft"))
    titulo.setObjectName("titulo")
    textos.addWidget(titulo)
    if subtitulo:
        sub = QLabel(subtitulo)
        sub.setObjectName("tenue")
        textos.addWidget(sub)
    cab.addLayout(textos, 1)
    cab.addStretch(1)
    layout.addLayout(cab)


class VentanaBase(ConFundido, QDialog):
    """Título, icono y la mica de Windows aplicada en `showEvent`.

    La mica NO puede aplicarse en `__init__`: necesita el `winId()` real, que no existe hasta que la
    ventana se muestra.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Telazocraft"))
        self.setWindowIcon(icons.app_icon())
        self.setMinimumWidth(560)

    def showEvent(self, evento):
        from ..interaction import aplicar_cursores_interactivos
        aplicar_cursores_interactivos(self)
        super().showEvent(evento)



def leer_marca_pasos(linea):
    """La lista de pasos que declara el proceso, o `None` si la línea no es esa declaración."""
    texto = str(linea or "")
    if not texto.startswith(MARCA_PASOS):
        return None
    partes = [p.strip() for p in texto[len(MARCA_PASOS):].split("|")]
    return [p for p in partes if p] or None


def leer_marca_paso(linea):
    """`(indice, texto)` si la línea anuncia un paso; `None` si es salida normal.

    El índice llega en base 1 —«paso 2 de 4» es lo que se lee— y sale en base 0, que es como se
    numeran los rótulos.
    """
    texto = str(linea or "")
    if not texto.startswith(MARCA_PASO):
        return None
    resto = texto[len(MARCA_PASO):].strip()
    cabeza, _, cola = resto.partition(" ")
    numero, _, _total = cabeza.partition("/")
    try:
        return max(0, int(numero) - 1), cola.strip()
    except ValueError:
        return None


class DialogoProceso(VentanaBase):
    """Un trabajo largo contado por pasos, con su detalle a mano pero fuera de la vista."""

    cancelar_pedido = Signal()

    def __init__(self, subtitulo, pasos=(), permite_cancelar=False, parent=None,
                 al_cerrar=None):
        super().__init__(parent)
        self.ok = False
        self.terminado = False
        self._pasos_texto = [str(p) for p in pasos]
        # Qué pasa al pulsar «Cerrar» tras terminar bien, dicho para este proceso concreto. Sin él
        # la ventana acabada parecía colgada (prueba del usuario, 07/10/2026).
        self.al_cerrar = tr("Ya puedes cerrar esta ventana.") if al_cerrar is None else al_cerrar

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(14)
        cabecera_app(v, subtitulo)

        self.pasos = []
        self._caja_pasos = QVBoxLayout()
        self._caja_pasos.setContentsMargins(0, 0, 0, 0)
        self._caja_pasos.setSpacing(4)
        v.addLayout(self._caja_pasos)
        self._crear_pasos()

        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        v.addWidget(self.barra)

        # Sin pasos declarados no se puede decir cuánto queda, y una barra parada al 0 % durante tres
        # minutos parece un programa colgado. La indeterminada al menos dice «sigo trabajando».
        self._aplicar_rango()

        self.estado = QLabel("")
        self.estado.setObjectName("tenue")
        self.estado.setWordWrap(True)
        v.addWidget(self.estado)

        self.btn_detalle = AnimatedButton(tr("Ver detalle"))
        self.btn_detalle.clicked.connect(self._alternar_detalle)
        self.detalle = QPlainTextEdit()
        self.detalle.setObjectName("log")
        self.detalle.setReadOnly(True)
        self.detalle.setMaximumHeight(160)
        self.detalle.setVisible(False)
        v.addWidget(self.detalle)

        self.mensaje = QLabel("")
        self.mensaje.setWordWrap(True)
        v.addWidget(self.mensaje)

        self.btn_cancelar = AnimatedButton(tr("Cancelar"))
        self.btn_cancelar.setVisible(bool(permite_cancelar))
        self.btn_cancelar.clicked.connect(self.cancelar_pedido.emit)
        self.btn_cerrar = AnimatedButton(tr("Cerrar"))
        self.btn_cerrar.setEnabled(False)
        self.btn_cerrar.clicked.connect(self.accept)
        pie = QHBoxLayout()
        pie.addWidget(self.btn_detalle)
        pie.addStretch(1)
        pie.addWidget(self.btn_cancelar)
        pie.addWidget(self.btn_cerrar)
        v.addLayout(pie)

    # ------------------------------------------------------------------ pasos
    def _crear_pasos(self):
        while self._caja_pasos.count():
            item = self._caja_pasos.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self.pasos = []
        for texto in self._pasos_texto:
            lbl = QLabel("○  " + texto)
            lbl.setObjectName("tenue")
            lbl.setWordWrap(True)
            self._caja_pasos.addWidget(lbl)
            self.pasos.append(lbl)

    def _aplicar_rango(self):
        if self._pasos_texto:
            self.barra.setRange(0, len(self._pasos_texto))
            self.barra.setValue(0)
        else:
            self.barra.setRange(0, 0)          # indeterminada: se mueve sin prometer un porcentaje

    def set_pasos(self, pasos):
        """Declara la lista de pasos ya abierta la ventana, si el proceso la anuncia al arrancar."""
        self._pasos_texto = [str(p) for p in pasos]
        self._crear_pasos()
        self._aplicar_rango()

    def set_paso(self, indice, texto=""):
        """Marca el paso `indice` como el que está en marcha y los anteriores como hechos."""
        for j, lbl in enumerate(self.pasos):
            base = self._pasos_texto[j]
            if j < indice:
                lbl.setText("✓  " + base)
                lbl.setObjectName("")
            elif j == indice:
                lbl.setText("▶  " + (texto or base))
                lbl.setObjectName("featuretitle")
            else:
                lbl.setText("○  " + base)
                lbl.setObjectName("tenue")
            # El QSS no se reaplica solo al cambiar `objectName`.
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)
        if self._pasos_texto:
            # Una descarga (0-100) o un instalador (indeterminada) cambian la escala: cada paso
            # nuevo vuelve a la de pasos.
            self.barra.setRange(0, len(self._pasos_texto))
            self.barra.setValue(max(0, min(indice, len(self._pasos_texto))))
        if texto:
            self.estado.setText(texto)

    # ------------------------------------------------------------------ salida
    def anadir_linea(self, texto):
        """Una línea del proceso: al detalle, y si anuncia un paso, también a la lista y la barra."""
        linea = str(texto or "")
        if linea.startswith('@@PROGRESO '):
            _,valor,rotulo=linea.split(' ',2)
            self.barra.setRange(0,100);self.barra.setValue(max(0,min(100,int(valor))));self.estado.setText(rotulo);return
        if linea == "@@INSTALANDO":
            # Cancelar un instalador en marcha puede dejar el SDK a medias.
            self.btn_cancelar.setEnabled(False)
            self.barra.setRange(0, 0)
            return
        if linea.startswith("@@DESCARGA "):
            try:
                leidos, total = map(int, linea.split()[1:])
            except (ValueError, TypeError):
                return
            if total > 0:
                self.barra.setRange(0, 100)
                self.barra.setValue(min(100, 100 * leidos // total))
                self.estado.setText(tr("Descargando: %.1f de %.1f MB") % (leidos / 1e6, total / 1e6))
            else:
                self.barra.setRange(0, 0)
                self.estado.setText(tr("Descargando: %.1f MB") % (leidos / 1e6))
            return
        declarados = leer_marca_pasos(linea)
        if declarados is not None:
            self.set_pasos(declarados)
            return
        marca = leer_marca_paso(linea)
        if marca is not None:
            indice, rotulo = marca
            self.set_paso(indice, rotulo)
            return
        self.detalle.appendPlainText(linea)
        if linea.strip():
            self.estado.setText(linea.strip())

    def terminar(self, ok, mensaje=""):
        self.ok = bool(ok)
        self.terminado = True
        if self._pasos_texto and ok:
            for j, lbl in enumerate(self.pasos):
                lbl.setText("✓  " + self._pasos_texto[j])
                lbl.setObjectName("")
                lbl.style().unpolish(lbl)
                lbl.style().polish(lbl)
            # Con un instalador en marcha la barra pasa a indeterminada (rango 0-0) y su máximo es 0:
            # «al máximo» la dejaba corriendo con todo ya hecho (visto el 07/10/2026). Se fija el rango.
            self.barra.setRange(0, len(self._pasos_texto))
            self.barra.setValue(self.barra.maximum())
        else:
            # La indeterminada se para: dejarla corriendo después de terminar dice que sigue algo en
            # marcha cuando ya no queda nada.
            self.barra.setRange(0, 1)
            self.barra.setValue(1 if ok else 0)
        self.estado.setText("")
        # Final bien visible: verde si salió bien, con lo que toca hacer ahora; rojo si falló.
        texto = ("✓  " if ok else "✗  ") + str(mensaje or "")
        if ok and self.al_cerrar:
            texto += "\n" + self.al_cerrar
        self.mensaje.setText(texto)
        self.mensaje.setObjectName("mensajeOk" if ok else "avisoPeligro")
        self.mensaje.style().unpolish(self.mensaje)
        self.mensaje.style().polish(self.mensaje)
        self.btn_cancelar.setEnabled(False)
        self.btn_cerrar.setEnabled(True)
        if not ok:
            # Cuando algo falla, el detalle es lo único que sirve: se abre solo.
            self.detalle.setVisible(True)
            self.btn_detalle.setText(tr("Ocultar detalle"))

    def _alternar_detalle(self):
        # `isHidden` y no `isVisible`: lo que interesa es si se ocultó a propósito, no si la ventana
        # que lo contiene está en pantalla.
        visible = self.detalle.isHidden()
        self.detalle.setVisible(visible)
        self.btn_detalle.setText(tr("Ocultar detalle") if visible else tr("Ver detalle"))

    # ------------------------------------------------------------------ cierre
    def closeEvent(self, event):
        """No se cierra a mitad: el proceso seguiría corriendo sin nadie mirando.

        Se controla aquí y no quitando el botón de cerrar con `setWindowFlag`: cambiar los flags
        después de mostrar la ventana hace que Qt recree el handle y la OCULTE.
        """
        if self.terminado:
            event.accept()
        else:
            event.ignore()

    def reject(self):
        if self.terminado:
            super().reject()

    def keyPressEvent(self, evento):
        # Escape es un `reject()` encubierto: se le aplica la misma regla que al aspa.
        if evento.key() == Qt.Key_Escape and not self.terminado:
            evento.ignore()
            return
        super().keyPressEvent(evento)
