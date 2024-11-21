from typing import cast
from qgis.core import (
    Qgis,
    QgsProject,
    QgsVectorLayer,
)
from qgis.utils import iface
from qgis.PyQt.QtCore import QCoreApplication, QSettings

from .. import config
from . import split, geom_compo, utils
from .utils import log

routes_composer = None


def start_routes_composer():
    global routes_composer
    try:
        if routes_composer is None:
            routes_composer = RoutesComposer()
        routes_composer.connect()
        config.script_running = True

        return routes_composer
    except Exception as e:
        print(f"Error starting routes composer: {str(e)}")
        return None


def stop_routes_composer():
    global routes_composer
    try:
        if routes_composer is not None:
            routes_composer.disconnect()
            routes_composer = None
            config.script_running = False

    except Exception as e:
        print(f"Error stopping routes composer: {str(e)}")


def start_geom_on_fly():
    global routes_composer
    try:
        if routes_composer is None:
            routes_composer = RoutesComposer()
        routes_composer.connect_geom()
        config.geom_on_fly_running = True

    except Exception as e:
        print(f"Error starting geometry on fly: {str(e)}")


def stop_geom_on_fly():
    global routes_composer
    try:
        if routes_composer is not None:
            routes_composer.disconnect_geom()
            config.geom_on_fly_running = False
    except Exception as e:
        print(f"Error stopping geometry on fly: {str(e)}")


