from PyQt5.QtCore import QVariant
from qgis.core import QgsField

from . import utils


class SegmentsBelonging:
    def __init__(
        self,
        segments_layer,
        compositions_layer,
        id_column_name,
        segments_column_name,
        compo_id_column_name,
    ):
        self.segments_layer = segments_layer
        self.compositions_layer = compositions_layer
        self.id_column_name = id_column_name
        self.segments_column_name = segments_column_name
        self.compo_id_column_name = compo_id_column_name

        self.belonging_column = "compositions"

        self.segment_manager = utils.SegmentManager(
            compositions_layer=self.compositions_layer,
            segments_layer=self.segments_layer,
            segments_column_name=self.segments_column_name,
            seg_id_column_name=self.id_column_name,
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

    @utils.timer_decorator
    def update_belonging_column(self):
        try:
            self.segment_manager.create_segments_of_compositions_dictionary()
            segments_appartenance = (
                self.segment_manager.create_segments_belonging_dictionary()
            )

            updates = {}
            attr_idx = self.segments_layer.fields().indexOf(self.belonging_column)

            self.segments_layer.startEditing()
            for segment in self.segments_layer.getFeatures():
                seg_id = segment[self.id_column_name]
                appartenance_str = ",".join(
                    sorted(map(str, segments_appartenance.get(seg_id, ["0"])), key=int)
                )

                # On ne peut mettre à jour via le data provider des entités non enregistrées.
                if segment.id() >= 0:
                    updates[segment.id()] = {attr_idx: appartenance_str}
                else:
                    self.segments_layer.changeAttributeValue(
                        segment.id(), attr_idx, appartenance_str
                    )

            if updates:
                self.segments_layer.dataProvider().changeAttributeValues(updates)

        except Exception as e:
            self.segments_layer.rollBack()
            raise e
