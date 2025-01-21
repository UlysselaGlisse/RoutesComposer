"""Event handlers for RoutesComposerDialog."""

from qgis.core import Qgis, QgsProject
from qgis.PyQt.QtCore import QObject, QSettings
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface

from ... import config
from ...connexions_handler import ConnexionsHandler


class EventHandlers(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog
        self.connexions_handler = ConnexionsHandler()

    def toggle_script(self):
        try:
            if not ConnexionsHandler.routes_composer_connected:
                if not self.dialog.layer_manager.check_layers_and_columns():
                    return
                self.dialog.layer_manager.save_selected_layers_and_columns()

                self.connexions_handler.connect_routes_composer()

                self.dialog.update_ui_state()
                if self.dialog.tool:
                    self.dialog.tool.update_icon()
            else:
                self.stop_running_routes_composer()

        except Exception as e:
            QMessageBox.critical(
                self.dialog,
                self.tr("Erreur"),
                self.tr(f"Une erreur est survenue: {str(e)}"),
            )

    def on_auto_start_check(self, state):
        """Save auto-start checkbox state."""
        project = QgsProject.instance()
        if project:
            project.writeEntry("routes_composer", "auto_start", bool(state))
            project.setDirty(True)

    def stop_running_routes_composer(self):
        self.connexions_handler.disconnect_routes_composer()

        if self.dialog.ui.geom_checkbox.isChecked():
            self.dialog.ui.geom_checkbox.setChecked(False)

        if self.dialog.ui.update_belonging_segments_checkbox.isChecked():
            self.dialog.ui.update_belonging_segments_checkbox.setChecked(False)

        if self.dialog.tool:
            self.dialog.tool.update_icon()

        self.dialog.update_ui_state()

    def on_geom_on_fly_check(self, state):
        project = QgsProject.instance()
        if project:
            project.writeEntry("routes_composer", "geom_on_fly", bool(state))
            project.setDirty(True)
            geom_on_fly = bool(state)

            if geom_on_fly and self.dialog.layer_manager.check_layers_and_columns():
                self.dialog.layer_manager.save_selected_layers_and_columns()
                self.connexions_handler.connect_geom_on_fly()

            elif not geom_on_fly:
                self.connexions_handler.disconnect_geom_on_fly()

    def on_belonging_check(self, state):
        project = QgsProject.instance()
        if project:
            project.writeEntry("routes_composer", "belonging", bool(state))
            project.setDirty(True)
            belonging = bool(state)

            if belonging and self.dialog.layer_manager.check_layers_and_columns():
                self.connexions_handler.connect_belonging()
            elif not belonging:
                self.connexions_handler.disconnect_belonging()

    def save_linkage(self):
        self.compositions_attr = self.dialog.ui.compositions_attr_combo.currentText()
        self.segments_attr = self.dialog.ui.segments_attr_combo.currentText()
        self.priority_mode = self.dialog.ui.priority_mode_combo.currentText()

        settings = QSettings()
        linkages = settings.value("routes_composer/attribute_linkages", []) or []

        new_linkage = {
            "compositions_attr": self.compositions_attr,
            "segments_attr": self.segments_attr,
            "priority_mode": self.priority_mode,
        }

        if new_linkage not in linkages:
            linkages.append(new_linkage)
            settings.setValue("routes_composer/attribute_linkages", linkages)
            self.dialog.ui.add_linkage_to_ui(new_linkage)

    def show_info(self):
        self.dialog.info.exec_()

    def show_config(self):
        self.dialog.options.load_options()
        self.dialog.options.exec_()

    def cancel_process(self):
        config.cancel_request = True
        self.dialog.ui.cancel_button.setEnabled(False)
        iface.messageBar().pushMessage(
            "Info",
            self.tr("Annulation en cours..."),
            level=Qgis.MessageLevel.Info,
        )
        self.dialog.ui.progress_bar.setVisible(False)
        self.dialog.ui.cancel_button.setVisible(False)
        self.dialog.resize(self.dialog.initial_size)
        self.dialog.adjustSize()
