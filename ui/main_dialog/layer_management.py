"""Layer and field management for RoutesComposerDialog."""

from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QObject, QSettings, Qt
from ...func.utils import log


class LayerManager(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

    def populate_segments_layer_combo(self, combo):
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

            default_layer_name = "segments"
            default_layer_index = combo.findText(default_layer_name)

            settings = QSettings()
            saved_segments_layer_id = settings.value(
                "routes_composer/segments_layer_id", ""
            )
            log(
                f"valeur enregistrée pour la couche segments: {saved_segments_layer_id}"
            )
            segments_index = combo.findData(saved_segments_layer_id)
            log(f"Segments_index: {segments_index}")

            if segments_index >= 0:
                combo.setCurrentIndex(segments_index)
            elif default_layer_index >= 0:
                combo.setCurrentIndex(default_layer_index)

            self.on_segments_layer_selected()

    def populate_compositions_layer_combo(self, combo):
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

            default_layer_name = "compositions"
            default_layer_index = combo.findText(default_layer_name)

            if default_layer_index >= 0:
                combo.setCurrentIndex(default_layer_index)
            else:
                settings = QSettings()
                saved_compositions_layer_id = settings.value(
                    "routes_composer/compositions_layer_id", ""
                )
                compositions_index = combo.findData(
                    saved_compositions_layer_id
                )
                if compositions_index >= 0:
                    combo.setCurrentIndex(compositions_index)

    def populate_id_column_combo(self, segments_layer):
        self.dialog.ui.id_column_combo.clear()

        if segments_layer:
            field_names = [field.name() for field in segments_layer.fields()]
            self.dialog.ui.id_column_combo.addItems(field_names)

    def populate_segments_column_combo(self, compositions_layer):
        self.dialog.ui.segments_column_combo.clear()

        if compositions_layer:
            field_names = [
                field.name() for field in compositions_layer.fields()
            ]
            self.dialog.ui.segments_column_combo.addItems(field_names)

    def on_segments_layer_selected(self):
        segments_id = self.dialog.ui.segments_combo.currentData()
        log(f"segment_id = {segments_id}")
        project = QgsProject.instance()
        if project:
            self.selected_segments_layer = project.mapLayer(segments_id)
            if self.selected_segments_layer:
                log(
                    f"Segments layer selected: {self.selected_segments_layer.name()}"
                )

                if not self.selected_segments_layer.isSpatial():
                    self.dialog.ui.segments_warning_label.setText(
                        self.tr(
                            "Attention: la couche des segments n'a pas de géométrie"
                        )
                    )
                    self.dialog.ui.segments_warning_label.setVisible(True)
                else:
                    self.dialog.ui.segments_warning_label.setVisible(False)

                self.populate_id_column_combo(self.selected_segments_layer)

                settings = QSettings()
                settings.setValue("routes_composer/id_column_name", "id")
                index = self.dialog.ui.id_column_combo.findText("id")
                if index >= 0:
                    self.dialog.ui.id_column_combo.setCurrentIndex(index)

            settings = QSettings()
            settings.setValue(
                "routes_composer/segments_layer_id", segments_id
            )

        self.dialog.adjustSize()

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
                settings = QSettings()
                settings.setValue(
                    "routes_composer/segments_column_name", "segments"
                )
                index = self.dialog.ui.segments_column_combo.findText(
                    "segments"
                )
                if index >= 0:
                    self.dialog.ui.segments_column_combo.setCurrentIndex(
                        index
                    )

            settings = QSettings()
            settings.setValue(
                "routes_composer/compositions_layer_id", compositions_id
            )

        self.dialog.adjustSize()

    def on_segments_column_selected(self):
        selected_segments_column = (
            self.dialog.ui.segments_column_combo.currentText()
        )

        if selected_segments_column:
            settings = QSettings()
            settings.setValue(
                "routes_composer/segments_column_name",
                selected_segments_column,
            )

            log(
                f"Column of lists of segments selected: {selected_segments_column}"
            )

    def on_id_column_selected(self):
        selected_id_column = self.dialog.ui.id_column_combo.currentText()

        if selected_id_column:
            settings = QSettings()
            settings.setValue(
                "routes_composer/id_column_name", selected_id_column
            )

            log(f"ID column selected: {selected_id_column}")
