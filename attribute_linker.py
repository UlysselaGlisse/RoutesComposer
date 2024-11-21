"""Functions for linking attributes."""
from .func.utils import log


class AttributeLinker:
    def __init__(self, segments_layer, compositions_layer, segments_attr,
                 compositions_attr, id_column_name, segments_column_name, priority_mode):
        self.segments_layer = segments_layer
        self.compositions_layer = compositions_layer
        self.segments_attr = segments_attr
        self.compositions_attr = compositions_attr
        self.id_column_name = id_column_name
        self.segments_column_name = segments_column_name
        self.priority_mode = priority_mode

    def start(self):
        """UNUSE Démarre la liaison des attributs."""
        self.compositions_layer.attributeValueChanged.connect(self.on_composition_changed)

    def stop(self):
        """UNUSE Arrête la liaison des attributs."""
        try:
            self.compositions_layer.attributeValueChanged.disconnect(self.on_composition_changed)
        except:
            pass

    def on_composition_changed(self, fid, idx, value):
        """UNUSE Appelé quand un attribut d'une composition change."""
        # Vérifie si c'est bien le champ qu'on suit qui a changé
        if self.compositions_layer.fields()[idx].name() != self.compositions_attr:
            return

        self.update_segments_attr_values()

    def update_segments_attr_values(self):
        """Met à jour l'attribut de segments."""
        self.segments_layer.startEditing()

        try:
            segments_to_update = {}

            for composition in self.compositions_layer.getFeatures():
                value = composition[self.compositions_attr]
                if value == 'NULL':
                    continue

                segments_list = composition[self.segments_column_name]
                if not segments_list:
                    continue

                segment_ids = [int(id_str) for id_str in segments_list.split(',') if id_str.strip()]

                for segment_id in segment_ids:
                    if self.priority_mode == 'none':
                        segments_to_update[segment_id] = value
                    elif segment_id not in segments_to_update:
                        segments_to_update[segment_id] = value
                    else:
                        current_value = segments_to_update[segment_id]
                        # Conversion explicite en nombres pour la comparaison, car sinon 0 n'est pas pris en compte.'
                        value_num = float(value) if value else 0
                        current_value_num = float(current_value) if current_value else 0

                        if self.priority_mode == 'min_value':
                            segments_to_update[segment_id] = value if value_num < current_value_num else current_value
                        elif self.priority_mode == 'max_value':
                            segments_to_update[segment_id] = value if value_num > current_value_num else current_value

            for segment in self.segments_layer.getFeatures():
                segment_id = segment[self.id_column_name]
                if segment_id not in segments_to_update:
                    continue

                new_value = segments_to_update[segment_id]
                feature_id = segment.id()

                segment[self.segments_attr] = new_value
                self.segments_layer.updateFeature(segment)

            self.segments_layer.commitChanges()

        except Exception as e:
            log(f"Erreur lors de la mise à jour : {str(e)}", level='ERROR')
            self.segments_layer.rollBack()
            return False
