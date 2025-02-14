from qgis.core import QgsProject
from qgis.PyQt.QtCore import QObject, QSettings, QVariant
from qgis.PyQt.QtWidgets import QMessageBox

from ...func.attributes import AttributeLinker
from ...func.segments_belonging import SegmentsBelonging
from ...func.utils import log


class AdvancedOptions(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

    def create_or_update_belonging_column(self):
        if (
            self.dialog.layer_manager.segments_layer.providerType()
            == "postgres"
        ):
            QMessageBox.warning(
                self.dialog,
                self.tr("Désolé..."),
                self.tr(
                    "La création d'une nouvelle colonne ne peut se faire directement avec une couche Postgis. "
                    "Veillez ajouter la nouvelle colonne avec la requête: 'ALTER TABLE segments ADD COLUMN compositions'.",
                ),
            )
            return
        project = QgsProject.instance()
        if not project:
            return
        id_field = self.dialog.layer_manager.compositions_layer.fields().field(
            self.dialog.ui.compo_id_column_combo.currentText()
        )
        if id_field.type() not in (QVariant.Int, QVariant.LongLong):
            QMessageBox.warning(
                self.dialog,
                self.tr("Erreur de validation"),
                self.tr(
                    "La colonne des identifiants de la couche 'compositions' doit être de type int."
                ),
            )
            return False

        if self.dialog.layer_manager.check_layers_and_columns():
            self.dialog.layer_manager.save_selected_layers_and_columns()
            belong = SegmentsBelonging(
                self.dialog.layer_manager.segments_layer,
                self.dialog.layer_manager.compositions_layer,
                self.dialog.ui.seg_id_column_combo.currentText(),
                self.dialog.ui.segments_column_combo.currentText(),
                self.dialog.ui.compo_id_column_combo.currentText(),
            )
            belong.create_belonging_column()
            if belong.update_belonging_column():
                self.dialog.layer_manager.segments_layer.reload()
                QMessageBox.information(
                    self.dialog,
                    self.tr("Succès"),
                    self.tr(
                        "La colonne d'appartenance des segments a été mise à jour avec succès."
                    ),
                )
            else:
                QMessageBox.warning(
                    self.dialog,
                    self.tr("Attention"),
                    self.tr(
                        "Une erreur est survenue lors de la mise à jour de la colonne d'appartenance des segments."
                    ),
                )

    def update_segments_attr_combo(self, segments_layer):
        self.dialog.ui.segments_attr_combo.clear()
        if segments_layer:
            field_names = [field.name() for field in segments_layer.fields()]
            self.dialog.ui.segments_attr_combo.addItems(field_names)

            settings = QSettings()
            layer_id = segments_layer.id()
            saved_attr = settings.value(
                f"routes_composer/segments_attr_{layer_id}", ""
            )

            if saved_attr:
                saved_index = self.dialog.ui.segments_attr_combo.findText(
                    saved_attr
                )
                if saved_index >= 0:
                    self.dialog.ui.segments_attr_combo.setCurrentIndex(
                        saved_index
                    )

    def update_compositions_attr_combo(self, compositions_layer):
        self.dialog.ui.compositions_attr_combo.clear()
        if compositions_layer:
            field_names = [
                field.name() for field in compositions_layer.fields()
            ]
            self.dialog.ui.compositions_attr_combo.addItems(field_names)

            settings = QSettings()
            layer_id = compositions_layer.id()

            saved_attr = settings.value(
                f"routes_composer/compositions_attr_{layer_id}", ""
            )

            if saved_attr:
                saved_index = self.dialog.ui.compositions_attr_combo.findText(
                    saved_attr
                )
                if saved_index >= 0:
                    self.dialog.ui.compositions_attr_combo.setCurrentIndex(
                        saved_index
                    )

    def on_segments_attr_selected(self):
        if self.dialog.ui.segments_attr_combo.currentText():
            selected_attr = self.dialog.ui.segments_attr_combo.currentText()
            layer = self.dialog.layer_manager.segments_layer
            if layer:
                settings = QSettings()
                settings.setValue(
                    f"routes_composer/segments_attr_{layer.id()}",
                    selected_attr,
                )
                field_index = (
                    self.dialog.layer_manager.segments_layer.fields().indexOf(
                        selected_attr
                    )
                )
                if field_index != -1:
                    field_type = (
                        self.dialog.layer_manager.segments_layer.fields()
                        .at(field_index)
                        .type()
                    )
                    if field_type == QVariant.String:
                        self.dialog.ui.priority_mode_combo.setCurrentText(
                            "none"
                        )

    def on_compositions_attr_selected(self):
        if self.dialog.ui.compositions_attr_combo.currentText():
            selected_attr = self.dialog.ui.compositions_attr_combo.currentText()
            layer = self.dialog.layer_manager.compositions_layer
            if layer:
                settings = QSettings()
                settings.setValue(
                    f"routes_composer/compositions_attr_{layer.id()}",
                    selected_attr,
                )
                field_index = self.dialog.layer_manager.compositions_layer.fields().indexOf(
                    selected_attr
                )
                if field_index != -1:
                    field_type = (
                        self.dialog.layer_manager.compositions_layer.fields()
                        .at(field_index)
                        .type()
                    )
                    if field_type == QVariant.String:
                        self.dialog.ui.priority_mode_combo.setCurrentText(
                            "none"
                        )

    def on_priority_mode_selected(self):
        selected_priority_mode = (
            self.dialog.ui.priority_mode_combo.currentText()
        )
        settings = QSettings()
        settings.setValue(
            "routes_composer/priority_mode", selected_priority_mode
        )
        log(f"Priority mode selected: {selected_priority_mode}")

    def start_attribute_linking(self):
        compositions_attr = self.dialog.ui.compositions_attr_combo.currentText()
        segments_attr = self.dialog.ui.segments_attr_combo.currentText()
        priority_mode = self.dialog.ui.priority_mode_combo.currentText()

        if (
            not self.dialog.ui.segments_combo.currentData()
            or not self.dialog.ui.compositions_combo.currentData()
            or not compositions_attr
            or not segments_attr
        ):
            QMessageBox.warning(
                self.dialog,
                self.tr("Attention"),
                self.tr(
                    "Veuillez sélectionner les couches segments et compositions ainsi que les attributs."
                ),
            )
            return

        if not self.dialog.layer_manager.check_layers_and_columns():
            return

        if (
            self.dialog.layer_manager.is_column_pk_attribute(
                self.dialog.layer_manager.compositions_layer, compositions_attr
            )
            or self.dialog.layer_manager.is_column_pk_attribute(
                self.dialog.layer_manager.segments_layer, segments_attr
            )
            or self.dialog.layer_manager.is_id_of_routes_composer(
                self.dialog.layer_manager.segments_layer, segments_attr
            )
        ):
            return

        linkage = {
            "compositions_attr": compositions_attr,
            "priority_mode": priority_mode,
            "segments_attr": segments_attr,
        }

        self.attribute_linker = AttributeLinker(
            segments_layer=self.dialog.layer_manager.segments_layer,
            compositions_layer=self.dialog.layer_manager.compositions_layer,
            seg_id_column_name=self.dialog.ui.seg_id_column_combo.currentText(),
            segments_column_name=self.dialog.ui.segments_column_combo.currentText(),
            linkages=[linkage],
        )
        if self.attribute_linker.update_segments_attr_values():
            self.dialog.layer_manager.segments_layer.reload()
            QMessageBox.information(
                self.dialog,
                self.tr("Succès"),
                self.tr(
                    f"L'attribut '{linkage.get('segments_attr', '')}' a été mis à jour avec succès."
                ),
            )

        else:
            QMessageBox.warning(
                self.dialog,
                self.tr("Attention"),
                self.tr(
                    f"Une erreur est survenue lors de la liaison de l'attribut '{linkage.get('segments_attr', '')}'."
                ),
            )
