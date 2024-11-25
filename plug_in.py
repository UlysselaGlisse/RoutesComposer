import os.path
from typing import cast
from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QTimer, QSettings, QCoreApplication, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from . import config
from .func.routes_composer import (
    routes_composer,
    start_routes_composer,
    start_geom_on_fly,
    stop_routes_composer,
    stop_geom_on_fly,
)
from .list_constructor import IDsBasket
from .ui.main_dialog.main import RoutesComposerDialog
from .func.utils import log


class RoutesComposerTool:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None
        self.actions = []
        self.menu = "Routes Composer Tool"
        self.toolbar = self.iface.addToolBar("Routes Composer")
        self.toolbar.setObjectName("RoutesComposerToolbar")
        self.project_loaded = False
        self.script_running = config.script_running
        self.iface = iface
        project = QgsProject.instance()
        if project:
            project.readProject.connect(self.on_project_load)
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            os.path.dirname(__file__),
            "i18n",
            "RoutesComposer_{}.qm".format(locale),
        )
        self.locale_path = locale_path
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        icon_path = os.path.join(
            os.path.dirname(__file__), "ui", "icons", "icon.png"
        )
        show_action = QAction(
            QIcon(icon_path),
            (
                QCoreApplication.translate(
                    "RoutesManagerTool", "Ouvrir Routes Composer"
                )
            ),
            self.iface.mainWindow(),
        )
        show_action.triggered.connect(self.show_dialog)
        self.toolbar.addAction(show_action)
        self.actions.append(show_action)

        icon_path = os.path.join(
            os.path.dirname(__file__), "ui", "icons", "ids_basket.png"
        )
        self.ids_basket_action = QAction(
            QIcon(icon_path),
            QCoreApplication.translate(
                "RoutesManagerTool", "Ouvrir le panier à segments"
            ),
            self.iface.mainWindow(),
        )
        self.ids_basket_action.setCheckable(True)
        self.ids_basket_action.triggered.connect(self.toggle_ids_basket)
        self.toolbar.addAction(self.ids_basket_action)
        self.actions.append(self.ids_basket_action)

    def on_project_load(self):
        log("r")
        self.reset_plugin_state()
        project = QgsProject.instance()
        if project:
            auto_start, _ = project.readBoolEntry(
                "routes_composer", "auto_start", False
            )
            log(f"auto_start value {auto_start}")
            if auto_start:
                QTimer.singleShot(1000, self.auto_start_script)

    def auto_start_script(self):
        project = QgsProject.instance()
        if project:
            auto_start, _ = project.readBoolEntry(
                "routes_composer", "auto_start", False
            )
            geom_on_fly, _ = project.readBoolEntry(
                "routes_composer", "geom_on_fly", False
            )
            if auto_start:
                start_routes_composer()
            if geom_on_fly:
                start_geom_on_fly()
            self.update_icon()

    def activate_ids_basket(self):
        project = QgsProject.instance()
        if not project:
            return
        settings = QSettings()
        segments_layer_id = settings.value(
            "routes_composer/segments_layer_id", ""
        )
        segments_layer = cast(
            QgsVectorLayer, project.mapLayer(segments_layer_id)
        )
        if segments_layer is None:
            return

        id_column_name = settings.value(
            "routes_composer/id_column_name", "id"
        )
        if id_column_name not in segments_layer.fields().names():
            return

        if segments_layer.isValid():
            canvas = self.iface.mapCanvas()
            tool = IDsBasket(canvas, segments_layer, id_column_name)
            canvas.setMapTool(tool)

    def toggle_ids_basket(self):
        if self.ids_basket_action.isChecked():
            self.activate_ids_basket()
        else:
            self.deactivate_ids_basket()

    def deactivate_ids_basket(self):
        self.ids_basket_action.setChecked(False)

    def reset_plugin_state(self):
        if routes_composer:
            stop_geom_on_fly()
            stop_routes_composer()

        if self.dialog:
            self.dialog.reset_ui_state()
            self.dialog.close()
            self.dialog = None
            self.update_icon()

    def unload(self):
        """Supprime les éléments de l'interface"""
        for action in self.actions:
            self.iface.removeToolBarIcon(action)
            self.iface.removePluginMenu(self.menu, action)
        if self.dialog:
            self.dialog.close()
        del self.toolbar

    def update_icon(self):
        icon_path = os.path.join(
            os.path.dirname(__file__),
            "ui",
            "icons",
            (
                "icon_run.png"
                if config.script_running is True
                else "icon_stop.png"
            ),
        )
        self.actions[0].setIcon(QIcon(icon_path))

    def show_dialog(self):
        """Affiche la fenêtre de dialogue"""
        if self.dialog is None:
            self.dialog = RoutesComposerDialog(self.iface.mainWindow(), self)
        self.dialog.show()
        self.dialog.activateWindow()
