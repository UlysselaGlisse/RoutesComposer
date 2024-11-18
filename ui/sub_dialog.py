from math import log
import re
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsCoordinateTransform,
    QgsGeometry
)
from qgis.utils import iface
from qgis.PyQt.QtWidgets import(
    QDialog,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QListWidget,
    QMessageBox,
    QPushButton,
    QWidget,
    QDockWidget,
)
from PyQt5 import QtWidgets
from .. import config
from ..func.utils import log


class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Informations sur le Gestionnaire de réseaux"))

        info_text = self.tr("""
        <b>Gestionnaire de réseaux</b><br><br>
        Ce plugin apporte une assistance dans la réalisation de réseaux en mettant <br /> à jour
        les compositions de segments en fonction des modifications <br /> faites sur les segments.<br><br>
        <i>Instructions :</i><br>
        <ol>
            <li>Sélectionnez les couches à utiliser <br /> (La couche des compositions doit avoir
                un champ nommé "segments")</li>
            <li>Cliquez sur 'Démarrer' pour activer le suivi</li>
            <li>Effectuez vos modifications sur les segments</li>
            <li>Les compositions seront mises à jour automatiquement</li>
            <li>Cliquez sur 'Arrêter' pour désactiver le suivi</li>
        </ol>

        Vous pouvez voir en détail ce qu'il se passe en activant les logs <br />
        Ceux-ci apparaîtront dans la console python de Qgis.
        """)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(info_text))

        self.info_logging_button = QPushButton()
        self.update_logging_button_text()
        self.info_logging_button.clicked.connect(self.toggle_info_logging)
        layout.addWidget(self.info_logging_button)

        self.setLayout(layout)

class SingleSegmentDialog(QDialog):
    def __init__(self, parent=None, old_id=None, new_id=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Vérification nécessaire"))
        self.setMinimumWidth(400)
        self.current_segments = [old_id, new_id]
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        warning_label = QLabel(self.tr("Attention, composition d'un seul segment. "
                                "Veuillez vérifier que la nouvelle composition est bonne."))
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        self.proposal_label = QLabel()
        self.update_proposal_label()
        layout.addWidget(self.proposal_label)

        buttons_layout = QHBoxLayout()

        invert_button = QPushButton(self.tr("Inverser l'ordre"))
        invert_button.clicked.connect(self.invert_order)
        buttons_layout.addWidget(invert_button)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_button)

        cancel_button = QPushButton(self.tr("Annuler"))
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def update_proposal_label(self):
        self.proposal_label.setText(self.tr("Nouvelle composition proposée: {cs}").format(cs=self.current_segments))

    def invert_order(self):
        self.current_segments.reverse()
        self.update_proposal_label()


class ErrorDialog(QDialog):
    def __init__(self, errors, segments_layer, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Erreurs détectées"))
        self.setMinimumWidth(600)
        self.resize(600, 300)

        self.setModal(False)
        self.segments_layer = segments_layer

        layout = QVBoxLayout()

        layout.addWidget(QLabel(self.tr("Détails des erreurs détectées :")))

        self.error_list_widget = QListWidget()
        displayed_segments = set()
        discont_error_dict = {}

        for error in errors:
            self.handle_error(error)

        layout.addWidget(self.error_list_widget)

        self.error_list_widget.itemClicked.connect(self.on_item_clicked)

        close_button = QPushButton(self.tr("Fermer"))
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

        self.setStyleSheet(self.get_stylesheet())

    def get_stylesheet(self):
        return """
            QDialog {
                background-color: #f9f9f9;
            }
            QLabel {
                font-weight: bold;
                margin-bottom: 10px;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px;
                background-color: #ffffff;
                selection-background-color: #e2e2e2;
            }
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 5px 10px;
                border: none;
                border-radius: 5px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """

    def handle_error(self, error):
        """Gérer et formater les erreurs pour affichage."""
        error_type = error.get('error_type')

        if error_type == 'failed_compositions':
            composition_id = error.get('composition_id', 'N/A')
            self.error_list_widget.addItem(self.tr("Les géométries pour les compositions suivantes n'ont pas pu être créées : {composition_id}.").format(composition_id=composition_id))

        elif error_type == 'discontinuity':
            segment_id1, segment_id2 = error.get('segment_ids', (None, None))
            composition_ids = error.get('composition_id', 'N/A')
            self.error_list_widget.addItem(f"Discontinuity in compositions: {composition_ids}. Non connected segments: {segment_id1}.")

    def on_item_clicked(self, item):
        """Gérer le clic sur un élément de la liste d'erreurs."""
        text = item.text()

        if "Discontinuity" in text:
            match = re.search(r"Non connected segments: (\d+)", text)
            if match:
                segment_id = match.group(1)
                self.zoom_to_segment(segment_id)

    def zoom_to_segment(self, segment_id):
        """Zoomer sur le segment spécifié dans la carte QGIS."""
        feature = next(self.segments_layer.getFeatures(QgsFeatureRequest().setFilterExpression(f'"id" = \'{segment_id}\'')), None)

        if feature:
            project = QgsProject.instance()
            if project:
                project_crs = project.crs()
                segment_crs = self.segments_layer.crs()

                if segment_crs != project_crs:
                    transform = QgsCoordinateTransform(segment_crs, project_crs, QgsProject.instance())
                    transformed_geom = QgsGeometry(feature.geometry())
                    transformed_geom.transform(transform)
                    iface.mapCanvas().setExtent(transformed_geom.boundingBox())
                else:
                    iface.mapCanvas().setExtent(feature.geometry().boundingBox())

                iface.mapCanvas().refresh()
        else:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Segment {segment_id} non trouvé.").format(segment_id=segment_id))
