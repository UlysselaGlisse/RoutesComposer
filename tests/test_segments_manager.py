import time
from functools import wraps

from qgis.core import QgsProject

# exécuter le fichier dans la console python.
# dans la console, par exemple:  manager.get_seg_for_comp(1)


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


class CompSeg:
    def __init__(self):
        self.segments_layer = QgsProject.instance().mapLayersByName("segments")[0]
        self.compositions_layer = QgsProject.instance().mapLayersByName("compositions")[
            0
        ]
        self.segments_column_name = "segments"
        self.id_column_name = "id"
        self.compo_id_column_name = "id"
        self.segments_list = {}

    @timer_decorator
    def dictionary_creation(self, fields=None):
        """Crée un dictionnaire des segments appartenant à chaque composition."""
        for composition in self.compositions_layer.getFeatures():
            compo_id = composition[self.compo_id_column_name]
            segments_str = composition[self.segments_column_name]

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

    @timer_decorator
    def create_segments_belonging_dictionary(self, fields=None):
        """Crée un dictionnaire des compositions auxquelles appartient chaque segment.

        Args:
            fields (list, optional): Liste des champs additionnels à inclure pour chaque composition.

        Returns:
            dict: Dictionnaire avec les segments comme clés et leurs appartenances comme valeurs
        """
        self.segment_appartenances = {}

        for composition in self.compositions_layer.getFeatures():
            comp_id = int(composition[self.compo_id_column_name])
            segments_str = composition[self.segments_column_name]

            composition_data = {"comp_id": comp_id}
            if fields:
                for field in fields:
                    composition_data[field] = composition[field]

            if segments_str:
                segments_list = [
                    int(id_str)
                    for id_str in segments_str.split(",")
                    if id_str.strip().isdigit()
                ]
                for seg_id in segments_list:
                    if seg_id not in self.segment_appartenances:
                        self.segment_appartenances[seg_id] = []

                    if fields:
                        self.segment_appartenances[seg_id].append(composition_data)
                    else:
                        self.segment_appartenances[seg_id].append(comp_id)

        return self.segment_appartenances

    @timer_decorator
    def create_compositions_by_segment_dictionary(self, fields=None):
        """Crée un dictionnaire listant les compositions contenant chaque segment."""
        compositions_by_segment = {}
        # {seg_id: [{'champ': valeur, 'champ': valeur}], seg_id: [{'champ': valeur, 'champ': valeur}]}

        for (
            composition_id,
            composition_data,
        ) in self.segments_list.items():  # seg_id {'champ': valeur, 'champ' : valeur}
            segments = (
                composition_data["segments"] if fields else composition_data
            )  # liste de segments
            for segment_id in segments:
                if segment_id not in compositions_by_segment:
                    compositions_by_segment[segment_id] = []

                if fields:
                    composition_info = {
                        field: composition_data[field] for field in fields
                    }
                    # {'champ': valeur, 'champ': valeur}
                    compositions_by_segment[segment_id].append(composition_info)
                else:
                    compositions_by_segment[segment_id].append(composition_id)

        return compositions_by_segment

    @timer_decorator
    def get_compositions_for_segment(self, segment_id: int) -> list:
        compositions_list = []

        request = (
            f"{self.segments_column_name} LIKE '%,{segment_id},%' OR "
            f"{self.segments_column_name} LIKE '{segment_id},%' OR "
            f"{self.segments_column_name} LIKE '%,{segment_id}' OR "
            f"{self.segments_column_name} = '{segment_id}'"
        )
        # Récupération des compositions filtrées
        for composition in self.compositions_layer.getFeatures(request):
            comp_id = int(composition[self.compo_id_column_name])
            compositions_list.append(comp_id)

        return compositions_list

    @timer_decorator
    def get_segments_for_compositions(self, composition_id: int) -> list:
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

    @timer_decorator
    def get_seg_for_comp(self, composition_id):
        """Retourne la liste des segments appartenant à une composition."""
        return self.segments_list.get(composition_id, [])

    @timer_decorator
    def get_comp_for_seg(self, segment_id):
        """Retourne la liste des compositions auxquelles appartient un segment."""
        compositions = []
        for composition_id, segments in self.segments_list.items():
            if segment_id in segments:
                compositions.append(composition_id)
        return compositions


manager = CompSeg()
