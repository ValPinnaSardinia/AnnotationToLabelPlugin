# -*- coding: utf-8 -*-
"""Compact native Qt dialog for Annotation to Label."""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from .annotation_converter import ConversionOptions


class AnnotationToLabelDialog(QDialog):
    """Collect layout and conversion settings from the user."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Annotation to Label")
        self.setMinimumWidth(390)
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        intro = QLabel(
            "Create a new print layout from the current map canvas and convert "
            "text annotations inside the canvas extent into layout labels."
        )
        intro.setWordWrap(True)
        intro.setObjectName("introLabel")
        main_layout.addWidget(intro)

        layout_box = QGroupBox("Layout")
        layout_form = QFormLayout(layout_box)
        layout_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        layout_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.layout_name_edit = QLineEdit()
        self.layout_name_edit.setPlaceholderText("e.g. Annotation labels")
        layout_form.addRow("Layout name", self.layout_name_edit)

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4", "A3", "A2", "A1", "A0", "A5"])
        layout_form.addRow("Page size", self.page_size_combo)

        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["Landscape", "Portrait"])
        layout_form.addRow("Orientation", self.orientation_combo)

        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 50)
        self.margin_spin.setSuffix(" mm")
        self.margin_spin.setValue(5)
        layout_form.addRow("Map margin", self.margin_spin)

        main_layout.addWidget(layout_box)

        options_box = QGroupBox("Options")
        options_layout = QVBoxLayout(options_box)
        options_layout.setSpacing(6)

        self.overwrite_check = QCheckBox("Overwrite existing layout with the same name")
        self.hide_annotations_check = QCheckBox("Hide annotations after conversion")
        self.hide_annotations_check.setChecked(True)
        self.north_arrow_check = QCheckBox("Add north arrow")
        self.north_arrow_check.setChecked(True)

        options_layout.addWidget(self.overwrite_check)
        options_layout.addWidget(self.hide_annotations_check)
        options_layout.addWidget(self.north_arrow_check)
        main_layout.addWidget(options_box)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Label font size"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(1, 72)
        self.font_size_spin.setValue(10)
        font_row.addWidget(self.font_size_spin)
        font_row.addStretch(1)
        main_layout.addLayout(font_row)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setStyleSheet(
            """
            QDialog { background: palette(window); }
            QLabel#introLabel {
                color: palette(mid);
                padding: 2px 1px 6px 1px;
            }
            QGroupBox {
                font-weight: 600;
                border: 1px solid palette(midlight);
                border-radius: 8px;
                margin-top: 10px;
                padding: 8px 8px 6px 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLineEdit, QComboBox, QSpinBox {
                min-height: 24px;
            }
            """
        )

    def accept(self) -> None:
        if not self.layout_name_edit.text().strip():
            self.layout_name_edit.setFocus()
            return
        super().accept()

    def options(self) -> ConversionOptions:
        return ConversionOptions(
            layout_name=self.layout_name_edit.text().strip(),
            page_size=self.page_size_combo.currentText(),
            orientation=self.orientation_combo.currentText(),
            overwrite_existing=self.overwrite_check.isChecked(),
            hide_annotations_after_conversion=self.hide_annotations_check.isChecked(),
            include_north_arrow=self.north_arrow_check.isChecked(),
            map_margin_mm=float(self.margin_spin.value()),
            font_size=int(self.font_size_spin.value()),
        )
