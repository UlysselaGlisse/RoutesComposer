"""Event handlers for RoutesComposerDialog."""

from qgis.core import QgsProject, Qgis
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface

from ... import config
from ...func.routes_composer import (
    start_routes_composer,
    stop_routes_composer,
    start_geom_on_fly,
    stop_geom_on_fly,
)
from ..sub_dialog import InfoDialog
from ...func.utils import log


class EventHandlers(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

    def toggle_script(self):
        log("r")

        try:
            if not config.script_running:
                if (
                    not self.dialog.ui.segments_combo.currentData()
                    or not self.dialog.ui.compositions_combo.currentData()
                ):
                    QMessageBox.warning(
                        self.dialog,
                        self.tr("Attention"),
                        self.tr(
                            "Veuillez sélectionner les couches segments et compositions"
                        ),
                    )
                    return

                if not self.dialog.ui.segments_column_combo.currentText():
                    QMessageBox.warning(
                        self.dialog,
                        self.tr("Attention"),
                        self.tr("Veuillez sélectionner la colonne segments"),
                    )
                    return

                start_routes_composer()

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

    def stop_running_routes_composer(self):
        log("r")

        stop_routes_composer()
        self.dialog.ui.geom_checkbox.setChecked(False)

        if self.dialog.tool:
            self.dialog.tool.update_icon()
            self.dialog.update_ui_state()

    def on_auto_start_check(self, state):
        log("r")

        """Save auto-start checkbox state."""
        project = QgsProject.instance()
        if project:
            project.writeEntry("routes_composer", "auto_start", bool(state))
            project.setDirty(True)

    def on_geom_on_fly_check(self, state):
        log("r")

        project = QgsProject.instance()
        if project:
            project.writeEntry("routes_composer", "geom_on_fly", bool(state))
            project.setDirty(True)
            geom_on_fly = bool(state)

            if geom_on_fly:
                start_geom_on_fly()
            else:
                stop_geom_on_fly()

    def show_info(self):
        log("r")

        info_dialog = InfoDialog()
        info_dialog.exec_()

    def cancel_process(self):
        log("r")

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
