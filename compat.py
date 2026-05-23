# -*- coding: utf-8 -*-
"""Small compatibility helpers for QGIS 3.x and future QGIS 4 / Qt6."""

from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.core import QgsLayoutItemPage, QgsUnitTypes


def exec_dialog(dialog: QDialog) -> int:
    """Execute a dialog using the Qt6 method when available."""
    if hasattr(dialog, "exec"):
        return dialog.exec()
    return dialog.exec_()


def standard_button(name: str):
    """Return QMessageBox standard buttons in a Qt5/Qt6 safe way."""
    enum = getattr(QMessageBox, "StandardButton", None)
    if enum is not None:
        return getattr(enum, name)
    return getattr(QMessageBox, name)


def layout_mm():
    """Return the layout millimetre unit in a QGIS 3 / QGIS 4 safe way."""
    enum = getattr(QgsUnitTypes, "LayoutUnit", None)
    if enum is not None:
        return enum.LayoutMillimeters
    return QgsUnitTypes.LayoutMillimeters


def page_orientation(name: str):
    """Return a QgsLayoutItemPage orientation enum from a user-facing name."""
    orientation_enum = getattr(QgsLayoutItemPage, "Orientation", None)
    if orientation_enum is not None:
        return orientation_enum.Portrait if name == "Portrait" else orientation_enum.Landscape
    return QgsLayoutItemPage.Portrait if name == "Portrait" else QgsLayoutItemPage.Landscape
