"""Functions to show compositions errors."""

import time
from collections import defaultdict
from functools import wraps
from typing import cast

from qgis.core import (
    QgsGeometry,
    QgsProject,
)


def timer_decorator(func):
    """Indique le temps que prend une fonction à s'exécuter."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} a pris {(end - start) * 1000:.2f} ms")
        return result

    return wrapper


def get_comp_id_column_name():
    project = QgsProject.instance()
    if not project:
        return ""

    compo_id_column_name, _ = (
        project.readEntry("routes_composer", "compo_id_column_name", "id") or "id"
    )

    if compo_id_column_name:
        return compo_id_column_name
    else:
        return ""


class ErrorsFinder:
    def __init__(self):
        self.segments_layer = QgsProject.instance().mapLayersByName("segments")[0]
        self.compositions_layer = QgsProject.instance().mapLayersByName("compositions")[0]

        self.segments_column_name = "segments"
        self.seg_id_column_name = "id"
        comp_id = get_comp_id_column_name()
        self.comp_id_column_name = comp_id if comp_id else ""

        self.errors = []
        self.segments_geom_dict = self._create_segments_geom_dict()
        self.used_segments_ids = set()

    @timer_decorator
    def verify_compositions(self):
        """
        Vérifie les segments présents dans les listes des compositions et la continuité des segments.
        """

        compositions = self.compositions_layer.getFeatures()

        for composition in compositions:
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
        discontinuity_errors = defaultdict(list)

        for i, current_segment_id in enumerate(segments_list):
            # Pour tous les segments sauf le dernier de la liste (dont la coninuité est vérifié par celle du précédent).
            if i < len(segments_list) - 1:
                current_segment_id = segments_list[i]
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
                    # si le premier ou le dernier point du segment courant ne touche ni le premier ni le dernier point du segment suivant, discontinuité.
                    distance_1 = current_points[-1].distance(next_points[-1])
                    distance_2 = current_points[-1].distance(next_points[0])
                    distance_3 = current_points[0].distance(next_points[-1])
                    distance_4 = current_points[0].distance(next_points[0])

                    if (
                        distance_1 < 0.001
                        or distance_2 < 0.001
                        or distance_3 < 0.001
                        or distance_4 < 0.001
                    ):
                        pass
                    else:
                        discontinuity_errors[current_segment_id].append(composition.id())
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


e = ErrorsFinder()
