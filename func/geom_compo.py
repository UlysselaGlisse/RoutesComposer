"""Functions for creating geometries of the compositions."""
import math
from collections import defaultdict
from os import error
from typing import List, Tuple
from qgis.utils import iface
from qgis.core import (
    QgsProject,
    QgsFeature,
    QgsGeometry,
    QgsVectorLayer,
    QgsPoint,
    QgsLineString,
    QgsWkbTypes,
    QgsField,
    QgsApplication
)
from PyQt5.QtCore import QVariant
from qgis.PyQt.QtWidgets import QMessageBox
from ..func.utils import get_features_list, log, timer_decorator
from .. import config
from ..ui.sub_dialog import ErrorDialog


def points_are_equal(point1: QgsPoint, point2: QgsPoint, tolerance=1e-8) -> bool:
    """
    Vérifie si deux points sont égaux.
    """
    return math.isclose(point1.x(), point2.x(), abs_tol=tolerance) and \
            math.isclose(point1.y(), point2.y(), abs_tol=tolerance)

def create_merged_geometry(segment_ids: List[int], segments_layer: QgsVectorLayer) -> Tuple[QgsGeometry, List[int]]:
    """
    Crée une géométrie fusionnée à partir d'une liste d'identifiants de segments.
    La fonction détermine automatiquement l'orientation de chaque segment en fonction
    de ses connexions avec les segments adjacents.
    """
    if not segment_ids:
        return QgsGeometry(), []

    not_connected_segments = []
    segments_points = {}
    for segment_id in segment_ids:
        segment_feature = next(segments_layer.getFeatures(f"id = {segment_id}"), None)
        if segment_feature:
            points = segment_feature.geometry().asPolyline()
            segments_points[segment_id] = points
        else:
            log(f"Segment ID {segment_id} non trouvé dans segments_layer", level='ERROR')
            continue

    if not segments_points:
        return QgsGeometry(), []

    result_points = []

    for i, current_segment_id in enumerate(segment_ids):
        current_points = segments_points.get(current_segment_id)
        if not current_points:
            log(f"Aucun point trouvé pour le segment: {current_segment_id}", level='ERROR')
            continue

        if len(segment_ids) > 1:
            # Tous les segments suaf le dernier de la liste.
            if i < len(segment_ids) - 1:
                next_points = segments_points.get(segment_ids[i + 1])
                if next_points:
                    # Le premier point touche le segment suivant
                    if points_are_equal(current_points[0], next_points[0]) or \
                       points_are_equal(current_points[0], next_points[-1]):
                        # On met tous les points sauf le dernier pour éviter les doublons.
                        result_points.extend(reversed(current_points[:-1]))
                    # Le dernier point touche le segment suivant
                    elif points_are_equal(current_points[-1], next_points[0]) or \
                        points_are_equal(current_points[-1], next_points[-1]):
                        result_points.extend(current_points[:-1])
                    else:
                        # Aucun des points ne touche le segment suivant. On met à l'endroit par défaut.'
                        result_points.extend(current_points[:-1])
                        not_connected_segments.append(current_segment_id)
            else:
                # Le dernier segment de la liste
                prev_points = segments_points.get(segment_ids[i - 1])
                if prev_points:
                    # Le dernier point touche le segment précédent.
                    if points_are_equal(prev_points[0], current_points[-1]) or \
                       points_are_equal(prev_points[-1], current_points[-1]):
                        result_points.extend(reversed(current_points))
                    # Le premier point touche le segment précédent.
                    elif points_are_equal(prev_points[0], current_points[0]) or \
                       points_are_equal(prev_points[-1], current_points[0]):
                        result_points.extend(current_points)
                    else:
                        # Aucun point ne touche le précédent, par défaut on met à l'endroit.'
                        result_points.extend(current_points)
                        not_connected_segments.append(current_segment_id)

        else:
            result_points.extend(current_points)

    if result_points:
        line_string = QgsLineString([QgsPoint(p.x(), p.y()) for p in result_points])
        return QgsGeometry.fromPolyline(line_string), not_connected_segments
    else:
        log("Aucun point trouvé après le traitement des segments.", level='WARNING')
        return QgsGeometry(), []

