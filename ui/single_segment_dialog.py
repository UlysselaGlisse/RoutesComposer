from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


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
