import os.path
from typing import cast
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QTimer, QSettings
from qgis.core import QgsApplication, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import (
    Qt,
    QTimer,
    QSettings,
    QCoreApplication,
    QTranslator
)
from .. import config
from .. import main
from .main_dialog import show_dialog, RoutesComposerDialog
from ..ids_basket import IDsBasket

class RoutesComposerTool:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None
        self.actions = []
        self.menu = 'Routes Composer Tool'
        self.toolbar = self.iface.addToolBar('Routes Composer')
        self.toolbar.setObjectName('RoutesComposerToolbar')
        self.project_loaded = False
        self.script_running = config.script_running
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        project = QgsProject.instance()
        if project:
            project.readProject.connect(self.on_project_load)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'RoutesComposer_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)


    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')
        show_action = QAction(
            QIcon(icon_path),
            'Ouvrir Routes Composer',
            self.iface.mainWindow()
        )
        show_action.triggered.connect(self.show_dialog)
        self.toolbar.addAction(show_action)
        self.actions.append(show_action)

        # Bouton pour select_tool
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'ids_basket.png')
        self.ids_basket_action = QAction(
            QIcon(icon_path),
            QCoreApplication.translate("RoutesManagerTool",'Ouvrir le panier à segments'),
            self.iface.mainWindow()
        )
        self.ids_basket_action.setCheckable(True)
        self.ids_basket_action.triggered.connect(self.toggle_ids_basket)
        self.toolbar.addAction(self.ids_basket_action)
        self.actions.append(self.ids_basket_action)

    def on_project_load(self):
        self.project_loaded = True
        project = QgsProject.instance()
        # Vérifier si l'auto-démarrage est activé pour ce projet
        if project:
            auto_start, _ = project.readBoolEntry("routes_composer", "auto_start", False)
            if auto_start:
                QTimer.singleShot(1000, self.auto_start_script)

    def auto_start_script(self):
        project = QgsProject.instance()
        if project:
            auto_start, _ = project.readBoolEntry("routes_composer", "auto_start", False)
            geom_on_fly, _ = project.readBoolEntry("routes_composer", "geom_on_fly", False)

            if auto_start:
                main.start_routes_composer()
                config.script_running = True
            if geom_on_fly:
                success = main.start_geom_on_fly()
                if success:
                    config.geom_on_fly_running = True
            self.update_icon()

    def activate_ids_basket(self):
        project = QgsProject.instance()
        if not project:
            return
        settings = QSettings()
        segments_layer_id = settings.value("routes_composer/segments_layer_id", "")
        segments_layer = cast(QgsVectorLayer, project.mapLayer(segments_layer_id))
        if segments_layer is None:
            return
        if 'id' not in segments_layer.fields().names():
            return

        if segments_layer.isValid():
            canvas = self.iface.mapCanvas()
            tool = IDsBasket(canvas, segments_layer, id_field='id')
            canvas.setMapTool(tool)

    def toggle_ids_basket(self):
        if self.ids_basket_action.isChecked():
            self.activate_ids_basket()
        else:
            self.deactivate_ids_basket()

    def deactivate_ids_basket(self):
        canvas = self.iface.mapCanvas()
        self.ids_basket_action.setChecked(False)

    def unload(self):
        """Supprime les éléments de l'interface"""
        for action in self.actions:
            self.iface.removeToolBarIcon(action)
            self.iface.removePluginMenu(self.menu, action)
        if self.dialog:
            self.dialog.close()
        del self.toolbar

    def update_icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon_run.png' if config.script_running is True else 'icon_stop.png')
        self.actions[0].setIcon(QIcon(icon_path))

    def show_dialog(self):
        """Affiche la fenêtre de dialogue"""
        if self.dialog is None:
            self.dialog = RoutesComposerDialog(self.iface.mainWindow(), self)
        self.dialog.show()
        self.dialog.activateWindow()
