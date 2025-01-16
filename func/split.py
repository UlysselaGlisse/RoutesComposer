"""functions used to handle segments spliting or merging."""

from qgis.core import (
    Qgis,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
)
from qgis.PyQt.QtWidgets import QDialog
from qgis.utils import iface

from ..ui.single_segment_dialog import SingleSegmentDialog
from .utils import get_features_list, log


class SplitManager:
    def __init__(self, routes_composer):
        self.routes_composer = routes_composer

    def get_compositions_list_segments(self, segment_id: int) -> list:
        """Récupère toutes les listes de segments contenant l'id du segment divisé."""
        if not segment_id:
            return []

        segments_lists_ids = []

        request = QgsFeatureRequest()
        expression = (
            f"{self.routes_composer.segments_column_name} LIKE '%,{segment_id},%' OR "
            f"{self.routes_composer.segments_column_name} LIKE '{segment_id},%' OR "
            f"{self.routes_composer.segments_column_name} LIKE '%,{segment_id}' OR "
            f"{self.routes_composer.segments_column_name} = '{segment_id}'"
        )
        request.setFilterExpression(expression)

        compositions = get_features_list(
            self.routes_composer.compositions_layer, request
        )

        for composition in compositions:
            segments_list_str = composition[self.routes_composer.segments_column_name]

            if not segments_list_str:
                continue

            try:
                segments_list_ids = [
                    int(id.strip()) for id in str(segments_list_str).split(",")
                ]
                if int(segment_id) in segments_list_ids:
                    log(f"Segment find in composition: {composition.id()}")
                    segments_lists_ids.append((composition.id(), segments_list_ids))

            except Exception as e:
                log(
                    f"Erreur lors du traitement de la composition {composition.id()}: {str(e)}",
                    level="WARNING",
                )

        return segments_lists_ids

    def update_compositions_segments(
        self,
        fid: int,
        old_id: int,
        new_id: int,
        original_feature: QgsFeature,
        new_feature: QgsFeature,
        segment_lists_ids: list,
    ) -> None:
        """Met à jour les compositions après division d'un segment."""

        self.routes_composer.compositions_layer.startEditing()

        original_geom = original_feature.geometry()
        new_geom = new_feature.geometry()

        for composition_id, segments_list in segment_lists_ids:
            try:
                old_index = segments_list.index(int(old_id))

                if len(segments_list) > 1:
                    last_segment = old_index == len(segments_list) - 1
                    segment_geom, is_new_geom = (
                        (new_geom if last_segment else original_geom),
                        (True if last_segment else False),
                    )

                    is_correctly_oriented = self.check_segment_orientation(
                        segment_geom, is_new_geom, segments_list, old_index
                    )

                    new_segments_list = segments_list.copy()
                    if is_correctly_oriented:
                        new_segments_list[old_index : old_index + 1] = [
                            int(old_id),
                            int(new_id),
                        ]
                    else:
                        new_segments_list[old_index : old_index + 1] = [
                            int(new_id),
                            int(old_id),
                        ]

                    if composition_id:
                        self.routes_composer.compositions_layer.changeAttributeValue(
                            composition_id,
                            self.routes_composer.segments_column_index,
                            ",".join(map(str, new_segments_list)),
                        )
                    log(
                        f"Composition {composition_id} has been updated with list: {new_segments_list}"
                    )

                else:
                    self.process_single_segment_composition(fid, old_id, new_id)

                self.routes_composer.compositions_layer.triggerRepaint()

            except Exception as e:
                raise Exception(
                    f"Erreur lors de la mise-à-jour automatique de la liste des segments {e}."
                )

    def check_segment_orientation(
        self,
        segment_geom: QgsGeometry,
        is_new_geom: bool,
        segments_list: list,
        old_index: int,
    ) -> bool:
        """Vérifie si un segment est orienté correctement par rapport aux segments adjacents."""
        if is_new_geom:
            adjacent_id = segments_list[old_index - 1]
        else:
            adjacent_id = segments_list[old_index + 1]

        adjacent_feature = next(
            self.routes_composer.segments_layer.getFeatures(
                f"{self.routes_composer.id_column_name} = {adjacent_id}"
            ),
            None,
        )

        if adjacent_feature:
            adjacent_geom = adjacent_feature.geometry()
            if not adjacent_geom.isEmpty():
                # Si la géométrie touche le segment précédant (si dernier) ou suivant: à l'envers.'
                if adjacent_geom.touches(segment_geom):
                    return False

        return True

    def process_single_segment_composition(self, fid: int, old_id: int, new_id: int):
        """Gère le cas d'une composition d'un seul segment."""
        dialog = SingleSegmentDialog(old_id=old_id, new_id=new_id)
        dialog.current_segments = [old_id, new_id]
        result = dialog.exec_()

        if result == QDialog.Accepted:
            composition = next(
                self.routes_composer.compositions_layer.getFeatures(
                    f"{self.routes_composer.segments_column_name} = '{old_id}'"
                ),
                None,
            )

            if composition:
                try:
                    new_segments_str = ",".join(map(str, dialog.current_segments))
                    self.routes_composer.compositions_layer.startEditing()
                    self.routes_composer.compositions_layer.changeAttributeValue(
                        composition.id(),
                        self.routes_composer.segments_column_index,
                        new_segments_str,
                    )
                    log(
                        f"Composition {composition.id()} has been updated with segments: '{new_segments_str}'"
                    )

                except Exception as e:
                    iface.messageBar().pushMessage(
                        "Erreur",
                        f"Erreur lors de la mise à jour de la composition: {str(e)}",
                        level=Qgis.MessageLevel.Critical,
                    )
            else:
                iface.messageBar().pushMessage(
                    "Attention",
                    f"Aucune composition trouvée avec le segment {old_id}",
                    level=Qgis.MessageLevel.Warning,
                )
            return dialog.current_segments
        else:
            return None

    def clean_invalid_segments(self) -> None:
        """Supprime les références aux segments qui n'existent plus dans la table segments."""
        valid_segments_ids = {
            str(f[self.routes_composer.id_column_name])
            for f in get_features_list(self.routes_composer.segments_layer)
            if f["id"] is not None
        }
        compositions = get_features_list(self.routes_composer.compositions_layer)

        self.routes_composer.compositions_layer.startEditing()
        for composition in compositions:
            segments_list_str = composition[self.routes_composer.segments_column_name]
            if (
                segments_list_str is None
                or str(segments_list_str).upper() == "NULL"
                or not segments_list_str
            ):
                continue

            segments_list = str(segments_list_str).split(",")
            valid_segments = [
                seg.strip()
                for seg in segments_list
                if seg.strip() in valid_segments_ids
            ]

            if len(valid_segments) != len(segments_list):
                new_segments_str = ",".join(valid_segments)
                log(
                    f"Removing segments {[seg.strip() for seg in segments_list if seg.strip() not in valid_segments_ids]} from composition {composition.id()}"
                )
                self.routes_composer.compositions_layer.changeAttributeValue(
                    composition.id(),
                    self.routes_composer.segments_column_index,
                    new_segments_str,
                )

    def has_duplicate_segment_id(self, segment_id: int) -> bool:
        """Vérifie si un id de segments existe plusieurs fois. Si oui, il s'agit d'un segment divisé."""
        expression = f"{self.routes_composer.id_column_name} = '{segment_id}'"
        request = QgsFeatureRequest().setFilterExpression(expression)
        request.setLimit(2)

        segments = get_features_list(self.routes_composer.segments_layer, request)
        return len(segments) > 1

    def update_segment_id(self, fid: int, next_id: int) -> None:
        """Met à jour l'id des segments divisés."""
        self.routes_composer.segments_layer.startEditing()
        self.routes_composer.segments_layer.changeAttributeValue(
            fid, self.routes_composer.id_column_index, int(next_id)
        )
        self.routes_composer.segments_layer.triggerRepaint()

    def get_next_id(self) -> int:
        next_id = int(
            self.routes_composer.segments_layer.maximumValue(
                self.routes_composer.id_column_index
            )
        )
        return next_id + 1
