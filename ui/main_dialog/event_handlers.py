"""Event handlers for RoutesComposerDialog."""

from qgis.core import Qgis, QgsProject
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface

from ...func.utils import log

from ... import config
from ...main_events_handler import MainEventsHandlers

class EventHandlers(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog
        self.main_events_handler = MainEventsHandlers()

    def toggle_script(self):
        try:
            if not MainEventsHandlers.routes_composer_connected:
                if not self.dialog.layer_manager.check_layers_and_columns():
                    return
                self.dialog.layer_manager.save_selected_layers_and_columns()

                self.main_events_handler.get_routes_composer_instance()

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

        self.main_events_handler.erase_routes_composer_instance()

        if self.dialog.ui.geom_checkbox.isChecked():
            self.dialog.ui.geom_checkbox.setChecked(False)
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
                self.main_events_handler.connect_geom_on_fly()

            elif not geom_on_fly:
                self.main_events_handler.disconnect_geom_on_fly()

    def on_belonging_check(self, state):
        project = QgsProject.instance()
        if project:
            project.writeEntry("routes_composer", "belonging", bool(state))
            project.setDirty(True)

    def show_info(self):
        self.dialog.info.exec_()

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
