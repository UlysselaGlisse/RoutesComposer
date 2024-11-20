"""Main dialog class. Dialog that's open when cliking on the icon."""
import os, gc
from typing import cast
from qgis.core import (
    Qgis,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QMessageBox,
    QProgressBar,
    QSpacerItem,
    QSizePolicy,
    QGridLayout
)
from qgis.PyQt.QtCore import (
    Qt,
    QSettings,
    QCoreApplication,
    QTranslator,
    QVariant
)
from qgis.utils import iface
from qgis.core import QgsProject
from . import config
from .attribute_linker import AttributeLinker
from .func import split
from .func.utils import get_features_list, log
from .func.warning import verify_segments, highlight_errors
from .func.geom_compo import GeomCompo
from .func import routes_composer
from .func import warning
from .ui.sub_dialog import InfoDialog, ErrorDialog

def show_dialog():
    dialog = RoutesComposerDialog(iface.mainWindow())
    dialog.show()
    return dialog

class RoutesComposerDialog(QDialog):
    """Dialogue principal"""
    def __init__(self, parent=None, tool=None):
        super().__init__(parent)
        self.tool = tool
        self.setWindowTitle(self.tr("Compositeur de Routes"))
        self.setMinimumWidth(400)
        self.initial_size = self.size()

        self.init_ui()
        self.load_settings()
        self.update_ui_state()
        self.translator = QTranslator()

    def load_styles(self):
        """Charge les styles à partir du fichier CSS."""
        with open(os.path.join(os.path.dirname(__file__),'ui', 'styles.css'), 'r') as f:
            return f.read()

    def init_ui(self):
        """Initialise l'interface utilisateur."""
        layout = QVBoxLayout()

        self.create_layer_configuration_group(layout)
        self.create_status_section(layout)
        self.create_control_buttons(layout)
        self.create_action_buttons(layout)

        self.create_advanced_options_group(layout)

        self.toggle_advanced_button_layout = QHBoxLayout()

        self.toggle_advanced_label = QLabel("Options avancées")
        self.toggle_advanced_arrow = QLabel("▶")
        self.toggle_advanced_arrow.setStyleSheet("cursor: pointer; margin-left: 2px;")

        self.toggle_advanced_label.mousePressEvent = lambda ev: self.toggle_advanced_options(ev)
        self.toggle_advanced_arrow.mousePressEvent = lambda ev: self.toggle_advanced_options(ev)

        self.toggle_advanced_button_layout.addWidget(self.toggle_advanced_label)
        self.toggle_advanced_button_layout.addWidget(self.toggle_advanced_arrow)

        self.toggle_advanced_button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(self.toggle_advanced_button_layout)

        self.advanced_options_container = QGroupBox()
        self.advanced_options_container.setLayout(QVBoxLayout())
        self.advanced_options_container.layout().addWidget(self.advanced_group)
        self.advanced_options_container.setVisible(False)

        layout.addWidget(self.advanced_options_container)
        self.setLayout(layout)

        stylesheet = self.load_styles()
        self.setStyleSheet(stylesheet)

        self.setup_signals()

    def create_layer_configuration_group(self, layout):
        """
        Groupe de sélection des couches, avertissement sur la géométrie des segments,
        et création en continue de la géométrie des compositions.
        """
        layers_group = QGroupBox(self.tr("Configuration des couches"))
        layers_layout = QVBoxLayout()
        max_combo_width = 200

        segments_layout = QHBoxLayout()
        segments_layout.addWidget(QLabel(self.tr("Couche segments:")))
        self.segments_combo = QComboBox()
        self.populate_layers_combo(self.segments_combo)

        self.segments_combo.setMaximumWidth(max_combo_width)
        segments_layout.addWidget(self.segments_combo)

        segments_layout.addWidget(QLabel(self.tr("Colonne id:")))
        self.id_column_combo = QComboBox()
        segments_layout.addWidget(self.id_column_combo)
        self.id_column_combo.setMaximumWidth(max_combo_width)

        self.segments_warning_label = QLabel()
        self.segments_warning_label.setStyleSheet("color: red;")
        self.segments_warning_label.setVisible(False)

        layers_layout.addLayout(segments_layout)
        layers_layout.addWidget(self.segments_warning_label)

        self.id_column_combo.setMaximumWidth(max_combo_width)
        layers_layout.addLayout(segments_layout)


        compositions_layout = QHBoxLayout()
        compositions_layout.addWidget(QLabel(self.tr("Couche compositions:")))
        self.compositions_combo = QComboBox()
        self.populate_layers_combo(self.compositions_combo)

        self.compositions_combo.setMaximumWidth(max_combo_width)
        compositions_layout.addWidget(self.compositions_combo)


        self.segments_column_combo = QComboBox()
        compositions_layout.addWidget(QLabel(self.tr("Liste:")))
        compositions_layout.addWidget(self.segments_column_combo)

        self.segments_column_combo.setMaximumWidth(max_combo_width)
        layers_layout.addLayout(compositions_layout)

        self.column_warning_label = QLabel()
        self.column_warning_label.setStyleSheet("color: red;")
        self.column_warning_label.setVisible(False)

        layers_layout.addWidget(self.column_warning_label)

        self.geom_checkbox = QCheckBox(self.tr("Activer la création géométrique en continue"))
        self.geom_checkbox.setVisible(False)
        settings = QSettings()
        geom_on_fly = settings.value("routes_composer/geom_on_fly", True, type=bool)
        self.geom_checkbox.setChecked(geom_on_fly)
        self.geom_checkbox.stateChanged.connect(self.on_geom_on_fly_check)

        layers_layout.addLayout(compositions_layout)
        layers_layout.addWidget(self.geom_checkbox)

        layers_group.setLayout(layers_layout)
        layout.addWidget(layers_group)

    def create_status_section(self, layout):
        self.status_label = QLabel(self.tr("Status: Arrêté"))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def create_control_buttons(self, layout):
        """Boutons pour démarrer/arrêter le suivi, info et auto-start."""
        buttons_layout = QHBoxLayout()

        self.start_button = QPushButton(self.tr("Démarrer"))
        self.start_button.setProperty("class", "start-button")
        self.start_button.clicked.connect(self.toggle_script)
        buttons_layout.addWidget(self.start_button)

        info_button = QPushButton(self.tr("Info"))
        info_button.setProperty("class", "info-button")
        info_button.clicked.connect(self.show_info)
        buttons_layout.addWidget(info_button)

        layout.addLayout(buttons_layout)

        self.auto_start_checkbox = QCheckBox(self.tr("Démarrer automatiquement au lancement du projet"))
        settings = QSettings()
        auto_start = settings.value("routes_composer/auto_start", True, type=bool)
        self.auto_start_checkbox.setChecked(auto_start)
        self.auto_start_checkbox.stateChanged.connect(self.on_auto_start_check)
        layout.addWidget(self.auto_start_checkbox)

    def create_action_buttons(self, layout):
        """Boutons pour vérifier les compositions et créer les géométries."""
        action_buttons_layout = QHBoxLayout()

        check_errors_button = QPushButton(self.tr("Vérifier les compositions"))
        check_errors_button.setProperty("class", "action-button")
        check_errors_button.clicked.connect(self.check_errors)
        action_buttons_layout.addWidget(check_errors_button)

        self.create_or_update_geom_button = QPushButton(self.tr("Créer les géométries"))
        self.create_or_update_geom_button.setProperty("class", "action-button")
        self.create_or_update_geom_button.clicked.connect(self.create_geometries)
        action_buttons_layout.addWidget(self.create_or_update_geom_button)

        layout.addLayout(action_buttons_layout)

        self.cancel_button = QPushButton(self.tr("Annuler"))
        self.cancel_button.setProperty("class", "cancel-button")
        self.cancel_button.clicked.connect(self.cancel_process)
        self.cancel_button.setVisible(False)
        action_buttons_layout.addWidget(self.cancel_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def create_advanced_options_group(self, layout):
        """Crée la section des options avancées."""
        self.advanced_group = QGroupBox(self.tr("Lier les attributs de deux couches:"))
        advanced_layout = QVBoxLayout()

        attributes_layout = QVBoxLayout()

        compositions_attr_layout = QHBoxLayout()
        compositions_attr_layout.addWidget(QLabel(self.tr("Attribut compositions:")))
        self.compositions_attr_combo = QComboBox()
        compositions_attr_layout.addWidget(self.compositions_attr_combo)
        attributes_layout.addLayout(compositions_attr_layout)

        segments_attr_layout = QHBoxLayout()
        segments_attr_layout.addWidget(QLabel(self.tr("Attribut segments:")))
        self.segments_attr_combo = QComboBox()
        segments_attr_layout.addWidget(self.segments_attr_combo)
        attributes_layout.addLayout(segments_attr_layout)

        priority_mode_layout = QHBoxLayout()
        priority_mode_layout.addWidget(QLabel(self.tr("Priorité:")))
        self.priority_mode_combo = QComboBox()
        self.priority_mode_combo.addItems([
            self.tr("none"),
            self.tr("min_value"),
            self.tr("max_value")
        ])
        priority_mode_layout.addWidget(self.priority_mode_combo)
        attributes_layout.addLayout(priority_mode_layout)

        advanced_layout.addLayout(attributes_layout)

        self.update_attributes_button = QPushButton(self.tr("Mettre à jour les attributs"))
        self.update_attributes_button.setProperty("class", "update-button")
        self.update_attributes_button.clicked.connect(self.start_attribute_linking)
        advanced_layout.addWidget(self.update_attributes_button)

        self.advanced_group.setLayout(advanced_layout)


    def load_settings(self):
        project = QgsProject.instance()
        if project:
            auto_start, _ = project.readBoolEntry("routes_composer", "auto_start", False)
            self.auto_start_checkbox.setChecked(auto_start)

            geom_on_fly, _ = project.readBoolEntry("routes_composer", "geom_on_fly", False)
            self.geom_checkbox.setChecked(geom_on_fly)

            settings = QSettings()
            segments_layer_id = settings.value("routes_composer/segments_layer_id", "")
            compositions_layer_id = settings.value("routes_composer/compositions_layer_id", "")
            saved_column = settings.value("routes_composer/segments_column_name", "segments")
            saved_id_column = settings.value("routes_composer/id_column_name", "")
            saved_segments_attr = settings.value("routes_composer/segments_attr_name", "")
            saved_compositions_attr = settings.value("routes_composer/compositions_attr_name", "")
            saved_priority_mode = settings.value("routes_composer/priority_mode", "aucune")


            segments_index = self.segments_combo.findData(segments_layer_id)
            compositions_index = self.compositions_combo.findData(compositions_layer_id)

            if segments_index >= 0:
                self.segments_combo.setCurrentIndex(segments_index)
            if compositions_index >= 0:
                self.compositions_combo.setCurrentIndex(compositions_index)
            if hasattr(self, 'segments_column_combo'):
                index = self.segments_column_combo.findText(saved_column)
                if index >= 0:
                    self.segments_column_combo.setCurrentIndex(index)

            if hasattr(self, 'id_column_combo'):
                id_index = self.id_column_combo.findText(saved_id_column)
                if id_index >= 0:
                    self.id_column_combo.setCurrentIndex(id_index)

            if hasattr(self, 'segments_attr_combo'):
                segments_attr_index = self.segments_attr_combo.findText(saved_segments_attr)
                if segments_attr_index >= 0:
                    self.segments_attr_combo.setCurrentIndex(segments_attr_index)

            if hasattr(self, 'compositions_attr_combo'):
                compositions_attr_index = self.compositions_attr_combo.findText(saved_compositions_attr)
                if compositions_attr_index >= 0:
                    self.compositions_attr_combo.setCurrentIndex(compositions_attr_index)

            self.priority_mode_combo.setCurrentText(saved_priority_mode)

    def setup_signals(self):
        self.segments_combo.currentIndexChanged.connect(self.on_layer_selected)
        self.compositions_combo.currentIndexChanged.connect(self.on_layer_selected)
        self.segments_column_combo.currentTextChanged.connect(self.on_column_selected)
        self.id_column_combo.currentTextChanged.connect(self.on_id_column_selected)
        self.segments_attr_combo.currentTextChanged.connect(self.on_segments_attr_selected)
        self.compositions_attr_combo.currentTextChanged.connect(self.on_compositions_attr_selected)
        self.priority_mode_combo.currentTextChanged.connect(self.on_priority_mode_selected)

    def toggle_script(self):
        """Démarre ou arrête le script."""
        try:
            print(f"is script_running: {config.script_running}")
            if not config.script_running:
                # Vérifier que les couches sont sélectionnées
                if not self.segments_combo.currentData() or not self.compositions_combo.currentData():
                    QMessageBox.warning(self, self.tr("Attention"), self.tr("Veuillez sélectionner les couches segments et compositions"))
                    return

                if not self.segments_column_combo.currentText():
                    QMessageBox.warning(self, self.tr("Attention"), self.tr("Veuillez sélectionner la colonne segments"))
                    return

                routes_composer.start_routes_composer()
                config.script_running = True
                if self.tool:
                    self.tool.update_icon()
            else:
                routes_composer.stop_routes_composer()
                config.script_running = False
                self.geom_checkbox.setChecked(False)
                if self.tool:
                    self.tool.update_icon()

            self.update_ui_state()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr(f"Une erreur est survenue: {str(e)}"))

    def update_ui_state(self):
        """Met à jour l'interface selon l'état du script."""
        if config.script_running is True:
            self.start_button.setText(self.tr("Arrêter"))
            self.status_label.setText(self.tr("Status: En cours d'exécution"))

        else:
            self.start_button.setText(self.tr("Démarrer"))
            self.status_label.setText(self.tr("Status: Arrêté"))

        self.start_button.setStyleSheet(self.get_start_button_style())

    def populate_layers_combo(self, combo):
        """Alimente les combos des couches."""
        combo.clear()
        project = QgsProject.instance()
        if project is not None:
            for layer in project.mapLayers().values():
                if isinstance(layer, QgsVectorLayer):
                    combo.addItem(layer.name(), layer.id())
                    data_provider = layer.dataProvider()

                    if data_provider is not None:
                        full_path = data_provider.dataSourceUri()
                        combo.setItemData(combo.count() - 1, full_path, Qt.ItemDataRole.ToolTipRole)
                    else:
                        combo.setItemData(combo.count() - 1, "Data provider not available", Qt.ItemDataRole.ToolTipRole)

    def populate_field_combo(self):
        """Alimente le combo des champs."""
        if not hasattr(self, 'segments_column_combo'):
            return

        self.segments_column_combo.clear()

        settings = QSettings()
        saved_column = settings.value("routes_composer/segments_column_name", "segments")

        if isinstance(self.selected_compositions_layer, QgsVectorLayer):
            field_names = [field.name() for field in self.selected_compositions_layer.fields()]
            self.segments_column_combo.addItems(field_names)

        index = self.segments_column_combo.findText(saved_column)
        if index >= 0:
            self.segments_column_combo.setCurrentIndex(index)

    def populate_id_fields_combo(self, segments_layer):
        """Remplit le combo avec les champs disponibles dans la couche segments."""
        self.id_column_combo.clear()
        field_names = [field.name() for field in segments_layer.fields()]
        self.id_column_combo.addItems(field_names)

    def on_layer_selected(self):
        """Méthode appelée quand une couche est sélectionnée dans les combobox."""
        segments_id = self.segments_combo.currentData()
        compositions_id = self.compositions_combo.currentData()

        project = QgsProject.instance()
        if project:
            # Vérification de la couche segments
            self.selected_segments_layer = project.mapLayer(segments_id)
            if self.selected_segments_layer:
                log(f"Segments layer selected: {self.selected_segments_layer.name()}")
                # Si la couche segment n'a pas de géométrie on renvoit une erreur.'
                if not self.selected_segments_layer.isSpatial():
                    self.segments_warning_label.setText(self.tr("Attention: la couche des segments n'a pas de géométrie"))
                    self.segments_warning_label.setVisible(True)
                else:
                    self.segments_warning_label.setVisible(False)

                self.populate_id_fields_combo(self.selected_segments_layer)

            # Vérification de la couche compositions
            self.selected_compositions_layer = project.mapLayer(compositions_id)
            if self.selected_compositions_layer:
                log(f"Compositions layer selected: {self.selected_compositions_layer.name()}")
                # Si la couche compositions a une géométrie, on propose le suivi de la géométrie en continue et on change pour Mettre à jour.
                if isinstance(self.selected_compositions_layer, QgsVectorLayer) and self.selected_compositions_layer.isSpatial():
                    self.geom_checkbox.setVisible(True)

                    self.create_or_update_geom_button.setText(self.tr("Mettre à jour les géométries"))
                    self.create_or_update_geom_button.clicked.disconnect()
                    self.create_or_update_geom_button.clicked.connect(self.update_geometries)
                else:
                    self.geom_checkbox.setVisible(False)
                    self.create_or_update_geom_button.setText(self.tr("Créer les géométries"))
                    self.create_or_update_geom_button.clicked.disconnect()
                    self.create_or_update_geom_button.clicked.connect(self.create_geometries)

            if isinstance(self.selected_compositions_layer, QgsVectorLayer):
                self.populate_field_combo()

            settings = QSettings()
            settings.setValue("routes_composer/segments_layer_id", segments_id)
            settings.setValue("routes_composer/compositions_layer_id", compositions_id)

        self.update_attr_combos()
        self.adjustSize()

    def on_column_selected(self):
        """Méthode appelée quand une colonne est sélectionnée."""
        if self.segments_column_combo.currentText():
            selected_column = self.segments_column_combo.currentText()

            if isinstance(self.selected_compositions_layer, QgsVectorLayer):
                fields = self.selected_compositions_layer.fields()
                field_index = fields.indexOf(selected_column)

                if field_index != -1:
                    field = fields.at(field_index)
                    # On vérifie si le champ des listes est de type string.
                    if field.type() != QVariant.String:
                        self.column_warning_label.setText(self.tr("Attention: la colonne segments n'est pas de type texte"))
                        self.column_warning_label.setVisible(True)
                    else:
                        self.column_warning_label.setVisible(False)

                    segments_column_index = field_index
                    settings = QSettings()
                    settings.setValue("routes_composer/segments_column_name", selected_column)

                    log(f"Column of lists of segments selected: {selected_column}")

    def on_id_column_selected(self):
        """Méthode appelée quand une colonne ID est sélectionnée."""
        selected_id_column = self.id_column_combo.currentText()

        if selected_id_column:
            settings = QSettings()
            settings.setValue("routes_composer/id_column_name", selected_id_column)

            log(f"ID column selected: {selected_id_column}")

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

    def toggle_advanced_options(self, event):
        """Affiche ou masque les options avancées."""
        is_visible = self.advanced_options_container.isVisible()
        self.advanced_options_container.setVisible(not is_visible)

        # Change le texte de la flèche en fonction de la visibilité
        if is_visible:
            self.toggle_advanced_arrow.setText("▶")  # Flèche vers la droite
        else:
            self.toggle_advanced_arrow.setText("▼")
        self.adjustSize()


    def on_segments_attr_selected(self):
        """Méthode appelée quand un attribut segments est sélectionné."""
        if self.segments_attr_combo.currentText():
            selected_segments_attr = self.segments_attr_combo.currentText()
            settings = QSettings()
            settings.setValue("routes_composer/segments_attr_name", selected_segments_attr)
            log(f"Segments attribute selected: {selected_segments_attr}")

            # Vérification du type de champ
            field_index = self.selected_segments_layer.fields().indexOf(selected_segments_attr)
            if field_index != -1:
                field_type = self.selected_segments_layer.fields().at(field_index).type()
                if field_type == QVariant.String:  # Type de champ texte
                    self.priority_mode_combo.setCurrentText(self.tr("none"))

    def on_compositions_attr_selected(self):
        """Méthode appelée quand un attribut compositions est sélectionné."""
        if self.compositions_attr_combo.currentText():
            selected_compositions_attr = self.compositions_attr_combo.currentText()
            settings = QSettings()
            settings.setValue("routes_composer/compositions_attr_name", selected_compositions_attr)
            log(f"Compositions attribute selected: {selected_compositions_attr}")

            # Vérification du type de champ
            field_index = self.selected_compositions_layer.fields().indexOf(selected_compositions_attr)
            if field_index != -1:
                field_type = self.selected_compositions_layer.fields().at(field_index).type()
                if field_type == QVariant.String:  # Type de champ texte
                    self.priority_mode_combo.setCurrentText(self.tr("none"))

    def on_priority_mode_selected(self):
        """Méthode appelée quand un mode de priorité est sélectionné."""
        selected_priority_mode = self.priority_mode_combo.currentText()
        settings = QSettings()
        settings.setValue("routes_composer/priority_mode", selected_priority_mode)
        log(f"Priority mode selected: {selected_priority_mode}")

    def update_attr_combos(self):
        """Met à jour les combos des attributs."""
        if not self.selected_segments_layer or not self.selected_compositions_layer:
            return

        self.segments_attr_combo.clear()
        self.compositions_attr_combo.clear()

        for field in self.selected_segments_layer.fields():
            self.segments_attr_combo.addItem(field.name())

        for field in self.selected_compositions_layer.fields():
            self.compositions_attr_combo.addItem(field.name())

    def start_attribute_linking(self):
        """Démarre la liaison des attributs."""
        if not self.segments_attr_combo.currentText() or not self.compositions_attr_combo.currentText():
            return

        segments_layer = cast(QgsVectorLayer, self.selected_segments_layer)
        compositions_layer = cast(QgsVectorLayer, self.selected_compositions_layer)
        segments_column_name = self.segments_column_combo.currentText()
        id_column_name = self.id_column_combo.currentText()
        segments_attr=self.segments_attr_combo.currentText()
        compositions_attr=self.compositions_attr_combo.currentText()
        priority_mode=self.priority_mode_combo.currentText().lower()

        self.attribute_linker = AttributeLinker(
            segments_layer=segments_layer,
            compositions_layer=compositions_layer,
            segments_attr=segments_attr,
            compositions_attr=compositions_attr,
            id_column_name=id_column_name,
            segments_column_name=segments_column_name,
            priority_mode=priority_mode
        )
        self.attribute_linker.update_segments_attr_values()

    def stop_attribute_linking(self):
        """UNUSE. Arrête la liaison des attributs."""
        if hasattr(self, 'attribute_linker'):
            self.attribute_linker.stop()

    def check_errors(self):
        """Vérifie les erreurs de compositions."""
        if not self.segments_combo.currentData() or not self.compositions_combo.currentData():
            QMessageBox.warning(self, self.tr("Attention"), self.tr("Veuillez sélectionner les couches segments et compositions"))
            return

        segments_layer = self.selected_segments_layer
        compositions_layer = self.selected_compositions_layer
        segments_column_name = self.segments_column_combo.currentText()
        id_column_name = self.id_column_combo.currentText()

        errors = verify_segments(segments_layer, compositions_layer, segments_column_name, id_column_name)

        if errors:
            # highlight_errors(errors, segments_layer)
            self.close()
            error_dialog = ErrorDialog(errors, segments_layer, id_column_name, compositions_layer, segments_column_name, self)
            error_dialog.show()
        else:
            QMessageBox.information(self, self.tr("Aucune erreur"), self.tr("Aucune erreur détectée."))

    def create_geometries(self):
        """Crée la géométries des compositions."""
        if not self.segments_combo.currentData() or not self.compositions_combo.currentData():
            QMessageBox.warning(self, self.tr("Attention"), self.tr("Veuillez sélectionner les couches segments et compositions"))
            return

        segments_layer = cast(QgsVectorLayer, self.selected_segments_layer)
        compositions_layer = cast(QgsVectorLayer, self.selected_compositions_layer)
        segments_column_name = self.segments_column_combo.currentText()
        id_column_name = self.id_column_combo.currentText()

        if segments_column_name not in compositions_layer.fields().names():
            iface.messageBar().pushWarning(
                self.tr("Erreur"),
                self.tr("Le champ {ss} n'existe pas dans la couche des compositions.").format(ss=self.segments_column_name)
            )
            return

        # Afficher la barre de progression
        self.progress_bar.setVisible(True)
        self.progress_bar.setMinimum(0)
        total_compositions = sum(1 for _ in get_features_list(compositions_layer))
        self.progress_bar.setMaximum(total_compositions)

        config.cancel_request = False
        self.cancel_button.setVisible(True)
        self.cancel_button.setEnabled(True)


        a = GeomCompo(segments_layer, compositions_layer, segments_column_name, id_column_name)
        errors_messages = a.create_compositions_geometries(self.progress_bar)

        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)

        if errors_messages:
            print(errors_messages)
            error_dialog = ErrorDialog(errors_messages, segments_layer, id_column_name, compositions_layer, segments_column_name, self)
            error_dialog.show()

        self.adjustSize()

    def update_geometries(self):
        """Met à jour les géométries des compositions existantes."""
        if not self.segments_combo.currentData() or not self.compositions_combo.currentData():
            QMessageBox.warning(self, self.tr("Attention"), self.tr("Veuillez sélectionner les couches segments et compositions"))
            return

        segments_layer = cast(QgsVectorLayer, self.selected_segments_layer)
        compositions_layer = cast(QgsVectorLayer, self.selected_compositions_layer)
        segments_column_name = self.segments_column_combo.currentText()
        id_column_name = self.id_column_combo.currentText()

        if segments_column_name not in compositions_layer.fields().names():
            iface.messageBar().pushWarning(
                self.tr("Erreur"),
                self.tr("Le champ {segments_column_name} n'existe pas dans la couche des compositions.").format(segments_column_name=segments_column_name)
            )
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setMinimum(0)
        total_compositions = sum(1 for _ in get_features_list(compositions_layer))
        self.progress_bar.setMaximum(total_compositions)

        config.cancel_request = False
        self.cancel_button.setVisible(True)
        self.cancel_button.setEnabled(True)

        a = GeomCompo(segments_layer, compositions_layer, segments_column_name, id_column_name)
        errors_messages = a.update_compositions_geometries(self.progress_bar)

        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)

        if errors_messages:
            error_dialog = ErrorDialog(errors_messages, segments_layer, id_column_name, compositions_layer, segments_column_name, self)
            error_dialog.show()

        self.adjustSize()

    def cancel_process(self):
        """Annule le processus de création des géométries."""
        config.cancel_request = True
        self.cancel_button.setEnabled(False)
        iface.messageBar().pushMessage("Info", self.tr("Annulation en cours..."), level=Qgis.MessageLevel.Info)
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.resize(self.initial_size)
        self.adjustSize()

    def show_info(self):
        info_dialog = InfoDialog(self)
        info_dialog.exec_()

    def closeEvent(self, a0):
        if a0:
            a0.accept()

    def on_auto_start_check(self, state):
        """Enregistre l'état de la checkbox d'auto-start"""
        project = QgsProject.instance()
        if project is not None:
            project.writeEntry("routes_composer", "auto_start", bool(state))
            project.setDirty(True)

    def on_geom_on_fly_check(self, state):
        """
        Démarre la création en continue de la géométrie des compositions,
        enregistre l'état dans le projet.

        Args:
        state : bool
        État de la checkbox. - True si cochée
        """
        project = QgsProject.instance()
        if project is not None:
            project.writeEntry("routes_composer", "geom_on_fly", bool(state))
            project.setDirty(True)
            geom_on_fly = bool(state)
            log(f"config state of geom_on_fly = {geom_on_fly}")
            if geom_on_fly:
                success = routes_composer.start_geom_on_fly()
                if success:
                    config.geom_on_fly_running = True
            if not geom_on_fly:
                success = routes_composer.stop_geom_on_fly()
                if success:
                    config.geom_on_fly_running = False
