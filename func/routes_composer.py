from PyQt5.QtWidgets import QMessageBox
from qgis.core import Qgis, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QObject, QSettings, QTranslator
from qgis.utils import iface
from typing_extensions import cast

from .. import config
from . import geom_compo, split
from .utils import log


class RoutesComposer(QObject):
    _instance = None

    @classmethod
    def get_instance(cls, parent=None):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)
        if RoutesComposer._instance is not None:
            raise Exception("Une instance de cette classe existe déjà.")

        self.project = QgsProject.instance()
        if not self.project:
            raise Exception(self.tr("Aucun projet QGIS n'est ouvert"))

        self.project.layersWillBeRemoved.connect(self.on_layer_removed)

        self.settings = QSettings()
        self.translator = QTranslator()

        self.segments_layer = self.get_segments_layer()
        self.compositions_layer = self.get_compositions_layer()
        self.segments_column_name, self.segments_column_index = (
            self.get_segments_column_name()
        )
        self.id_column_name, self.id_column_index = self.get_id_column_name()

        self.split_manager = split.SplitManager(self)
        self.geom = geom_compo.GeomCompo(
            self.segments_layer,
            self.compositions_layer,
            self.id_column_name,
            self.segments_column_name,
        )

        self.is_connected = False

    @classmethod
    def destroy_instance(cls):
        log("r")
        cls._instance = None

    def feature_added(self, feature_id):
        """Fonction prinicpale. Traite l'ajout d'une nouvelle entité dans la couche segments."""
        # Pendant l'enregistrement: fid >= 0.'
        log(feature_id)
        if feature_id >= 0:
            return
            log("feature_id >=0")
        if self.segments_layer is None or self.compositions_layer is None:
            return
            log("layers are not goods")

        source_feature = self.segments_layer.getFeature(feature_id)
        if not source_feature.isValid() and source_feature.fields().names():
            return
            log("source_feature problem")

        segment_id = int(source_feature.attributes()[self.id_column_index])
        log(f"{segment_id}")
        if segment_id is None:
            return
            log("no segment_id associate with feature_id")

        if self.split_manager.has_duplicate_segment_id(segment_id):
            log("segment splited")
            new_geometry = source_feature.geometry()
            if not new_geometry or new_geometry.isEmpty():
                return
                log("segment has no geometry")

            original_feature = next(
                self.segments_layer.getFeatures(
                    f"{self.id_column_name} = {segment_id}"
                ),
                None,
            )

            if original_feature:
                segments_lists_ids = self.split_manager.get_compositions_list_segments(
                    segment_id
                )
                if not segments_lists_ids:
                    QMessageBox.information(
                        None,
                        "RoutesComposer",
                        f"Attention: Le segment {segment_id} n'est dans aucune composition",
                    )
                next_id = self.split_manager.get_next_id()
                self.split_manager.update_segment_id(feature_id, next_id)

                if segments_lists_ids:
                    self.split_manager.update_compositions_segments(
                        feature_id,
                        segment_id,
                        next_id,
                        original_feature,
                        source_feature,
                        segments_lists_ids,
                    )
        log("segment was not splited")

    def features_deleted(self, fids):
        """Nettoie les compositions des segments supprimés."""
        for fid in fids:
            if fid >= 0:
                return
        if self.segments_layer is None or self.compositions_layer is None:
            return

        self.split_manager.clean_invalid_segments()

    def geometry_changed(self, fid):
        """Crée la géométrie des compositions lors du changement de la géométrie d'un segment"""
        if self.segments_layer is None or self.compositions_layer is None:
            return

        source_feature = self.segments_layer.getFeature(fid)
        if not source_feature.isValid():
            return
        log(fid)

        segment_id = source_feature.attributes()[self.id_column_index]
        if segment_id is None:
            return
        log(segment_id)

        log(
            f"Updating geometries for modified segment {segment_id}",
            level="INFO",
        )
        self.geom.update_geometries_on_the_fly(segment_id)
        self.compositions_layer.triggerRepaint()

    def connect(self):
        try:
            if self.segments_layer is not None and not self.is_connected:
                self.segments_layer.featureAdded.connect(self.feature_added)
                self.segments_layer.featuresDeleted.connect(self.features_deleted)
                self.is_connected = True
                config.script_running = True

                log("Script has started", level="INFO")
                iface.messageBar().pushMessage(
                    "Info",
                    self.tr(
                        "Le suivi par RoutesComposer a démarré",
                    ),
                    level=Qgis.MessageLevel.Info,
                )
                return True

        except Exception as e:
            iface.messageBar().pushMessage(
                self.tr("Erreur"),
                str(e),
                level=Qgis.MessageLevel.Critical,
            )
            return False

    def disconnect_routes_composer(self):
        try:
            if self.segments_layer is not None and self.is_connected:
                self.segments_layer.featureAdded.disconnect(self.feature_added)
                self.segments_layer.featuresDeleted.disconnect(self.features_deleted)
                self.is_connected = False

                self.segments_layer = None
                self.compositions_layer = None
                self.segments_column_name = None
                self.segments_column_index = None
                self.id_column_name = None
                self.id_column_index = None
                config.script_running = False

                log("Script has been stopped.", level="INFO")
                iface.messageBar().pushMessage(
                    "Info",
                    self.tr(
                        "Le suivi par RoutesComposer est arrêté",
                    ),
                    level=Qgis.MessageLevel.Info,
                )
            else:
                log("Segments layer is None or is_connect is false.")
        except Exception as e:
            iface.messageBar().pushMessage(
                self.tr("Erreur"),
                str(e),
                level=Qgis.MessageLevel.Critical,
            )

    def connect_geom(self):
        """Démarre la création en continue des géométries de compositions."""
        try:
            if not self.project:
                return
            geom_on_fly, _ = self.project.readBoolEntry(
                "routes_composer", "geom_on_fly", False
            )
            if geom_on_fly:
                if self.segments_layer is not None:
                    self.segments_layer.geometryChanged.connect(self.geometry_changed)
                    log("GeomOnFly has started")
        except TypeError:
            log(
                "La fonction geometry_changed n'a pas pu être connectée.",
                level="WARNING",
            )

    def disconnect_geom(self):
        try:
            if self.segments_layer is None:
                self.destroy_instance()
            else:
                self.segments_layer.geometryChanged.disconnect(self.geometry_changed)

            log("GeomOnFly has been stoped")

        except TypeError:
            log(
                "La fonction geometry_changed n'était pas connectée.",
                level="WARNING",
            )

    def get_segments_layer(self):
        if not self.project:
            return

        self.segments_layer_id = self.settings.value(
            "routes_composer/segments_layer_id", ""
        )
        if not self.segments_layer_id:
            return
        self.segments_layer = cast(
            QgsVectorLayer, self.project.mapLayer(self.segments_layer_id)
        )
        if self.segments_layer is None:
            raise Exception(
                self.tr(
                    "Veuillez sélectionner une couche de segments valide",
                )
            )
            return

        if not isinstance(self.segments_layer, QgsVectorLayer):
            raise Exception(
                self.tr(
                    "La couche de segments n'est pas une couche vectorielle valide",
                )
            )
            return

        return self.segments_layer

    def get_compositions_layer(self):
        if not self.project:
            return
        self.compositions_layer_id = self.settings.value(
            "routes_composer/compositions_layer_id", ""
        )
        if not self.compositions_layer_id:
            return
        self.compositions_layer = cast(
            QgsVectorLayer, self.project.mapLayer(self.compositions_layer_id)
        )
        if self.compositions_layer is None:
            raise Exception(
                self.tr(
                    "Veuillez sélectionner une couche de compositions valide",
                )
            )
        if not isinstance(self.compositions_layer, QgsVectorLayer):
            raise Exception(
                self.tr(
                    "La couche de compositions n'est pas une couche vectorielle valide",
                )
            )

        return self.compositions_layer

    def get_segments_column_name(self):
        self.segments_column_name = self.settings.value(
            "routes_composer/segments_column_name", "segments"
        )
        if self.compositions_layer is not None:
            self.segments_column_index = int(
                self.compositions_layer.fields().indexOf(self.segments_column_name)
            )

            if self.segments_column_index == -1:
                raise Exception(
                    self.tr(
                        "Le champ '{segments_column_name}' n'existe pas dans la couche compositions".format(
                            segments_column_name=self.segments_column_name
                        ),
                    )
                )

        return self.segments_column_name, self.segments_column_index

    def get_id_column_name(self):
        self.id_column_name = self.settings.value(
            "routes_composer/id_column_name", "id"
        )
        if self.segments_layer is not None:
            self.id_column_index = self.segments_layer.fields().indexOf(
                self.id_column_name
            )
        if self.id_column_index == -1:
            raise Exception(
                self.tr(
                    f"Le champ {self.id_column_name} n'a pas été trouvé dans la couche segments",
                )
            )

        return self.id_column_name, self.id_column_index

    def on_layer_removed(self, layer_ids):
        if self.is_connected:
            for remove_layer_id in layer_ids:
                if (
                    remove_layer_id == self.compositions_layer_id
                    or remove_layer_id == self.segments_layer_id
                ):
                    log("layer followed removed")
                    from ..ui.main_dialog.main import RoutesComposerDialog

                    dialog = RoutesComposerDialog.get_instance()
                    dialog.event_handlers.stop_running_routes_composer()

                    if dialog.ui.geom_checkbox.isChecked():
                        dialog.ui.geom_checkbox.setChecked(False)
