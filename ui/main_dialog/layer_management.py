"""Layer and field management for RoutesComposerDialog."""

import re
from typing import cast

from qgis.core import QgsVectorLayer, QgsWkbTypes
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QObject,
    QSettings,
    Qt,
    QVariant,
)
from qgis.PyQt.QtWidgets import QMessageBox

from ...ctrl.connexions_handler import ConnexionsHandler
from ...func.utils import log
from ...routes_composer import RoutesComposer


class LayerManager(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog
        self.project = self.dialog.project
        self.settings = QSettings()

    def refresh_layers_combo(self, combo):
        if self.project:
            combo.clear()

            for layer in self.project.mapLayers().values():
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

    # def populate_layer_combo(self, combo, type_name):
    #     """
    #     Popule le combo avec les couches de type QgsVectorLayer.
    #     :param combo: QComboBox à remplir.
    #     :param type_name: Nom du type de couche ('segments' ou 'compositions').
    #     """
    #     if self.project:
    #         saved_layer_id, _ = self.project.readEntry(
    #             "routes_composer", f"{type_name}_layer_id", ""
    #         )
    #         combo.clear()

    #         # Ajouter les couches de la carte
    #         for layer in self.project.mapLayers().values():
    #             if isinstance(layer, QgsVectorLayer):
    #                 combo.addItem(layer.name(), layer.id())
    #                 data_provider = layer.dataProvider()
    #                 if data_provider is not None:
    #                     full_path = data_provider.dataSourceUri()
    #                     combo.setItemData(
    #                         combo.count() - 1,
    #                         full_path,
    #                         Qt.ItemDataRole.ToolTipRole,
    #                     )

    #         # Sélectionner la couche enregistrée ou selon le nom
    #         if saved_layer_id:
    #             index = combo.findData(saved_layer_id)
    #             if index >= 0:
    #                 combo.setCurrentIndex(index)
    #             else:
    #                 regex_pattern = r"^" + type_name + r"s?[_]|[_]?" + type_name + r"s?$"
    #                 for i in range(combo.count()):
    #                     if re.search(regex_pattern, combo.itemText(i), re.IGNORECASE):
    #                         combo.setCurrentIndex(i)
    #                         break

    def populate_segments_layer_combo(self, combo):
        if self.project:
            saved_segments_layer_id, _ = self.project.readEntry(
                "routes_composer", "segments_layer_id", ""
            )
            segments_index = combo.findData(saved_segments_layer_id)

            if segments_index >= 0:
                combo.setCurrentIndex(segments_index)
            else:
                segments_pattern = re.compile(
                    r"^segment?s?[_]|[_]?segment?s?$", re.IGNORECASE
                )
                for i in range(combo.count()):
                    if segments_pattern.search(combo.itemText(i)):
                        combo.setCurrentIndex(i)
                        break

        self.on_segments_layer_selected()

    def populate_compositions_layer_combo(self, combo):
        if self.project:
            saved_compositions_layer_id = self.settings.value(
                "routes_composer/compositions_layer_id", ""
            )
            log(saved_compositions_layer_id)
            compositions_index = combo.findData(saved_compositions_layer_id)

            if compositions_index >= 0:
                combo.setCurrentIndex(compositions_index)
            else:
                compositions_pattern = re.compile(
                    r"^composition?s?[_]|[_]?composition?s?$", re.IGNORECASE
                )
                for i in range(combo.count()):
                    if compositions_pattern.search(combo.itemText(i)):
                        combo.setCurrentIndex(i)
                        break

        self.on_compositions_layer_selected()

    def populate_seg_id_column_combo(self, segments_layer):
        self.dialog.ui.seg_id_column_combo.clear()

        if segments_layer:
            field_names = [field.name() for field in segments_layer.fields()]
            self.dialog.ui.seg_id_column_combo.addItems(field_names)

            seg_id_column_name = self.settings.value(
                "routes_composer/seg_id_column_name", ""
            )
            seg_id_column_idx = self.dialog.ui.seg_id_column_combo.findText(
                seg_id_column_name
            )
            if seg_id_column_idx >= 0:
                self.dialog.ui.seg_id_column_combo.setCurrentIndex(seg_id_column_idx)
            else:
                seg_id_pattern = re.compile(r"^id?s?[_]|[_]?id?s?$", re.IGNORECASE)
                for i in range(self.dialog.ui.seg_id_column_combo.count()):
                    if seg_id_pattern.search(
                        self.dialog.ui.seg_id_column_combo.itemText(i)
                    ):
                        self.dialog.ui.seg_id_column_combo.setCurrentIndex(i)
                        break

    def populate_segments_column_combo(self, compositions_layer):
        self.dialog.ui.segments_column_combo.clear()

        if compositions_layer:
            field_names = [field.name() for field in compositions_layer.fields()]
            self.dialog.ui.segments_column_combo.addItems(field_names)

            segments_column_name = self.settings.value(
                "routes_composer/segments_column_name", ""
            )
            segments_column_idx = self.dialog.ui.segments_column_combo.findText(
                segments_column_name
            )

            if segments_column_idx >= 0:
                self.dialog.ui.segments_column_combo.setCurrentIndex(segments_column_idx)
            else:
                segments_column_pattern = re.compile(
                    r"^segment?s?[_]|[_]?segment?s?$", re.IGNORECASE
                )
                for i in range(self.dialog.ui.segments_column_combo.count()):
                    if segments_column_pattern.search(
                        self.dialog.ui.segments_column_combo.itemText(i)
                    ):
                        self.dialog.ui.segments_column_combo.setCurrentIndex(i)
                        break

    def populate_compo_id_column_combo(self, compositions_layer):
        self.dialog.ui.compo_id_column_combo.clear()

        if compositions_layer:
            field_names = [field.name() for field in compositions_layer.fields()]
            self.dialog.ui.compo_id_column_combo.addItems(field_names)

            compo_id_column_name = self.settings.value(
                "routes_composer/compo_id_column_name", ""
            )
            compo_id_column_idx = self.dialog.ui.compo_id_column_combo.findText(
                compo_id_column_name
            )

            if compo_id_column_idx >= 0:
                self.dialog.ui.compo_id_column_combo.setCurrentIndex(compo_id_column_idx)
            else:
                compo_id_column_pattern = re.compile(
                    r"^id?s?[_]|[_]?id?s?$", re.IGNORECASE
                )
                for i in range(self.dialog.ui.compo_id_column_combo.count()):
                    if compo_id_column_pattern.search(
                        self.dialog.ui.compo_id_column_combo.itemText(i)
                    ):
                        self.dialog.ui.compo_id_column_combo.setCurrentIndex(i)
                        break

    def on_segments_layer_selected(self):
        segments_id = self.dialog.ui.segments_combo.currentData()

        if ConnexionsHandler.routes_composer_connected:
            routes_composer = RoutesComposer.get_instance()
            if routes_composer.segments_layer is not None:
                if routes_composer.segments_layer.id() != segments_id:
                    self.dialog.event_handlers.stop_running_routes_composer()

        self.segments_layer = cast(QgsVectorLayer, self.project.mapLayer(segments_id))
        if self.segments_layer is not None:
            self.check_segments_layer(message_type="warning")
            self.populate_seg_id_column_combo(self.segments_layer)
            self.dialog.advanced_options.update_segments_attr_combo(self.segments_layer)

            log(f"Segments layer selected: {self.segments_layer.name()}")

    def on_compositions_layer_selected(self):
        compositions_id = self.dialog.ui.compositions_combo.currentData()

        if ConnexionsHandler.routes_composer_connected:
            routes_composer = RoutesComposer.get_instance()
            if routes_composer.compositions_layer is not None:
                if routes_composer.compositions_layer.id() != compositions_id:
                    self.dialog.event_handlers.stop_running_routes_composer()

        self.compositions_layer = cast(
            QgsVectorLayer, self.project.mapLayer(compositions_id)
        )
        if self.compositions_layer is not None:
            self.check_compositions_layer(message_type="warning")
            self.populate_segments_column_combo(self.compositions_layer)
            self.populate_compo_id_column_combo(self.compositions_layer)
            self.dialog.advanced_options.update_compositions_attr_combo(
                self.compositions_layer
            )

            log(f"Compositions layer selected: {self.compositions_layer.name()}")

    def check_layers_and_columns(self):
        if not self.check_segments_layer(message_type="box"):
            return False

        if not self.check_compositions_layer(message_type="box"):
            return False

        if not self.is_id_column_valid():
            return False

        if not self.is_segments_column_valid():
            return False

        else:
            return True

    def save_selected_layers_and_columns(self):
        segments_id = self.dialog.ui.segments_combo.currentData()
        self.project.writeEntry("routes_composer", "segments_layer_id", segments_id)

        compositions_id = self.dialog.ui.compositions_combo.currentData()
        self.settings.setValue("routes_composer/compositions_layer_id", compositions_id)

        id_column = self.dialog.ui.seg_id_column_combo.currentText()
        self.settings.setValue("routes_composer/seg_id_column_name", id_column)

        segments_column = self.dialog.ui.segments_column_combo.currentText()
        self.settings.setValue("routes_composer/segments_column_name", segments_column)

        compo_id_column = self.dialog.ui.compo_id_column_combo.currentText()
        self.settings.setValue("routes_composer/compo_id_column_name", compo_id_column)

        self.project.setDirty(True)
        return True

    def check_segments_layer(self, message_type="box"):
        if not isinstance(self.segments_layer, QgsVectorLayer):
            QMessageBox.warning(
                self.dialog,
                self.tr("Attention"),
                self.tr(
                    "La couche de segments n'est pas une couche vectorielle valide",
                ),
            )
            return False

        if (
            self.segments_layer.geometryType() != QgsWkbTypes.LineGeometry  # type: ignore
        ):
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

    def is_column_pk_attribute(self, layer, column_name):
        """
        Vérifie si une colonne n'est pas utilisée comme clé primaire dans une couche.

        Returns:
            bool: True si la colonne est une clé primaire, False sinon
        """
        pk_attributes = layer.primaryKeyAttributes()
        if not pk_attributes:
            QMessageBox.warning(
                self.dialog,
                self.tr("Erreur de validation"),
                self.tr("La couche n'a pas de colonne d'identifiants uniques."),
            )
            return True

        if layer.primaryKeyAttributes():
            pk_field_names = [
                layer.fields().field(pk_index).name()
                for pk_index in layer.primaryKeyAttributes()
            ]
            if column_name in pk_field_names:
                QMessageBox.warning(
                    self.dialog,
                    self.tr("Erreur de validation"),
                    self.tr(
                        f"La colonne d'identifiants unique '{column_name}' ne peut être utilisée ici"
                    ),
                )
                return True
        return False

    def is_id_of_routes_composer(self, layer, column_name):
        """
        Vérifie si une colonne est déjà utilisée comme identifiant unique dans routes composer.

        Returns:
            bool: True si la colonne est déjà utilisée, False sinon
        """
        if column_name == self.dialog.ui.seg_id_column_combo.currentText():
            QMessageBox.warning(
                self.dialog,
                self.tr("Erreur de validation"),
                self.tr(
                    f"La colonne '{column_name}' est utilisée par routes composer, elle ne peut donc être utilisée ici."
                ),
            )
            return True
        return False

    def is_id_column_valid(self):
        if self.segments_layer is None:
            return False

        seg_id_column_name = self.dialog.ui.seg_id_column_combo.currentText()
        if not seg_id_column_name:
            return False

        if seg_id_column_name not in self.segments_layer.fields().names():
            return False

        if self.is_column_pk_attribute(self.segments_layer, seg_id_column_name):
            return False

        id_field = self.segments_layer.fields().field(seg_id_column_name)
        if id_field.type() not in (QVariant.Int, QVariant.LongLong):
            QMessageBox.warning(
                self.dialog,
                self.tr("Erreur de validation"),
                self.tr("La colonne 'id' de la couche 'segments' doit être de type int."),
            )
            return False

        return True

    def check_compositions_layer(self, message_type="box"):
        if not isinstance(self.compositions_layer, QgsVectorLayer):
            raise Exception(
                QCoreApplication.translate(
                    "RoutesComposer",
                    "La couche des compositions n'est pas une couche vectorielle valide",
                )
            )
            return False

        if self.compositions_layer.isSpatial():
            if (
                self.compositions_layer.geometryType() != QgsWkbTypes.LineGeometry  # type: ignore
            ):
                if message_type == "box":
                    QMessageBox.warning(
                        self.dialog,
                        self.tr("Attention"),
                        self.tr(
                            "Veuillez sélectionnez une couche compositions de type LineString ou sans géométrie"
                        ),
                    )
                    return False

                elif message_type == "warning":
                    self.dialog.ui.compositions_warning_label.setText(
                        self.tr(
                            "Attention: la géométrie de la couche de compositions doit être de type LineString"
                        )
                    )
                    self.dialog.ui.compositions_warning_label.setVisible(True)
                    return False
            else:
                self.dialog.ui.compositions_warning_label.setVisible(False)

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

        segments_column_name = self.dialog.ui.segments_column_combo.currentText()
        if not segments_column_name:
            return False

        if segments_column_name not in self.compositions_layer.fields().names():
            return False

        segment_field = self.compositions_layer.fields().field(segments_column_name)

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

        for composition in self.compositions_layer.getFeatures():
            if count >= max_features:
                break

            segment_value = composition[segments_column_name]
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
