"""Construct ui for main dialog"""

from qgis.PyQt.QtCore import QObject, Qt
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from ... import config
from ...func.utils import log


class UiBuilder(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

    def init_ui(self):

        layout = QVBoxLayout()

        self.create_layer_configuration_group(layout)
        self.create_status_section(layout)
        self.create_control_buttons(layout)
        self.create_action_buttons(layout)
        self.create_advanced_options_toggle(layout)

        self.dialog.setLayout(layout)
        self.dialog.setStyleSheet(self.dialog.load_styles())

    def create_layer_configuration_group(self, layout):

        layers_group = QGroupBox(self.tr("Configuration des couches"))
        layers_layout = QVBoxLayout()
        max_combo_width = 200

        segments_layout = QHBoxLayout()
        segments_layout.addWidget(QLabel(self.tr("Couche segments:")))
        self.segments_combo = QComboBox()

        self.segments_combo.setMaximumWidth(max_combo_width)
        segments_layout.addWidget(self.segments_combo)

        segments_layout.addWidget(QLabel(self.tr("Colonne id:")))
        self.id_column_combo = QComboBox()
        segments_layout.addWidget(self.id_column_combo)
        self.id_column_combo.setMaximumWidth(max_combo_width)

        layers_layout.addLayout(segments_layout)

        self.segments_warning_label = QLabel()
        self.segments_warning_label.setStyleSheet("color: red;")
        self.segments_warning_label.setVisible(False)
        layers_layout.addWidget(self.segments_warning_label)

        compositions_layout = QHBoxLayout()
        compositions_layout.addWidget(QLabel(self.tr("Couche compositions:")))
        self.compositions_combo = QComboBox()

        self.compositions_combo.setMaximumWidth(max_combo_width)
        compositions_layout.addWidget(self.compositions_combo)

        self.segments_column_combo = QComboBox()
        compositions_layout.addWidget(QLabel(self.tr("Liste:")))
        compositions_layout.addWidget(self.segments_column_combo)
        self.segments_column_combo.setMaximumWidth(max_combo_width)

        layers_layout.addLayout(compositions_layout)

        self.geom_checkbox = QCheckBox(
            self.tr("Activer la création géométrique en continue")
        )
        self.geom_checkbox.setVisible(False)
        self.geom_checkbox.stateChanged.connect(
            self.dialog.event_handlers.on_geom_on_fly_check
        )

        layers_layout.addWidget(self.geom_checkbox)
        layers_group.setLayout(layers_layout)
        layout.addWidget(layers_group)

    def create_status_section(self, layout):

        self.status_label = QLabel(self.tr("Status: Arrêté"))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def create_control_buttons(self, layout):

        buttons_layout = QHBoxLayout()

        self.start_button = QPushButton(self.tr("Démarrer"))
        self.start_button.setProperty("class", "start-button")
        self.start_button.clicked.connect(
            self.dialog.event_handlers.toggle_script
        )
        buttons_layout.addWidget(self.start_button)

        info_button = QPushButton(self.tr("Info"))
        info_button.setProperty("class", "info-button")
        info_button.clicked.connect(self.dialog.event_handlers.show_info)
        buttons_layout.addWidget(info_button)

        layout.addLayout(buttons_layout)

        self.auto_start_checkbox = QCheckBox(
            self.tr("Démarrer automatiquement au lancement du projet")
        )
        self.auto_start_checkbox.stateChanged.connect(
            self.dialog.event_handlers.on_auto_start_check
        )
        layout.addWidget(self.auto_start_checkbox)

    def create_action_buttons(self, layout):

        action_buttons_layout = QHBoxLayout()

        check_errors_button = QPushButton(
            self.tr("Vérifier les compositions")
        )
        check_errors_button.setProperty("class", "action-button")
        check_errors_button.clicked.connect(
            self.dialog.geometry_ops.check_errors
        )
        action_buttons_layout.addWidget(check_errors_button)

        self.create_or_update_geom_button = QPushButton(
            self.tr("Créer les géométries")
        )
        self.create_or_update_geom_button.setProperty(
            "class", "action-button"
        )
        self.create_or_update_geom_button.clicked.connect(
            self.dialog.geometry_ops.create_geometries
        )
        action_buttons_layout.addWidget(self.create_or_update_geom_button)

        layout.addLayout(action_buttons_layout)

        self.cancel_button = QPushButton(self.tr("Annuler"))
        self.cancel_button.setProperty("class", "cancel-button")
        self.cancel_button.clicked.connect(
            self.dialog.event_handlers.cancel_process
        )
        self.cancel_button.setVisible(False)
        action_buttons_layout.addWidget(self.cancel_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def create_advanced_options_toggle(self, layout):

        self.toggle_advanced_button_layout = QHBoxLayout()
        self.toggle_advanced_label = QLabel(self.tr("Options avancées"))
        self.toggle_advanced_arrow = QLabel("▶")
        self.toggle_advanced_arrow.setStyleSheet(
            "cursor: pointer; margin-left: 2px;"
        )

        self.toggle_advanced_label.mousePressEvent = (
            lambda ev: self.toggle_advanced_options(ev)
        )
        self.toggle_advanced_arrow.mousePressEvent = (
            lambda ev: self.toggle_advanced_options(ev)
        )

        self.toggle_advanced_button_layout.addWidget(
            self.toggle_advanced_label
        )
        self.toggle_advanced_button_layout.addWidget(
            self.toggle_advanced_arrow
        )
        self.toggle_advanced_button_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft
        )

        layout.addLayout(self.toggle_advanced_button_layout)

        self.create_advanced_options_container()
        layout.addWidget(self.advanced_options_container)

    def create_advanced_options_container(self):

        self.advanced_options_container = QGroupBox()
        self.advanced_options_container.setLayout(QVBoxLayout())
        self.advanced_group = self.create_advanced_group()
        self.advanced_options_container.layout().addWidget(
            self.advanced_group
        )
        self.advanced_options_container.setVisible(False)

    def create_advanced_group(self):

        advanced_group = QGroupBox(
            self.tr("Lier les attributs de deux couches:")
        )
        advanced_layout = QVBoxLayout()

        self.compositions_attr_combo = QComboBox()
        self.segments_attr_combo = QComboBox()
        self.priority_mode_combo = self.create_priority_mode_combo()

        advanced_layout.addLayout(self.create_attributes_layout())
        self.update_attributes_button = QPushButton(
            self.tr("Mettre à jour les attributs")
        )
        self.update_attributes_button.setProperty("class", "update-button")
        self.update_attributes_button.clicked.connect(
            self.dialog.advanced_options.start_attribute_linking
        )
        advanced_layout.addWidget(self.update_attributes_button)

        advanced_group.setLayout(advanced_layout)
        return advanced_group

    def create_attributes_layout(self):

        attributes_layout = QVBoxLayout()

        compositions_attr_layout = QHBoxLayout()
        compositions_attr_layout.addWidget(
            QLabel(self.tr("Attribut compositions:"))
        )
        compositions_attr_layout.addWidget(self.compositions_attr_combo)
        attributes_layout.addLayout(compositions_attr_layout)

        segments_attr_layout = QHBoxLayout()
        segments_attr_layout.addWidget(QLabel(self.tr("Attribut segments:")))
        segments_attr_layout.addWidget(self.segments_attr_combo)
        attributes_layout.addLayout(segments_attr_layout)

        priority_mode_layout = QHBoxLayout()
        priority_mode_layout.addWidget(QLabel(self.tr("Priorité:")))
        priority_mode_layout.addWidget(self.priority_mode_combo)
        attributes_layout.addLayout(priority_mode_layout)

        return attributes_layout

    def create_priority_mode_combo(self):

        combo = QComboBox()
        combo.addItems(
            [self.tr("none"), self.tr("min_value"), self.tr("max_value")]
        )
        return combo

    def toggle_advanced_options(self, event):

        self.advanced_options_container.setVisible(
            not self.advanced_options_container.isVisible()
        )
        arrow_text = (
            "▼" if self.advanced_options_container.isVisible() else "▶"
        )
        self.toggle_advanced_arrow.setText(arrow_text)

        self.dialog.adjustSize()

    def get_start_button_style(self):
        # TODO: Mettre le css dans le fichier styles, je n'y suis pas arrivé pour l'instant.
        if not config.script_running:
            return """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #9e9e9e;
                    color: white;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #757575;
                }
            """
