import os.path
from typing import cast

from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTimer, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .func.list_constructor import IDsBasket
from .func.utils import log
from .main_events_handler import MainEventsHandlers
from .ui.main_dialog.main import RoutesComposerDialog


class RoutesComposerTool:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None
        self.actions = []
        self.menu = "Routes Composer Tool"
        self.toolbar = self.iface.addToolBar("Routes Composer")
        self.toolbar.setObjectName("RoutesComposerToolbar")
        self.project_loaded = False
        self.main_events_handler = MainEventsHandlers()
        self.iface = iface
        project = QgsProject.instance()
        if project:
            project.readProject.connect(self.on_project_load)
            project.layerRemoved.connect(self.update_icon)

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
        self.iface.mapCanvas().mapToolSet.connect(self.deactivate_ids_basket)

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "ui", "icons", "icon.png")
        show_action = QAction(
            QIcon(icon_path),
            (QCoreApplication.translate("RoutesManagerTool", "Ouvrir Routes Composer")),
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
                "RoutesManagerTool",
                """
                Sélectionner des entités sur la carte et ouvrir le formulaire d'attributs<br>
                <br>
                <b>z</b> : retire le dernier segment du panier<br>
                <b>r</b> : le rétabli<br>
                <b>e</b> : vide la panier<br>
                <b>alt + clique</b> : sélectionne tous les segments d'une composition<br>
                <b>shift + clique-droit</b> : copie la liste dans le presse-papier<br>
                <b>q</b> : quitte l'outil
                """,
            ),
            self.iface.mainWindow(),
        )
        self.ids_basket_action.setCheckable(True)
        self.ids_basket_action.triggered.connect(self.toggle_ids_basket)
        self.toolbar.addAction(self.ids_basket_action)
        self.actions.append(self.ids_basket_action)

    def on_project_load(self):
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
            belonging, _ = project.readBoolEntry("routes_composer", "belonging", False)

            if self.checks_layers():
                if auto_start:
                    self.main_events_handler.connect_routes_composer()
                if geom_on_fly:
                    self.main_events_handler.connect_geom_on_fly()
                if belonging:
                    self.main_events_handler.connect_belonging()

            self.update_icon()

    def checks_layers(self):
        project = QgsProject.instance()
        if project:
            settings = QSettings()
            saved_segments_layer_id = settings.value(
                "routes_composer/segments_layer_id", ""
            )
            saved_compositions_layer_id = settings.value(
                "routes_composer/compositions_layer_id", ""
            )
            if not project.mapLayer(saved_segments_layer_id) or not project.mapLayer(
                saved_compositions_layer_id
            ):
                return False

            return True

    def activate_ids_basket(self):
        project = QgsProject.instance()
        if not project:
            return
        settings = QSettings()
        segments_layer_id = settings.value("routes_composer/segments_layer_id", "")
        segments_layer = cast(QgsVectorLayer, project.mapLayer(segments_layer_id))
        if segments_layer is None:
            return
        compositions_layer_id = settings.value(
            "routes_composer/compositions_layer_id", ""
        )
        compositions_layer = cast(
            QgsVectorLayer, project.mapLayer(compositions_layer_id)
        )
        if compositions_layer is None:
            return

        segments_column_name = settings.value(
            "routes_composer/segments_column_name", "segments"
        )
        if segments_column_name not in compositions_layer.fields().names():
            return

        id_column_name = settings.value("routes_composer/id_column_name", "id")
        if id_column_name not in segments_layer.fields().names():
            return

        if segments_layer.isValid():
            canvas = self.iface.mapCanvas()
            tool = IDsBasket(
                canvas,
                segments_layer,
                compositions_layer,
                id_column_name,
                segments_column_name,
            )
            canvas.setMapTool(tool)

    def toggle_ids_basket(self):
        if self.ids_basket_action.isChecked():
            self.activate_ids_basket()
        else:
            self.ids_basket_action.setChecked(False)

    def deactivate_ids_basket(self, tool):
        if not isinstance(tool, IDsBasket):
            self.ids_basket_action.setChecked(False)

    def reset_plugin_state(self):
        if self.dialog:
            self.dialog.reset_ui_state()
            self.dialog.close()

    def unload(self):
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
            ("icon_run.png" if MainEventsHandlers.routes_composer_connected is True else "icon_stop.png"),
        )
        self.actions[0].setIcon(QIcon(icon_path))

    def show_dialog(self):
        if self.dialog is None:
            self.dialog = RoutesComposerDialog(self.iface.mainWindow(), self)
        self.dialog.show()
        self.dialog.activateWindow()
