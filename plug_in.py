import os.path
from typing import cast

from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTimer, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .ctrl.connexions_handler import ConnexionsHandler
from .func.list_constructor import IDsBasket
from .ui.main_dialog.main import RoutesComposerDialog


class RoutesComposerTool:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None
        self.actions = []
        self.menu = "Routes Composer Tool"
        self.toolbar = self.iface.addToolBar("Routes Composer")
        self.toolbar.setObjectName("RoutesComposerToolbar")
        self.connexions_handler = ConnexionsHandler()

        self.project = QgsProject.instance()
        if self.project:
            self.project.readProject.connect(self.on_project_load)
            self.project.layerRemoved.connect(self.update_icon)

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
                """Sélectionner des entités sur la carte et ouvrir le formulaire d'attributs<br><br><b>z</b> : retire le dernier segment du panier<br><b>r</b> : le rétabli<br><b>e</b> : vide la panier<br><b>alt + clique</b> : sélectionne tous les segments d'une composition<br><b>shift + clique-droit</b> : copie la liste dans le presse-papier<br><b>q</b> : quitte l'outil""",
            ),
            self.iface.mainWindow(),
        )
        self.ids_basket_action.setCheckable(True)
        self.ids_basket_action.triggered.connect(self.toggle_ids_basket)
        self.toolbar.addAction(self.ids_basket_action)
        self.actions.append(self.ids_basket_action)

    def on_project_load(self):
        if self.project:
            auto_start, _ = self.project.readBoolEntry(
                "routes_composer", "auto_start", False
            )
            if auto_start:
                QTimer.singleShot(1000, self.auto_start_script)

    def auto_start_script(self):
        if self.project:
            auto_start, _ = self.project.readBoolEntry(
                "routes_composer", "auto_start", False
            )

            if self.checks_layers():
                if auto_start:
                    self.connexions_handler.connect_routes_composer()

            self.update_icon()

    def checks_layers(self):
        settings = QSettings()
        if self.project:
            saved_segments_layer_id, _ = self.project.readEntry(
                "routes_composer", "segments_layer_id", ""
            )
            saved_compositions_layer_id = settings.value(
                "routes_composer/compositions_layer_id", ""
            )
            if not self.project.mapLayer(
                saved_segments_layer_id
            ) or not self.project.mapLayer(saved_compositions_layer_id):
                return False

            return True

    def activate_ids_basket(self):
        if not self.project:
            return
        settings = QSettings()
        segments_layer_id, _ = self.project.readEntry(
            "routes_composer", "segments_layer_id", ""
        )
        segments_layer = cast(QgsVectorLayer, self.project.mapLayer(segments_layer_id))
        if segments_layer is None:
            return

        compositions_layer_id = settings.value(
            "routes_composer/compositions_layer_id", ""
        )
        compositions_layer = cast(
            QgsVectorLayer, self.project.mapLayer(compositions_layer_id)
        )
        if compositions_layer is None:
            return

        segments_column_name = settings.value(
            "routes_composer/segments_column_name", "segments"
        )
        if segments_column_name not in compositions_layer.fields().names():
            return

        seg_id_column_name = settings.value("routes_composer/seg_id_column_name", "id")
        if seg_id_column_name not in segments_layer.fields().names():
            return

        if segments_layer.isValid():
            canvas = self.iface.mapCanvas()
            tool = IDsBasket(
                canvas,
                segments_layer,
                compositions_layer,
                seg_id_column_name,
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

    def unload(self):
        for action in self.actions:
            self.iface.removeToolBarIcon(action)
            self.iface.removePluginMenu(self.menu, action)
        if self.dialog:
            self.dialog.close()
        del self.toolbar
        if self.connexions_handler.routes_composer_connected:
            self.connexions_handler.delete_routes_composer()

    def update_icon(self):
        icon_path = os.path.join(
            os.path.dirname(__file__),
            "ui",
            "icons",
            (
                "icon_run.png"
                if ConnexionsHandler.routes_composer_connected is True
                else "icon_stop.png"
            ),
        )
        self.actions[0].setIcon(QIcon(icon_path))

    def show_dialog(self):
        if self.dialog is None:
            self.dialog = RoutesComposerDialog(self.iface.mainWindow(), self)
        self.dialog.show()
        self.dialog.activateWindow()
