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
        print(f"{func.__name__} a pris {(end - start)*1000:.2f} ms")
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

    # Par défaut, retourne une liste
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


def log(message:str, level:str="INFO"):
    """Fonction pour gérer l'affichage des logs"""
    if config.logging_enabled is True:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
            :-3
        ]

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
