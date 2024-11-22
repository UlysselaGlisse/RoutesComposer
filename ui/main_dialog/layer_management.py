"""Layer and field management for RoutesComposerDialog."""
from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QObject, QSettings, Qt
from ...func.utils import log


class LayerManager(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

    def populate_layers_combo(self, combo):
        combo.clear()
        project = QgsProject.instance()
        if project:
            for layer in project.mapLayers().values():
                if isinstance(layer, QgsVectorLayer):
                    combo.addItem(layer.name(), layer.id())
                    data_provider = layer.dataProvider()
                    if data_provider is not None:
                        full_path = data_provider.dataSourceUri()
                        combo.setItemData(combo.count() - 1, full_path, Qt.ItemDataRole.ToolTipRole)
                    else:
                        combo.setItemData(combo.count() - 1, "Data provider not available", Qt.ItemDataRole.ToolTipRole)

    def populate_id_column_combo(self, segments_layer):
        self.dialog.ui.id_column_combo.clear()

        if segments_layer:
            field_names = [field.name() for field in segments_layer.fields()]
            self.dialog.ui.id_column_combo.addItems(field_names)

            settings = QSettings()
            saved_id_column = settings.value("routes_composer/id_column_name", "id")

            if saved_id_column in field_names:
                index = self.dialog.ui.id_column_combo.findText(saved_id_column)
                if index >= 0:
                    self.dialog.ui.id_column_combo.setCurrentIndex(index)

    def populate_segments_column_combo(self, compositions_layer):
        self.dialog.ui.segments_column_combo.clear()

        if compositions_layer:
            field_names = [field.name() for field in compositions_layer.fields()]
            self.dialog.ui.segments_column_combo.addItems(field_names)

            settings = QSettings()
            saved_segments_column = settings.value("routes_composer/segments_column_name", "segments")

            if saved_segments_column in field_names:
                index = self.dialog.ui.segments_column_combo.findText(saved_segments_column)
                if index >= 0:
                    self.dialog.ui.segments_column_combo.setCurrentIndex(index)

    def refresh_combos(self):
        current_segments_id = self.dialog.ui.segments_combo.currentData()
        current_compositions_id = self.dialog.ui.compositions_combo.currentData()

        self.dialog.ui.segments_combo.blockSignals(True)
        self.dialog.ui.compositions_combo.blockSignals(True)

        self.populate_layers_combo(self.dialog.ui.segments_combo)
        self.populate_layers_combo(self.dialog.ui.compositions_combo)

        segments_index = self.dialog.ui.segments_combo.findData(current_segments_id)
        compositions_index = self.dialog.ui.compositions_combo.findData(current_compositions_id)

        if segments_index >= 0:
            self.dialog.ui.segments_combo.setCurrentIndex(segments_index)
        if compositions_index >= 0:
            self.dialog.ui.compositions_combo.setCurrentIndex(compositions_index)

        self.dialog.ui.segments_combo.blockSignals(False)
        self.dialog.ui.compositions_combo.blockSignals(False)

    def on_segments_layer_selected(self):
        segments_id = self.dialog.ui.segments_combo.currentData()

        project = QgsProject.instance()
        if project:
            self.selected_segments_layer = project.mapLayer(segments_id)
            if self.selected_segments_layer:
                log(f"Segments layer selected: {self.selected_segments_layer.name()}")

                if not self.selected_segments_layer.isSpatial():
                    self.dialog.ui.segments_warning_label.setText(
                        self.tr("Attention: la couche des segments n'a pas de géométrie"))
                    self.dialog.ui.segments_warning_label.setVisible(True)
                else:
                    self.dialog.ui.segments_warning_label.setVisible(False)

                self.populate_id_column_combo(self.selected_segments_layer)

            settings = QSettings()
            settings.setValue("routes_composer/segments_layer_id", segments_id)

        self.dialog.adjustSize()

    def on_compositions_layer_selected(self):
        compositions_id = self.dialog.ui.compositions_combo.currentData()

        project = QgsProject.instance()
        if project:
            self.selected_compositions_layer = project.mapLayer(compositions_id)
            if self.selected_compositions_layer:
                log(f"Compositions layer selected: {self.selected_compositions_layer.name()}")
                if isinstance(self.selected_compositions_layer, QgsVectorLayer) and self.selected_compositions_layer.isSpatial():
                    self.dialog.ui.geom_checkbox.setVisible(True)

                    self.dialog.ui.create_or_update_geom_button.setText(
                        self.tr("Mettre à jour les géométries"))
                    self.dialog.ui.create_or_update_geom_button.clicked.disconnect()
                    self.dialog.ui.create_or_update_geom_button.clicked.connect(self.dialog.geometry_ops.update_geometries)
                else:
                    self.dialog.ui.geom_checkbox.setVisible(False)
                    self.dialog.ui.create_or_update_geom_button.setText(
                        self.tr("Créer les géométries"))
                    self.dialog.ui.create_or_update_geom_button.clicked.disconnect()
                    self.dialog.ui.create_or_update_geom_button.clicked.connect(self.dialog.geometry_ops.create_geometries)

            if isinstance(self.selected_compositions_layer, QgsVectorLayer):
                self.populate_segments_column_combo(self.selected_compositions_layer)

            settings = QSettings()
            settings.setValue("routes_composer/compositions_layer_id", compositions_id)

        self.dialog.adjustSize()

    def on_segments_column_selected(self):
        selected_segments_column = self.dialog.ui.segments_column_combo.currentText()

        if selected_segments_column:
            settings = QSettings()
            settings.setValue("routes_composer/segments_column_name", selected_segments_column)

            log(f"Column of lists of segments selected: {selected_segments_column}")

    def on_id_column_selected(self):
        selected_id_column = self.dialog.ui.id_column_combo.currentText()

        if selected_id_column:
            settings = QSettings()
            settings.setValue("routes_composer/id_column_name", selected_id_column)

            log(f"ID column selected: {selected_id_column}")
