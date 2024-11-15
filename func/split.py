"""functions used to handle segments spliting or merging."""

from logging import log
from qgis.core import (
    Qgis,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsVectorLayer,
)
from qgis.utils import List, Optional, iface
from qgis.PyQt.QtWidgets import (
    QDialog,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QWidget,
    QHBoxLayout,
)
from . import utils
from .utils import get_features_list, log, timer_decorator
from ..ui.sub_dialog import SingleSegmentDialog


def get_compositions_list_segments(segment_id: int, compositions_layer: QgsVectorLayer,  segments_column_name: str) -> list:
    """Récupère toutes les listes de segments contenant l'id du segment divisé."""
    if not segment_id:
        return []

    all_segments_lists = []

    request = QgsFeatureRequest()
    expression = (
        f"{segments_column_name} LIKE '%,{segment_id},%' OR "
        f"{segments_column_name} LIKE '{segment_id},%' OR "
        f"{segments_column_name} LIKE '%,{segment_id}' OR "
        f"{segments_column_name} = '{segment_id}'"
    )
    request.setFilterExpression(expression)

    features = utils.get_features_list(compositions_layer, request)

    for feature in features:
        segments_str = feature[segments_column_name]

        if not segments_str:
            continue

        try:
            segments_ids = [int(id.strip()) for id in str(segments_str).split(',')]
            if int(segment_id) in segments_ids:
                log(f"Segment find in composition: {feature.id()}")
                all_segments_lists.append(segments_ids)

        except Exception as e:
            log(f"Erreur lors du traitement de la composition {feature.id()}: {str(e)}", level='WARNING')

    return all_segments_lists


def update_compositions_segments(segments_layer: QgsVectorLayer, compositions_layer: QgsVectorLayer,
    segments_column_name: str, segments_column_index: int, old_id: int, new_id: int,
    original_feature: QgsFeature, new_feature: QgsFeature, segment_lists: list) -> None:
    """Met à jour les compositions après division d'un segment."""
    compositions_layer.startEditing()

    original_geom = original_feature.geometry()
    new_geom = new_feature.geometry()

    compositions_dict = {feature[segments_column_name]: feature.id() for feature in utils.get_features_list(compositions_layer)}
    for segments_list in segment_lists:
        try:
            old_index = segments_list.index(int(old_id))
            # Pour vérifier l'orientation du segment on doit d'abord vérifier si c'est le dernier de la liste
            # car une logique différente s'applique dans ce cas.
            if old_index < len(segments_list) - 1:
                segment_geom = original_geom
                original_geometry = True
            else:
                segment_geom = new_geom
                original_geometry = False

            # Vérifier l'orientation
            is_correctly_oriented = check_segment_orientation(segments_layer, segment_geom,
                original_geometry, segments_list, old_index)

            # On ajuste la nouvelle liste en fonction de l'orientation du segment.'
            new_segments_list = segments_list.copy()
            if is_correctly_oriented:
                new_segments_list[old_index:old_index+1] = [int(old_id), int(new_id)]
            else:
                new_segments_list[old_index:old_index+1] = [int(new_id), int(old_id)]

            # Mettre à jour la composition
            composition_id = compositions_dict.get(','.join(map(str, segments_list)))
            log(f"Composition {composition_id} has been updated with list: {new_segments_list}")
            if composition_id:
                compositions_layer.changeAttributeValue(
                    composition_id,
                    segments_column_index,
                    ','.join(map(str, new_segments_list))
            )
        except Exception as e:
            raise Exception("La composition .. n'a pa pu être mis-à-jour")


def check_segment_orientation(segments_layer: QgsVectorLayer, segment_geom: QgsGeometry, original_geometry: bool,
    segments_list: list, old_index: int) -> bool:
    """Vérifie si un segment est orienté correctement par rapport aux segments adjacents."""
    segment_points = segment_geom.asPolyline()

    if original_geometry is True:
        # Chercher la géométrie de l'ancien segment'
        next_id = segments_list[old_index + 1] if old_index < len(segments_list) - 1 else None

        expression = f"\"id\" = '{next_id}'"
        request = QgsFeatureRequest().setFilterExpression(expression)
        next_feature = next(segments_layer.getFeatures(request), None)

        if next_feature:
            next_geom = next_feature.geometry()
        else:
            next_geom = None

        # Vérifier avec le segment suivant
        if next_geom and not next_geom.isEmpty():
            next_points = next_geom.asPolyline()
            # Si le segment original touche le segment suivant: à l'envers.'
            if segment_points[0].distance(next_points[0]) < 0.01 or segment_points[0].distance(next_points[-1]) < 0.01:
                return False

    if original_geometry is False:
        # Chercher la géométrie du nouveau segment
        prev_id = segments_list[old_index - 1]

        expression = f"\"id\" = '{prev_id}'"
        request = QgsFeatureRequest().setFilterExpression(expression)
        prev_feature = next(segments_layer.getFeatures(request), None)

        if prev_feature:
            prev_geom = prev_feature.geometry()
        else:
            prev_geom = None
        # Vérifier avec le segment précédent
        if prev_geom and not prev_geom.isEmpty():
            prev_points = prev_geom.asPolyline()
            # Si le nouveau segment touche le segment précédent: à l'envers.'
            if segment_points[-1].distance(prev_points[0]) < 0.01 or segment_points[-1].distance(prev_points[-1]) < 0.01:
                return False

    return True


