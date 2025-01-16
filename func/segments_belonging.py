from qgis.core import QgsField
from PyQt5.QtCore import QVariant


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

        self.segment_appartenances = {}
        self.belonging_column = "compositions"

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
            comp_id = str(int(composition["id"]))
            segments_str = composition[self.segments_column_name]

            # Conversion de la chaîne de segments en liste
            if segments_str:
                segments_list = [
                    int(id_str)
                    for id_str in segments_str.split(",")
                    if id_str.strip().isdigit()
                ]
                # Mise à jour du dictionnaire des appartenances
                for seg_id in segments_list:
                    if seg_id not in self.segment_appartenances:
                        self.segment_appartenances[seg_id] = []

                    self.segment_appartenances[seg_id].append(str(comp_id))

    def create_or_update_belonging_column(self):
        try:
            self.create_belonging_column()
            self.dictionary_creation()

            attr_idx = self.segments_layer.fields().indexOf(self.belonging_column)
            updates = {}

            for segment in self.segments_layer.getFeatures():
                seg_id = segment["id"]
                appartenance_str = ",".join(
                    self.segment_appartenances.get(seg_id, ["0"])
                )
                updates[segment.id()] = {attr_idx: appartenance_str}

            self.segments_layer.dataProvider().changeAttributeValues(updates)

        except Exception as e:
            self.segments_layer.rollBack()
            raise e
