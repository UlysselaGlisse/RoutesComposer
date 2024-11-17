from typing import cast
from qgis.core import (
    Qgis,
    QgsFeatureRequest,
    QgsProject,
    QgsSettings,
    QgsVectorLayer,
)
from qgis.utils import iface
from qgis.PyQt.QtCore import (
    QTimer,
    QSettings,
    QCoreApplication,
)
from .ui.main_dialog import RoutesComposerDialog
from . import config
from .func import(
    split,
    geom_compo,
    utils,
    errors as e
)
from .func.utils import log

segments_layer: QgsVectorLayer
compositions_layer: QgsVectorLayer

def feature_added(fid):
    """Fonction prinicpale. Traite l'ajout d'une nouvelle entité dans la couche segments."""
    # Lorsque Qgis enregistre les couches: fid >= 0, comme le script ne doit pas s'exécuter à ce moment, on le vérifie.'
    if fid >= 0:
        return

    global last_fid, segments_column_name, segments_column_index, id_column_index

    log(f"New feature added with fid: '{fid}'", level='INFO')
    # Initialisation
    segments_column_name = config.segments_column_name
    segments_column_index = config.segments_column_index
    id_column_index = config.id_column_index

    source_feature = segments_layer.getFeature(fid)
    if not source_feature.isValid() and source_feature.fields().names():
          return

    segment_id = source_feature.attributes()[id_column_index]
    if segment_id is None:
        log("No segment id, return.")
        return

    log(f"With corresponding segment id: '{segment_id}'", level='INFO')

    # Le segment a-t-il était divisé ?
    if split.has_duplicate_segment_id(segments_layer, segment_id):
        log(f"Segment '{segment_id}' has been split")
        new_geometry = source_feature.geometry()
        if not new_geometry or new_geometry.isEmpty():
            return

        # Récupérer le segment original.
        expression = f"\"id\" = '{segment_id}' AND $id != {fid}"
        request = QgsFeatureRequest().setFilterExpression(expression)
        original_feature = next(segments_layer.getFeatures(request), None)
        print(original_feature)

        if not original_feature:
            return
        # Récupérer toutes les compositions contenant ce segment
        segments_lists_ids = split.get_compositions_list_segments(segment_id, compositions_layer, segments_column_name)
        log(f"Segment find into {len(segments_lists_ids)} compositions.", level='INFO')

        if not segments_lists_ids:
            return

        next_id = split.get_next_id(segments_layer, id_column_index)
        log(f"New segment id to attribute: '{next_id}'", level='INFO')

        split.update_segment_id(segments_layer, fid, next_id, id_column_index)

        segment_unique = False

        for segment_list_ids in segments_lists_ids:
            if len(segment_list_ids) == 1:
                segment_unique = True
                iface.mapCanvas().refresh()

        if segment_unique == True:
            log(f"Single segment found, open dialog.")
            new_segments = split.process_single_segment_composition(segments_layer, compositions_layer,
                segments_column_name, segments_column_index, fid, segment_id, next_id)
            if new_segments is None:
                pass
        else:
            split.update_compositions_segments(segments_layer, compositions_layer, segments_column_name,
                segments_column_index, segment_id, next_id, original_feature, source_feature, segments_lists_ids)

    compositions_layer.triggerRepaint()


def features_deleted(fids):
    """Nettoie les compositions des segments supprimés."""
    global segments_column_name, segments_column_index
    segments_column_name = config.segments_column_name
    segments_column_index = config.segments_column_index

    split.clean_invalid_segments(segments_layer, compositions_layer, segments_column_name, segments_column_index)
    log(f"Compositions has been updated.")


def geometry_changed(fid):
    """Crée la géométrie des compositions lors du changement de la géométrie d'un segment"""
    # Initialisation
    log(f"Geometry has changed for fid: '{fid}'", level='INFO')
    global segments_layer, compositions_layer

    segments_column_name = config.segments_column_name
    segments_column_index = config.segments_column_index
    id_column_index = config.id_column_index

    source_feature = segments_layer.getFeature(fid)
    if not source_feature.isValid() and source_feature.fields().names():
          return

    segment_id = source_feature.attributes()[id_column_index]
    if segment_id is None:
        log("No segment id, return.")
        return

    log(f"With corresponding segment id: '{segment_id}'", level='INFO')

    for composition in utils.get_features_list(compositions_layer):
        segments_str = composition[segments_column_name]
        if str(segment_id) in segments_str.split(','):
            # Obtenir la liste des segments pour cette composition
            segment_ids = [int(id_str) for id_str in segments_str.split(',') if id_str.strip().isdigit()]

            a = geom_compo.GeomCompo(segments_layer, compositions_layer, segments_column_name)
            new_geometry = a.create_merged_geometry(segment_ids)

            if new_geometry:
                # Mettre à jour la géométrie de la composition
                compositions_layer.startEditing()
                compositions_layer.changeGeometry(composition.id(), new_geometry[0])
                log(f"Updated geometry for composition {composition.id()}", level='INFO')
            else:
                log(f"Failed to create geometry for composition {composition.id()}", level='WARNING')

    compositions_layer.triggerRepaint()


