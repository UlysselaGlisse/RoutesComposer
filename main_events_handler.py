from qgis.PyQt.QtCore import QSettings

from .func.routes_composer import RoutesComposer


class MainEventsHandlers:
    routes_composer_connected = False
    geom_on_fly_connected = False
    belonging_connected = False

    def __init__(self):
        self.settings = QSettings()
        self.active_linkages = []

    def connect_routes_composer(self):
        routes_composer = RoutesComposer.get_instance()
        if not routes_composer.routes_composer_connected:
            routes_composer.connect_routes_composer()

            MainEventsHandlers.routes_composer_connected = True

    def disconnect_routes_composer(self):
        routes_composer = RoutesComposer.get_instance()
        if routes_composer.routes_composer_connected:
            routes_composer.disconnect_routes_composer()

            MainEventsHandlers.routes_composer_connected = False

    def connect_geom_on_fly(self):
        routes_composer = RoutesComposer.get_instance()
        routes_composer.connect_geom()

        MainEventsHandlers.geom_on_fly_connected = True

    def disconnect_geom_on_fly(self):
        routes_composer = RoutesComposer.get_instance()
        routes_composer.disconnect_geom()

        MainEventsHandlers.geom_on_fly_connected = False

    def connect_belonging(self):
        routes_composer = RoutesComposer.get_instance()
        routes_composer.connect_belonging()

        MainEventsHandlers.belonging_connected = True

    def disconnect_belonging(self):
        routes_composer = RoutesComposer.get_instance()
        routes_composer.disconnect_belonging()

        MainEventsHandlers.belonging_connected = False

    def connect_attribute_linker(self, compositions_attr, segments_attr, priority_mode):
        linkage = {
            'compositions_attr': compositions_attr,
            'segments_attr': segments_attr,
            'priority_mode': priority_mode
        }

        if linkage not in self.active_linkages:
            self.active_linkages.append(linkage)
            routes_composer = RoutesComposer.get_instance()
            routes_composer.connect_attribute_linker(compositions_attr, segments_attr, priority_mode)

    def disconnect_attribute_linker(self, compositions_attr, segments_attr, priority_mode):
        linkage = {
            'compositions_attr': compositions_attr,
            'segments_attr': segments_attr,
            'priority_mode': priority_mode
        }

        if linkage in self.active_linkages:
            self.active_linkages.remove(linkage)
            routes_composer = RoutesComposer.get_instance()
            routes_composer.disconnect_attribute_linker(compositions_attr, segments_attr, priority_mode)
