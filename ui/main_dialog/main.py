"""Main dialog class. Dialog that's open when clicking on the icon."""

import os

from qgis.core import QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator
from qgis.PyQt.QtWidgets import QApplication, QDialog
from qgis.utils import iface

from ...ctrl.connexions_handler import ConnexionsHandler
from .advanced_options import AdvancedOptions
from .event_handlers import EventHandlers
from .geometry_operations import GeometryOperations
from .info_dialog import InfoDialog
from .layer_management import LayerManager
from .options import PluginOptions
from .ui_builder import UiBuilder


def show_dialog():
    dialog = RoutesComposerDialog.get_instance(iface.mainWindow())
    dialog.show()
    return dialog


class RoutesComposerDialog(QDialog):
    _instance = None

    @classmethod
    def get_instance(cls, parent=None, tool=None):
        if not cls._instance:
            cls._instance = cls(parent, tool)
        return cls._instance

    def __init__(self, parent=None, tool=None):
        super().__init__(parent)
        self.tool = tool
        self.setWindowTitle(self.tr("Compositeur de Routes"))

        self.project = QgsProject.instance()
        if not self.project:
            return

        self.ui = UiBuilder(self)
        self.info = InfoDialog(self)
        self.layer_manager = LayerManager(self)
        self.event_handlers = EventHandlers(self)
        self.geometry_ops = GeometryOperations(self)
        self.advanced_options = AdvancedOptions(self)
        self.options = PluginOptions(self)

        self.translator = QTranslator()

        self.ui.init_ui()
        self.load_settings()
        self.setup_signals()
        self.ui.init_linkages()
        self.update_ui_state()

    def get_theme_stylesheet(self):
        """Méthode statique pour obtenir le style selon le thème actuel"""
        if QApplication.instance().palette().window().color().lightness() < 128:  # type: ignore
            theme_file = "dark_theme.css"
        else:
            theme_file = "light_theme.css"

        style_file = os.path.join(os.path.dirname(__file__), "..", "styles", theme_file)

        if os.path.exists(style_file):
            with open(style_file, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def load_styles(self):
        return self.get_theme_stylesheet()

    def load_settings(self):
        project = QgsProject.instance()
        if project:
            settings = QSettings()

            self.layer_manager.populate_segments_layer_combo(self.ui.segments_combo)
            self.layer_manager.populate_compositions_layer_combo(
                self.ui.compositions_combo
            )

            auto_start, _ = project.readBoolEntry("routes_composer", "auto_start", False)
            self.ui.auto_start_checkbox.setChecked(auto_start)

            geom_on_fly, _ = project.readBoolEntry(
                "routes_composer", "geom_on_fly", False
            )
            self.ui.geom_checkbox.setChecked(geom_on_fly)

            saved_segments_attr = settings.value("routes_composer/segments_attr_name", "")
            saved_compositions_attr = settings.value(
                "routes_composer/compositions_attr_name", ""
            )
            saved_priority_mode = settings.value(
                "routes_composer/priority_mode", "aucune"
            )

            if saved_segments_attr:
                segments_attr_index = self.ui.segments_attr_combo.findText(
                    saved_segments_attr
                )
                if segments_attr_index >= 0:
                    self.ui.segments_attr_combo.setCurrentIndex(segments_attr_index)
            if saved_compositions_attr:
                compositions_attr_index = self.ui.compositions_attr_combo.findText(
                    saved_compositions_attr
                )
                if compositions_attr_index >= 0:
                    self.ui.compositions_attr_combo.setCurrentIndex(
                        compositions_attr_index
                    )

            self.ui.priority_mode_combo.setCurrentText(saved_priority_mode)

            belonging, _ = project.readBoolEntry("routes_composer", "belonging", False)
            self.ui.update_belonging_segments_checkbox.setChecked(belonging)

    def setup_signals(self):
        # Layers

        self.ui.segments_combo.currentIndexChanged.connect(
            self.layer_manager.on_segments_layer_selected
        )
        self.ui.compositions_combo.currentIndexChanged.connect(
            self.layer_manager.on_compositions_layer_selected
        )

        # Routes composer

        self.ui.start_button.clicked.connect(self.event_handlers.toggle_script)
        self.ui.auto_start_checkbox.stateChanged.connect(
            self.event_handlers.on_auto_start_check
        )

        # Info

        self.ui.info_button.clicked.connect(self.event_handlers.show_info)

        # Geom

        self.ui.geom_checkbox.stateChanged.connect(
            self.event_handlers.on_geom_on_fly_check
        )
        self.ui.check_errors_button.clicked.connect(self.geometry_ops.check_errors)
        self.ui.create_or_update_geom_button.clicked.connect(
            self.geometry_ops.create_geometries
        )
        self.ui.cancel_button.clicked.connect(self.event_handlers.cancel_process)

        # Advanced options

        self.ui.segments_attr_combo.currentTextChanged.connect(
            self.advanced_options.on_segments_attr_selected
        )
        self.ui.compositions_attr_combo.currentTextChanged.connect(
            self.advanced_options.on_compositions_attr_selected
        )
        self.ui.priority_mode_combo.currentTextChanged.connect(
            self.advanced_options.on_priority_mode_selected
        )
        self.ui.update_attributes_button.clicked.connect(
            self.advanced_options.start_attribute_linking
        )

        self.ui.save_linkage_button.clicked.connect(self.event_handlers.save_linkage)

        # Appartenance des segments

        self.ui.belonging_segments_button.clicked.connect(
            self.advanced_options.create_or_update_belonging_column
        )
        self.ui.update_belonging_segments_checkbox.stateChanged.connect(
            self.event_handlers.on_belonging_check
        )

        # options
        self.ui.settings_button.clicked.connect(self.event_handlers.show_config)

    def update_ui_state(self):
        if ConnexionsHandler.routes_composer_connected:
            self.ui.start_button.setText(self.tr("Arrêter"))
            self.ui.status_label.setText(self.tr("Status: En cours d'exécution"))
        else:
            self.ui.start_button.setText(self.tr("Démarrer"))
            self.ui.status_label.setText(self.tr("Status: Arrêté"))

        self.ui.start_button.setStyleSheet(self.ui.get_start_button_style())

    def closeEvent(self, a0):
        if a0 is not None:
            a0.accept()

    def showEvent(self, a0):
        if a0 is not None:
            super().showEvent(a0)
            self.update_ui_state()

            self.ui.segments_combo.blockSignals(True)
            self.ui.compositions_combo.blockSignals(True)
            self.ui.segments_attr_combo.blockSignals(True)
            self.ui.compositions_attr_combo.blockSignals(True)

            self.layer_manager.refresh_layers_combo(self.ui.segments_combo)
            self.layer_manager.refresh_layers_combo(self.ui.compositions_combo)

            self.layer_manager.populate_segments_layer_combo(self.ui.segments_combo)
            self.layer_manager.populate_compositions_layer_combo(
                self.ui.compositions_combo
            )

            self.ui.segments_combo.blockSignals(False)
            self.ui.compositions_combo.blockSignals(False)
            self.ui.segments_attr_combo.blockSignals(False)
            self.ui.compositions_attr_combo.blockSignals(False)
