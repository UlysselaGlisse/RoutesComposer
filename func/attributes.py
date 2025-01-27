from collections import Counter

from qgis.core import QgsFeatureRequest

from .utils import SegmentManager


class AttributeLinker:
    def __init__(
        self,
        segments_layer,
        compositions_layer,
        seg_id_column_name,
        segments_column_name,
        linkages,
    ):
        self.segments_layer = segments_layer
        self.compositions_layer = compositions_layer
        self.seg_id_column_name = seg_id_column_name
        self.segments_column_name = segments_column_name
        self.linkages = linkages

        self.segments_manager = SegmentManager(
            compositions_layer=self.compositions_layer,
            segments_layer=self.segments_layer,
            segments_column_name=self.segments_column_name,
            seg_id_column_name=self.seg_id_column_name,
        )

    def update_segments_attr_values(self, composition_id=None):
        try:
            segments_to_update = set()

            compositions_attrs = [
                linkage["compositions_attr"] for linkage in self.linkages
            ]
            self.segments_with_new_values = {
                linkage["segments_attr"]: {} for linkage in self.linkages
            }
            attr_indices = {
                linkage["segments_attr"]: self.segments_layer.fields().indexOf(
                    linkage["segments_attr"]
                )
                for linkage in self.linkages
            }

            self.segments_list = (
                self.segments_manager.create_segments_of_compositions_dictionary(
                    compositions_attrs
                )
            )

            if composition_id:
                compositions_to_process = []
                segments = self.segments_list.get(composition_id, {}).get(
                    "segments", ""
                )
                if segments:
                    for segment in segments:
                        segment = int(segment)
                        compos = self.segments_manager.get_compositions_for_segment(
                            segment
                        )
                        compositions_to_process.extend(compos)

                compositions_to_process = list(compositions_to_process)
            else:
                compositions_to_process = self.segments_list.keys()

            for linkage in self.linkages:
                segments_attr = linkage["segments_attr"]
                compositions_attr = linkage["compositions_attr"]
                priority_mode = linkage["priority_mode"]

                if priority_mode == "most_frequent":
                    segments_list = (
                        self.segments_manager.create_compositions_by_segment_dictionary(
                            compositions_attrs
                        )
                    )
                    for segment_id, compositions in segments_list.items():
                        print(segment_id, compositions)
                        if composition_id:
                            compositions = [
                                comp
                                for comp in compositions
                                if comp["id"] in compositions_to_process
                            ]
                            if not compositions:
                                continue

                        segments_to_update.add(segment_id)
                        attribute_values = [
                            comp[compositions_attr] for comp in compositions
                        ]
                        counter = Counter(attribute_values)
                        most_common = counter.most_common(1)[0][0]
                        if most_common:
                            self.segments_with_new_values[segments_attr][segment_id] = (
                                most_common
                            )

                else:
                    for comp_id in compositions_to_process:
                        value = self.segments_list.get(comp_id, []).get(
                            compositions_attr, "NULL"
                        )
                        segments = self.segments_list.get(comp_id, []).get(
                            "segments", ""
                        )

                        for segment_id in segments:
                            segments_to_update.add(segment_id)
                            self._update_segment_value(
                                self.segments_with_new_values[segments_attr],
                                segment_id,
                                value,
                                priority_mode,
                            )
            updates = {}
            if segments_to_update:
                expr = f'"{self.seg_id_column_name}" IN ({",".join(map(str, segments_to_update))})'
                request = QgsFeatureRequest().setFilterExpression(expr)

                for segment in self.segments_layer.getFeatures(request):
                    seg_id = segment[self.seg_id_column_name]

                    feature_updates = {}
                    for segments_attr, values in self.segments_with_new_values.items():
                        if seg_id in values:
                            feature_updates[attr_indices[segments_attr]] = values[
                                seg_id
                            ]
                    if feature_updates:
                        updates[segment.id()] = feature_updates

            if updates:
                self.segments_layer.dataProvider().changeAttributeValues(updates)
            return True

        except Exception:
            self.segments_layer.rollBack()
            return False

    def _update_segment_value(self, values_dict, segment_id, new_value, priority_mode):
        if priority_mode == "none":
            values_dict[segment_id] = new_value

        elif segment_id not in values_dict:
            values_dict[segment_id] = new_value
        else:
            current_value = values_dict[segment_id]
            value_num = float(new_value) if new_value else 0
            current_value_num = float(current_value) if current_value else 0

            if priority_mode == "min_value":
                values_dict[segment_id] = (
                    new_value if value_num < current_value_num else current_value
                )
            elif priority_mode == "max_value":
                values_dict[segment_id] = (
                    new_value if value_num > current_value_num else current_value
                )
