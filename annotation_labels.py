# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AnnotationToLabel
                                 A QGIS plugin
 This plugins converts the canvan annotations on layout labels
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-04-16
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Valerio Pinna
        email                : pinnavalerio@yahoo.co.uk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar
from PyQt5.QtGui import QFont
from qgis.core import *
from qgis.utils import iface
import sys

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .annotation_labels_dialog import AnnotationToLabelDialog
import os.path



class AnnotationToLabel:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'AnnotationToLabel_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Annotation to Label')
        
        self.toolbar = iface.mainWindow().findChild( QToolBar, u'AnnotationToLabelToolbar' )
        if not self.toolbar:
            self.toolbar = iface.addToolBar( u'Annotation To Label Toolbar' )
            self.toolbar.setObjectName( u'Annotation To Label Toolbar' )
            self.toolbar.setToolTip("Annotation to Label Toolbar")
               
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
    
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('AnnotationToLabel', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        
        
        
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
       
        
        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)
            
            
        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
                
        self.annotationtolabels= self.add_action( 
            icon_path = ':/plugins/annotation_labels/icons/annotationtolabel_icon.png',
            text=self.tr(u'Convert the Text annotations to labels'),
            callback=self.run,
            parent=self.iface.mainWindow())
        # will be set False in run()
        self.first_start = True
        
        
        self.showannotationtolabels= self.add_action( 
            icon_path = ':/plugins/annotation_labels/icons/annotationtolabel_show_icon.png',
            text=self.tr(u'Show all the Text annotations'),
            callback=self.showTextAnnotations,
            parent=self.iface.mainWindow())
        # will be set False in run()
        
        self.first_start = True
        
               
        self.hideannotationtolabels= self.add_action(  
            icon_path = ':/plugins/annotation_labels/icons/annotationtolabel_hide_icon.png',
            text=self.tr(u'Hide all the Text annotations'),
            callback=self.hideTextAnnotations,
            parent=self.iface.mainWindow())
        # will be set False in run()
        self.first_start = True
 
        
        self.removeannotationtolabels= self.add_action( 
            icon_path = ':/plugins/annotation_labels/icons/annotationtolabel_remove_icon.png',
            text=self.tr(u'Remove all the Text annotations'),
            callback=self.removeTextAnnotations,
            parent=self.iface.mainWindow())
        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Annotation to Label'),
                action)
            self.iface.removeToolBarIcon(action)
            
    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = AnnotationToLabelDialog()

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        
                
        if result:
            #Creates a new layout
            project = QgsProject.instance()                                  
            manager = project.layoutManager()
            layout = QgsPrintLayout(project)                   
            layoutName = self.dlg.Layoutname_lineEdit.text()
            page_size = self.dlg.pagesizecomboBox.currentText()
            
            if self.dlg.pageorientationcomboBox.currentText() == 'Landscape':
                page_orientation = QgsLayoutItemPage.Orientation.Landscape
            if self.dlg.pageorientationcomboBox.currentText() == 'Portrait':
                page_orientation = QgsLayoutItemPage.Orientation.Portrait
            
            layouts_list = manager.printLayouts()
            
            print ('Test1')
            for layout in layouts_list:
                if layout.name() == layoutName:
                    reply = QMessageBox.question(iface.mainWindow(), 'Continue?', 
                    'The layout already exists. Do you want to overwrite it?', QMessageBox.Yes, QMessageBox.No)
                    if reply == QMessageBox.No: 
                        return self.dontdonothing()
                        
                    if reply == QMessageBox.Yes:
                       manager.removeLayout(layout)
                       continue 

            #define layout name
            newlayout = QgsPrintLayout(project)    
            newlayout.setName(layoutName)
            newlayout.initializeDefaults()
            #define layout page size
            pc = newlayout.pageCollection()
            pc.pages()[0].setPageSize(page_size, page_orientation)
            manager.addLayout(newlayout)

            layout_page_size_w=pc.pages()[0].pageSize().width()
            layout_page_size_h=pc.pages()[0].pageSize().height()

            map=QgsLayoutItemMap(newlayout)
            map.setRect(10,10,10,10)
            #map.zoomToExtent(iface.mapCanvas().extent())
            map.setExtent(iface.mapCanvas().extent())
            ###map.setScale(iface.mapCanvas().scale())
            map.attemptMove(QgsLayoutPoint(5,5,QgsUnitTypes.LayoutMillimeters))
            map.attemptResize(QgsLayoutSize(layout_page_size_w-10,layout_page_size_h-10, QgsUnitTypes.LayoutMillimeters))
            map.setFrameEnabled(True)
            
            newlayout.addLayoutItem(map)

            map_extent_x_min=map.extent().xMinimum()
            map_extent_y_min=map.extent().yMinimum()
            map_extent_x_max=map.extent().xMaximum()
            map_extent_y_max=map.extent().yMaximum()
            ext_geom = QgsGeometry.fromRect(map.extent())

            max_x_lenght= map_extent_x_max - map_extent_x_min
            max_y_lenght= map_extent_y_min - map_extent_y_max
            
            ##north arrow
            arrow_image = QgsApplication.svgPaths()[0] + "arrows/Arrow_03.svg"
            north = QgsLayoutItemPicture(newlayout)
            north.setPicturePath(arrow_image)
            newlayout.addLayoutItem(north)
            north.attemptResize(QgsLayoutSize(layout_page_size_w*0.05,layout_page_size_h*0.08,QgsUnitTypes.LayoutMillimeters))
            north.attemptMove(QgsLayoutPoint(5,5,QgsUnitTypes.LayoutMillimeters))

            ### Collect the txt from annotation and creates the label
            ann_list = []
            manager_annotation = QgsProject.instance().annotationManager()
            for i in manager_annotation.annotations():
                a = (i.document())
                ann_text = a.toPlainText() # testo annotazione
                ann_list.append(ann_text)
                pos = (ann_list.index(ann_text))/2 # posizione annotazione nella lista
                x_annot = i.mapPosition().x()   
                y_annot = i.mapPosition().y() 
                i_geom = QgsGeometry.fromPointXY(i.mapPosition())

                if i_geom.within(ext_geom):
                    x_lenght_to_0 = (x_annot- map_extent_x_min)*layout_page_size_w
                    x_on_map = x_lenght_to_0/max_x_lenght
                        
                    y_lenght_to_0 = (y_annot- map_extent_y_max)*layout_page_size_h
                    y_on_map = y_lenght_to_0/max_y_lenght
                   
                    ###label creation 
                    map_label = QgsLayoutItemLabel(newlayout)    
                    map_label.setText(ann_text)
                    map_label.setFont(QFont("MS Shell Dlg 2", 10))
                    map_label.adjustSizeToText() 
                    newlayout.addLayoutItem(map_label)

                    ##label position based on relative coordinates 
                    map_label.attemptMove(QgsLayoutPoint(x_on_map, y_on_map, QgsUnitTypes.LayoutMillimeters))
                i.setVisible(False)
                               
            layout_created = manager.layoutByName(layoutName)
            iface.openLayoutDesigner(layout_created)
            iface.messageBar().pushMessage(
            "Annotation To Label Plugin", 
            "All Text Annotations are now temporarily hidden.To re-show them, use the tool in the plugin toolbar.",
            level=Qgis.Info, duration=0)

    def hideTextAnnotations(self):
        """Run method that performs all the real work"""
        manager_annotation = QgsProject.instance().annotationManager()
        for i in manager_annotation.annotations():
            i.setVisible(False)
            
    def showTextAnnotations(self):
        """Run method that performs all the real work"""
        manager_annotation = QgsProject.instance().annotationManager()
        for i in manager_annotation.annotations():
            i.setVisible(True)
  
    def removeTextAnnotations(self):
        """Run method that performs all the real work"""
        manager = QgsProject.instance().annotationManager()
        for i in manager.annotations():
           manager.removeAnnotation(i)
           
    def dontdonothing(self):
        pass
    