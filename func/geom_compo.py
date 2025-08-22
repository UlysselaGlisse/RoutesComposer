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
from .utils import LayersAssociationManager, log


class GeomCompo:
    def __init__(
        self,
        segments_layer,
        compositions_layer,
        seg_id_column_name,
        segments_column_name,
    ):
        self.segments_layer = segments_layer
        self.compositions_layer = compositions_layer
        self.seg_id_column_name = seg_id_column_name
        self.segments_column_name = segments_column_name

        self.lam = LayersAssociationManager(
            self.compositions_layer,
            self.segments_layer,
            self.segments_column_name,
            self.seg_id_column_name,
        )

    def update_geometries_on_the_fly(self, segment_id):
        affected_compositions = self.lam.get_compositions_for_segment(
            segment_id, get_feature="yes"
        )
        if not affected_compositions:
            return

        needed_segments = {
            seg_id
            for composition in affected_compositions
            for seg_id in self.lam.convert_segments_list(
                composition[self.segments_column_name]
            )
        }

        segments_points = {}
        expr = f"{self.seg_id_column_name} IN ({','.join(map(str, needed_segments))})"
        segments = self.segments_layer.getFeatures(expr)
        segments_points = {
            segment[self.seg_id_column_name]: segment.geometry().asPolyline()
            for segment in segments
            if segment.geometry() and not segment.geometry().isEmpty()
        }

        updates = {}
        for composition in affected_compositions:
            segments_list = self.lam.convert_segments_list(
                composition[self.segments_column_name]
            )

            new_geometry = self.create_merged_geometry(
                segments_list, segments_points
            )
            if new_geometry:
                if composition.id() >= 0:
                    updates[composition.id()] = new_geometry[0]
                else:
                    if not self.compositions_layer.isEditable():
                        self.compositions_layer.startEditing()
                    try:
                        self.compositions_layer.changeGeometry(
                            composition.id(), new_geometry[0]
                        )
                    except Exception as e:
                        log(f"Error occurred while updating geometry: {e}")

        if updates:
            try:
                self.compositions_layer.dataProvider().changeGeometryValues(
                    updates
                )
            except Exception as e:
                raise Exception(
                    f"Error occurred while updating geometries: {e}"
                )

    def update_compositions_geometries(self, progress_bar, mode="update"):
        provider, new_layer = None, None
        if mode == "new":
            provider, new_layer = self.create_new_layer()
            if provider is None or new_layer is None:
                return None

        processed_count = 0
        failed_compositions = []
        not_connected_segments = defaultdict(list)
        segments_points = self.get_segments_points()

        for composition in self.compositions_layer.getFeatures():
            if config.cancel_request:
                log("Mise à jour des géométries annulée...", level="INFO")
                self.compositions_layer.rollBack()
                break

            segments_list = self.lam.convert_segments_list(
                composition[self.segments_column_name]
            )
            if segments_list is not None:
                new_geometry, non_connected = self.create_merged_geometry(
                    segments_list,
                    segments_points,
                )
                if provider is not None:
                    failed_compositions.extend(
                        self.handle_geometry_creation(
                            provider,
                            composition,
                            new_geometry,
                        ),
                    )
                else:
                    failed_compositions.extend(
                        self.handle_geometry_update(composition, new_geometry),
                    )
                not_connected_segments.update(
                    self.update_not_connected_segments(
                        composition.id(), non_connected
                    ),
                )

            processed_count += 1
            progress_bar.setValue(processed_count)

            if processed_count % 5 == 0:
                QgsApplication.processEvents()

        if provider is not None:
            project = QgsProject.instance()
            if not project:
                return None

            project.addMapLayer(new_layer)

        self.compositions_layer.updateFields()
        return self._generate_error_messages(
            failed_compositions,
            not_connected_segments,
        )

    def points_are_equal(
        self,
        point1: QgsPoint,
        point2: QgsPoint,
        tolerance=1e-8,
    ) -> bool:
        return math.isclose(
            point1.x(), point2.x(), abs_tol=tolerance
        ) and math.isclose(
            point1.y(),
            point2.y(),
            abs_tol=tolerance,
        )

    def create_merged_geometry(
        self,
        segment_ids: List[int],
        segments_points: dict,
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
                                    (current_segment_id, segment_ids[i + 1]),
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
                                    (current_segment_id, segment_ids[i - 1]),
                                )

            else:
                result_points.extend(current_points)

        if result_points:
            line_string = QgsLineString(
                [QgsPoint(p.x(), p.y()) for p in result_points]
            )
            return QgsGeometry(line_string), not_connected_segments
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
                return list(reversed(current_points)), []

            # Le premier point touche le segment adjacent
            if self.points_are_equal(current_points[0], adjacent_points[p]):
                if last_segment == "no":
                    return list(reversed(current_points)), []
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
            segment_id = segment_feature[self.seg_id_column_name]
            geom = segment_feature.geometry()

            if geom is None or geom.isNull():
                continue

            points = geom.asPolyline()
            if points:
                segments_points[segment_id] = points

        return segments_points

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
        return {
            tuple(segment_ids): [composition_id]
            for segment_ids in non_connected
        }

    def _generate_error_messages(
        self, failed_compositions, not_connected_segments
    ):
        errors_messages = []

        if failed_compositions:
            failed_ids = ", ".join(map(str, failed_compositions))
            errors_messages.append(
                {
                    "error_type": "failed_compositions",
                    "composition_id": failed_ids,
                },
            )

        if not_connected_segments:
            for segment_ids, compositions_ids in not_connected_segments.items():
                disconnected_ids = ", ".join(map(str, sorted(compositions_ids)))
                errors_messages.append(
                    {
                        "error_type": "discontinuity",
                        "composition_id": disconnected_ids,
                        "segment_ids": segment_ids,
                    },
                )

        return errors_messages
