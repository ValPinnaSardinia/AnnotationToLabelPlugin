# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AnnotationToLabel
                                 A QGIS plugin
 This plugins converts the canvan annotations on layout labels
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2022-04-16
        copyright            : (C) 2022 by Valerio Pinna
        email                : pinnavalerio@yahoo.co.uk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load AnnotationToLabel class from file AnnotationToLabel.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .annotation_labels import AnnotationToLabel
    return AnnotationToLabel(iface)
