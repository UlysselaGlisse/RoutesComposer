"""Layer and field management for RoutesComposerDialog."""

from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes
from qgis.PyQt.QtCore import QObject, QSettings, Qt
from ...func.utils import log


class LayerManager(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

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
            self.selected_segments_layer = project.mapLayer(segments_id)
            if self.selected_segments_layer:
                log(
                    f"Segments layer selected: {self.selected_segments_layer.name()}"
                )
                if (
                    self.selected_segments_layer.geometryType()
                    != QgsWkbTypes.LineGeometry
                ):
                    self.dialog.ui.segments_warning_label.setText(
                        self.tr(
                            "Attention: la géométrie de la couche des segments doit être de type ligne"
                        )
                    )
                    self.dialog.ui.segments_warning_label.setVisible(True)
                else:
                    self.dialog.ui.segments_warning_label.setVisible(False)

                self.populate_id_column_combo(self.selected_segments_layer)
                self.dialog.advanced_options.update_segments_attr_combo(
                    self.selected_segments_layer
                )

    def on_compositions_layer_selected(self):
        compositions_id = self.dialog.ui.compositions_combo.currentData()

        project = QgsProject.instance()
        if project:
            self.selected_compositions_layer = project.mapLayer(
                compositions_id
            )
            if self.selected_compositions_layer:
                log(
                    f"Compositions layer selected: {self.selected_compositions_layer.name()}"
                )
                if (
                    isinstance(
                        self.selected_compositions_layer, QgsVectorLayer
                    )
                    and self.selected_compositions_layer.isSpatial()
                ):
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

            if isinstance(self.selected_compositions_layer, QgsVectorLayer):
                self.populate_segments_column_combo(
                    self.selected_compositions_layer
                )
                self.dialog.advanced_options.update_compositions_attr_combo(
                    self.selected_compositions_layer
                )
