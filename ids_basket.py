from qgis.PyQt.QtWidgets import QLabel
from qgis.PyQt.QtCore import Qt, QPoint
from qgis.PyQt.QtGui import QClipboard, QCursor
from qgis.core import (QgsApplication, QgsPointXY, QgsRectangle, QgsFeatureRequest,
                      QgsProject, QgsCoordinateTransform, QgsCoordinateReferenceSystem,
                      QgsGeometry, QgsSpatialIndex)
from qgis.gui import QgsMapCanvas, QgsMapTool
from qgis.utils import iface

class IDsBasket(QgsMapTool):
    def __init__(self, canvas, layer, id_field='id'):

        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer
        self.id_field = id_field
        self.selected_ids = []
        self.removed_ids = []
        self.canvas = canvas

        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.label = QLabel(self.canvas)
        self.label.setText("")
        self.label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.9);
            padding: 5px;
            border-radius: 3px;
            color: black;
        """)
        self.label.hide()

        project = QgsProject.instance()
        if not project:
            return
        self.crs_project = project.crs()
        self.crs_layer = self.layer.crs()

        self.transform = QgsCoordinateTransform(
            self.crs_project,
            self.crs_layer,
            QgsProject.instance()
        )

        self.spatial_index = QgsSpatialIndex()
        for feature in self.layer.getFeatures():
            self.spatial_index.addFeature(feature)

        self.connectivity_cache = {}

    def canvasReleaseEvent(self, e):
        if not e:
            return
        if e.button() == Qt.RightButton:
            self.selected_ids.clear()
            self.layer.removeSelection()
            self.update_label()

            return

        if e.button() == Qt.LeftButton:
            click_point = self.toMapCoordinates(e.pos())
            transformed_point = self.transform.transform(click_point)

            search_radius = 80
            search_rectangle = QgsRectangle(
                transformed_point.x() - search_radius,
                transformed_point.y() - search_radius,
                transformed_point.x() + search_radius,
                transformed_point.y() + search_radius
            )

            request = QgsFeatureRequest()
            request.setFilterRect(search_rectangle)

            closest_feature = None
            min_distance = float('inf')

            for feature in self.layer.getFeatures(request):
                distance = feature.geometry().distance(
                    QgsGeometry.fromPointXY(QgsPointXY(transformed_point))
                )
                if distance <= search_radius and distance < min_distance:
                    min_distance = distance
                    closest_feature = feature

            if closest_feature:
                feature_id = closest_feature[self.id_field]

                if not self.selected_ids:
                    self.selected_ids.append(feature_id)
                else:
                    # Chercher le chemin entre le dernier point sélectionné et le nouveau
                    last_id = self.selected_ids[-1]
                    if last_id != feature_id:
                        path = self.find_connected_segments(last_id, feature_id)
                        for segment_id in path:
                            if segment_id not in self.selected_ids:
                                self.selected_ids.append(segment_id)
                        if feature_id not in self.selected_ids:
                            self.selected_ids.append(feature_id)

                self.copy_ids_to_clipboard()
                self.update_label()
                self.highlight_selected_segments()

    def highlight_selected_segments(self):
        """Met en surbrillance (sélection de qgis) les segments sélectionnés"""

        expr = f"\"{self.id_field}\" IN ({','.join(map(str, self.selected_ids))})"

        self.layer.selectByExpression(expr)

    def keyPressEvent(self, e):
        if not e:
            return
        if e.key() == Qt.Key_Z:
            self.remove_last_segment()
        elif e.key() == Qt.Key_E:
            self.restore_last_removed_segment()

    def remove_last_segment(self):
        """Supprime le dernier segment sélectionné."""
        if self.selected_ids:
            last_id = self.selected_ids.pop()
            self.removed_ids.append(last_id)
            self.layer.removeSelection()
            self.highlight_selected_segments()
            self.update_label()

    def restore_last_removed_segment(self):
        """Restaure le dernier segment supprimé."""
        if self.removed_ids:
            last_removed_id = self.removed_ids.pop()
            self.selected_ids.append(last_removed_id)
            self.highlight_selected_segments()
            self.update_label()

    def find_connected_segments(self, start_id, end_id):
        if start_id == end_id:
            return [start_id]

        visited = set()
        queue = [(start_id, [start_id])]

        while queue:
            current_id, path = queue.pop(0)

            if current_id == end_id:
                return path

            if current_id in visited:
                continue

            visited.add(current_id)

            for next_id in self.get_connected_segments(current_id):
                if next_id not in visited:
                    new_path = path + [next_id]
                    queue.append((next_id, new_path))

        return []

    def get_connected_segments(self, segment_id):
        if segment_id in self.connectivity_cache:
            return self.connectivity_cache[segment_id]

        connected = []

        request = QgsFeatureRequest().setFilterExpression(f"\"{self.id_field}\" = {segment_id}")
        current_feature = next(self.layer.getFeatures(request))
        current_geom = current_feature.geometry()

        bbox = current_geom.boundingBox()
        bbox.grow(0.0001)

        candidates = self.spatial_index.intersects(bbox)

        request = QgsFeatureRequest().setFilterFids(candidates)
        for feature in self.layer.getFeatures(request):
            if feature[self.id_field] == segment_id:
                continue

            other_geom = feature.geometry()

            # Je ne suis pas sûr que touches soit la meilleure solution.
            if current_geom.touches(other_geom):
                connected.append(feature[self.id_field])

        self.connectivity_cache[segment_id] = connected
        return connected

    def copy_ids_to_clipboard(self):
        """Copie la liste des IDs dans le presse-papiers"""
        if self.selected_ids:
            ids_text = ','.join(map(str, self.selected_ids))
            clipboard = QgsApplication.clipboard()
            clipboard.setText(ids_text)

    def update_label(self):
        if self.selected_ids:
            self.label.setText(', '.join(map(str, self.selected_ids)))
            self.label.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.9);
                padding: 5px;
                border-radius: 3px;
                color: black;
            """)
        else:
            self.label.setText("")
            self.label.setStyleSheet("""
                background-color: rgba(0, 0, 0, 0);
                padding: 0;
                border-radius: 0;
                color: white;
            """)

        self.label.adjustSize()

    def canvasMoveEvent(self, e):
        if not e:
            return
        mousePos = e.pos()

        # # TODO : ne marche pas: je pense que la classe ne sait pas où est la souris hors du canvas.
        # if not mousePos:
        #     self.label.hide()
        #     return

        labelPos = mousePos + QPoint(20, 0)

        if labelPos.x() + self.label.width() > self.canvas.width():
            labelPos.setX(mousePos.x() - self.label.width() - 5)

        self.label.move(labelPos)
        self.label.show()

    def deactivate(self):
        self.label.hide()
        self.selected_ids = []
        self.layer.removeSelection()
        super().deactivate()