def start_script():
    """Démarre le script."""
    global segments_layer, compositions_layer, id_column_index
    try:
        settings = QSettings()
        segments_layer_id = settings.value("routes_composer/segments_layer_id", "")
        compositions_layer_id = settings.value("routes_composer/compositions_layer_id", "")
        segments_column_name = settings.value("routes_composer/segments_column_name", "segments")

        project = QgsProject.instance()
        if not project:
            raise Exception(QCoreApplication.translate("RoutesComposer","Aucun projet QGIS n'est ouvert"))

        segments_layer = cast(QgsVectorLayer, project.mapLayer(segments_layer_id))
        compositions_layer = cast(QgsVectorLayer, project.mapLayer(compositions_layer_id))

        if not segments_layer.isValid():
            raise Exception(QCoreApplication.translate("RoutesComposer","Veuillez sélectionner une couche de segments valide"))
        if not compositions_layer.isValid():
            raise Exception(QCoreApplication.translate("RoutesComposer","Veuillez sélectionner une couche de compositions valide"))

        if not isinstance(segments_layer, QgsVectorLayer):
            raise Exception(QCoreApplication.translate("RoutesComposer","La couche de segments n'est pas une couche vectorielle valide"))
        if not isinstance(compositions_layer, QgsVectorLayer):
            raise Exception(QCoreApplication.translate("RoutesComposer","La couche de compositions n'est pas une couche vectorielle valide"))

        config.segments_column_name = segments_column_name

        segments_column_index = compositions_layer.fields().indexOf(segments_column_name)
        if segments_column_index == -1:
            raise Exception(QCoreApplication.translate("RoutesComposer", "Le champ '{segments_column_name}' n'existe pas dans la couche compositions".format(segments_column_name=segments_column_name)))

        config.segments_column_index = segments_column_index

        id_column_index = segments_layer.fields().indexOf('id')
        if id_column_index == -1:
            raise Exception(QCoreApplication.translate("RoutesComposer","Le champ 'id' n'a pas été trouvé dans la couche segments"))

        config.id_column_index = id_column_index

        segments_layer.featureAdded.connect(feature_added)
        segments_layer.featuresDeleted.connect(features_deleted)

        log("Script has started", level='INFO')
        iface.messageBar().pushMessage("Info", QCoreApplication.translate("RoutesComposer","Le suivi par RoutesComposer a démarré"), level=Qgis.MessageLevel.Info)
        return True

    except Exception as e:
        iface.messageBar().pushMessage(QCoreApplication.translate("RoutesComposer","Erreur"), str(e), level=Qgis.MessageLevel.Critical)
        return False


def stop_script():
    """Arrête l'exécution du script."""
    try :
        segments_layer.featureAdded.disconnect(feature_added)
        segments_layer.featuresDeleted.disconnect(features_deleted)

        log("Script has been stopped.", level='INFO')
        iface.messageBar().pushMessage("Info", QCoreApplication.translate("RoutesComposer","Le suivi par RoutesComposer est arrêté"), level=Qgis.MessageLevel.Info)

    except Exception as e:
        iface.messageBar().pushMessage(QCoreApplication.translate("RoutesComposer","Erreur"), str(e), level=Qgis.MessageLevel.Critical)
        return False


def start_geom_on_fly():
    """Démarre la création en continue des géométries de compositions."""
    try:
        project = QgsProject.instance()
        if not project:
            raise Exception(QCoreApplication.translate("RoutesComposer", "Aucun projet QGIS n'est ouvert"))
        settings = QgsSettings()
        segments_layer_id = settings.value("routes_composer/segments_layer_id", "")
        segments_layer = cast(QgsVectorLayer, project.mapLayer(segments_layer_id))

        geom_on_fly, _ = project.readBoolEntry("routes_composer", "geom_on_fly", False)
        if geom_on_fly:
            segments_layer.geometryChanged.connect(geometry_changed)
    except TypeError:
        log("La fonction geometry_changed n'a pas pu être connectée.", level='WARNING')


def stop_geom_on_fly():
    try:
        project = QgsProject.instance()
        if not project:
            raise Exception(QCoreApplication.translate("RoutesComposer","Aucun projet QGIS n'est ouvert"))
        settings = QgsSettings()
        segments_layer_id = settings.value("routes_composer/segments_layer_id", "")
        segments_layer = cast(QgsVectorLayer, project.mapLayer(segments_layer_id))

        geom_on_fly, _ = project.readBoolEntry("routes_composer", "geom_on_fly", False)
        if geom_on_fly is False:
            segments_layer.geometryChanged.disconnect(geometry_changed)
    except TypeError:
        log("La fonction geometry_changed n'était pas connectée.", level='WARNING')