def process_single_segment_composition(segments_layer: QgsVectorLayer, compositions_layer: QgsVectorLayer,
    segments_column_name: str, segments_column_index: int, fid: int, old_id: int, new_id: int):
    """Gère le cas d'une composition d'un seul segment."""

    dialog = SingleSegmentDialog(old_id=old_id, new_id=new_id)
    dialog.current_segments = [old_id, new_id]
    result = dialog.exec_()

    if result == QDialog.Accepted:
        # Rechercher la composition qui contient ce segment
        expression = f"{segments_column_name} = '{old_id}'"
        request = QgsFeatureRequest().setFilterExpression(expression)
        composition_feature = next(compositions_layer.getFeatures(request), None)

        if composition_feature:
            try:
                new_segments_str = ','.join(map(str, dialog.current_segments))
                compositions_layer.startEditing()
                success = compositions_layer.changeAttributeValue(
                    composition_feature.id(),
                    segments_column_index,
                    new_segments_str
                )
                log(f"Composition {composition_feature.id()} has been updated with segments: '{new_segments_str}'")
            except Exception as e:
                iface.messageBar().pushMessage(
                    "Erreur",
                    f"Erreur lors de la mise à jour de la composition: {str(e)}",
                    level=Qgis.MessageLevel.Critical
                )
        else:
            iface.messageBar().pushMessage(
                "Attention",
                f"Aucune composition trouvée avec le segment {old_id}",
                level=Qgis.MessageLevel.Warning
            )
        return dialog.current_segments
    else:
        return None

@timer_decorator
def clean_invalid_segments(segments_layer: QgsVectorLayer, compositions_layer: QgsVectorLayer,
    segments_column_name: str, segments_column_index: int) -> None:
    """Supprime les références aux segments qui n'existent plus dans la table segments."""

    valid_segments_ids = {str(f['id']) for f in utils.get_features_list(segments_layer) if f['id'] is not None}
    compositions = utils.get_features_list(compositions_layer)

    compositions_layer.startEditing()
    for composition in compositions:
        segments_list_str = composition[segments_column_name]
        if segments_list_str is None or str(segments_list_str).upper() == 'NULL' or not segments_list_str:
            continue

        segments_list = str(segments_list_str).split(',')
        valid_segments = [seg.strip() for seg in segments_list if seg.strip() in valid_segments_ids]

        if len(valid_segments) != len(segments_list):
            new_segments_str = ','.join(valid_segments)
            log(f"Removing segments {[seg.strip() for seg in segments_list if seg.strip() not in valid_segments_ids]} from composition {composition.id()}")
            compositions_layer.changeAttributeValue(
                composition.id(),
                segments_column_index,
                new_segments_str
            )


def has_duplicate_segment_id(segments_layer: QgsVectorLayer, segment_id:int) -> bool:
    """Vérifie si un id de segments existe plusieurs fois. Si oui, il s'agit d'un segment divisé."""

    expression = f"\"id\" = '{segment_id}'"
    request = QgsFeatureRequest().setFilterExpression(expression)
    request.setLimit(2)

    features = utils.get_features_list(segments_layer, request)
    return len(features) > 1


def update_segment_id(segments_layer: QgsVectorLayer, fid: int, next_id: int, id_column_index: int) -> None:
    """Met à jour l'id des segments divisés."""
    segments_layer.startEditing()
    segments_layer.changeAttributeValue(fid,
        id_column_index,
        str(next_id))


def get_next_id(segments_layer: QgsVectorLayer, id_column_index:int) -> int:
    """Retourne le dernier id disponible."""
    next_id = int(segments_layer.maximumValue(id_column_index))
    return next_id + 1
