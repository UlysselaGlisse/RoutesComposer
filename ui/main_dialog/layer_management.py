"""Layer and field management for RoutesComposerDialog."""

from typing import cast
from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes
from qgis.PyQt.QtCore import (
    QObject,
    QSettings,
    Qt,
    QVariant,
    QCoreApplication,
)
from qgis.PyQt.QtWidgets import QMessageBox
from ...func.utils import log, get_features_list


class LayerManager(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog
        self.segments_manager = None
        self.compositions_layer = None

    def refresh_layers_combo(self, combo):
        combo.clear()

        project = QgsProject.instance()
        if project:
            for layer in project.mapLayers().values():
                if isinstance(layer, QgsVectorLayer):
                    combo.addItem(layer.name(), layer.id())
                    data_provider = layer.dataProvider()
                    if data_provider is not None:
                        full_path = data_provider.dataSourceUri()
                        combo.setItemData(
                            combo.count() - 1,
                            full_path,
                            Qt.ItemDataRole.ToolTipRole,
                        )

    def populate_segments_layer_combo(self, combo):
        settings = QSettings()
        saved_segments_layer_id = settings.value(
            "routes_composer/segments_layer_id", ""
        )

        segments_index = combo.findData(saved_segments_layer_id)
        if segments_index >= 0:
            combo.setCurrentIndex(segments_index)
        else:
            default_index = combo.findText("segments")
            if default_index >= 0:
                combo.setCurrentIndex(default_index)

        self.dialog.ui.id_column_combo.blockSignals(True)
        self.on_segments_layer_selected()
        self.dialog.ui.id_column_combo.blockSignals(False)

    def populate_compositions_layer_combo(self, combo):
        settings = QSettings()
        saved_compositions_layer_id = settings.value(
            "routes_composer/compositions_layer_id", ""
        )

        compositions_index = combo.findData(saved_compositions_layer_id)
        if compositions_index >= 0:
            combo.setCurrentIndex(compositions_index)
        else:
            default_index = combo.findText("compositions")
            if default_index >= 0:
                combo.setCurrentIndex(default_index)

        self.dialog.ui.segments_column_combo.blockSignals(True)
        self.on_compositions_layer_selected()
        self.dialog.ui.segments_column_combo.blockSignals(False)

    def populate_id_column_combo(self, segments_layer):
        self.dialog.ui.id_column_combo.clear()

        if segments_layer:
            field_names = [field.name() for field in segments_layer.fields()]
            self.dialog.ui.id_column_combo.addItems(field_names)

            settings = QSettings()
            saved_id_column = settings.value(
                "routes_composer/id_column_name", ""
            )

            saved_index = self.dialog.ui.id_column_combo.findText(
                saved_id_column
            )
            if saved_index >= 0:
                self.dialog.ui.id_column_combo.setCurrentIndex(saved_index)
            else:
                default_index = self.dialog.ui.id_column_combo.findText("id")
                if default_index >= 0:
                    self.dialog.ui.id_column_combo.setCurrentIndex(
                        default_index
                    )
                elif self.dialog.ui.id_column_combo.count() > 0:
                    self.dialog.ui.id_column_combo.setCurrentIndex(0)

    def populate_segments_column_combo(self, compositions_layer):
        self.dialog.ui.segments_column_combo.clear()

        if compositions_layer:
            field_names = [
                field.name() for field in compositions_layer.fields()
            ]
            self.dialog.ui.segments_column_combo.addItems(field_names)

            settings = QSettings()
            saved_segments_column = settings.value(
                "routes_composer/segments_column_name", ""
            )

            saved_index = self.dialog.ui.segments_column_combo.findText(
                saved_segments_column
            )
            if saved_index >= 0:
                self.dialog.ui.segments_column_combo.setCurrentIndex(
                    saved_index
                )
            else:
                default_index = self.dialog.ui.segments_column_combo.findText(
                    "segments"
                )
                if default_index >= 0:
                    self.dialog.ui.segments_column_combo.setCurrentIndex(
                        default_index
                    )
                elif self.dialog.ui.segments_column_combo.count() > 0:
                    self.dialog.ui.segments_column_combo.setCurrentIndex(0)

    def on_segments_layer_selected(self):
        segments_id = self.dialog.ui.segments_combo.currentData()

        project = QgsProject.instance()
        if project:
            self.segments_layer = cast(
                QgsVectorLayer, project.mapLayer(segments_id)
            )
            if self.segments_layer is not None:
                log(f"Segments layer selected: {self.segments_layer.name()}")
                self.check_segments_layer(message_type="warning")
                self.populate_id_column_combo(self.segments_layer)
                self.dialog.advanced_options.update_segments_attr_combo(
                    self.segments_layer
                )

    def on_compositions_layer_selected(self):
        compositions_id = self.dialog.ui.compositions_combo.currentData()

        project = QgsProject.instance()
        if project:
            self.compositions_layer = cast(
                QgsVectorLayer, project.mapLayer(compositions_id)
            )
            if self.compositions_layer is not None:
                log(
                    f"Compositions layer selected: {self.compositions_layer.name()}"
                )
            if self.check_compositions_layer():
                self.populate_segments_column_combo(self.compositions_layer)
                self.dialog.advanced_options.update_compositions_attr_combo(
                    self.compositions_layer
                )

    def check_layers_and_columns(self):
        if not self.check_segments_layer(message_type="box"):
            return False

        if not self.is_id_column_valid():
            return False

        if not self.is_segments_column_valid():
            return False

        else:
            self.save_selected_layers_and_columns()
            return True

    def save_selected_layers_and_columns(self):
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

    def check_segments_layer(self, message_type="box"):
        if not isinstance(self.segments_layer, QgsVectorLayer):
            raise Exception(
                QCoreApplication.translate(
                    "RoutesComposer",
                    "La couche de segments n'est pas une couche vectorielle valide",
                )
            )
            return False

        if (
            self.segments_layer.geometryType() != QgsWkbTypes.LineGeometry  # type: ignore
        ):  # ignore
            if message_type == "box":
                QMessageBox.warning(
                    self.dialog,
                    self.tr("Attention"),
                    self.tr(
                        "Veuillez sélectionnez une couche segments de type LineString"
                    ),
                )
                return False

            elif message_type == "warning":
                self.dialog.ui.segments_warning_label.setText(
                    self.tr(
                        "Attention: la géométrie de la couche des segments doit être de type LineString"
                    )
                )
                self.dialog.ui.segments_warning_label.setVisible(True)
                return False
        else:
            self.dialog.ui.segments_warning_label.setVisible(False)
            return True

    def is_id_column_valid(self):
        if self.segments_layer is None:
            return False

        id_column_name = self.dialog.ui.id_column_combo.currentText()
        if not id_column_name:
            return False

        if id_column_name not in self.segments_layer.fields().names():
            return False

        id_field = self.segments_layer.fields().field(id_column_name)

        if id_field.type() not in (QVariant.Int, QVariant.LongLong):
            QMessageBox.warning(
                self.dialog,
                self.tr("Erreur de validation"),
                self.tr(
                    "La colonne 'id' de la couche 'segments' doit être de type int."
                ),
            )
            return False

        return True

    def check_compositions_layer(self):
        if not isinstance(self.compositions_layer, QgsVectorLayer):
            return False

        if self.compositions_layer.isSpatial():

            self.dialog.ui.geom_checkbox.setVisible(True)

            self.dialog.ui.create_or_update_geom_button.setText(
                self.tr("Mettre à jour les géométries")
            )
            self.dialog.ui.create_or_update_geom_button.clicked.disconnect()
            self.dialog.ui.create_or_update_geom_button.clicked.connect(
                self.dialog.geometry_ops.update_geometries
            )
        else:
            self.dialog.ui.geom_checkbox.setVisible(False)
            self.dialog.ui.create_or_update_geom_button.setText(
                self.tr("Créer les géométries")
            )
            self.dialog.ui.create_or_update_geom_button.clicked.disconnect()
            self.dialog.ui.create_or_update_geom_button.clicked.connect(
                self.dialog.geometry_ops.create_geometries
            )

        return True

    def is_segments_column_valid(self):
        if self.compositions_layer is None:
            return False

        segments_column_name = (
            self.dialog.ui.segments_column_combo.currentText()
        )
        if not segments_column_name:
            return False

        if (
            segments_column_name
            not in self.compositions_layer.fields().names()
        ):
            return False

        segment_field = self.compositions_layer.fields().field(
            segments_column_name
        )

        if segment_field.type() != QVariant.String:
            QMessageBox.warning(
                self.dialog,
                self.tr("Erreur de validation"),
                self.tr(
                    "La colonne 'segments' de la couche 'compositions' doit être de type texte."
                ),
            )
            return False

        count = 0
        max_features = 10

        for feature in get_features_list(self.compositions_layer):
            if count >= max_features:
                break

            segment_value = feature[segments_column_name]
            if not self.validate_segment_value(segment_value):
                QMessageBox.warning(
                    self.dialog,
                    self.tr("Erreur de validation"),
                    self.tr(
                        "La colonne 'segments' de la couche 'compositions' doit être de type texte et ne peut contenir que des chiffres et des virgules."
                    ),
                )
                return False

            count += 1

        return True

    def validate_segment_value(self, value):
        if value is None or value == "":
            return True

        if isinstance(value, QVariant):
            value = str(value)

        if value.isdigit():
            return True

        if all(c.isdigit() or c == "," for c in value.strip()):
            return True

        return False
