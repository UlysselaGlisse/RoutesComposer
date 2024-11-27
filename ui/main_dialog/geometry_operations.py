"""Handle geometries operation of the main dialog"""

from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QMessageBox

from .errors_dialog import ErrorDialog

from ... import config
from ...func.geom_compo import GeomCompo
from ...func.warning import verify_segments


class GeometryOperations(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

    def create_geometries(self):
        if self.dialog.layer_manager.check_layers_and_columns():
            self.setup_progress_bar(
                self.dialog.layer_manager.compositions_layer
            )
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
        if self.dialog.layer_manager.check_layers_and_columns():
            self.setup_progress_bar(
                self.dialog.layer_manager.compositions_layer
            )
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
        total_compositions = (
            self.dialog.layer_manager.compositions_layer.featureCount()
        )
        self.dialog.ui.progress_bar.setMaximum(total_compositions)

        config.cancel_request = False
        self.dialog.ui.cancel_button.setVisible(True)
        self.dialog.ui.cancel_button.setEnabled(True)

    def cleanup_after_operation(self, errors_messages):

        self.dialog.ui.progress_bar.setVisible(False)
        self.dialog.ui.cancel_button.setVisible(False)

        if errors_messages:
            error_dialog = ErrorDialog(self.dialog, errors_messages)

            error_dialog.display_errors(errors_messages)
            error_dialog.exec()

        self.dialog.adjustSize()

    def check_errors(self):
        """Vérifie les erreurs de compositions."""
        if (
            not self.dialog.ui.segments_combo.currentData()
            or not self.dialog.ui.compositions_combo.currentData()
            or not self.dialog.ui.segments_column_combo.currentText()
            or not self.dialog.ui.id_column_combo.currentText()
        ):
            QMessageBox.warning(
                self.dialog,
                self.tr("Attention"),
                self.tr(
                    "Veuillez sélectionner les couches segments et compositions ainsi que leurs colonnes respectives."
                ),
            )
            return

        segments_layer = self.dialog.layer_manager.segments_layer
        compositions_layer = self.dialog.layer_manager.compositions_layer
        segments_column_name = (
            self.dialog.ui.segments_column_combo.currentText()
        )
        id_column_name = self.dialog.ui.id_column_combo.currentText()

        errors = verify_segments(
            segments_layer,
            compositions_layer,
            segments_column_name,
            id_column_name,
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
