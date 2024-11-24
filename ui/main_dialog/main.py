"""Main dialog class. Dialog that's open when clicking on the icon."""

import os
from qgis.core import QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator
from qgis.PyQt.QtWidgets import QDialog
from qgis.utils import iface

from ... import config
from .advanced_options import AdvancedOptions
from .event_handlers import EventHandlers
from .geometry_operations import GeometryOperations
from .layer_management import LayerManager
from .ui_builder import UiBuilder
from ...func.utils import log


def show_dialog():
    dialog = RoutesComposerDialog(iface.mainWindow())
    dialog.show()
    return dialog


class RoutesComposerDialog(QDialog):

    def __init__(self, parent=None, tool=None):
        super().__init__(parent)
        self.tool = tool
        self.setWindowTitle(self.tr("Compositeur de Routes"))
        self.setMinimumWidth(400)
        self.initial_size = self.size()

        self.ui = UiBuilder(self)
        self.event_handlers = EventHandlers(self)
        self.layer_manager = LayerManager(self)
        self.geometry_ops = GeometryOperations(self)
        self.advanced_options = AdvancedOptions(self)

        self.ui.init_ui()
        self.load_settings()
        self.setup_signals()
        self.update_ui_state()

        self.translator = QTranslator()

    def load_styles(self):
        with open(
            os.path.join(os.path.dirname(__file__), "..", "styles.css"), "r"
        ) as f:
            return f.read()

    def load_settings(self):
        log("r")
        project = QgsProject.instance()
        if project:
            settings = QSettings()

            auto_start, _ = project.readBoolEntry(
                "routes_composer", "auto_start", False
            )
            self.ui.auto_start_checkbox.setChecked(auto_start)

            geom_on_fly, _ = project.readBoolEntry(
                "routes_composer", "geom_on_fly", False
            )
            self.ui.geom_checkbox.setChecked(geom_on_fly)

            saved_segments_attr = settings.value(
                "routes_composer/segments_attr_name", ""
            )
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
                    self.ui.segments_attr_combo.setCurrentIndex(
                        segments_attr_index
                    )
            if saved_compositions_attr:
                compositions_attr_index = (
                    self.ui.compositions_attr_combo.findText(
                        saved_compositions_attr
                    )
                )
                if compositions_attr_index >= 0:
                    self.ui.compositions_attr_combo.setCurrentIndex(
                        compositions_attr_index
                    )

            self.ui.priority_mode_combo.setCurrentText(saved_priority_mode)

    def setup_signals(self):
        self.ui.segments_combo.currentIndexChanged.connect(
            self.layer_manager.on_segments_layer_selected
        )
        self.ui.compositions_combo.currentIndexChanged.connect(
            self.layer_manager.on_compositions_layer_selected
        )
        self.ui.segments_column_combo.currentTextChanged.connect(
            self.layer_manager.on_segments_column_selected
        )
        self.ui.id_column_combo.currentTextChanged.connect(
            self.layer_manager.on_id_column_selected
        )

        self.ui.segments_attr_combo.currentTextChanged.connect(
            self.advanced_options.on_segments_attr_selected
        )
        self.ui.compositions_attr_combo.currentTextChanged.connect(
            self.advanced_options.on_compositions_attr_selected
        )
        self.ui.priority_mode_combo.currentTextChanged.connect(
            self.advanced_options.on_priority_mode_selected
        )

    def update_ui_state(self):
        if config.script_running:
            self.ui.start_button.setText(self.tr("Arrêter"))
            self.ui.status_label.setText(
                self.tr("Status: En cours d'exécution")
            )
        else:
            self.ui.start_button.setText(self.tr("Démarrer"))
            self.ui.status_label.setText(self.tr("Status: Arrêté"))

        self.ui.start_button.setStyleSheet(self.ui.get_start_button_style())

    def closeEvent(self, a0):
        if a0 is not None:
            a0.accept()

    def showEvent(self, a0):
        if a0 is not None:
            log("r")
            super().showEvent(a0)
            self.ui.segments_combo.blockSignals(True)
            self.ui.compositions_combo.blockSignals(True)
            self.ui.segments_attr_combo.blockSignals(True)
            self.ui.compositions_attr_combo.blockSignals(True)

            self.layer_manager.refresh_layers_combo(self.ui.segments_combo)
            self.layer_manager.refresh_layers_combo(
                self.ui.compositions_combo
            )

            self.layer_manager.populate_segments_layer_combo(
                self.ui.segments_combo
            )
            self.layer_manager.populate_compositions_layer_combo(
                self.ui.compositions_combo
            )

            self.ui.segments_combo.blockSignals(False)
            self.ui.compositions_combo.blockSignals(False)
            self.ui.segments_attr_combo.blockSignals(False)
            self.ui.compositions_attr_combo.blockSignals(False)
