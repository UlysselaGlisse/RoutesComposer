from PyQt5.QtCore import QVariant
from qgis.core import QgsFeatureRequest, QgsField

from .utils import LayersAssociationManager


class SegmentsBelonging:
    def __init__(
        self,
        segments_layer,
        compositions_layer,
        seg_id_column_name,
        segments_column_name,
        compo_id_column_name,
    ):
        self.segments_layer = segments_layer
        self.compositions_layer = compositions_layer
        self.seg_id_column_name = seg_id_column_name
        self.segments_column_name = segments_column_name
        self.compo_id_column_name = compo_id_column_name

        self.belonging_column = "compositions"

        self.segments_manager = LayersAssociationManager(
            compositions_layer=self.compositions_layer,
            segments_layer=self.segments_layer,
            segments_column_name=self.segments_column_name,
            seg_id_column_name=self.seg_id_column_name,
            compo_id_column_name=self.compo_id_column_name,
        )

    def create_belonging_column(self):
        fields = self.segments_layer.fields()
        if self.belonging_column not in fields.names():
            # Création du champ s'il n'existe pas
            field = QgsField(self.belonging_column, QVariant.String)
            self.segments_layer.dataProvider().addAttributes([field])
            self.segments_layer.updateFields()
        else:
            return

    def update_belonging_column(self, composition_id=None):
        try:
            segments_belonging = (
                self.segments_manager.create_segments_belonging_dictionary()
            )
            features = None

            if composition_id:
                segments_to_update = set()

                segments_list = self.segments_manager.get_segments_list_for_composition(
                    composition_id
                )
                if segments_list:
                    for segment in segments_list:
                        segments_to_update.add(segment)

                    if segments_to_update:
                        expr = f'"{self.seg_id_column_name}" IN ({",".join(map(str, segments_to_update))})'
                        request = QgsFeatureRequest().setFilterExpression(expr)

                        features = self.segments_layer.getFeatures(request)

            if features is None:
                features = self.segments_layer.getFeatures()

            updates = {}
            attr_idx = self.segments_layer.fields().indexOf(self.belonging_column)

            for segment in features:
                appartenance_str = ",".join(
                    sorted(
                        segments_belonging.get(segment[self.seg_id_column_name], [])
                    )
                )
                if segment.id() >= 0:
                    updates[segment.id()] = {attr_idx: appartenance_str}
                else:
                    self.segments_layer.changeAttributeValue(
                        segment.id(), attr_idx, appartenance_str
                    )

            if updates:
                self.segments_layer.dataProvider().changeAttributeValues(updates)

            return True

        except Exception as e:
            self.segments_layer.rollBack()
            raise e
            return False
