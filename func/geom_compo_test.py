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

class GeomCompo:
    def __init__(self, segments_layer, compositions_layer, segments_column_name):
        self.segments_layer = segments_layer
        self.compositions_layer = compositions_layer
        self.segments_column_name = segments_column_name

    def points_are_equal(self, point1: QgsPoint, point2: QgsPoint, tolerance=1e-8) -> bool:
        """
        Vérifie si deux points sont égaux.
        """
        return math.isclose(point1.x(), point2.x(), abs_tol=tolerance) and \
                math.isclose(point1.y(), point2.y(), abs_tol=tolerance)

    def create_merged_geometry(self, segment_ids):
        """
        Crée une géométrie fusionnée à partir d'une liste d'identifiants de segments.
        La fonction détermine automatiquement l'orientation de chaque segment en fonction
        de ses connexions avec les segments adjacents.
        """
        merged = QgsGeometry()

        for i, segment_id in enumerate(segment_ids):
            if len(segment_ids) > 1:

                for segment_id in segment_ids:
                    index = segment_ids.index(segment_id)
                    segment_geom = next(self.segments_layer.getFeatures(f"{self.id_column_name} = '{segment_id}'")).geometry()
                    segment_points = segment_geom.asPolyline()

                    next_segment_id = index + 1
                    next_segment_geom = next(self.segments_layer.getFeatures(f"{self.id_column_name} = '{next_segment_id}'")).geometry()
                    next_segment_point = next_segment_geom.asPolyline()

                    if segment_id == segment_ids[0]:
                        for i in next_segment_point[0,1]:
                            if not segment_geom.asPolyline()[-1].distance(i) < 0.001:
                                merged = QgsGeometry.fromPolylineXY(segment_geom.asPolyline()[::-1])
                            else:
                                merged = segment_geom
                    else:
                        for i in next_segment_point[0,1]:
                            if not segment_geom.asPolyline()[-1].distance(i) < 0.001:
                                merged = merged.combine(QgsGeometry.fromPolylineXY(segment_geom.asPolyline()[::-1]))
                            else:
                                merged = merged.combine(segment_geom)
            else:
                merged = segment_geom =next(self.segments_layer.getFeatures(f"{self.id_column_name} = '{segment_id}'")).geometry()

        return merged

    def create_compositions_geometries(self, progress_bar):

        new_layer = QgsVectorLayer("LineString?crs=" + self.segments_layer.crs().authid(), "Merged Geometries", "memory")
        provider = new_layer.dataProvider()

        provider = new_layer.dataProvider()

        if provider is None:
            log("Le fournisseur de données de la nouvelle couche est None.", level='ERROR')
            return [{'error_type': 'provider_creation_failed'}]

        provider.addAttributes(self.compositions_layer.fields())
        new_layer.updateFields()

        total_compositions = sum(1 for _ in get_features_list(self.compositions_layer))
        processed_count = 0
        failed_compositions = []
        not_connected_segments = defaultdict(list)

        progress_bar.setRange(0, total_compositions)
        progress_bar.setValue(0)

        for composition in get_features_list(self.compositions_layer):
            if config.cancel_request:
                log("Création des géométries annulée...", level='INFO')
                break

            segments_str = composition[self.segments_column_name]

            if isinstance(segments_str, str):
                segment_ids = [int(id_str) for id_str in segments_str.split(',') if id_str.strip().isdigit()]
                if not segment_ids:
                    log(f"Composition ID {composition.id()} ne contient pas d'identifiants de segments valides.", level='WARNING')
                    processed_count += 1
                    progress_bar.setValue(processed_count)
                    continue

                new_geometry = self.create_merged_geometry(segment_ids)

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
