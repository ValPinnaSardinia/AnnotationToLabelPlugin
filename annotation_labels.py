# -*- coding: utf-8 -*-
"""Main QGIS plugin entry point for Annotation to Label."""

import os
import traceback

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar
from qgis.core import Qgis

# Required when using compiled Qt resources generated from resources.qrc.
from . import resources  # noqa: F401
from .annotation_converter import AnnotationConversionError, AnnotationConverter
from .annotation_labels_dialog import AnnotationToLabelDialog
from .compat import exec_dialog, standard_button


class AnnotationToLabel:
    """QGIS plugin controller.

    The class only owns GUI integration and user interaction. Processing logic is
    delegated to AnnotationConverter so future layout/export changes stay isolated.
    """

    PLUGIN_NAME = "Annotation to Label"
    MENU_NAME = "&Annotation to Label"
    TOOLBAR_OBJECT_NAME = "AnnotationToLabelToolbar"

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.toolbar = None
        self.translator = None
        self.converter = AnnotationConverter(iface)
        self._install_translation()

    def tr(self, message: str) -> str:
        return QCoreApplication.translate("AnnotationToLabel", message)

    def _install_translation(self) -> None:
        locale = QSettings().value("locale/userLocale", "en")
        locale = str(locale)[0:2]
        locale_path = os.path.join(self.plugin_dir, "i18n", f"AnnotationToLabel_{locale}.qm")
        if not os.path.exists(locale_path):
            return
        self.translator = QTranslator()
        if self.translator.load(locale_path):
            QCoreApplication.installTranslator(self.translator)

    def initGui(self) -> None:
        """Create QGIS menu and toolbar actions."""
        self.toolbar = self.iface.mainWindow().findChild(QToolBar, self.TOOLBAR_OBJECT_NAME)
        if self.toolbar is None:
            self.toolbar = self.iface.addToolBar(self.tr("Annotation to Label"))
            self.toolbar.setObjectName(self.TOOLBAR_OBJECT_NAME)
            self.toolbar.setToolTip(self.tr("Annotation to Label"))

        self._add_action(
            icon_path=":/plugins/annotation_labels/icons/annotationtolabel_icon.png",
            text=self.tr("Convert text annotations to layout labels"),
            callback=self.run,
            status_tip=self.tr("Create a layout and convert visible text annotations to labels."),
        )
        self._add_action(
            icon_path=":/plugins/annotation_labels/icons/annotationtolabel_show_icon.png",
            text=self.tr("Show text annotations"),
            callback=self.show_text_annotations,
            status_tip=self.tr("Show all project text annotations."),
        )
        self._add_action(
            icon_path=":/plugins/annotation_labels/icons/annotationtolabel_hide_icon.png",
            text=self.tr("Hide text annotations"),
            callback=self.hide_text_annotations,
            status_tip=self.tr("Hide all project text annotations."),
        )
        self._add_action(
            icon_path=":/plugins/annotation_labels/icons/annotationtolabel_remove_icon.png",
            text=self.tr("Remove text annotations"),
            callback=self.remove_text_annotations,
            status_tip=self.tr("Remove all text annotations from the project."),
        )

    def unload(self) -> None:
        """Remove plugin actions from QGIS."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(self.MENU_NAME), action)
            if self.toolbar is not None:
                self.toolbar.removeAction(action)
        self.actions.clear()

    def _add_action(self, icon_path: str, text: str, callback, status_tip: str = "") -> QAction:
        action = QAction(QIcon(icon_path), text, self.iface.mainWindow())
        action.triggered.connect(callback)
        if status_tip:
            action.setStatusTip(status_tip)
        if self.toolbar is not None:
            self.toolbar.addAction(action)
        self.iface.addPluginToMenu(self.tr(self.MENU_NAME), action)
        self.actions.append(action)
        return action

    def run(self) -> None:
        """Open the conversion dialog and run the conversion."""
        dialog = AnnotationToLabelDialog(self.iface.mainWindow())
        if exec_dialog(dialog) != int(QMessageBox.DialogCode.Accepted) if hasattr(QMessageBox, "DialogCode") else dialog.Rejected:
            return

        options = dialog.options()
        try:
            result = self.converter.convert(options)
            layout = Qgis.QGIS_VERSION  # harmless access keeps Qgis import used in older linters
            del layout
            created_layout = self.iface.project().layoutManager().layoutByName(result.layout_name)
            if created_layout is not None:
                self.iface.openLayoutDesigner(created_layout)
            self.iface.messageBar().pushMessage(
                self.PLUGIN_NAME,
                self.tr(
                    f"Created layout '{result.layout_name}' with {result.labels_created} labels. "
                    f"{result.annotations_outside_extent} annotations were outside the canvas extent."
                ),
                level=Qgis.MessageLevel.Success if hasattr(Qgis, "MessageLevel") else Qgis.Success,
                duration=8,
            )
        except AnnotationConversionError as exc:
            QMessageBox.warning(self.iface.mainWindow(), self.PLUGIN_NAME, str(exc))
        except Exception as exc:  # noqa: BLE001 - final GUI safety net for production plugin
            self._show_unexpected_error(exc)

    def hide_text_annotations(self) -> None:
        count = self.converter.set_text_annotations_visible(False)
        self._push_info(self.tr(f"Hidden {count} annotations."))

    def show_text_annotations(self) -> None:
        count = self.converter.set_text_annotations_visible(True)
        self._push_info(self.tr(f"Shown {count} annotations."))

    def remove_text_annotations(self) -> None:
        yes = standard_button("Yes")
        no = standard_button("No")
        reply = QMessageBox.question(
            self.iface.mainWindow(),
            self.PLUGIN_NAME,
            self.tr("Remove all text annotations from the project? This cannot be undone."),
            yes | no,
            no,
        )
        if reply != yes:
            return
        count = self.converter.remove_text_annotations()
        self._push_info(self.tr(f"Removed {count} text annotations."))

    def _push_info(self, message: str) -> None:
        self.iface.messageBar().pushMessage(self.PLUGIN_NAME, message, level=Qgis.Info, duration=5)

    def _show_unexpected_error(self, exc: Exception) -> None:
        details = traceback.format_exc()
        message = self.tr(
            "An unexpected error occurred while running Annotation to Label.\n\n"
            f"{exc}\n\n"
            "Please copy the details below if you report this issue."
        )
        box = QMessageBox(self.iface.mainWindow())
        box.setIcon(QMessageBox.Icon.Critical if hasattr(QMessageBox, "Icon") else QMessageBox.Critical)
        box.setWindowTitle(self.PLUGIN_NAME)
        box.setText(message)
        box.setDetailedText(details)
        box.exec() if hasattr(box, "exec") else box.exec_()
