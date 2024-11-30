"""Handle geometries operation of the main dialog"""

from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsProject

from ... import config
from ...func.geom_compo import GeomCompo
from ...func.warning import verify_segments
from .errors_dialog import ErrorDialog


class GeometryOperations(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

    def create_geometries(self):
        project = QgsProject.instance()
        if not project:
            return
        if self.dialog.layer_manager.check_layers_and_columns():
            self.setup_progress_bar(self.dialog.layer_manager.compositions_layer)
            geom_compo = GeomCompo(
                self.dialog.layer_manager.segments_layer,
                self.dialog.layer_manager.compositions_layer,
                self.dialog.ui.id_column_combo.currentText(),
                self.dialog.ui.segments_column_combo.currentText(),
            )

            errors_messages = geom_compo.update_compositions_geometries(
                self.dialog.ui.progress_bar, mode="new"
            )
            self.cleanup_after_operation(errors_messages)

    def update_geometries(self):
        project = QgsProject.instance()
        if not project:
            return
        if self.dialog.layer_manager.check_layers_and_columns():
            self.setup_progress_bar(self.dialog.layer_manager.compositions_layer)
            geom_compo = GeomCompo(
                self.dialog.layer_manager.segments_layer,
                self.dialog.layer_manager.compositions_layer,
                self.dialog.ui.id_column_combo.currentText(),
                self.dialog.ui.segments_column_combo.currentText(),
            )
            errors_messages = geom_compo.update_compositions_geometries(
                self.dialog.ui.progress_bar, mode="update"
            )
            self.cleanup_after_operation(errors_messages)

    def setup_progress_bar(self, compositions_layer):
        self.dialog.ui.progress_bar.setVisible(True)
        self.dialog.ui.progress_bar.setMinimum(0)
        total_compositions = self.dialog.layer_manager.compositions_layer.featureCount()
        self.dialog.ui.progress_bar.setMaximum(total_compositions)

        config.cancel_request = False
        self.dialog.ui.cancel_button.setVisible(True)
        self.dialog.ui.cancel_button.setEnabled(True)

    def cleanup_after_operation(self, errors_messages):
        self.dialog.ui.progress_bar.setVisible(False)
        self.dialog.ui.cancel_button.setVisible(False)

        if errors_messages:
            self.error_dialog = ErrorDialog(self.dialog, errors_messages)

            self.error_dialog.display_errors(errors_messages)
            self.error_dialog.show()
        else:
            QMessageBox.information(
                self.dialog,
                self.tr("Création des géométries"),
                self.tr("Aucune erreur détectée durant la création des géométries."),
            )

    def check_errors(self):
        if self.dialog.layer_manager.check_layers_and_columns():
            errors = verify_segments(
                self.dialog.layer_manager.segments_layer,
                self.dialog.layer_manager.compositions_layer,
                self.dialog.ui.segments_column_combo.currentText(),
                self.dialog.ui.id_column_combo.currentText(),
            )

            if errors:
                self.error_dialog = ErrorDialog(
                    self.dialog,
                    errors,
                )
                self.dialog.close()
                self.error_dialog.refresh_errors()
                self.error_dialog.show()
            else:
                QMessageBox.information(
                    self.dialog,
                    self.tr("Aucune erreur"),
                    self.tr("Aucune erreur détectée."),
                )
