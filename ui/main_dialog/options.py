from PyQt5.QtWidgets import QDialog
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QVBoxLayout,
)

from ... import config


class PluginOptionsWidget(QDialog):
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

        self.show_label_checkbox = QCheckBox(self.tr("Afficher le label près de la souris"))
        self.show_label_checkbox.setChecked(True)
        self.show_label_checkbox.stateChanged.connect(self.save_options)

        segment_basket_layout.addWidget(self.show_label_checkbox)
        segment_basket_group.setLayout(segment_basket_layout)

        layout.addWidget(segment_basket_group)

        # Développement
        dev_group = QGroupBox(self.tr("Développement"))
        dev_layout = QVBoxLayout()

        self.log_checkbox = QCheckBox(self.tr("Activer les logs dans la console python"))
        self.log_checkbox.setChecked(True)
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

    def load_options(self):
        settings = QSettings()

        show_label = settings.value(
            "routes_composer/ids_basket_label_hide",
            True,
            type=bool
        )
        self.show_label_checkbox.setChecked(show_label)

        log_checkbox = settings.value(
            "routes_composer/log",
            True,
            type=bool
        )
        self.log_checkbox.setChecked(log_checkbox)
        config.logging_enabled = log_checkbox
