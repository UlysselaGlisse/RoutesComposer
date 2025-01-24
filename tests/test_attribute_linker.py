import time
from functools import wraps

from qgis.core import QgsFeatureRequest, QgsProject

# exécuter le fichier dans la console python.
# dans la console, par exemple:  manager.update_segments_attr_values()


def timer_decorator(func):
    """Indique le temps que prend une fonction à s'exécuter."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} a pris {(end - start) * 1000:.2f} ms")
        return result

    return wrapper


class AttributeLinker:
    def __init__(self):
        segments_layer = QgsProject.instance().mapLayersByName("segments")[0]
        compositions_layer = QgsProject.instance().mapLayersByName("compositions")[0]
        segments_column_name = "segments"
        id_column_name = "id"

        self.segments_layer = segments_layer
        self.compositions_layer = compositions_layer
        self.id_column_name = id_column_name
        self.segments_column_name = segments_column_name
        self.linkages = [
            {
                "segments_attr": "importance",
                "compositions_attr": "importance",
                "priority_mode": "min_value",
            },
            {
                "segments_attr": "massif",
                "compositions_attr": "massif",
                "priority_mode": "none",
            },
            {
                "segments_attr": "mdiff",
                "compositions_attr": "mdiff",
                "priority_mode": "min_value",
            },
        ]

        self.segments_manager = SegmentManager(
            compositions_layer=self.compositions_layer,
            segments_layer=self.segments_layer,
            segments_column_name=self.segments_column_name,
            seg_id_column_name=self.id_column_name,
        )

        self.segment_appartenances = {}

    @timer_decorator
    def update_segments_attr_values(self, composition_id=None):
        try:
            segments_to_update = set()
            compositions_attrs = [
                linkage["compositions_attr"] for linkage in self.linkages
            ]

            segments_list = (
                self.segments_manager.create_segments_of_compositions_dictionary(
                    compositions_attrs
                )
            )

            segments_with_new_values = {
                linkage["segments_attr"]: {} for linkage in self.linkages
            }

            attr_indices = {
                linkage["segments_attr"]: self.segments_layer.fields().indexOf(
                    linkage["segments_attr"]
                )
                for linkage in self.linkages
            }

            if composition_id:
                compositions_to_process = set()
                segments = segments_list.get(composition_id, {}).get("segments", "")
                if segments:
                    for segment in segments:
                        segment = int(segment)
                        compos = self.segments_manager.get_compositions_for_segment(
                            segment
                        )
                        compositions_to_process.update(compos)
            else:
                compositions_to_process = segments_list.keys()

            for linkage in self.linkages:
                segments_attr = linkage["segments_attr"]
                compositions_attr = linkage["compositions_attr"]
                priority_mode = linkage["priority_mode"]

                for comp_id in compositions_to_process:
                    value = segments_list.get(comp_id, []).get(
                        compositions_attr, "NULL"
                    )
                    segments = segments_list.get(comp_id, []).get("segments", "")

                    for segment_id in segments:
                        segments_to_update.add(segment_id)
                        self._update_segment_value(
                            segments_with_new_values[segments_attr],
                            segment_id,
                            value,
                            priority_mode,
                        )

            updates = {}
            if segments_to_update:
                expr = f'"{self.id_column_name}" IN ({",".join(map(str, segments_to_update))})'
                request = QgsFeatureRequest().setFilterExpression(expr)

                for segment in self.segments_layer.getFeatures(request):
                    seg_id = segment[self.id_column_name]
                    feature_updates = {}
                    for segments_attr, values in segments_with_new_values.items():
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
        """Helper method to update segment values based on priority mode"""
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


class SegmentManager:
    def __init__(
        self,
        compositions_layer,
        segments_layer,
        segments_column_name="segments",
        seg_id_column_name="id",
        compo_id_column_name="id",
    ):
        self.compositions_layer = compositions_layer
        self.segments_layer = segments_layer
        self.segments_column_name = segments_column_name
        self.seg_id_column_name = seg_id_column_name
        self.compo_id_column_name = compo_id_column_name

        self.segment_appartenances = {}
        self.segments_list = {}

    def create_segments_of_compositions_dictionary(self, fields=None):
        """Crée un dictionnaire des segments appartenant à chaque composition."""
        for composition in self.compositions_layer.getFeatures():
            segments_str = composition[self.segments_column_name]
            compo_id = composition[self.compo_id_column_name]

            if segments_str:
                segments_list = [
                    int(id_str)
                    for id_str in segments_str.split(",")
                    if id_str.strip().isdigit()
                ]
                if fields:
                    composition_data = {"segments": segments_list}
                    for field in fields:
                        composition_data[field] = composition[field]

                    self.segments_list[compo_id] = composition_data
                else:
                    self.segments_list[compo_id] = segments_list

        return self.segments_list

    def create_segments_belonging_dictionary(self):
        """Crée un dictionnaire des compositions auxquelles appartient chaque segment."""
        for composition in self.compositions_layer.getFeatures():
            comp_id = str(int(composition[self.compo_id_column_name]))
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

        return self.segment_appartenances

    def get_attributes_from_compositions(self, composition_id, attribute_name=None):
        """
        Retourne les attributs d'une composition.
        """
        feature = self.compositions_layer.getFeature(composition_id)
        if attribute_name is not None:
            return feature[attribute_name]
        return feature.attributes()

    def get_segments_for_composition(self, composition_id):
        """Retourne la liste des segments appartenant à une composition."""
        return self.segment_appartenances.get(composition_id, [])

    def get_compositions_for_segment(self, segment_id: int) -> list:
        compositions_list = []

        request = (
            f"{self.segments_column_name} LIKE '%,{segment_id},%' OR "
            f"{self.segments_column_name} LIKE '{segment_id},%' OR "
            f"{self.segments_column_name} LIKE '%,{segment_id}' OR "
            f"{self.segments_column_name} = '{segment_id}'"
        )
        for composition in self.compositions_layer.getFeatures(request):
            comp_id = int(composition[self.compo_id_column_name])
            compositions_list.append(comp_id)

        return compositions_list


manager = AttributeLinker()
