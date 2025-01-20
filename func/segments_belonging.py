from PyQt5.QtCore import QVariant
from qgis.core import QgsField

from .utils import log, timer_decorator


class SegmentsBelonging:
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

        self.belonging_column = "compositions"

        self.segment_appartenances = {}

    def create_belonging_column(self):
        fields = self.segments_layer.fields()
        if self.belonging_column not in fields.names():
            # Création du champ s'il n'existe pas
            field = QgsField(self.belonging_column, QVariant.String)
            self.segments_layer.dataProvider().addAttributes([field])
            self.segments_layer.updateFields()
        else:
            return

    def dictionary_creation(self):
        self.compositions_layer.startEditing()
        for composition in self.compositions_layer.getFeatures():
            # TO DO: Je choisis arbitrairement la colonne 'id'. Il faudra peut-être laisser le choix.
            comp_id = str(int(composition["id"]))
            segments_str = composition[self.segments_column_name]

            if segments_str:
                segments_list = [
                    int(id_str)
                    for id_str in segments_str.split(",")
                    if id_str.strip().isdigit()
                ]
                for seg_id in segments_list:
                    if seg_id not in self.segment_appartenances:
                        self.segment_appartenances[seg_id] = []

                    self.segment_appartenances[seg_id].append(str(comp_id))

    @timer_decorator
    def create_or_update_belonging_column(self):
        try:
            self.create_belonging_column()
            self.dictionary_creation()

            updates = {}
            attr_idx = self.segments_layer.fields().indexOf(self.belonging_column)
            self.segments_layer.startEditing()

            for segment in self.segments_layer.getFeatures():
                seg_id = segment[self.id_column_name]
                appartenance_str = ",".join(
                    self.segment_appartenances.get(seg_id, ["0"])
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
