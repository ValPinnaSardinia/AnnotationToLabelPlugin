# -*- coding: utf-8 -*-
"""Annotation-to-layout conversion logic.

This module intentionally contains no plugin menu or dialog code. Keeping the
conversion logic separate makes the plugin easier to test, maintain, and extend.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, List, Optional

from qgis.PyQt.QtGui import QFont
from qgis.core import (
    QgsApplication,
    QgsLayoutItemLabel,
    QgsLayoutItemMap,
    QgsLayoutItemPicture,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsPointXY,
    QgsPrintLayout,
    QgsProject,
    QgsUnitTypes,
)

from .compat import layout_mm, page_orientation


@dataclass(frozen=True)
class ConversionOptions:
    """User options for generating a layout from map canvas text annotations."""

    layout_name: str
    page_size: str = "A4"
    orientation: str = "Landscape"
    overwrite_existing: bool = False
    hide_annotations_after_conversion: bool = True
    include_north_arrow: bool = True
    map_margin_mm: float = 5.0
    font_family: str = "Arial"
    font_size: int = 10


@dataclass(frozen=True)
class TextAnnotationRecord:
    """A minimal safe representation of a text annotation."""

    text: str
    point: QgsPointXY


@dataclass(frozen=True)
class ConversionResult:
    """Summary returned after conversion."""

    layout_name: str
    annotations_found: int
    labels_created: int
    annotations_outside_extent: int


class AnnotationConversionError(RuntimeError):
    """Raised for expected, user-facing conversion failures."""


class AnnotationConverter:
    """Create a print layout and convert visible text annotations into labels."""

    def __init__(self, iface):
        self.iface = iface

    def collect_text_annotations(self) -> List[TextAnnotationRecord]:
        """Collect text annotations with valid map positions from the project."""
        manager = QgsProject.instance().annotationManager()
        records: List[TextAnnotationRecord] = []

        for annotation in list(manager.annotations()):
            text = self._annotation_text(annotation)
            point = self._annotation_point(annotation)
            if not text or point is None:
                continue
            records.append(TextAnnotationRecord(text=text, point=point))

        return records

    def set_text_annotations_visible(self, visible: bool) -> int:
        """Show or hide project annotations. Returns the number processed."""
        manager = QgsProject.instance().annotationManager()
        count = 0
        for annotation in list(manager.annotations()):
            if hasattr(annotation, "setVisible"):
                annotation.setVisible(visible)
                count += 1
        return count

    def remove_text_annotations(self) -> int:
        """Remove text annotations only, leaving non-text annotations untouched."""
        manager = QgsProject.instance().annotationManager()
        removed = 0
        for annotation in list(manager.annotations()):
            if self._annotation_text(annotation):
                manager.removeAnnotation(annotation)
                removed += 1
        return removed

    def convert(self, options: ConversionOptions) -> ConversionResult:
        """Create a layout from the current canvas extent and convert annotations."""
        self._validate_options(options)

        records = self.collect_text_annotations()
        if not records:
            raise AnnotationConversionError("No text annotations were found in the current project.")

        canvas = self.iface.mapCanvas()
        extent = canvas.extent()
        if extent is None or extent.isEmpty():
            raise AnnotationConversionError("The current map canvas extent is empty.")

        project = QgsProject.instance()
        manager = project.layoutManager()
        existing = manager.layoutByName(options.layout_name)
        if existing is not None:
            if not options.overwrite_existing:
                raise AnnotationConversionError(
                    f"A layout named '{options.layout_name}' already exists."
                )
            manager.removeLayout(existing)

        layout = self._create_layout(project, options)
        page = layout.pageCollection().pages()[0]
        page_width = page.pageSize().width()
        page_height = page.pageSize().height()

        map_item = self._add_map_item(layout, extent, page_width, page_height, options.map_margin_mm)
        if options.include_north_arrow:
            self._add_north_arrow(layout, page_width, page_height, options.map_margin_mm)

        labels_created = 0
        outside_extent = 0
        for record in records:
            if not extent.contains(record.point):
                outside_extent += 1
                continue
            x_mm, y_mm = self._map_point_to_layout_mm(map_item, record.point)
            self._add_label(layout, record.text, x_mm, y_mm, options)
            labels_created += 1

        manager.addLayout(layout)

        if options.hide_annotations_after_conversion:
            self.set_text_annotations_visible(False)

        return ConversionResult(
            layout_name=options.layout_name,
            annotations_found=len(records),
            labels_created=labels_created,
            annotations_outside_extent=outside_extent,
        )

    @staticmethod
    def _annotation_text(annotation) -> str:
        """Return plain text from a QgsTextAnnotation-like object."""
        document_getter = getattr(annotation, "document", None)
        if not callable(document_getter):
            return ""
        document = document_getter()
        if document is None or not hasattr(document, "toPlainText"):
            return ""
        return document.toPlainText().strip()

    @staticmethod
    def _annotation_point(annotation) -> Optional[QgsPointXY]:
        """Return map position if available."""
        position_getter = getattr(annotation, "mapPosition", None)
        if not callable(position_getter):
            return None
        point = position_getter()
        if point is None:
            return None
        return QgsPointXY(point.x(), point.y())

    @staticmethod
    def _validate_options(options: ConversionOptions) -> None:
        if not options.layout_name.strip():
            raise AnnotationConversionError("Please provide a layout name.")
        if options.map_margin_mm < 0:
            raise AnnotationConversionError("Map margin cannot be negative.")
        if options.font_size < 1 or options.font_size > 72:
            raise AnnotationConversionError("Font size must be between 1 and 72 pt.")

    @staticmethod
    def _create_layout(project: QgsProject, options: ConversionOptions) -> QgsPrintLayout:
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(options.layout_name.strip())
        pages = layout.pageCollection().pages()
        if not pages:
            raise AnnotationConversionError("Could not initialise a layout page.")
        pages[0].setPageSize(options.page_size, page_orientation(options.orientation))
        return layout

    @staticmethod
    def _add_map_item(layout: QgsPrintLayout, extent, page_width: float, page_height: float, margin: float) -> QgsLayoutItemMap:
        unit = layout_mm()
        map_item = QgsLayoutItemMap(layout)
        map_item.setRect(0, 0, page_width - (margin * 2), page_height - (margin * 2))
        map_item.setExtent(extent)
        map_item.setFrameEnabled(True)
        layout.addLayoutItem(map_item)
        map_item.attemptMove(QgsLayoutPoint(margin, margin, unit))
        map_item.attemptResize(QgsLayoutSize(page_width - (margin * 2), page_height - (margin * 2), unit))
        return map_item

    @staticmethod
    def _add_north_arrow(layout: QgsPrintLayout, page_width: float, page_height: float, margin: float) -> None:
        arrow_path = AnnotationConverter._find_north_arrow_svg()
        if not arrow_path:
            return

        unit = layout_mm()
        north = QgsLayoutItemPicture(layout)
        north.setPicturePath(arrow_path)
        layout.addLayoutItem(north)
        north.attemptResize(QgsLayoutSize(max(8.0, page_width * 0.05), max(12.0, page_height * 0.08), unit))
        north.attemptMove(QgsLayoutPoint(margin + 2.0, margin + 2.0, unit))

    @staticmethod
    def _find_north_arrow_svg() -> str:
        for svg_root in QgsApplication.svgPaths():
            candidate = os.path.join(svg_root, "arrows", "Arrow_03.svg")
            if os.path.exists(candidate):
                return candidate
        return ""

    @staticmethod
    def _map_point_to_layout_mm(map_item: QgsLayoutItemMap, point: QgsPointXY) -> tuple[float, float]:
        extent = map_item.extent()
        width = extent.width()
        height = extent.height()
        if width <= 0 or height <= 0:
            raise AnnotationConversionError("The map extent has invalid dimensions.")

        item_pos = map_item.positionWithUnits()
        item_size = map_item.sizeWithUnits()
        map_left = item_pos.x()
        map_top = item_pos.y()
        map_width = item_size.width()
        map_height = item_size.height()

        x_ratio = (point.x() - extent.xMinimum()) / width
        y_ratio = (extent.yMaximum() - point.y()) / height

        x_mm = map_left + (x_ratio * map_width)
        y_mm = map_top + (y_ratio * map_height)
        return x_mm, y_mm

    @staticmethod
    def _add_label(layout: QgsPrintLayout, text: str, x_mm: float, y_mm: float, options: ConversionOptions) -> None:
        unit = layout_mm()
        label = QgsLayoutItemLabel(layout)
        label.setText(text)
        label.setFont(QFont(options.font_family, options.font_size))
        label.adjustSizeToText()
        layout.addLayoutItem(label)
        label.attemptMove(QgsLayoutPoint(x_mm, y_mm, unit))
