from qgis.PyQt.QtCore import QSettings
from .func.routes_composer import RoutesComposer

class MainEventsHandlers:
    routes_composer_connected = False
    geom_on_fly_connected = False

    def __init__(self):
        self.settings = QSettings()

    def get_routes_composer_instance(self):
        routes_composer = RoutesComposer.get_instance()
        if not routes_composer.is_connected:
            routes_composer.connect()

            MainEventsHandlers.routes_composer_connected = True

    def erase_routes_composer_instance(self):
        routes_composer = RoutesComposer.get_instance()
        if routes_composer.is_connected:
            routes_composer.disconnect_routes_composer()
            routes_composer.destroy_instance()

            MainEventsHandlers.routes_composer_connected = False

    def connect_geom_on_fly(self):
        routes_composer = RoutesComposer.get_instance()
        routes_composer.connect_geom()

        MainEventsHandlers.geom_on_fly_connected = True

    def disconnect_geom_on_fly(self):
        routes_composer = RoutesComposer.get_instance()
        routes_composer.disconnect_geom()

        MainEventsHandlers.geom_on_fly_connected = False
