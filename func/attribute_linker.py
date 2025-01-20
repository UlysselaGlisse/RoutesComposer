"""Functions for linking attributes."""

from .utils import log, timer_decorator


class AttributeLinker:
    def __init__(
        self,
        segments_layer,
        compositions_layer,
        segments_attr,
        compositions_attr,
        id_column_name,
        segments_column_name,
        priority_mode,
    ):
        self.segments_layer = segments_layer
        self.compositions_layer = compositions_layer
        self.segments_attr = segments_attr
        self.compositions_attr = compositions_attr
        self.id_column_name = id_column_name
        self.segments_column_name = segments_column_name
        self.priority_mode = priority_mode

        self.segment_appartenances = {}

    @timer_decorator
    def update_segments_attr_values(self):
        log("r")
        try:
            valid_segment_ids = {
                feature[self.id_column_name]
                for feature in self.segments_layer.getFeatures()
            }
            attr_idx = self.segments_layer.fields().indexOf(self.segments_attr)
            segments_to_update = {}

            for composition in self.compositions_layer.getFeatures():
                value = composition[self.compositions_attr]
                if value == "NULL":
                    continue

                segments_list = composition[self.segments_column_name]
                if not segments_list:
                    continue

                segment_ids = [
                    int(id_str) for id_str in segments_list.split(",") if id_str.strip()
                ]

                for segment_id in segment_ids:
                    if segment_id not in valid_segment_ids:
                        log(
                            f"ID de segment invalide ignoré : {segment_id}",
                            level="WARNING",
                        )
                        continue

                    if self.priority_mode == "none":
                        segments_to_update[segment_id] = value
                    elif segment_id not in segments_to_update:
                        segments_to_update[segment_id] = value
                    else:
                        current_value = segments_to_update[segment_id]
                        # Conversion explicite en nombres pour la comparaison,
                        # car sinon 0 n'est pas pris en compte.'
                        value_num = float(value) if value else 0
                        current_value_num = float(current_value) if current_value else 0

                        if self.priority_mode == "min_value":
                            segments_to_update[segment_id] = (
                                value
                                if value_num < current_value_num
                                else current_value
                            )
                        elif self.priority_mode == "max_value":
                            segments_to_update[segment_id] = (
                                value
                                if value_num > current_value_num
                                else current_value
                            )

            self.segments_layer.startEditing()
            updates = {}

            for segment in self.segments_layer.getFeatures():
                seg_id = segment[self.id_column_name]
                value = segments_to_update.get(seg_id)

                if segment.id() >= 0:
                    updates[segment.id()] = {attr_idx: value}
                else:
                    self.segments_layer.changeAttributeValue(
                        segment.id(), attr_idx, value
                    )
            if updates:
                self.segments_layer.dataProvider().changeAttributeValues(updates)
            return True

        except Exception as e:
            log(f"Erreur lors de la mise à jour : {str(e)}", level="ERROR")
            self.segments_layer.rollBack()
            return False
