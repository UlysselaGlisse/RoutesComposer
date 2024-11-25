"""Event handlers for RoutesComposerDialog."""

from qgis.core import QgsProject, Qgis, QgsWkbTypes, QgsVectorLayer
from qgis.PyQt.QtCore import QObject, QSettings, QVariant
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface

from ... import config
from ...func.routes_composer import RoutesComposer

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
                    or not self.dialog.ui.segments_column_combo.currentText()
                    or not self.dialog.ui.id_column_combo.currentText()
                ):
                    QMessageBox.warning(
                        self.dialog,
                        self.tr("Attention"),
                        self.tr(
                            "Veuillez sélectionner les couches segments et compositions"
                        ),
                    )
                    return

                if (
                    self.dialog.layer_manager.selected_segments_layer.geometryType()
                    != QgsWkbTypes.LineGeometry
                ):
                    QMessageBox.warning(
                        self.dialog,
                        self.tr("Attention"),
                        self.tr(
                            "Veuillez sélectionnez une couche segments de type LineString"
                        ),
                    )
                    return

                compositions_layer = (
                    self.dialog.layer_manager.selected_compositions_layer
                )
                segments_column_name = (
                    self.dialog.ui.segments_column_combo.currentText()
                )
                if (
                    not compositions_layer
                    or not self.is_segments_column_valid(
                        compositions_layer, segments_column_name
                    )
                ):
                    QMessageBox.warning(
                        self.dialog,
                        self.tr("Erreur de validation"),
                        self.tr(
                            "La colonne 'segments' de la couche 'compositions' doit être de type texte et ne peut contenir que des chiffres et des virgules."
                        ),
                    )
                    return

                self.save_selected_layers_and_columns()

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
        log("r")
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
            routes_composer.disconnect()
            routes_composer.disconnect()
            routes_composer.destroy_instance()

            if self.dialog.tool:
                self.dialog.tool.update_icon()
                self.dialog.update_ui_state()

    def validate_segments_column(self):
        compositions_layer = (
            self.dialog.layer_manager.selected_compositions_layer()
        )
        segments_column_name = (
            self.dialog.ui.segments_column_combo.currentText()
        )

        if (
            compositions_layer is None
            or segments_column_name not in compositions_layer.fields().names()
        ):
            return False

        return compositions_layer, segments_column_name

    def is_segments_column_valid(
        self, compositions_layer, segments_column_name
    ):
        segment_field = compositions_layer.fields().field(
            segments_column_name
        )

        if segment_field.type() != QVariant.String:
            return False

        count = 0
        max_features = 2

        for feature in compositions_layer.getFeatures():
            if count >= max_features:
                break

            segment_value = feature[segments_column_name]
            if not self.validate_segment_value(segment_value):
                return False

            count += 1

        return True

    def validate_segment_value(self, value):

        if value is None:
            return False

        if not isinstance(value, str):
            return False

        if not value.strip():
            return False

        if all(c.isdigit() or c == "," for c in value.strip()):
            return True

    def on_geom_on_fly_check(self, state):
        log("r")
        project = QgsProject.instance()
        if project:
            project.writeEntry("routes_composer", "geom_on_fly", bool(state))
            project.setDirty(True)
            geom_on_fly = bool(state)

            if geom_on_fly:
                routes_composer = RoutesComposer.get_instance()
                routes_composer.connect_geom()
            else:
                routes_composer = RoutesComposer.get_instance()
                routes_composer.disconnect_geom()

    def save_selected_layers_and_columns(self):
        log("r")
        project = QgsProject.instance()
        if project:
            settings = QSettings()

            segments_id = self.dialog.ui.segments_combo.currentData()
            settings.setValue(
                "routes_composer/segments_layer_id", segments_id
            )

            compositions_id = self.dialog.ui.compositions_combo.currentData()
            settings.setValue(
                "routes_composer/compositions_layer_id", compositions_id
            )

            id_column = self.dialog.ui.id_column_combo.currentText()
            settings.setValue("routes_composer/id_column_name", id_column)

            segments_column = (
                self.dialog.ui.segments_column_combo.currentText()
            )
            settings.setValue(
                "routes_composer/segments_column_name", segments_column
            )

            project.setDirty(True)

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
