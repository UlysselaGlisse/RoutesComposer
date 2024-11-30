"""Functions for creating geometries of the compositions."""

import math
from collections import defaultdict
from typing import List, Tuple

from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsLineString,
    QgsPoint,
    QgsProject,
    QgsVectorLayer,
)

from .. import config
from ..func.utils import get_features_list, log


class GeomCompo:
    def __init__(
        self,
        segments_layer,
        compositions_layer,
        id_column_name,
        segments_column_name,
    ):
        self.segments_layer = segments_layer
        self.compositions_layer = compositions_layer
        self.id_column_name = id_column_name
        self.segments_column_name = segments_column_name

    def update_geometries_on_the_fly(self, segment_id):
        affected_compositions = []
        expr = (
            f"{self.segments_column_name} LIKE '%,{segment_id},%' OR "
            f"{self.segments_column_name} LIKE '{segment_id},%' OR "
            f"{self.segments_column_name} LIKE '%,{segment_id}' OR "
            f"{self.segments_column_name} = '{segment_id}'"
        )
        for composition in self.compositions_layer.getFeatures(expr):
            affected_compositions.append(composition)

        if not affected_compositions:
            return

        needed_segments = set()
        for composition in affected_compositions:
            segments_str = str(composition[self.segments_column_name])
            segment_ids = [
                int(id_str) for id_str in segments_str.split(",") if id_str.strip()
            ]
            needed_segments.update(segment_ids)

        segments_points = {}
        expr = f"{self.id_column_name} IN ({','.join(map(str, needed_segments))})"
        for segment in self.segments_layer.getFeatures(expr):
            points = segment.geometry().asPolyline()
            if points:
                segments_points[segment[self.id_column_name]] = points

        self.compositions_layer.startEditing()
        for composition in affected_compositions:
            segments_str = str(composition[self.segments_column_name])
            segment_ids = [
                int(id_str) for id_str in segments_str.split(",") if id_str.strip()
            ]

            new_geometry = self.create_merged_geometry(segment_ids, segments_points)
            if new_geometry:
                self.compositions_layer.changeGeometry(
                    composition.id(), new_geometry[0]
                )

    def update_compositions_geometries(self, progress_bar, mode="update"):
        provider, new_layer = None, None
        if mode == "new":
            provider, new_layer = self.create_new_layer()
            if provider is None or new_layer is None:
                return

        processed_count = 0
        failed_compositions = []
        not_connected_segments = defaultdict(list)
        segments_points = self.get_segments_points()

        for composition in get_features_list(self.compositions_layer):
            if config.cancel_request:
                log("Mise à jour des géométries annulée...", level="INFO")
                self.compositions_layer.rollBack()
                break

            segment_ids = self.get_segments_ids(composition)
            if segment_ids is not None:
                new_geometry, non_connected = self.create_merged_geometry(
                    segment_ids, segments_points
                )
                if provider is not None:
                    failed_compositions.extend(
                        self.handle_geometry_creation(
                            provider, composition, new_geometry
                        )
                    )
                else:
                    failed_compositions.extend(
                        self.handle_geometry_update(composition, new_geometry)
                    )
                not_connected_segments.update(
                    self.update_not_connected_segments(composition.id(), non_connected)
                )

            processed_count += 1
            progress_bar.setValue(processed_count)

            if processed_count % 5 == 0:
                QgsApplication.processEvents()

        if provider is not None:
            project = QgsProject.instance()
            if not project:
                return

            project.addMapLayer(new_layer)

        self.compositions_layer.updateFields()
        return self._generate_error_messages(
            failed_compositions, not_connected_segments
        )

    def points_are_equal(
        self, point1: QgsPoint, point2: QgsPoint, tolerance=1e-8
    ) -> bool:
        return math.isclose(point1.x(), point2.x(), abs_tol=tolerance) and math.isclose(
            point1.y(), point2.y(), abs_tol=tolerance
        )

    def create_merged_geometry(
        self, segment_ids: List[int], segments_points: dict
    ) -> Tuple[QgsGeometry, List[Tuple[int, int]]]:
        if not segment_ids:
            return QgsGeometry(), []

        not_connected_segments = []
        result_points = []

        for i, current_segment_id in enumerate(segment_ids):
            current_points = segments_points.get(current_segment_id)
            if not current_points:
                log(
                    f"Aucun point trouvé pour le segment: {current_segment_id}",
                    level="ERROR",
                )
                continue

            if len(segment_ids) > 1:
                # Tous les segments suaf le dernier de la liste.
                if i < len(segment_ids) - 1:
                    next_points = segments_points.get(segment_ids[i + 1])
                    if next_points:
                        current_points, not_connected_segment = (
                            self.check_segment_orientation(
                                current_points,
                                next_points,
                                current_segment_id,
                                segment_ids[i + 1],
                                last_segment="no",
                            )
                        )
                        if current_points:
                            result_points.extend(current_points[:-1])
                            if not_connected_segment:
                                not_connected_segments.append(
                                    (current_segment_id, segment_ids[i + 1])
                                )

                else:
                    prev_points = segments_points.get(segment_ids[i - 1])
                    if prev_points:
                        current_points, not_connected_segment = (
                            self.check_segment_orientation(
                                current_points,
                                prev_points,
                                current_segment_id,
                                segment_ids[i - 1],
                                last_segment="yes",
                            )
                        )
                        if current_points:
                            result_points.extend(current_points)
                            if not_connected_segment:
                                not_connected_segments.append(
                                    (current_segment_id, segment_ids[i - 1])
                                )

            else:
                result_points.extend(current_points)

        if result_points:
            line_string = QgsLineString([QgsPoint(p.x(), p.y()) for p in result_points])
            return QgsGeometry(line_string), not_connected_segments
        else:
            log(
                "Aucun point trouvé après le traitement des segments.",
                level="WARNING",
            )
            return QgsGeometry(), []

    def check_segment_orientation(
        self,
        current_points,
        adjacent_points,
        current_segment_id,
        adjacent_segment_id,
        last_segment="no",
    ):
        for p in [0, -1]:
            # Le dernier point touche le segment adjacent
            if self.points_are_equal(current_points[-1], adjacent_points[p]):
                if last_segment == "no":
                    return current_points, []
                else:
                    return list(reversed(current_points)), []

            # Le premier point touche le segment adjacent
            elif self.points_are_equal(current_points[0], adjacent_points[p]):
                if last_segment == "no":
                    return list(reversed(current_points)), []
                else:
                    return current_points, []

        # si aucun point ne se touche, on renvoie la géométrie actuel.
        return current_points, [current_segment_id, adjacent_segment_id]

    def create_new_layer(
        self,
    ):
        new_layer = QgsVectorLayer(
            "LineString?crs=" + self.segments_layer.crs().authid(),
            self.compositions_layer.name(),
            "memory",
        )
        provider = new_layer.dataProvider()

        if provider is None:
            log(
                "Le fournisseur de données de la nouvelle couche est None.",
                level="ERROR",
            )
            return None, None

        provider.addAttributes(self.compositions_layer.fields())
        new_layer.updateFields()

        return provider, new_layer

    def get_segments_points(self):
        segments_points = {}
        for segment_feature in self.segments_layer.getFeatures():
            segment_id = segment_feature[self.id_column_name]
            points = segment_feature.geometry().asPolyline()
            if points:
                segments_points[segment_id] = points

        return segments_points

    def get_segments_ids(self, composition):
        segments_str = composition[self.segments_column_name]
        if not isinstance(segments_str, str):
            return None

        segment_ids = [
            int(id_str)
            for id_str in segments_str.split(",")
            if id_str.strip().isdigit()
        ]

        if not segment_ids:
            log(
                f"Composition ID {composition.id()} ne contient pas d'identifiants de segments valides.",
                level="WARNING",
            )
            return None

        return segment_ids

    def handle_geometry_creation(self, provider, composition, new_geometry):
        failed_compositions = []
        if new_geometry:
            feature = QgsFeature()
            feature.setGeometry(new_geometry)
            feature.setAttributes(composition.attributes())
            provider.addFeature(feature)
        else:
            log(
                f"La géométrie pour la composition ID {composition.id()} est vide après traitement des segments.",
                level="WARNING",
            )
            failed_compositions.append(composition.id())

        return failed_compositions

    def handle_geometry_update(self, composition, new_geometry):
        failed_compositions = []
        if new_geometry:
            composition.setGeometry(new_geometry)
            self.compositions_layer.updateFeature(composition)
        else:
            log(
                f"La géométrie pour la composition ID {composition.id()} est vide après traitement des segments.",
                level="WARNING",
            )
            failed_compositions.append(composition.id())

        return failed_compositions

    def update_not_connected_segments(self, composition_id, non_connected):
        if not non_connected:
            return {}
        return {tuple(segment_ids): [composition_id] for segment_ids in non_connected}

    def _generate_error_messages(self, failed_compositions, not_connected_segments):
        errors_messages = []

        if failed_compositions:
            failed_ids = ", ".join(map(str, failed_compositions))
            errors_messages.append(
                {
                    "error_type": "failed_compositions",
                    "composition_id": failed_ids,
                }
            )

        if not_connected_segments:
            for segment_ids, compositions_ids in not_connected_segments.items():
                disconnected_ids = ", ".join(map(str, sorted(compositions_ids)))
                errors_messages.append(
                    {
                        "error_type": "discontinuity",
                        "composition_id": disconnected_ids,
                        "segment_ids": segment_ids,
                    }
                )

        return errors_messages
