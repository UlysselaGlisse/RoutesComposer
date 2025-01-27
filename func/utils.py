"""Basic functions for the project."""

import datetime
import inspect
import logging
import time
from functools import wraps

from .. import config


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


def print_geometry_info(geometry, label):
    """Affiche les informations détaillées sur une géométrie."""
    if geometry.isNull():
        return

    points = geometry.asPolyline()
    print(
        f"""
    {label}:
    - Type: {geometry.wkbType()}
    - Longueur: {geometry.length():.2f}
    - Nombre de points: {len(points)}
    - Premier point: {points[0]}
    - Dernier point: {points[-1]}
    """
    )


def log(message: str, level: str = "INFO"):
    """Fonction pour gérer l'affichage des logs"""
    if config.logging_enabled is True:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        current_frame = inspect.currentframe()

        if current_frame and current_frame.f_back:
            calling_function = current_frame.f_back.f_code.co_name
        else:
            calling_function = "NA"

        log_message = f"[{level}][{timestamp}][{calling_function}] {message}"
        print(log_message)

        if level == "DEBUG":
            logging.debug(log_message)
        elif level == "INFO":
            logging.info(log_message)
        elif level == "WARNING":
            logging.warning(log_message)
        elif level == "ERROR":
            logging.error(log_message)
        elif level == "CRITICAL":
            logging.critical(log_message)
        else:
            logging.info(log_message)


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
        """
        Crée un dictionnaire des segments appartenant à chaque composition.

        Return:
            {comp_id: {'champ': valeur, 'champ': valeur}, comp_id: {'champ': valeur, 'champ': valeur}}
        """
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

    def create_compositions_by_segment_dictionary(self, fields=None):
        """
        Crée un dictionnaire listant les compositions contenant chaque segment.
        Return:
            {seg_id: [{'champ': valeur, 'champ': valeur}, {'champ': valeur, 'champ': valeur}], seg_id: [{'champ': valeur, 'champ': valeur}]}
        """
        compositions_by_segment = {}

        for (
            composition_id,
            composition_data,
        ) in self.segments_list.items():
            segments = composition_data["segments"] if fields else composition_data
            for segment_id in segments:
                if segment_id not in compositions_by_segment:
                    compositions_by_segment[segment_id] = []

                if fields:
                    composition_info = {
                        field: composition_data[field] for field in fields
                    }
                    composition_info["id"] = composition_id
                    compositions_by_segment[segment_id].append(composition_info)
                else:
                    compositions_by_segment[segment_id].append(composition_id)

        return compositions_by_segment

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
