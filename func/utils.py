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

    def create_segments_of_compositions_dictionary(self):
        """Crée un dictionnaire des segments appartenant à chaque composition."""
        for composition in self.compositions_layer.getFeatures():
            segments_str = composition[self.segments_column_name]

            if segments_str:
                segments_list = [
                    int(id_str)
                    for id_str in segments_str.split(",")
                    if id_str.strip().isdigit()
                ]
                self.segments_list[composition[self.compo_id_column_name]] = (
                    segments_list
                )

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

    def get_segments_for_composition(self, composition_id):
        """Retourne la liste des segments appartenant à une composition."""
        return self.segment_appartenances.get(composition_id, [])

    def get_compositions_for_segment(self, segment_id):
        """Retourne la liste des compositions auxquelles appartient un segment."""
        compositions = []
        for composition_id, segments in self.segment_appartenances.items():
            if segment_id in segments:
                compositions.append(composition_id)
        return compositions
