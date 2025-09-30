"""Functions to show compositions errors."""

from typing import cast

from qgis.core import (
    QgsGeometry,
)

from . import utils


class ErrorsFinder:
    def __init__(
        self, segments_layer, compositions_layer, segments_column_name, seg_id_column_name
    ):
        self.segments_layer = segments_layer
        self.compositions_layer = compositions_layer
        self.segments_column_name = segments_column_name
        self.seg_id_column_name = seg_id_column_name
        self.comp_id_column_name = utils.get_comp_id_column_name()
        comp_id = utils.get_comp_id_column_name()
        self.comp_id_column_name = comp_id if comp_id else ""

        self.errors = []
        self.segments_geom_dict = self._create_segments_geom_dict()
        self.used_segments_ids = set()

    def verify_compositions(self):
        """
        Vérifie les segments présents dans les listes des compositions et la continuité des segments.
        """

        for composition in self.compositions_layer.getFeatures():
            segments_list_str = composition[self.segments_column_name]
            if self.check_empty_list(composition, segments_list_str):
                segments_list = [seg.strip() for seg in str(segments_list_str).split(",")]

                self.check_duplicate_and_invalid_seg_id(composition, segments_list)
                self.check_discontinuity(composition, segments_list)

                self.used_segments_ids.update(segments_list)

        self.check_unused_segments()

        return self.errors

    def check_empty_list(self, composition, segments_list_str):
        if (
            segments_list_str is None
            or str(segments_list_str).upper() == "NULL"
            or not segments_list_str
        ):
            self.errors.append(
                {
                    "composition_id": composition[self.comp_id_column_name]
                    if self.comp_id_column_name
                    else composition.id(),
                    "error_type": "empty_segments_list",
                }
            )
            return False
        return True

    def check_duplicate_and_invalid_seg_id(self, composition, segments_list):
        seen_segments = set()
        for segment_id in segments_list:
            if not segment_id.isdigit():
                self.errors.append(
                    {
                        "composition_id": composition[self.comp_id_column_name]
                        if self.comp_id_column_name
                        else composition.id(),
                        "error_type": "invalid_segment_id",
                        "segment_list": (segments_list),
                        "invalid_segment_id": segment_id,
                    }
                )
            elif segment_id in seen_segments:
                self.errors.append(
                    {
                        "composition_id": composition[self.comp_id_column_name]
                        if self.comp_id_column_name
                        else composition.id(),
                        "error_type": "duplicate_segment_id",
                        "segment_list": (segments_list),
                        "duplicate_segment_id": segment_id,
                    }
                )
            else:
                seen_segments.add(segment_id)

    def check_discontinuity(self, composition, segments_list):
        for i, current_segment_id in enumerate(segments_list):
            # Pour tous les segments sauf le dernier de la liste (dont la continuité est vérifiée par celle du précédent).
            if i < len(segments_list) - 1:
                next_segment_id = segments_list[i + 1]

                if current_segment_id not in self.segments_geom_dict:
                    self.errors.append(
                        {
                            "composition_id": composition[self.comp_id_column_name]
                            if self.comp_id_column_name
                            else composition.id(),
                            "error_type": "missing_segment",
                            "segment_ids": (current_segment_id, None),
                            "missing_segment_id": current_segment_id,
                        }
                    )
                    continue

                if next_segment_id not in self.segments_geom_dict:
                    self.errors.append(
                        {
                            "composition_id": composition[self.comp_id_column_name]
                            if self.comp_id_column_name
                            else composition.id(),
                            "error_type": "missing_segment",
                            "segment_ids": (next_segment_id, None),
                            "missing_segment_id": next_segment_id,
                        }
                    )
                    continue

                current_geom = cast(
                    QgsGeometry, self.segments_geom_dict[current_segment_id]
                )
                next_geom = cast(QgsGeometry, self.segments_geom_dict[next_segment_id])

                current_points = current_geom.asPolyline()
                next_points = next_geom.asPolyline()

                if current_points and next_points:
                    # Calculer les distances entre les extrémités
                    distance_current_end_next_end = current_points[-1].distance(
                        next_points[-1]
                    )
                    distance_current_end_next_first = current_points[-1].distance(
                        next_points[0]
                    )
                    distance_current_first_next_end = current_points[0].distance(
                        next_points[-1]
                    )
                    distance_current_first_next_first = current_points[0].distance(
                        next_points[0]
                    )

                    # Vérifier s'il y a continuité
                    has_continuity = (
                        distance_current_end_next_end < 0.001
                        or distance_current_end_next_first < 0.001
                        or distance_current_first_next_end < 0.001
                        or distance_current_first_next_first < 0.001
                    )

                    if has_continuity:
                        # On cherche de potentiels aller-retours. Pour cela, on vérfie que le point de connexion
                        # entre le segment courant, le segment précédent et suivant n'est pas le même.
                        current_next_connection_point = None
                        if distance_current_end_next_first < 0.001:
                            current_next_connection_point = current_points[-1]
                        elif distance_current_end_next_end < 0.001:
                            current_next_connection_point = current_points[-1]
                        elif distance_current_first_next_first < 0.001:
                            current_next_connection_point = current_points[0]
                        elif distance_current_first_next_end < 0.001:
                            current_next_connection_point = current_points[0]

                        # Vérifier les aller-retours si ce n'est pas le premier segment
                        if i > 0 and current_next_connection_point is not None:
                            previous_segment_id = segments_list[i - 1]
                            if previous_segment_id in self.segments_geom_dict:
                                previous_geom = cast(
                                    QgsGeometry,
                                    self.segments_geom_dict[previous_segment_id],
                                )
                                previous_points = previous_geom.asPolyline()

                                if previous_points:
                                    # Calculer les distances entre les extrémités du segment précédent et courant
                                    distance_prev_end_current_end = previous_points[
                                        -1
                                    ].distance(current_points[-1])
                                    distance_prev_end_current_first = previous_points[
                                        -1
                                    ].distance(current_points[0])
                                    distance_prev_first_current_end = previous_points[
                                        0
                                    ].distance(current_points[-1])
                                    distance_prev_first_current_first = previous_points[
                                        0
                                    ].distance(current_points[0])

                                    # Déterminer le point de connexion entre précédent et courant
                                    prev_current_connection_point = None
                                    if distance_prev_end_current_first < 0.001:
                                        prev_current_connection_point = current_points[0]
                                    elif distance_prev_end_current_end < 0.001:
                                        prev_current_connection_point = current_points[-1]
                                    elif distance_prev_first_current_first < 0.001:
                                        prev_current_connection_point = current_points[0]
                                    elif distance_prev_first_current_end < 0.001:
                                        prev_current_connection_point = current_points[-1]

                                    # Si les deux points de connexion sont identiques (aller-retour)
                                    if (
                                        prev_current_connection_point is not None
                                        and current_next_connection_point.distance(
                                            prev_current_connection_point
                                        )
                                        < 0.001
                                    ):
                                        self.errors.append(
                                            {
                                                "composition_id": composition[
                                                    self.comp_id_column_name
                                                ]
                                                if self.comp_id_column_name
                                                else composition.id(),
                                                "error_type": "useless_segment",
                                                "segment_ids": (
                                                    current_segment_id,
                                                    next_segment_id,
                                                ),
                                            }
                                        )
                    else:
                        # discontinuité
                        self.errors.append(
                            {
                                "composition_id": composition[self.comp_id_column_name]
                                if self.comp_id_column_name
                                else composition.id(),
                                "error_type": "discontinuity",
                                "segment_ids": (
                                    current_segment_id,
                                    next_segment_id,
                                ),
                            }
                        )

    def check_unused_segments(self):
        unused_segment_ids = set(self.segments_geom_dict.keys()) - self.used_segments_ids
        for segment_id in unused_segment_ids:
            self.errors.append(
                {
                    "composition_id": None,
                    "error_type": "unused_segment",
                    "segment_ids": (segment_id, None),
                    "unused_segment_id": segment_id,
                }
            )

    def _create_segments_geom_dict(self):
        return {
            str(seg[self.seg_id_column_name]): seg.geometry()
            for seg in self.segments_layer.getFeatures()
        }
