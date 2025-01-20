"""Construct ui for main dialog"""
import os

from qgis.PyQt.QtCore import QObject, QSettings, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from ...main_events_handler import MainEventsHandlers
from ...func.utils import log


class UiBuilder(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.create_header_layout(main_layout)

        self.create_layer_configuration_group(main_layout)
        self.create_status_section(main_layout)
        self.create_control_buttons(main_layout)
        self.create_action_buttons(main_layout)
        self.create_advanced_options_toggle(main_layout)

        self.dialog.setLayout(main_layout)
        self.dialog.setStyleSheet(self.dialog.load_styles())

    def create_header_layout(self, layout):
        header_layout = QHBoxLayout()

        self.configuration_label = QLabel(self.tr("Configuration des couches"))
        self.configuration_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.configuration_label, alignment=Qt.AlignmentFlag.AlignLeft)

        # Create settings button
        header_layout.addStretch()

        self.settings_button = QToolButton()
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "icon_gear.png")
        self.settings_button.setIcon(QIcon(icon_path))
        self.settings_button.setToolTip(self.tr("Réglages et configurations"))

        header_layout.addWidget(self.settings_button)

        layout.addLayout(header_layout)

    def create_layer_configuration_group(self, layout):
        layers_group = QGroupBox()
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
        compositions_layout.addWidget(QLabel(self.tr("Liste d'ids:")))
        compositions_layout.addWidget(self.segments_column_combo)
        self.segments_column_combo.setMaximumWidth(max_combo_width)

        layers_layout.addLayout(compositions_layout)

        self.compositions_warning_label = QLabel()
        self.compositions_warning_label.setStyleSheet("color: red;")
        self.compositions_warning_label.setVisible(False)
        layers_layout.addWidget(self.compositions_warning_label)

        self.geom_checkbox = QCheckBox(
            self.tr("Activer la création géométrique en continue")
        )
        self.geom_checkbox.setVisible(False)

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

        buttons_layout.addWidget(self.start_button)

        self.info_button = QPushButton(self.tr("Info"))
        self.info_button.setProperty("class", "info-button")

        buttons_layout.addWidget(self.info_button)

        layout.addLayout(buttons_layout)

        self.auto_start_checkbox = QCheckBox(
            self.tr("Démarrer automatiquement au lancement du projet")
        )

        layout.addWidget(self.auto_start_checkbox)

    def create_action_buttons(self, layout):
        action_buttons_layout = QHBoxLayout()

        self.check_errors_button = QPushButton(self.tr("Vérifier les compositions"))
        self.check_errors_button.setProperty("class", "action-button")

        action_buttons_layout.addWidget(self.check_errors_button)

        self.create_or_update_geom_button = QPushButton(self.tr("Créer les géométries"))
        self.create_or_update_geom_button.setProperty("class", "action-button")

        action_buttons_layout.addWidget(self.create_or_update_geom_button)

        layout.addLayout(action_buttons_layout)

        progress_layout = QHBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        self.cancel_button = QPushButton(self.tr("Annuler"))
        self.cancel_button.setProperty("class", "cancel-button")

        self.cancel_button.setVisible(False)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.cancel_button)

        layout.addLayout(progress_layout)

    def create_advanced_options_toggle(self, layout):
        self.toggle_advanced_button_layout = QHBoxLayout()
        self.toggle_advanced_label = QLabel(self.tr("Options avancées"))
        self.toggle_advanced_arrow = QLabel("▶")
        self.toggle_advanced_arrow.setStyleSheet("cursor: pointer; margin-left: 2px;")

        self.toggle_advanced_label.mousePressEvent = (
            lambda ev: self.toggle_advanced_options(ev)
        )
        self.toggle_advanced_arrow.mousePressEvent = (
            lambda ev: self.toggle_advanced_options(ev)
        )

        self.toggle_advanced_button_layout.addWidget(self.toggle_advanced_label)
        self.toggle_advanced_button_layout.addWidget(self.toggle_advanced_arrow)
        self.toggle_advanced_button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(self.toggle_advanced_button_layout)

        self.create_advanced_options_container()
        layout.addWidget(self.advanced_options_container)

    def create_advanced_options_container(self):
        self.advanced_options_container = QGroupBox()
        self.advanced_options_container.setLayout(QVBoxLayout())
        self.advanced_group = self.create_advanced_group()
        self.advanced_options_container.layout().addWidget(  # type: ignore
            self.advanced_group
        )

        self.belonging_group = self.create_belonging_group()
        self.advanced_options_container.layout().addWidget(self.belonging_group)

        self.advanced_options_container.setVisible(False)

    def create_advanced_group(self):
        advanced_group = QGroupBox(self.tr("Lier les attributs de deux couches:"))
        advanced_group.setToolTip(
            self.tr(
                "Permet de donner la valeur de l'attribut de la composition aux segments qu'elle contient.<br><br>"
                "<strong>Exemple :</strong><br>"
                "Si la route composée des segments 1, 2 et 3 est de difficulté 8, "
                "alors l'attribut 'difficulté' des segments "
                "1, 2 et 3 sera mis à jour pour devenir 8."
            )
        )
        button_layout = QHBoxLayout()
        self.linked_layout = QVBoxLayout()

        self.linked_layout_group = QGroupBox(self.tr("Liaisons enregistrées"))
        self.linked_layout_group.setLayout(self.linked_layout)
        self.linked_layout_group.setVisible(False)

        self.compositions_attr_combo = QComboBox()
        self.segments_attr_combo = QComboBox()
        self.priority_mode_combo = self.create_priority_mode_combo()

        advanced_layout = QVBoxLayout()
        advanced_layout.addLayout(self.create_attributes_layout())

        self.save_linkage_button = QPushButton(self.tr("Enregistrer la liaison"))
        self.save_linkage_button.setProperty("class", "action-button")
        self.save_linkage_button.clicked.connect(self.dialog.event_handlers.save_linkage)

        self.update_attributes_button = QPushButton(
            self.tr("Mettre à jour les attributs")
        )
        self.update_attributes_button.setProperty("class", "action-button")

        button_layout.addWidget(self.save_linkage_button)
        button_layout.addWidget(self.update_attributes_button)

        advanced_layout.addLayout(button_layout)
        advanced_layout.addWidget(self.linked_layout_group)

        advanced_group.setLayout(advanced_layout)


        return advanced_group

    def add_linkage_to_ui(self, linkage):
        linkage_layout = QHBoxLayout()

        label_text = (f"{self.compositions_combo.currentText()}: {linkage['compositions_attr']} -> "
                    f"{self.segments_combo.currentText()}: {linkage['segments_attr']} "
                    f"(priorité: {linkage['priority_mode']})")

        label = QLabel(label_text)
        delete_button = QPushButton("✖")
        delete_button.setFixedSize(20, 20)
        delete_button.clicked.connect(lambda: self.remove_linkage(linkage_layout, linkage))

        linkage_layout.addWidget(label)
        linkage_layout.addWidget(delete_button)

        self.linked_layout.addLayout(linkage_layout)
        self.linked_layout_group.setVisible(True)

        # # Connecter la liaison
        # main_events_handler = MainEventsHandlers()
        # main_events_handler.connect_attribute_linker(
        #     linkage['compositions_attr'],
        #     linkage['segments_attr'],
        #     linkage['priority_mode']
        # )

    def init_linkages(self):
        settings = QSettings()
        linkages = settings.value("routes_composer/attribute_linkages", []) or []

        for linkage in linkages:
            self.add_linkage_to_ui(linkage)

    def remove_linkage(self, layout, linkage):
        # Retirer la liaison des QSettings
        settings = QSettings()
        linkages = settings.value("routes_composer/attribute_linkages", [])
        linkages.remove(linkage)
        settings.setValue("routes_composer/attribute_linkages", linkages)

        # Nettoyer l'UI
        self.linked_layout.removeItem(layout)
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        layout.deleteLater()

        # # Déconnecter la liaison
        # main_events_handler = MainEventsHandlers()
        # main_events_handler.disconnect_attribute_linker(
        #     linkage['compositions_attr'],
        #     linkage['segments_attr'],
        #     linkage['priority_mode']
        # )

        if self.linked_layout.count() == 0:
            self.linked_layout_group.setVisible(False)

    def create_belonging_group(self):
        belonging_group = QGroupBox(self.tr("Appartenance des segments"))
        belonging_group.setToolTip(
            self.tr(
                "Crée un nouveau champ dans la couche des segments <br> avec l'id des compositions dans lequel chaque segment est utilisé."
            )
        )

        belonging_layout = QVBoxLayout()

        self.belonging_segments_button = QPushButton(
            self.tr("Créer/Mettre à jour le champ 'compositions' dans segments")
        )
        self.belonging_segments_button.setProperty("class", "action-button")
        belonging_layout.addWidget(self.belonging_segments_button)

        self.update_belonging_segments_checkbox = QCheckBox(
            self.tr("Mettre à jour le champ appartenance des segments en continue")
        )
        belonging_layout.addWidget(self.update_belonging_segments_checkbox)

        belonging_group.setLayout(belonging_layout)

        return belonging_group

    def create_attributes_layout(self):
        attributes_layout = QVBoxLayout()

        compositions_attr_layout = QHBoxLayout()
        compositions_attr_layout.addWidget(QLabel(self.tr("Attribut compositions:")))
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
        combo.addItems([self.tr("none"), self.tr("min_value"), self.tr("max_value")])
        combo.setToolTip(
            self.tr(
                "Sélectionnez le mode de priorité pour le lien des attributs.<br>"
                "<strong>Options disponibles:</strong><br>"
                "- <em>none</em>: Pas de priorité.<br>"
                "- <em>min_value</em>: Prioriser la valeur minimale.<br>"
                "- <em>max_value</em>: Prioriser la valeur maximale."
            )
        )
        return combo

    def toggle_advanced_options(self, event):
        self.advanced_options_container.setVisible(
            not self.advanced_options_container.isVisible()
        )
        arrow_text = "▼" if self.advanced_options_container.isVisible() else "▶"
        self.toggle_advanced_arrow.setText(arrow_text)

        self.dialog.adjustSize()

    def get_start_button_style(self):
        # TODO: Mettre le css dans le fichier styles css.
        if not MainEventsHandlers.routes_composer_connected:
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
