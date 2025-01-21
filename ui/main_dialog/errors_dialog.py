import re

from PyQt5 import QtWidgets
from qgis.core import (
    QgsCoordinateTransform,
    QgsFeatureRequest,
    QgsGeometry,
    QgsProject,
)
from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)
from qgis.utils import iface

from ...func import warning


class ErrorDialog(QDialog):
    def __init__(self, dialog, errors, parent=None):
        super().__init__(parent)

        self.dialog = dialog
        self.segments_layer = self.dialog.layer_manager.segments_layer
        self.compositions_layer = self.dialog.layer_manager.compositions_layer
        self.segments_column_name = self.dialog.ui.segments_column_combo.currentText()
        self.id_column_name = self.dialog.ui.seg_id_column_combo.currentText()

        self.setWindowTitle(self.tr("Erreurs détectées"))
        self.setMinimumWidth(600)
        self.resize(600, 300)

        self.setModal(False)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()

        label = QLabel(self.tr("Détails des erreurs détectées :"))
        header_layout.addWidget(label)

        refresh_button = QPushButton()
        refresh_button.setIcon(
            QtWidgets.QApplication.style().standardIcon(  # type: ignore
                QtWidgets.QStyle.SP_BrowserReload  # type: ignore
            )
        )
        refresh_button.setToolTip(self.tr("Rafraîchir les erreurs"))
        refresh_button.clicked.connect(self.refresh_errors)
        refresh_button.setFixedSize(30, 30)
        header_layout.addWidget(refresh_button)

        layout.addLayout(header_layout)

        info_label = QLabel(
            self.tr("L'id des compositions est celui du fournisseur de données.")
        )
        info_label.setStyleSheet("font-style: italic; font-weight: normal;")
        info_label.setContentsMargins(0, 0, 0, 10)
        layout.addWidget(info_label)

        self.error_tree_widget = QTreeWidget()
        self.error_tree_widget.setHeaderLabels(
            [self.tr("Type d'erreur"), self.tr("Détails")]
        )

        layout.addWidget(self.error_tree_widget)

        self.error_tree_widget.itemClicked.connect(self.on_item_clicked)

        self.setLayout(layout)

        self.setStyleSheet(self.get_stylesheet())

    def refresh_errors(self):
        errors = warning.verify_compositions(
            self.segments_layer,
            self.compositions_layer,
            self.segments_column_name,
            self.id_column_name,
        )
        self.display_errors(errors)

    def get_stylesheet(self):
        return """
            QDialog {
                background-color: #f9f9f9;
            }
            QLabel {
                font-weight: bold;
                margin-bottom: 10px;
            }
            QTreeWidget {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px;
                background-color: #ffffff;
            }
            QPushButton {
                background-color: white; /* Changer le fond du bouton en blanc */
                color: black; /* Vous pouvez changer la couleur du texte si nécessaire */
                padding: 5px 10px;
                border: 1px solid #cccccc; /* Ajouter un bord pour le style */
                border-radius: 5px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #e2e2e2; /* Changez de couleur au survol pour réagir */
            }
            QPushButton:pressed { /* État lorsqu'il est enfoncé */
                background-color: #d9d9d9; /* Une autre couleur de fond lorsqu'il est enfoncé */
                border: 1px solid #999999;
            }
            QPushButton[icon] {
                background-color: transparent;
                border: 1px solid #cccccc;
                min-width: 30px;
                min-height: 30px;
                margin-left: 10px;
            }
        """

    def display_errors(self, errors):
        self.error_tree_widget.clear()
        error_types = {}

        for error in errors:
            error_type = error.get("error_type")
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)

        for error_type, error_list in error_types.items():
            type_item = QTreeWidgetItem(self.error_tree_widget, [self.tr(error_type)])
            type_item.setExpanded(True)
            for error in error_list:
                detail = self.format_error_detail(error)
                QTreeWidgetItem(type_item, [self.tr(""), detail])

        self.error_tree_widget.resizeColumnToContents(0)

    def format_error_detail(self, error):
        error_type = error.get("error_type")
        composition_id = error.get("composition_id", "N/A")

        if error_type == "failed_compositions":
            return self.tr(
                "Les géométries pour les compositions suivantes n'ont pas pu être créées : {composition_id}."
            ).format(composition_id=composition_id)

        elif error_type == "discontinuity":
            segment_id1, segment_id2 = error.get("segment_ids", (None, None))
            return self.tr(
                "Compositions: {composition_ids}. Entre les segments: {segment_id1}, {segment_id2}."
            ).format(
                composition_ids=composition_id,
                segment_id1=segment_id1,
                segment_id2=segment_id2,
            )

        elif error_type == "missing_segment":
            missing_segment_id = error.get("missing_segment_id", "N/A")
            return self.tr(
                "Composition : {composition_id}. Segment: {missing_segment_id}."
            ).format(
                composition_id=composition_id,
                missing_segment_id=missing_segment_id,
            )

        elif error_type == "unused_segment":
            unused_segment_id = error.get("unused_segment_id", "N/A")
            return self.tr(
                "Segment {unused_segment_id} n'est utilisé dans aucune composition."
            ).format(unused_segment_id=unused_segment_id)

        elif error_type == "empty_segments_list":
            return self.tr(
                "Composition : {composition_id}. Liste de segments vide.."
            ).format(composition_id=composition_id)
        elif error_type == "invalid_segment_id":
            invalid_segment_id = error.get("invalid_segment_id")
            segment_list = error.get("segment_list")
            return self.tr(
                "Composition : {composition_id}. Dans la liste: {segment_list}, l'id: '{invalid_segment_id}' est invalide."
            ).format(
                composition_id=composition_id,
                segment_list=segment_list,
                invalid_segment_id=invalid_segment_id,
            )

        return self.tr("Erreur inconnue. Détails: {details}").format(details=str(error))

    def on_item_clicked(self, item):
        if not item.parent():
            return

        error_type = item.parent().text(0)
        detail_text = item.text(1)

        if error_type == self.tr("discontinuity"):
            match = re.search(r"segments: (\d+), (\d+)", detail_text)
            if match:
                first_segment_id = match.group(1)
                self.zoom_to_segment(first_segment_id)

        elif error_type == self.tr("missing_segment"):
            match = re.search(r"Segment: (\d+)", detail_text)
            if match:
                missing_segment_id = match.group(1)
                self.zoom_to_segment(missing_segment_id)

        elif error_type == self.tr("unused_segment"):
            match = re.search(r"Segment (\d+)", detail_text)
            if match:
                unused_segment_id = match.group(1)
                self.zoom_to_segment(unused_segment_id)

    def zoom_to_segment(self, segment_id):
        feature = next(
            self.segments_layer.getFeatures(
                QgsFeatureRequest().setFilterExpression(
                    f"\"{self.id_column_name}\" = '{segment_id}'"
                )
            ),
            None,
        )

        if feature:
            project = QgsProject.instance()
            if project:
                project_crs = project.crs()
                segment_crs = self.segments_layer.crs()

                if segment_crs != project_crs:
                    transform = QgsCoordinateTransform(
                        segment_crs, project_crs, QgsProject.instance()
                    )
                    transformed_geom = QgsGeometry(feature.geometry())
                    transformed_geom.transform(transform)
                    iface.mapCanvas().setExtent(transformed_geom.boundingBox())
                else:
                    iface.mapCanvas().setExtent(feature.geometry().boundingBox())

                iface.mapCanvas().refresh()
        else:
            QMessageBox.warning(
                self,
                self.tr("Erreur"),
                self.tr("Segment {segment_id} non trouvé.").format(
                    segment_id=segment_id
                ),
            )
