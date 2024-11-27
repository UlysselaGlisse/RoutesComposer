"""Event handlers for RoutesComposerDialog."""

from qgis.core import QgsProject, Qgis
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface

from ... import config
from ...func.routes_composer import RoutesComposer

from ..sub_dialog import InfoDialog


class EventHandlers(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

    def toggle_script(self):
        try:
            if not config.script_running:
                if not self.dialog.layer_manager.check_layers_and_columns():
                    return
                self.dialog.layer_manager.save_selected_layers_and_columns()

                routes_composer = RoutesComposer.get_instance()
                if not routes_composer.is_connected:
                    routes_composer.connect()

                if self.dialog.tool:
                    self.dialog.tool.update_icon()
                    self.dialog.update_ui_state()
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
        if self.dialog.ui.geom_checkbox.isChecked():
            self.dialog.ui.geom_checkbox.setChecked(False)

        routes_composer = RoutesComposer.get_instance()
        if routes_composer.is_connected:
            routes_composer.disconnect_routes_composer()
            routes_composer.destroy_instance()

            if self.dialog.tool:
                self.dialog.tool.update_icon()
                self.dialog.update_ui_state()

    def on_geom_on_fly_check(self, state):
        project = QgsProject.instance()
        if project:
            project.writeEntry("routes_composer", "geom_on_fly", bool(state))
            project.setDirty(True)
            geom_on_fly = bool(state)

            if (
                geom_on_fly
                and self.dialog.layer_manager.check_layers_and_columns()
            ):
                routes_composer = RoutesComposer.get_instance()
                routes_composer.connect_geom()
            else:
                routes_composer = RoutesComposer.get_instance()
                routes_composer.disconnect_geom()

    def show_info(self):

        info_dialog = InfoDialog()
        info_dialog.exec_()

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
