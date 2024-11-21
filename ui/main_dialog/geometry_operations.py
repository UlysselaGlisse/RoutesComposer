"""Handle geometries operation of the main dialog"""
from typing import cast
from qgis.core import QgsVectorLayer
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface

from ... import config
from ...func.geom_compo import GeomCompo
from ...func.utils import get_features_list
from ...func.warning import verify_segments
from ..sub_dialog import ErrorDialog


class GeometryOperations:
    def __init__(self, dialog):
        self.dialog = dialog

    def create_geometries(self):
        """Create geometries of the compositions."""
        if not self.dialog.ui.segments_combo.currentData() or not self.dialog.ui.compositions_combo.currentData():
            QMessageBox.warning(self.dialog, self.dialog.tr("Attention"),
                              self.dialog.tr("Veuillez sélectionner les couches segments et compositions"))
            return

        segments_layer = cast(QgsVectorLayer, self.dialog.layer_manager.selected_segments_layer)
        compositions_layer = cast(QgsVectorLayer, self.dialog.layer_manager.selected_compositions_layer)
        segments_column_name = self.dialog.ui.segments_column_combo.currentText()
        id_column_name = self.dialog.ui.id_column_combo.currentText()

        if segments_column_name not in compositions_layer.fields().names():
            iface.messageBar().pushWarning(
                self.dialog.tr("Erreur"),
                self.dialog.tr("Le champ {ss} n'existe pas dans la couche des compositions.").format(ss=segments_column_name)
            )
            return

        self.setup_progress_bar(compositions_layer)

        config.cancel_request = False
        self.dialog.ui.cancel_button.setVisible(True)
        self.dialog.ui.cancel_button.setEnabled(True)

        geom_compo = GeomCompo(segments_layer, compositions_layer, segments_column_name, id_column_name)
        errors_messages = geom_compo.create_compositions_geometries(self.dialog.ui.progress_bar)

        self.cleanup_after_operation(errors_messages, segments_layer, id_column_name, compositions_layer, segments_column_name)

    def update_geometries(self):
        """Update existing geometries."""
        if not self.dialog.ui.segments_combo.currentData() or not self.dialog.ui.compositions_combo.currentData():
            QMessageBox.warning(self.dialog, self.dialog.tr("Attention"),
                              self.dialog.tr("Veuillez sélectionner les couches segments et compositions"))
            return

        segments_layer = cast(QgsVectorLayer, self.dialog.layer_manager.selected_segments_layer)
        compositions_layer = cast(QgsVectorLayer, self.dialog.layer_manager.selected_compositions_layer)
        segments_column_name = self.dialog.ui.segments_column_combo.currentText()
        id_column_name = self.dialog.ui.id_column_combo.currentText()

        if segments_column_name not in compositions_layer.fields().names():
            iface.messageBar().pushWarning(
                self.dialog.tr("Erreur"),
                self.dialog.tr("Le champ {segments_column_name} n'existe pas dans la couche des compositions.").format(
                    segments_column_name=segments_column_name)
            )
            return

        self.setup_progress_bar(compositions_layer)

        config.cancel_request = False
        self.dialog.ui.cancel_button.setVisible(True)
        self.dialog.ui.cancel_button.setEnabled(True)

        geom_compo = GeomCompo(segments_layer, compositions_layer, segments_column_name, id_column_name)
        errors_messages = geom_compo.update_compositions_geometries(self.dialog.ui.progress_bar)

        self.cleanup_after_operation(errors_messages, segments_layer, id_column_name, compositions_layer, segments_column_name)

    def setup_progress_bar(self, compositions_layer):
        self.dialog.ui.progress_bar.setVisible(True)
        self.dialog.ui.progress_bar.setMinimum(0)
        total_compositions = sum(1 for _ in get_features_list(compositions_layer))
        self.dialog.ui.progress_bar.setMaximum(total_compositions)

    def cleanup_after_operation(self, errors_messages, segments_layer, id_column_name, compositions_layer, segments_column_name):
        self.dialog.ui.progress_bar.setVisible(False)
        self.dialog.ui.cancel_button.setVisible(False)

        if errors_messages:
            error_dialog = ErrorDialog(errors_messages, segments_layer, id_column_name, compositions_layer, segments_column_name, self.dialog)
            error_dialog.show()

        self.dialog.adjustSize()

    def check_errors(self):
        """Vérifie les erreurs de compositions."""
        if (not self.dialog.ui.segments_combo.currentData() or not self.dialog.ui.compositions_combo.currentData()
            or not self.dialog.ui.segments_column_combo.currentText() or not self.dialog.ui.id_column_combo.currentText()):
            QMessageBox.warning(self.dialog, self.dialog.tr("Attention"), self.dialog.tr("Veuillez sélectionner les couches segments et compositions ainsi que leurs colonnes respectives."))
            return

        segments_layer = self.dialog.layer_manager.selected_segments_layer
        compositions_layer = self.dialog.layer_manager.selected_compositions_layer
        segments_column_name = self.dialog.ui.segments_column_combo.currentText()
        id_column_name = self.dialog.ui.id_column_combo.currentText()

        errors = verify_segments(segments_layer, compositions_layer, segments_column_name, id_column_name)

        if errors:
            self.dialog.close()
            error_dialog = ErrorDialog(errors, segments_layer, id_column_name, compositions_layer, segments_column_name)
            error_dialog.show()
        else:
            QMessageBox.information(self.dialog, self.dialog.tr("Aucune erreur"), self.dialog.tr("Aucune erreur détectée."))
