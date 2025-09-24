from qgis.PyQt.QtCore import QSettings

from ..routes_composer import RoutesComposer


class ConnexionsHandler:
    routes_composer_connected = False

    def __init__(self):
        self.settings = QSettings()

    def connect_routes_composer(self):
        routes_composer = RoutesComposer.get_instance()
        if not routes_composer.routes_composer_connected:
            routes_composer.connect_routes_composer()

            ConnexionsHandler.routes_composer_connected = True

    def disconnect_routes_composer(self):
        routes_composer = RoutesComposer.get_instance()
        if routes_composer.routes_composer_connected:
            routes_composer.disconnect_routes_composer()

            ConnexionsHandler.routes_composer_connected = False

    def reconnect_routes_composer(self):
        routes_composer = RoutesComposer.get_instance()
        routes_composer.__init__()
        routes_composer.connect_routes_composer()

        ConnexionsHandler.routes_composer_connected = True

    def delete_routes_composer(self):
        routes_composer = RoutesComposer.get_instance()
        if routes_composer.routes_composer_connected:
            routes_composer.disconnect_routes_composer()
            del routes_composer

            ConnexionsHandler.routes_composer_connected = False
