import time
from functools import wraps

from qgis.core import QgsProject

"""
1. Ouvrir le fichier dans la console python.
2. Changer le nom des couches (segments, compositions) charger dans qgis ou changer les noms à l'initialisation de LayersAssociationManager
3. Exécuter le fichier.
4. Dans la console, taper a.une_des_fonctions_à_tester()
"""


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


def get_features_list(layer, request=None, return_as="list"):
    """Retourne une liste ou un set d'entités."""
    features = []
    if request:
        iterator = layer.getFeatures(request)
    else:
        iterator = layer.getFeatures()

    feature = next(iterator, None)
    while feature:
        features.append(feature)
        feature = next(iterator, None)

    if return_as == "set":
        return set(features)

    return features


class LayersAssociationManager:
    def __init__(self):
        self.segments_layer = QgsProject.instance().mapLayersByName("segments")[0]
        self.compositions_layer = QgsProject.instance().mapLayersByName("compositions")[0]

        self.segments_column_name = "segments"
        self.seg_id_column_name = "id"
        self.compo_id_column_name = "id"
        self.segments_list = {}

    @timer_decorator
    def get_features(self):
        valid_segments_ids = {
            int(f[self.seg_id_column_name])
            for f in self.segments_layer.getFeatures()
            if f.id() is not None
        }
        if not valid_segments_ids:
            # Tentative de récupération avec une approche alternative
            try:
                alternative_ids = {
                    int(f[self.seg_id_column_name])
                    for f in self.segments_layer.dataProvider().getFeatures()
                    if f.id() is not None and f[self.seg_id_column_name] is not None
                }
                if alternative_ids:
                    print(f"Alternative method found {len(alternative_ids)} segments")
                    valid_segments_ids = alternative_ids
                else:
                    print(
                        "Alternative method also failed - aborting to prevent data loss"
                    )
                    return
            except Exception as e:
                print(f"Alternative method failed: {e} - aborting")
                return
        print(len(valid_segments_ids))

    @timer_decorator
    def create_segments_list_and_values_dictionary(self, fields=None):
        """
        Crée un dictionnaire des compositions avec la liste des segments, et possiblement la valeur d'un ou plusieurs champs.

        Args:
            fields (list[str], optional): Liste des champs additionnels à inclure pour chaque composition.
                Si None, retourne uniquement la liste des segments.

        Returns:
            dict:
                - Si fields est None :
                    {comp_id (int): list[int]}  # Liste des ids des segments
                - Si fields est renseigné :
                    {
                        comp_id (int): {
                            'segments': list[int],  # Liste des ids des segments
                            'field1': value1,       # Valeurs des champs additionnels
                            'field2': value2,
                            ...
                        }
                    }
        """
        for composition in self.compositions_layer.getFeatures():
            compo_id = composition[self.compo_id_column_name]
            segments_list = self.convert_segments_list(
                composition[self.segments_column_name]
            )

            if fields:
                composition_data = {"segments": segments_list}
                for field in fields:
                    composition_data[field] = composition[field]

                self.segments_list[compo_id] = composition_data
            else:
                self.segments_list[compo_id] = segments_list

        return self.segments_list

    def create_segments_belonging_dictionary(self):
        """
        Crée un dictionnaire des segments avec la liste des compositions auxquelles ils appartiennent.

        Returns:
            dict: {seg_id (int): list[str]}  # Liste des ids de compositions.
        """
        self.segment_belonging = {}

        for composition in self.compositions_layer.getFeatures():
            comp_id = composition[self.compo_id_column_name]
            segments_list = self.convert_segments_list(
                composition[self.segments_column_name]
            )

            for seg_id in segments_list:
                if seg_id not in self.segment_belonging:
                    self.segment_belonging[seg_id] = []

                self.segment_belonging[seg_id].append(str(comp_id))

        return self.segment_belonging

    def create_values_of_compositions_for_each_segment_dictionary(self, fields):
        """
        Crée un dictionnaire des segments avec la valeur des champs de compositions auxquelles ils appartiennent.

        Args:
            fields(list[str]): Liste des champs passée à la fonction create_segments_list_and_values_dictionary

        Returns:
            dict:
                {
                    seg_id (int): [
                        {
                            field1: value1,
                            field2: value2,
                            ...,
                            'id': comp_id (int)
                        },
                        {...}, # Autres compositions contenant ce segment
                    ],
                    ... # Autres segments
                }
        Example:
            {
                12: [
                    {'importance': 2, 'id': 123},
                    {'importance': 0, 'id': 124},
                    ...
                ],
                13: [
                    {'importance': 0, 'id': 123},
                    ...
                ]
            }
        """
        if not self.segments_list:
            self.create_segments_list_and_values_dictionary(fields)

        compositions_by_segment = {}

        for (
            composition_id,
            composition_data,
        ) in self.segments_list.items():
            segments = composition_data["segments"]
            for segment_id in segments:
                if segment_id not in compositions_by_segment:
                    compositions_by_segment[segment_id] = []

                composition_info = {field: composition_data[field] for field in fields}
                composition_info["id"] = composition_id
                compositions_by_segment[segment_id].append(composition_info)

        return compositions_by_segment

    def get_compositions_for_segment(self, segment_id, get_feature="no"):
        """
        Retourne la liste des compositions auxquelles un segment appartient.

        Returns:
            list[int] # Liste des ids de compositions
        """
        if not segment_id:
            return []

        compositions_list = []

        request = (
            f"{self.segments_column_name} LIKE '%,{segment_id},%' OR "
            f"{self.segments_column_name} LIKE '{segment_id},%' OR "
            f"{self.segments_column_name} LIKE '%,{segment_id}' OR "
            f"{self.segments_column_name} = '{segment_id}'"
        )
        for composition in self.compositions_layer.getFeatures(request):
            if get_feature == "yes":
                compositions_list.append(composition)
            else:
                comp_id = int(composition[self.compo_id_column_name])
                compositions_list.append(comp_id)

        return compositions_list

    def get_segments_list_for_segment(self, segment_id):
        """
        Récupère les listes de segments contenant l'id du segment.

        Returns:
            list[tuple]: (comp_id (int), list[int]) # Liste des ids de segments
        """
        if not segment_id:
            return []

        segments_lists_ids = []

        request = (
            f"{self.segments_column_name} LIKE '%,{segment_id},%' OR "
            f"{self.segments_column_name} LIKE '{segment_id},%' OR "
            f"{self.segments_column_name} LIKE '%,{segment_id}' OR "
            f"{self.segments_column_name} = '{segment_id}'"
        )
        for composition in self.compositions_layer.getFeatures(request):
            segments_list = self.convert_segments_list(
                composition[self.segments_column_name]
            )
            if int(segment_id) in segments_list:
                segments_lists_ids.append((composition.id(), segments_list))

        return segments_lists_ids

    def get_segments_list_for_composition(self, composition_id):
        """
        Retourne la liste de segments d'une composition

        Returns:
            list[int] # Liste des ids de segments
        """
        if not composition_id:
            return []

        request = f"{self.compo_id_column_name} = {composition_id}"
        for composition in self.compositions_layer.getFeatures(request):
            segments_list_str = composition[self.segments_column_name]

            return self.convert_segments_list(segments_list_str)

    def convert_segments_list(self, segments_list_str):
        """
        Convertit une chaîne d'ids de segments en liste d'entiers.

        Args:
            segments_list_str: Chaîne contenant les ids de segments séparées par des virgules dans la couche compositions

        Returns:
            list[int]

        Example:
            "1,2,3" -> [1,2,3]
        """
        if not segments_list_str:
            return []

        return [
            int(id_str)
            for id_str in segments_list_str.split(",")
            if id_str.strip().isdigit()
        ]


a = LayersAssociationManager()
