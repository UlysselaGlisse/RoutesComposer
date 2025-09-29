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
from .utils import log


class SplitManager:
    def __init__(self, routes_composer):
        self.rc = routes_composer

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

        self.rc.compositions_layer.startEditing()

        original_geom = original_feature.geometry()
        new_geom = new_feature.geometry()

        updates = {}
        try:
            self.rc.is_splitting = True

            for composition_id, segments_list in segment_lists_ids:
                if len(segments_list) > 1:
                    old_index = segments_list.index(int(old_id))
                    # On utilise la géométrie de la nouvelle entité pour déterminer
                    # le sens que pour le dernier segment de la liste.
                    last_segment = old_index == len(segments_list) - 1
                    segment_geom = new_geom if last_segment else original_geom
                    is_new_geom = True if last_segment else False

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

                    new_segments_list = ",".join(map(str, new_segments_list))

                    if composition_id >= 0:
                        updates[composition_id] = {
                            self.rc.segments_column_index: new_segments_list
                        }
                    else:
                        self.rc.compositions_layer.changeAttributeValue(
                            composition_id,
                            self.rc.segments_column_index,
                            new_segments_list,
                        )
                else:
                    self.process_single_segment_composition(fid, old_id, new_id)

            if updates:
                self.rc.compositions_layer.startEditing()
                self.rc.compositions_layer.dataProvider().changeAttributeValues(updates)

            self.rc.compositions_layer.reload()

        except Exception as e:
            raise Exception(
                f"Erreur lors de la mise-à-jour automatique de la liste des segments {e}."
            )
        finally:
            self.rc.is_splitting = False

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
            self.rc.segments_layer.getFeatures(
                f"{self.rc.seg_id_column_name} = {adjacent_id}"
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
                self.rc.compositions_layer.getFeatures(
                    f"{self.rc.segments_column_name} = '{old_id}'"
                ),
                None,
            )

            if composition:
                try:
                    new_segments_str = ",".join(map(str, dialog.current_segments))
                    self.rc.compositions_layer.startEditing()
                    self.rc.compositions_layer.changeAttributeValue(
                        composition.id(),
                        self.rc.segments_column_index,
                        new_segments_str,
                    )
                    log(
                        f"Composition {composition.id()} (data provider) has been updated with segments: '{new_segments_str}'"
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
            f[self.rc.seg_id_column_name]
            for f in self.rc.segments_layer.getFeatures()
            if f.id() is not None
        }

        self.rc.compositions_layer.startEditing()
        for composition in self.rc.compositions_layer.getFeatures():
            segments_list = self.rc.lam.convert_segments_list(
                composition[self.rc.segments_column_name]
            )
            valid_segments = [seg for seg in segments_list if seg in valid_segments_ids]

            if len(valid_segments) != len(segments_list):
                new_segments_str = ",".join(map(str, valid_segments))
                log(
                    f"Removing segments {[seg for seg in segments_list if seg not in valid_segments_ids]} from composition {composition.id()}"
                )
                self.rc.compositions_layer.changeAttributeValue(
                    composition.id(),
                    self.rc.segments_column_index,
                    new_segments_str,
                )

    def has_duplicate_segment_id(self, segment_id: int) -> bool:
        """Vérifie si un id de segments existe plusieurs fois. Si oui, il s'agit d'un segment divisé."""
        expression = f"{self.rc.seg_id_column_name} = '{segment_id}'"
        request = QgsFeatureRequest().setFilterExpression(expression)
        request.setLimit(2)

        segments = list(self.rc.segments_layer.getFeatures(request))
        return len(segments) > 1

    def update_segment_id(self, fid: int, next_id: int) -> None:
        """Met à jour l'id des segments divisés."""
        self.rc.segments_layer.startEditing()
        self.rc.segments_layer.changeAttributeValue(
            fid, self.rc.id_column_index, int(next_id)
        )
        self.rc.segments_layer.triggerRepaint()

    def get_next_id(self) -> int:
        next_id = int(self.rc.segments_layer.maximumValue(self.rc.id_column_index))
        return next_id + 1