class RoutesComposer:
    def __init__(self):
        self.project = QgsProject.instance()
        if not self.project:
            raise Exception(QCoreApplication.translate("RoutesComposer","Aucun projet QGIS n'est ouvert"))
        self.settings = QSettings()

        self.segments_layer = self.get_segments_layer()
        self.compositions_layer = self.get_compositions_layer()
        self.segments_column_name, self.segments_column_index = self.get_segments_column_name()
        self.id_column_name, self.id_column_index = self.get_id_column_name()

        if self.segments_layer is None or self.compositions_layer is None:
            raise ValueError("Invalid layers: segments_layer or compositions_layer is None")

        self.split_manager = split.SplitManager(
            self.segments_layer,
            self.compositions_layer,
            self.segments_column_name,
            self.segments_column_index,
            self.id_column_name,
            self.id_column_index
        )
        self.geom_compo = geom_compo.GeomCompo(
            self.segments_layer,
            self.compositions_layer,
            self.segments_column_name,
            self.id_column_name
        )
        self.is_connected = False

    def connect(self):
        try:
            if self.segments_layer is not None and not self.is_connected:
                self.segments_layer.featureAdded.connect(self.feature_added)
                self.segments_layer.featuresDeleted.connect(self.features_deleted)
                self.is_connected = True

                log("Script has started", level='INFO')
                iface.messageBar().pushMessage("Info",QCoreApplication.translate("RoutesComposer","Le suivi par RoutesComposer a démarré"), level=Qgis.MessageLevel.Info)
                return True

        except Exception as e:
            iface.messageBar().pushMessage(QCoreApplication.translate("RoutesComposer","Erreur"), str(e), level=Qgis.MessageLevel.Critical)
            return False

    def disconnect(self):
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
                routes_composer = None

                log("Script has been stopped.", level='INFO')
                iface.messageBar().pushMessage(
                    "Info",
                    QCoreApplication.translate("RoutesComposer", "Le suivi par RoutesComposer est arrêté"),
                    level=Qgis.MessageLevel.Info
                )
            else:
                print("Segments layer is None or is_connect is false.")
        except Exception as e:
            iface.messageBar().pushMessage(QCoreApplication.translate("RoutesComposer","Erreur"), str(e), level=Qgis.MessageLevel.Critical)

    def connect_geom(self):
        """Démarre la création en continue des géométries de compositions."""
        try:
            geom_on_fly, _ = self.project.readBoolEntry("routes_composer", "geom_on_fly", False)
            if geom_on_fly:
                if self.segments_layer is not None:
                    self.segments_layer.geometryChanged.connect(self.geometry_changed)
                    log("GeomOnFly has started")
        except TypeError:
            log("La fonction geometry_changed n'a pas pu être connectée.", level='WARNING')

    def disconnect_geom(self):
        try:
            if self.segments_layer is not None:
                self.segments_layer.geometryChanged.disconnect(self.geometry_changed)
                log("GeomOnFly has been stoped")

        except TypeError:
            log("La fonction geometry_changed n'était pas connectée.", level='WARNING')

    def feature_added(self, fid):
        """Fonction prinicpale. Traite l'ajout d'une nouvelle entité dans la couche segments."""
        # Pendant l'enregistrement: fid >= 0.'
        if fid >= 0:
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

            original_feature = next(self.segments_layer.getFeatures(f"{self.id_column_name} = {segment_id}"), None)

            if original_feature:
                segments_lists_ids = self.split_manager.get_compositions_list_segments(segment_id)
                if segments_lists_ids:
                    next_id = self.split_manager.get_next_id()
                    self.split_manager.update_segment_id(fid, next_id)
                    self.split_manager.update_compositions_segments(fid, segment_id, next_id, original_feature, source_feature, segments_lists_ids)

    def features_deleted(self, fids):
        """Nettoie les compositions des segments supprimés."""
        log(f"fids = {fids}" )
        for fid in fids:
            if fid >= 0:
                return

        self.split_manager.clean_invalid_segments()

    def geometry_changed(self, fid):
        """Crée la géométrie des compositions lors du changement de la géométrie d'un segment"""
        # Initialisation
        log(f"Geometry has changed for fid: '{fid}'", level='INFO')

        source_feature = self.segments_layer.getFeature(fid)
        if not source_feature.isValid() and source_feature.fields().names():
            return

        segment_id = source_feature.attributes()[self.id_column_index]
        if segment_id is None:
            log("No segment id, return.")
            return

        log(f"With corresponding segment id: '{segment_id}'", level='INFO')

        for composition in utils.get_features_list(self.compositions_layer):
            segments_str = str(composition[self.segments_column_name])
            if str(segment_id) in segments_str.split(','):
                # Obtenir la liste des segments pour cette composition
                segment_ids = [int(id_str) for id_str in segments_str.split(',') if id_str.strip().isdigit()]

                a = geom_compo.GeomCompo(self.segments_layer, self.compositions_layer, self.segments_column_name, self.id_column_name)
                new_geometry = a.create_merged_geometry(segment_ids)

                if new_geometry:
                    # Mettre à jour la géométrie de la composition
                    self.compositions_layer.startEditing()
                    self.compositions_layer.changeGeometry(composition.id(), new_geometry[0])
                    log(f"Updated geometry for composition {composition.id()}", level='INFO')
                else:
                    log(f"Failed to create geometry for composition {composition.id()}", level='WARNING')

        self.compositions_layer.triggerRepaint()

    def get_segments_layer(self):

        segments_layer_id = self.settings.value("routes_composer/segments_layer_id", "")
        if not segments_layer_id:
            return
        self.segments_layer = cast(QgsVectorLayer, self.project.mapLayer(segments_layer_id))
        if not self.segments_layer.isValid():
            raise Exception(QCoreApplication.translate("RoutesComposer","Veuillez sélectionner une couche de segments valide"))
            return
        if not isinstance(self.segments_layer, QgsVectorLayer):
            raise Exception(QCoreApplication.translate("RoutesComposer","La couche de segments n'est pas une couche vectorielle valide"))
            return

        return self.segments_layer

    def get_compositions_layer(self):

        compositions_layer_id = self.settings.value("routes_composer/compositions_layer_id", "")
        self.compositions_layer = cast(QgsVectorLayer, self.project.mapLayer(compositions_layer_id))
        if not self.compositions_layer.isValid():
            raise Exception(QCoreApplication.translate("RoutesComposer","Veuillez sélectionner une couche de compositions valide"))
        if not isinstance(self.compositions_layer, QgsVectorLayer):
            raise Exception(QCoreApplication.translate("RoutesComposer","La couche de compositions n'est pas une couche vectorielle valide"))

        return self.compositions_layer

    def get_segments_column_name(self):
        self.segments_column_name = self.settings.value("routes_composer/segments_column_name", "segments")
        self.segments_column_index = self.compositions_layer.fields().indexOf(self.segments_column_name)
        if self.segments_column_index == -1:
            raise Exception(QCoreApplication.translate("RoutesComposer", "Le champ '{segments_column_name}' n'existe pas dans la couche compositions".format(segments_column_name=segments_column_name)))

        return self.segments_column_name, self.segments_column_index

    def get_id_column_name(self):
        self.id_column_name = self.settings.value("routes_composer/id_column_name", "id")
        if self.segments_layer is not None:
            self.id_column_index = self.segments_layer.fields().indexOf(self.id_column_name)
        if self.id_column_index == -1:
            raise Exception(QCoreApplication.translate("RoutesComposer",f"Le champ {self.id_column_name} n'a pas été trouvé dans la couche segments"))

        return self.id_column_name, self.id_column_index