def create_compositions_geometries(compositions_layer: QgsVectorLayer, segments_layer: QgsVectorLayer, segments_list_field: str, progress_bar):

    new_layer = QgsVectorLayer("LineString?crs=" + segments_layer.crs().authid(), "Merged Geometries", "memory")
    provider = new_layer.dataProvider()

    provider = new_layer.dataProvider()

    if provider is None:
        log("Le fournisseur de données de la nouvelle couche est None.", level='ERROR')
        return [{'error_type': 'provider_creation_failed'}]

    provider.addAttributes(compositions_layer.fields())
    new_layer.updateFields()

    total_compositions = sum(1 for _ in get_features_list(compositions_layer))
    processed_count = 0
    failed_compositions = []
    not_connected_segments = defaultdict(list)

    progress_bar.setRange(0, total_compositions)
    progress_bar.setValue(0)

    for composition in get_features_list(compositions_layer):
        if config.cancel_request:
            log("Création des géométries annulée...", level='INFO')
            break

        segments_str = composition[segments_list_field]

        if isinstance(segments_str, str):
            segment_ids = [int(id_str) for id_str in segments_str.split(',') if id_str.strip().isdigit()]
            if not segment_ids:
                log(f"Composition ID {composition.id()} ne contient pas d'identifiants de segments valides.", level='WARNING')
                processed_count += 1
                progress_bar.setValue(processed_count)
                continue

            new_geometry, non_connected = create_merged_geometry(segment_ids, segments_layer)
            for segment_id in non_connected:
                not_connected_segments[segment_id].append(composition.id())

            if new_geometry:
                feature = QgsFeature()
                feature.setGeometry(new_geometry)
                feature.setAttributes(composition.attributes())
                provider.addFeature(feature)
            else:
                log(f"La géométrie pour la composition ID {composition.id()} est vide après traitement des segments.", level='WARNING')
                failed_compositions.append(composition.id())

        processed_count += 1
        progress_bar.setValue(processed_count)

        # Pour garder l'appli fonctionnelle'
        if processed_count % 10 == 0:
            QgsApplication.processEvents()

    project = QgsProject.instance()
    if not project:
        return
    project.addMapLayer(new_layer)

    errors_messages = []

    if failed_compositions:
        failed_ids = ', '.join(map(str, failed_compositions))
        errors_messages.append({
            'error_type': 'failed_compositions',
            'composition_id': failed_ids,
        })

    if not_connected_segments:
        for segment_id, compositions_ids in not_connected_segments.items():
            disconnected_ids = ', '.join(map(str, sorted(compositions_ids)))
            errors_messages.append({
                'error_type': 'discontinuity',
                'composition_id': disconnected_ids,
                'segment_ids': (segment_id, segment_id)
            })

    return errors_messages

def update_compositions_geometries(compositions_layer, segments_layer, segments_list_field, progress_bar):

    total_compositions = sum(1 for _ in get_features_list(compositions_layer))
    processed_count = 0
    failed_compositions = []
    not_connected_segments = defaultdict(list)

    progress_bar.setRange(0, total_compositions)
    progress_bar.setValue(0)

    for composition in get_features_list(compositions_layer):
        if config.cancel_request:
            log("Mise à jour des géométries annulée...", level='INFO')
            break
        segments_str = composition[segments_list_field]

        if isinstance(segments_str, str):
            segment_ids = [int(id_str) for id_str in segments_str.split(',') if id_str.strip().isdigit()]
            if not segment_ids:
                log(f"Composition ID {composition.id()} ne contient pas d'identifiants de segments valides.", level='WARNING')
                processed_count += 1
                progress_bar.setValue(processed_count)
                continue

            new_geometry, non_connected = create_merged_geometry(segment_ids, segments_layer)
            for segment_id in non_connected:
                not_connected_segments[segment_id].append(composition.id())

            if new_geometry:
                composition.setGeometry(new_geometry)
                compositions_layer.updateFeature(composition)
            else:
                log(f"La géométrie pour la composition ID {composition.id()} est vide après traitement des segments.", level='WARNING')
                failed_compositions.append(composition.id())

        processed_count += 1
        progress_bar.setValue(processed_count)

        if processed_count % 10 == 0:
            QgsApplication.processEvents()

    compositions_layer.updateFields()

    errors_messages = []

    if failed_compositions:
        failed_ids = ', '.join(map(str, failed_compositions))
        errors_messages.append({
            'error_type': 'failed_compositions',
            'composition_id': failed_ids,
        })

    if not_connected_segments:
        for segment_id, compositions_ids in not_connected_segments.items():
            disconnected_ids = ', '.join(map(str, sorted(compositions_ids)))
            errors_messages.append({
                'error_type': 'discontinuity',
                'composition_id': disconnected_ids,
                'segment_ids': (segment_id, segment_id)
            })

    return errors_messages
