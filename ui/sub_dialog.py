from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            self.tr("Informations sur le Gestionnaire de réseaux")
        )

        info_text = self.tr(
            """
        <b>Gestionnaire de compositions de segments</b><br><br>
        Ce plugin apporte une assistance dans la réalisation de compositions de segments.<br><br>
        <i>Instructions :</i><br>
        <ol>
            <li><b>Sélectionnez les couches :</b><br />
                - Une couche segments avec un champ 'id' qui sera utilisé pour faire vos compositions.<br />
                - Une couche compositions avec un champ dans lequel vous entrez les listes de segments (sans espaces et séparées par une virgule, par exemple 1,2,3).</li>
            <li><b>Panier à segments :</b><br />
                Cliquez sur l'icône, une petite bulle apparaîtra à droite du curseur. Sélectionnez les segments qui vous intéressent. La liste se remplira.<br />
                L'outil cherchera toujours à combler les trous entre deux segments.<br />
                Vous pouvez appuyer sur <b>z</b> pour retirer le dernier segment ajouté à la liste et sur <b>e</b> pour le rétablir.</li>
        </ol>
        """
        )

        layout = QVBoxLayout()
        layout.addWidget(QLabel(info_text))
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

        warning_label = QLabel(
            self.tr(
                "Attention, composition d'un seul segment. "
                "Veuillez vérifier que la nouvelle composition est bonne."
            )
        )
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
        self.proposal_label.setText(
            self.tr("Nouvelle composition proposée: {cs}").format(
                cs=self.current_segments
            )
        )

    def invert_order(self):
        self.current_segments.reverse()
        self.update_proposal_label()
