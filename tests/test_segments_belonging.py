import time
from functools import wraps
from typing import cast

from PyQt5.QtCore import QVariant
from qgis.core import QgsFeatureRequest, QgsField, QgsProject, QgsVectorLayer

# exécuter le fichier dans la console python.
# dans la console, par exemple:  manager.update_belonging_column()


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


class SegmentsBelonging:
    def __init__(self):
        project = QgsProject.instance()
        if not project:
            return
        segments_layer = project.mapLayersByName("segments")[0]
        compositions_layer = project.mapLayersByName("compositions")[0]
        segments_column_name = "segments"
        seg_id_column_name = "id"
        compo_id_column_name = "id"
        belonging_column = "compositions"

        self.segments_layer = cast(QgsVectorLayer, segments_layer)
        self.compositions_layer = cast(QgsVectorLayer, compositions_layer)
        self.seg_id_column_name = seg_id_column_name
        self.segments_column_name = segments_column_name
        self.compo_id_column_name = compo_id_column_name
        self.belonging_column = belonging_column

        self.segments_manager = SegmentManager(
            compositions_layer=self.compositions_layer,
            segments_layer=self.segments_layer,
            segments_column_name=self.segments_column_name,
            seg_id_column_name=self.seg_id_column_name,
        )

        self.segment_appartenances = {}

    def create_belonging_column(self):
        fields = self.segments_layer.fields()
        if self.belonging_column not in fields.names():
            # Création du champ s'il n'existe pas
            field = QgsField(self.belonging_column, QVariant.String)
            self.segments_layer.dataProvider().addAttributes([field])
            self.segments_layer.updateFields()
            return True
        else:
            return False

    @timer_decorator
    def update_belonging_column(self, composition_id=None):
        try:
            segments_appartenance = (
                self.segments_manager.create_segments_belonging_dictionary()
            )

            segments_to_update = set()

            if composition_id:
                segments = self.segments_manager.get_segments_for_composition(
                    composition_id
                )
                for segment in segments:
                    segments_to_update.add(segment)
            elif self.create_belonging_column():
                print("champ crée")
                segments_to_update = list(segments_appartenance.keys())
            else:
                segments_to_update = list(segments_appartenance.keys())

            attr_idx = self.segments_layer.fields().indexOf(self.belonging_column)
            updates = {}

            if segments_to_update:
                expr = f'"{self.seg_id_column_name}" IN ({",".join(map(str, segments_to_update))})'
                request = QgsFeatureRequest().setFilterExpression(expr)

                for segment in self.segments_layer.getFeatures(request):
                    appartenance_str = ",".join(
                        sorted(
                            segments_appartenance.get(
                                segment[self.seg_id_column_name], []
                            )
                        )
                    )
                    updates[segment.id()] = {attr_idx: appartenance_str}

            if updates:
                self.segments_layer.dataProvider().changeAttributeValues(updates)

            return True

        except Exception as e:
            self.segments_layer.rollBack()
            raise e
            return False


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

        self.segments_list = {}

    def create_segments_of_compositions_dictionary(self, fields=None):
        """Crée un dictionnaire des segments appartenant à chaque composition."""
        self.segment_list = {}

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
        self.segment_appartenances = {}

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

    def get_segments_for_composition(self, composition_id: int) -> list:
        segments_list = []

        request = f"{self.compo_id_column_name} = {composition_id}"
        for composition in self.compositions_layer.getFeatures(request):
            segments_str = composition[self.segments_column_name]
            if segments_str:
                segments_list = [
                    int(id_str)
                    for id_str in segments_str.split(",")
                    if id_str.strip().isdigit()
                ]

        return segments_list


manager = SegmentsBelonging()
