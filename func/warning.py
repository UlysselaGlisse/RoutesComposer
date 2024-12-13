"""Functions to show compositions errors."""

from collections import defaultdict
from typing import cast

from qgis.core import (
    QgsGeometry,
)

from . import utils

error_layer = None


def verify_segments(
    segments_layer, compositions_layer, segments_column_name, id_column_name
):
    """
    Vérifie les segments présents dans les listes des compositions et la continuité des segments.
    """
    errors = []

    segments_geom_dict = {
        str(seg[id_column_name]): seg.geometry()
        for seg in utils.get_features_list(segments_layer)
    }
    compositions = utils.get_features_list(compositions_layer)

    used_segment_ids = set()
    discontinuity_errors = defaultdict(list)

    for composition in compositions:
        segments_str = composition[segments_column_name]
        if (
            segments_str is None
            or str(segments_str).upper() == "NULL"
            or not segments_str
        ):
            errors.append(
                {
                    "composition_id": composition.id(),
                    "error_type": "empty_segments_list",
                }
            )
            continue
        segments_list = [seg.strip() for seg in str(segments_str).split(",")]
        for segment_id in segments_list:
            if not segment_id.isdigit():
                errors.append(
                    {
                        "composition_id": composition.id(),
                        "error_type": "invalid_segment_id",
                        "segment_list": (segments_list),
                        "invalid_segment_id": segment_id,
                    }
                )
        used_segment_ids.update(segments_list)

        for i, current_segment_id in enumerate(segments_list):
            # Pour tous les segments sauf le dernier de la liste (dont la coninuité est vérifié par celle du précédent).
            if i < len(segments_list) - 1:

                current_segment_id = segments_list[i]
                next_segment_id = segments_list[i + 1]

                if current_segment_id not in segments_geom_dict:
                    errors.append(
                        {
                            "composition_id": composition.id(),
                            "error_type": "missing_segment",
                            "segment_ids": (current_segment_id, None),
                            "missing_segment_id": current_segment_id,
                        }
                    )
                    continue

                if next_segment_id not in segments_geom_dict:
                    errors.append(
                        {
                            "composition_id": composition.id(),
                            "error_type": "missing_segment",
                            "segment_ids": (next_segment_id, None),
                            "missing_segment_id": next_segment_id,
                        }
                    )
                    continue

                current_geom = cast(
                    QgsGeometry, segments_geom_dict[current_segment_id]
                )
                next_geom = cast(
                    QgsGeometry, segments_geom_dict[next_segment_id]
                )

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
                        discontinuity_errors[current_segment_id].append(
                            composition.id()
                        )
                        errors.append(
                            {
                                "composition_id": composition.id(),
                                "error_type": "discontinuity",
                                "segment_ids": (
                                    current_segment_id,
                                    next_segment_id,
                                ),
                            }
                        )

    unused_segment_ids = set(segments_geom_dict.keys()) - used_segment_ids
    for segment_id in unused_segment_ids:
        errors.append(
            {
                "composition_id": None,
                "error_type": "unused_segment",
                "segment_ids": (segment_id, None),
                "unused_segment_id": segment_id,
            }
        )

    return errors
