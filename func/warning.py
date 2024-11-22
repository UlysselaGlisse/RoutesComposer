"""Functions to show compositions errors."""

from collections import defaultdict
from typing import cast
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsGeometry,
    QgsLineSymbol,
    QgsProject,
    QgsVectorLayer,
)
from PyQt5.QtCore import QVariant
from qgis.utils import iface

from . import utils
from .utils import log

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

    discontinuity_errors = defaultdict(list)

    for composition in compositions:
        segments_str = composition[segments_column_name]
        if (
            segments_str is None
            or str(segments_str).upper() == "NULL"
            or not segments_str
        ):
            continue
        segments_list = [seg.strip() for seg in str(segments_str).split(",")]
        log(
            f"Composition {composition.id()} début de traitement pour la liste: {segments_list}"
        )

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
                        distance_1 < 0.1
                        or distance_2 < 0.1
                        or distance_3 < 0.1
                        or distance_4 < 0.1
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

    formatted_errors = []

    for error in errors:
        if error["error_type"] == "missing_segment":
            formatted_errors.append(
                {
                    "error_type": "missing_segment",
                    "composition_id": error["composition_id"],
                    "segment_ids": error["segment_ids"],
                    "missing_segment_id": error["missing_segment_id"],
                }
            )
        elif error["error_type"] == "discontinuity":
            segment_ids = error["segment_ids"]
            composition_id = error["composition_id"]
            formatted_errors.append(
                {
                    "error_type": "discontinuity",
                    "composition_id": composition_id,
                    "segment_ids": segment_ids,
                }
            )

    return formatted_errors


def highlight_errors(errors, segments_layer, id_column_name):
    """
    Crée une nouvelle couche temporaire avec les segments ayant des erreurs.
    Fonctionnelle, mais non utilisée pour le moment.
    """
    error_layer_name = "Erreurs"
    project = QgsProject.instance()
    if not project:
        return

    existing_layers = project.mapLayers().values()
    error_layer = next(
        (
            layer
            for layer in existing_layers
            if layer.name() == error_layer_name
        ),
        None,
    )
    if error_layer is None:
        error_layer = QgsVectorLayer(
            "LineString?crs=" + segments_layer.crs().authid(),
            "Erreurs",
            "memory",
        )
        provider = error_layer.dataProvider()

        provider.addAttributes(
            [
                QgsField("segment_id", QVariant.Int),
                QgsField("error_type", QVariant.String),
                QgsField("composition_id", QVariant.Int),
            ]
        )
        error_layer.updateFields()

        symbol = QgsLineSymbol.createSimple({"color": "red", "width": "2"})
        error_layer.renderer().setSymbol(symbol)

        QgsProject.instance().addMapLayer(error_layer)
    else:
        error_layer.dataProvider().truncate()

    features = []
    for error in errors:
        if error["error_type"] == "discontinuity":
            segment_id1 = int(error["segment_ids"][0])
            segment_id2 = int(error["segment_ids"][1])

            segment_id1_feature = next(
                segments_layer.getFeatures(
                    QgsFeatureRequest().setFilterExpression(
                        f"\"{id_column_name}\" = '{segment_id1}'"
                    )
                ),
                None,
            )
            geom1 = (
                segment_id1_feature.geometry() if segment_id1_feature else None
            )

            segment_id2_feature = next(
                segments_layer.getFeatures(
                    QgsFeatureRequest().setFilterExpression(
                        f"\"{id_column_name}\" = '{segment_id2}'"
                    )
                ),
                None,
            )
            geom2 = (
                segment_id2_feature.geometry() if segment_id2_feature else None
            )

            if geom1 and geom2 and geom1.isGeosValid() and geom2.isGeosValid():
                feat1 = QgsFeature()
                feat1.setGeometry(geom1)
                feat1.setAttributes(
                    [segment_id1, error["error_type"], error["composition_id"]]
                )
                features.append(feat1)

                feat2 = QgsFeature()
                feat2.setGeometry(geom2)
                feat2.setAttributes(
                    [segment_id2, error["error_type"], error["composition_id"]]
                )
                features.append(feat2)

    if features:
        error_layer.dataProvider().addFeatures(features)
        error_layer.updateExtents()
    else:
        print("Aucune nouvelle erreur à ajouter.")

    iface.mapCanvas().refresh()
