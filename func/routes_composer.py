from typing import cast
from PyQt5.QtWidgets import QMessageBox
from qgis.core import Qgis, QgsProject, QgsVectorLayer
from qgis.utils import iface
from qgis.PyQt.QtCore import QCoreApplication, QSettings

from .. import config
from . import split, geom_compo
from .utils import log


class RoutesComposer:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if RoutesComposer._instance is not None:
            raise Exception("Une instance de cette classe existe déjà.")
        self.project = QgsProject.instance()
        if not self.project:
            raise Exception(
                QCoreApplication.translate(
                    "RoutesComposer", "Aucun projet QGIS n'est ouvert"
                )
            )
        # self.project.layerRemoved.connect(self.on_layer_removed)
        self.settings = QSettings()

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
        cls._instance = None

    def feature_added(self, fid):
        """Fonction prinicpale. Traite l'ajout d'une nouvelle entité dans la couche segments."""
        # Pendant l'enregistrement: fid >= 0.'
        if fid >= 0:
            return
        if self.segments_layer is None or self.compositions_layer is None:
            return

        source_feature = self.segments_layer.getFeature(fid)
        if not source_feature.isValid() and source_feature.fields().names():
            return

        segment_id = source_feature.attributes()[self.id_column_index]
        if segment_id is None:
            return

        if self.split_manager.has_duplicate_segment_id(segment_id):

            new_geometry = source_feature.geometry()
            if not new_geometry or new_geometry.isEmpty():
                return

            original_feature = next(
                self.segments_layer.getFeatures(
                    f"{self.id_column_name} = {segment_id}"
                ),
                None,
            )

            if original_feature:
                segments_lists_ids = (
                    self.split_manager.get_compositions_list_segments(
                        segment_id
                    )
                )
                if not segments_lists_ids:
                    QMessageBox.information(
                        None,
                        "RoutesComposer",
                        f"Attention: Le segment {segment_id} n'est dans aucune composition",
                    )
                next_id = self.split_manager.get_next_id()
                self.split_manager.update_segment_id(fid, next_id)

                if segments_lists_ids:
                    self.split_manager.update_compositions_segments(
                        fid,
                        segment_id,
                        next_id,
                        original_feature,
                        source_feature,
                        segments_lists_ids,
                    )

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

        segment_id = source_feature.attributes()[self.id_column_index]
        if segment_id is None:
            return

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
                self.segments_layer.featuresDeleted.connect(
                    self.features_deleted
                )
                self.is_connected = True
                config.script_running = True

                log("Script has started", level="INFO")
                iface.messageBar().pushMessage(
                    "Info",
                    QCoreApplication.translate(
                        "RoutesComposer",
                        "Le suivi par RoutesComposer a démarré",
                    ),
                    level=Qgis.MessageLevel.Info,
                )
                return True

        except Exception as e:
            iface.messageBar().pushMessage(
                QCoreApplication.translate("RoutesComposer", "Erreur"),
                str(e),
                level=Qgis.MessageLevel.Critical,
            )
            return False

    def disconnect(self):
        try:
            if self.segments_layer is not None and self.is_connected:
                self.segments_layer.featureAdded.disconnect(
                    self.feature_added
                )
                self.segments_layer.featuresDeleted.disconnect(
                    self.features_deleted
                )
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
                    QCoreApplication.translate(
                        "RoutesComposer",
                        "Le suivi par RoutesComposer est arrêté",
                    ),
                    level=Qgis.MessageLevel.Info,
                )
            else:
                log("Segments layer is None or is_connect is false.")
        except Exception as e:
            iface.messageBar().pushMessage(
                QCoreApplication.translate("RoutesComposer", "Erreur"),
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
                    self.segments_layer.geometryChanged.connect(
                        self.geometry_changed
                    )
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
                self.segments_layer.geometryChanged.disconnect(
                    self.geometry_changed
                )

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
                QCoreApplication.translate(
                    "RoutesComposer",
                    "Veuillez sélectionner une couche de segments valide",
                )
            )
            return

        if not isinstance(self.segments_layer, QgsVectorLayer):
            raise Exception(
                QCoreApplication.translate(
                    "RoutesComposer",
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
                QCoreApplication.translate(
                    "RoutesComposer",
                    "Veuillez sélectionner une couche de compositions valide",
                )
            )
        if not isinstance(self.compositions_layer, QgsVectorLayer):
            raise Exception(
                QCoreApplication.translate(
                    "RoutesComposer",
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
                self.compositions_layer.fields().indexOf(
                    self.segments_column_name
                )
            )

            if self.segments_column_index == -1:
                raise Exception(
                    QCoreApplication.translate(
                        "RoutesComposer",
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
                QCoreApplication.translate(
                    "RoutesComposer",
                    f"Le champ {self.id_column_name} n'a pas été trouvé dans la couche segments",
                )
            )

        return self.id_column_name, self.id_column_index

    def on_layer_removed(self, layer_id):
        if not self.project:
            return
        if not self.project.mapLayer(
            self.segments_layer_id
        ) or not self.project.mapLayer(self.compositions_layer_id):
            from ..ui.main_dialog.main import RoutesComposerDialog

            dialog = RoutesComposerDialog.get_instance()
            if dialog:
                dialog.event_handlers.stop_running_routes_composer()
