from PyQt5.QtWidgets import QDialog
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QVBoxLayout,
)

from ... import config


class PluginOptions(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)

        self.iface = iface
        self.setWindowTitle("Options du Plugin")
        self.setup_ui()
        self.load_options()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Panier à segments
        segment_basket_group = QGroupBox(self.tr("Panier à segments"))
        segment_basket_layout = QVBoxLayout()

        self.show_label_checkbox = QCheckBox(
            self.tr("Afficher le label près de la souris")
        )
        self.show_label_checkbox.setChecked(True)
        self.show_label_checkbox.stateChanged.connect(self.save_options)

        segment_basket_layout.addWidget(self.show_label_checkbox)

        # self.departure_name_checkbox = QCheckBox(
        #     self.tr("Ajouter le nom du départ lors de la sélection")
        # )
        # self.departure_name_checkbox.setChecked(False)
        # self.departure_name_checkbox.stateChanged.connect(self.save_options)

        # # Combo box pour le champ du nom de départ
        # self.departure_field_combo = QComboBox()
        # composition_layer = self.get_compositions_layer()

        # field_names = [field.name() for field in composition_layer.fields()]
        # self.departure_field_combo.addItems(field_names)
        # self.departure_field_combo.currentTextChanged.connect(self.save_options)

        # self.departure_field_combo.hide()
        # self.departure_name_checkbox.stateChanged.connect(
        #     self.toggle_field_combo
        # )

        # Ajouter les widgets au layout
        # segment_basket_layout.addWidget(self.departure_name_checkbox)
        # segment_basket_layout.addWidget(self.departure_field_combo)
        segment_basket_group.setLayout(segment_basket_layout)

        layout.addWidget(segment_basket_group)

        # Développement
        dev_group = QGroupBox(self.tr("Développement"))
        dev_layout = QVBoxLayout()

        self.log_checkbox = QCheckBox(
            self.tr("Activer les logs dans la console python")
        )
        self.log_checkbox.setChecked(False)
        self.log_checkbox.stateChanged.connect(self.save_options)

        dev_layout.addWidget(self.log_checkbox)
        dev_group.setLayout(dev_layout)

        layout.addWidget(dev_group)

        self.setLayout(layout)

    def save_options(self):
        settings = QSettings()

        show_label = self.show_label_checkbox.isChecked()
        settings.setValue("routes_composer/ids_basket_label_hide", show_label)

        log_checkbox = self.log_checkbox.isChecked()
        settings.setValue("routes_composer/log", log_checkbox)
        config.logging_enabled = log_checkbox

        # departure_checkbox = self.departure_name_checkbox.isChecked()
        # settings.setValue(
        #     "routes_composer/departure_checkbox", departure_checkbox
        # )

        # departure_field = self.departure_field_combo.currentText()
        # settings.setValue(
        #     "routes_composer/departure_field_name", departure_field
        # )

    def load_options(self):
        settings = QSettings()

        show_label = settings.value(
            "routes_composer/ids_basket_label_hide", False, type=bool
        )
        self.show_label_checkbox.setChecked(show_label)

        log_checkbox = settings.value("routes_composer/log", False, type=bool)
        self.log_checkbox.setChecked(log_checkbox)

        # departure_checkbox = settings.value(
        #     "routes_composer/departure_checkbox", False, type=bool
        # )
        # self.departure_name_checkbox.setChecked(departure_checkbox)

        # departure_field = settings.value(
        #     "routes_composer/departure_field_name", "", type=str
        # )
        # self.departure_field_combo.setCurrentText(departure_field)

    # def populate_field_combo(self, layer):
    #     self.departure_field_combo.clear()
    #     if layer:
    #         fields = layer.fields()
    #         field_names = [field.name() for field in fields]
    #         self.departure_field_combo.addItems(field_names)

    # def get_compositions_layer(self):
    #     project = QgsProject.instance()
    #     if not project:
    #         return
    #     settings = QSettings()
    #     self.compositions_layer_id = settings.value(
    #         "routes_composer/compositions_layer_id", ""
    #     )
    #     if not self.compositions_layer_id:
    #         return
    #     self.compositions_layer = project.mapLayer(self.compositions_layer_id)

    #     return self.compositions_layer

    # def toggle_field_combo(self, state):
    #     self.departure_field_combo.setVisible(state == Qt.Checked)
