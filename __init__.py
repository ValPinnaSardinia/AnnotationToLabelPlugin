# -*- coding: utf-8 -*-
"""QGIS plugin factory."""


def classFactory(iface):  # pylint: disable=invalid-name
    from .annotation_labels import AnnotationToLabel

    return AnnotationToLabel(iface)
